import websockets
import json
import asyncio
import cv2
import threading
from time import perf_counter

from aiortc import (RTCPeerConnection, RTCSessionDescription, RTCIceCandidate)
from .video import VideoWindow


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
        self.connected = False
        self.send_lock = asyncio.Lock()
        self.video_window = None

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
            await self.send_command({"ping": current_time})
            
    async def on_track(self, track):
        print("Track received:", track.kind)
        if track.kind == "video":
            await self.handle_video(track)

    async def handle_video(self, track):
        """
        Handle incoming video track.
        """
        if not self.video_window:
            self.video_window = VideoWindow("Received Video")
            
        # start displaying the video on a separate thread so it doesn't block the main thread with the threading library
        self.video_window.start_video_display_thread(track)


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

    async def send_command(self, command):
        if hasattr(self, 'data_channel') and self.data_channel.readyState == "open":
            async with self.send_lock:  # Acquire the lock before sending data
                try:
                    self.data_channel.send(json.dumps(command))
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


from aiortc import MediaStreamTrack
from av import VideoFrame
import numpy as np
import asyncio

class DummyVideoTrack(MediaStreamTrack):
    """
    A dummy video track that generates black frames.
    """
    kind = "video"

    def __init__(self):
        super().__init__()  # Initialize the base class
        self._frame_count = 0

    async def recv(self):
        """
        A coroutine that produces video frames.
        Generates a new frame every time it's called.
        """
        pts, time_base = await self.next_timestamp()
        
        print('frame')

        # Frame dimensions and format
        width, height = 640, 480
        frame = np.zeros((height, width, 3), np.uint8)  # Black frame

        # Optionally, modify the frame to add text, patterns, or increment a frame counter

        # Convert the numpy array to a video frame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame
