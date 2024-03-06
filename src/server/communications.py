import asyncio
import websockets
import json
import traceback
import socket

from aiortc import RTCPeerConnection, RTCSessionDescription

from .video import CameraStreamTrack, Camera

class MotorWebSocketServer:
    def __init__(self, motor_controller, host, port):
        self.motor_controller = motor_controller
        self.host = host
        self.port = port

    async def handle_client(self, websocket, path):
        async for message in websocket:
            try:
                command = json.loads(message)
                if 'action' in command and 'value' in command:
                    self.motor_controller.action(command['action'], command['value'])
                    await websocket.send(json.dumps({'status': 'success'}))
                else:
                    await websocket.send(json.dumps({'status': 'error', 'message': 'Invalid command format'}))
            except Exception as e:
                await websocket.send(json.dumps({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}))

        # Stop the motor controller when the connection is lost
        await self.motor_controller.stop()
    
    def print_server_info(self):
        # Determine the actual IP when the server is bound to '0.0.0.0'
        if self.host == "0.0.0.0":
            # Attempt to determine the "real" IP by connecting to a public DNS server
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))  # Google's DNS server
                    ip = s.getsockname()[0]
            except Exception:
                ip = "unable to determine IP"
            print(f"Server started at ws://{ip}:{self.port}")
        else:
            print(f"Server started at ws://{self.host}:{self.port}")

    def run(self):
        start_server = websockets.serve(self.handle_client, self.host, self.port)
        
        self.print_server_info()
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


class MotorWebRTCClient:
    def __init__(self, motor_controller, battlebot_name, camera_source):
        self.motor_controller = motor_controller
        self.battlebot_name = battlebot_name
        self.camera_source = camera_source  # Camera source for video streaming
        self.pc = RTCPeerConnection()
        self.websocket = None
        self.camera = Camera()
        self.data_channel = None  # Initialize data_channel attribute
        
        # Set up event listener for data channel as soon as the peer connection is created
        self.pc.on("datachannel", self.on_data_channel)

    async def connect_to_signal_server(self):
        self.ws_url = f"wss://butrosgroot.com/ws/battle_bot/signal/{self.battlebot_name}/"
        print(f"Connecting to signaling server at {self.ws_url}")
        self.websocket = await websockets.connect(self.ws_url)
        print("Connected to signaling server.")

    async def handle_signaling(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)

                if "sdp" in data:
                    await self.handle_sdp(data)
                elif "ice" in data:
                    await self.handle_ice(data)
        except Exception as e:
            print(f"Error in handle_signaling: {e}, {traceback.format_exc()}")

    async def handle_sdp(self, data):
        description = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
        await self.pc.setRemoteDescription(description)

        if description.type == "offer":
            # Check if a camera is available and add video track if it is
            if self.camera.is_camera_available():
                print("Camera found, adding video track.")
                self.camera.start()
                self.pc.addTrack(CameraStreamTrack(self.camera))
            else:
                print("No camera found, proceeding without video.")
            
            await self.pc.setLocalDescription(await self.pc.createAnswer())
            await self.websocket.send(json.dumps({"sdp": self.pc.localDescription.sdp, "type": self.pc.localDescription.type}))

    async def handle_ice(self, data):
        candidate = data["candidate"]
        await self.pc.addIceCandidate(candidate)

    async def on_data_channel(self, event):
        print("Data channel event triggered")
        self.data_channel = event
        self.data_channel.on("open", self.on_data_channel_open)
        self.data_channel.on("message", self.on_data_channel_message)
        self.pc.on("statechange", self.on_ice_connection_state_change)

    async def on_data_channel_open(self):
        print("Data Channel is open")

    async def on_data_channel_message(self, message):
        data = json.loads(message)
        if 'ping' in data:
            await self.send_data({'pong': data['ping']})
        if 'x' in data and 'y' in data and 'speed' in data:
            print(f"Received data: {data}")
            self.motor_controller.action(data['x'], data['y'], data['speed'])
            
    async def on_ice_connection_state_change(self, event=None):
        print(f"ICE connection state is {self.pc.iceConnectionState}")
        if self.pc.iceConnectionState in ["failed", "disconnected", "closed"]:
            self.motor_controller.stop()
            self.camera.stop()
            print("ICE connection lost, setting up for reconnect...")
            self.pc = RTCPeerConnection()
            self.pc.on("datachannel", self.on_data_channel)

    async def send_data(self, message):
        if self.data_channel and self.data_channel.readyState == "open":
            try:
                self.data_channel.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")
        else:
            print("Data channel is not open or not set up yet.")

    async def run(self):
        while True:
            try:
                await self.connect_to_signal_server()
                await self.handle_signaling()
            except Exception as e:
                print(f"Connection lost, error: {e}. Retrying...")
                await asyncio.sleep(5)