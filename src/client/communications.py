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
        self.data_channel.on("open", self.on_data_channel_open)
        self.data_channel.on("message", self.on_data_channel_message)


    def on_data_channel_open(self):
        print("Data Channel is open")


    def on_data_channel_message(self, message):
        print(f"Message from Data Channel: {message}")


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
        answer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
        await self.pc.setRemoteDescription(answer)


    async def handle_new_ice_candidate(self, data):
        candidate = RTCIceCandidate(sdpMLineIndex=data["sdpMLineIndex"], candidate=data["candidate"])
        await self.pc.addIceCandidate(candidate)


    async def send_command(self, action, value):
        if hasattr(self, 'data_channel') and self.data_channel.readyState == "open":
            command = json.dumps({"action": action, "value": value})
            self.data_channel.send(command)
        else:
            print("Data channel is not set up yet.")


    async def close(self):
        await self.pc.close()
        await self.ws.close()