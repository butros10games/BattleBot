import asyncio
import websockets
import json
import traceback
import socket
from aiortc import RTCPeerConnection, RTCSessionDescription

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
    def __init__(self, motor_controller, battlebot_name):
        self.motor_controller = motor_controller
        self.battlebot_name = battlebot_name
        self.pc = RTCPeerConnection()

    async def connect_to_signal_server(self):
        self.ws_url = f"wss://butrosgroot.com/ws/battle_bot/signal/{self.battlebot_name}/"
        print(f"Connecting to signaling server at {self.ws_url}")
        async with websockets.connect(self.ws_url) as websocket:
            print("Connected to the signaling server")
            await self.handle_signaling(websocket)

    async def handle_signaling(self, websocket):
        try:
            async for message in websocket:
                data = json.loads(message)

                if "sdp" in data:
                    await self.handle_sdp(data, websocket)
                elif "ice" in data:
                    await self.handle_ice(data)
        except Exception as e:
            print(f"Error in handle_signaling: {e}")

    async def handle_sdp(self, data, websocket):
        description = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
        # Check signaling state before setting remote description
        if self.pc.signalingState == "stable" and description.type == "answer":
            print("Ignoring unexpected answer in stable state.")
            return
        await self.pc.setRemoteDescription(description)

        if description.type == "offer":
            await self.pc.setLocalDescription(await self.pc.createAnswer())
            await websocket.send(json.dumps({"sdp": self.pc.localDescription.sdp, "type": self.pc.localDescription.type}))
            self.pc.on("datachannel", self.on_data_channel)
        elif description.type == "answer":
            print("Unexpected answer received, ignoring.")
        else:
            print(f"Unknown message type: {description.type}")

    async def handle_ice(self, data):
        candidate = data["candidate"]
        await self.pc.addIceCandidate(candidate)

    async def on_data_channel(self, event):
        data_channel = event
        data_channel.on("open", self.on_data_channel_open)
        data_channel.on("message", self.on_data_channel_message)

    async def on_data_channel_open(self):
        print("Data Channel is open")

    async def on_data_channel_message(self, message):
        data = json.loads(message)
        print(f"Received data: {data}")
        if 'action' in data and 'value' in data:
            self.motor_controller.action(data['action'], data['value'])

    async def run(self):
        while True:
            try:
                await self.connect_to_signal_server()
            except Exception as e:
                print(f"Connection lost, error: {e}. Retrying...")
                await asyncio.sleep(5)