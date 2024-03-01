import websockets
import json
import asyncio
import cv2
import time
from time import perf_counter

from aiortc import (RTCPeerConnection, RTCSessionDescription, RTCIceCandidate)
from .video import DummyVideoTrack


class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.connected = False

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            print("Connected to the WebSocket server.")
        except Exception as e:
            print(f"Failed to connect to WebSocket server: {e}")

    def send_command(self, action, value):
        command = json.dumps({"action": action, "value": value})
        try:
            self.websocket.send(command)
        except Exception as e:
            print(f"Error sending command: {e}")


class WebRTCClient:
    def __init__(self, url, gui):
        self.url = url
        self.pc = RTCPeerConnection()
        self.connected = False
        self.send_lock = False
        self.read_lock = asyncio.Semaphore(1)
        self.gui = gui
        self.total_time = 0
        self.total_frames = 0

    async def connect(self):
        async with websockets.connect(self.url) as ws:
            self.ws = ws
            await self.setup_data_channel()
            await self.create_and_send_offer()
            self.ping_task = asyncio.create_task(self.ping_timer())
            self.pc.on("track", self.on_track)
            await self.receive_messages()
            
    async def setup_data_channel(self):
        self.data_channel = self.pc.createDataChannel("dataChannel")
        self.data_channel.on("open", self.data_channel_open)
        self.data_channel.on("message", self.on_data_channel_message)
        
    async def data_channel_open(self):
        print("Data Channel is open")
        self.connected = True
        
    async def on_data_channel_message(self, message):
        message = json.loads(message)
        
        if "pong" in message:
            current_time = perf_counter() 
            pong_time = message["pong"]

            ping_time = (current_time - pong_time) * 1000  # convert to milliseconds

            print(f"pong received. {ping_time} ms")
        else:
            print(f"Message from Data Channel: {message}")

    async def ping_timer(self):
        while True:
            await asyncio.sleep(10)
            current_time = perf_counter()
            self.send_command({"ping": current_time})
            
    async def receive_frame(self, track):
        while True:
            async with self.read_lock:
                current_time = perf_counter()
                self.send_lock = True
                frame = await track.recv()
                self.send_lock = False
                self.total_time += perf_counter() - current_time
                self.total_frames += 1
                print('frame received')
                self.gui.send_frame(frame)
                
                if self.total_frames > 10:
                    sleep_time = self.total_time / self.total_frames
                else:
                    sleep_time = 0.01
                
                print(f"Sleep time: {sleep_time}")
                
                time.sleep(sleep_time)
            
    async def on_track(self, track):
        while True:
            print("Track received:", track.kind)
            if track.kind == "video":
                self.video_channel = track
                await self.receive_frame(track)

    async def create_and_send_offer(self):
        dummy_track = DummyVideoTrack()
        self.pc.addTrack(dummy_track)
        
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

    def send_command(self, command):
        if hasattr(self, 'data_channel') and self.data_channel.readyState == "open":
            try:
                if self.send_lock is False:
                    self.send_lock = True
                    self.data_channel.send(json.dumps(command))
                    self.send_lock = False
            except Exception as e:
                print(f"Error sending message: {e}, traceback: {e.__traceback__}")
        else:
            print("Data channel is not open or not set up yet.")

    async def close(self):
        if self.ping_task:
            self.ping_task.cancel()
            
        cv2.destroyAllWindows()  # Close video display window
        await self.pc.close()
        await self.ws.close()
