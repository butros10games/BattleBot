import websockets
import json
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            print("Connected to the WebSocket server.")
        except Exception as e:
            print(f"Failed to connect to WebSocket server: {e}")

    async def send_command(self, action, value):
        command = json.dumps({"action": action, "value": value})
        try:
            await self.websocket.send(command)
            response = await self.websocket.recv()
            # print(f"Server response: {response}")
        except Exception as e:
            print(f"Error sending command: {e}")


class WebRTCClient:
    def __init__(self, url):
        self.url = url
        self.pc = RTCPeerConnection()

    async def connect(self):
        async with websockets.connect(self.url) as ws:
            self.ws = ws
            await self.setup_data_channel()
            await self.create_and_send_offer()
            await self.receive_messages()

    async def setup_data_channel(self):
        self.data_channel = self.pc.createDataChannel("dataChannel")
        self.data_channel.on("open", lambda: print("Data Channel is open"))
        self.data_channel.on("message", lambda message: print(f"Message from Data Channel: {message}"))

    async def create_and_send_offer(self):
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        await self.ws.send(json.dumps({"sdp": self.pc.localDescription.sdp, "type": self.pc.localDescription.type}))

    async def receive_messages(self):
        async for message in self.ws:
            data = json.loads(message)
            if "sdp" in data:
                await self.handle_answer(data)
            elif "ice" in data:
                await self.handle_new_ice_candidate(data)

    async def handle_answer(self, data):
        print(f"Received answer: {data}")
        
        message_type = data["type"]
        if message_type == "answer":
            answer = RTCSessionDescription(sdp=data["sdp"], type=message_type)
            await self.pc.setRemoteDescription(answer)
        elif message_type == "offer":
            print("Unexpected offer received, ignoring.")
        else:
            print(f"Unknown message type: {message_type}")

    async def handle_new_ice_candidate(self, data):
        candidate = RTCIceCandidate(sdpMLineIndex=data["sdpMLineIndex"], candidate=data["candidate"])
        await self.pc.addIceCandidate(candidate)

    async def send_command(self, action, value):
        if hasattr(self, 'data_channel') and self.data_channel.readyState == "open":
            command = json.dumps({"action": action, "value": value})
            try:
                self.data_channel.send(command)
            except Exception as e:
                print(f"Error sending message: {e}")
        else:
            print("Data channel is not open or not set up yet.")

    async def close(self):
        await self.pc.close()
        await self.ws.close()