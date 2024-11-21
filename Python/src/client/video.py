import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np
import asyncio
import time
import socket
import struct

print("Video module loaded.")


class VideoWindow:
    print("VideoWindow class loaded.")

    def __init__(self, window_name="Video"):
        self.window_name = window_name
        self.win_error = False
        self.depth_map = False
        self.pre_frame_queue = asyncio.Queue()
        self.post_frame_queue = asyncio.Queue()
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame2 = None
        self.width = 1280

        self.init_socket()

    def init_socket(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("localhost", 65432))
        self.client_socket.setblocking(False)

    async def add_frame_queue(self, frame):
        # print("       Adding frame to pre_frame_queue.")
        """
        Add a frame to the pre_frame_queue.
        """
        await self.pre_frame_queue.put(frame)

    async def process_frames(self):
        print("       Processing frames.")
        """
        Process the frames from the pre_frame_queue and put them into the post_frame_queue.
        """
        while True:
            frame = await self.pre_frame_queue.get()
            if not self.pre_frame_queue.empty():
                continue

            img_yuv = frame.to_ndarray(format="yuv420p")
            img_rgb = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB_I420)

            img_rgb = img_rgb[:, : self.width]
            if img_rgb.shape[1] == self.width * 2:
                frame2 = img_rgb[:, self.width :]
                self.last_frame2 = frame2
            elif self.last_frame2 is not None:
                img_rgb = np.hstack((img_rgb, self.last_frame2))

            img_rgb_flipped = cv2.flip(img_rgb, -1)

            scale_percent = 50  # percent of original size
            width = int(img_rgb.shape[1] * scale_percent / 100)
            height = int(img_rgb.shape[0] * scale_percent / 100)
            dim = (width, height)
            img_rgb = cv2.resize(img_rgb_flipped, dim, interpolation=cv2.INTER_AREA)

            # Send frame to the socket
            await self.send_frame_to_socket(img_rgb)

            # Receive processed frame from the socket
            processed_frame = await self.receive_frame_from_socket()

            await self.post_frame_queue.put(processed_frame)

    async def display_frame(self):
        print("       Displaying frame.")
        """
        Display the video frame inside of a window.
        """
        while True:
            frame = await self.post_frame_queue.get()

            # Display the image in a separate thread
            cv2.imshow(self.window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                return True  # Indicate that the window should close

    async def send_frame_to_socket(self, frame):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, encoded_frame = cv2.imencode(".jpg", frame, encode_param)
        data = encoded_frame.tobytes()
        frame_length = struct.pack("!I", len(data))
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(self.client_socket, frame_length + data)

    async def receive_frame_from_socket(self):
        loop = asyncio.get_event_loop()
        data = await loop.sock_recv(self.client_socket, 4)
        if not data:
            return None
        frame_length = struct.unpack("!I", data)[0]
        frame_data = b""
        while len(frame_data) < frame_length:
            packet = await loop.sock_recv(
                self.client_socket, frame_length - len(frame_data)
            )
            if not packet:
                break
            frame_data += packet
        np_frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
        return frame

    def _get_system_metrics(self):
        print("       _get_system_metrics function loaded.")
        """
        Get the system metrics of the video window.
        """
        if self.win_error:
            try:
                import win32api

                return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
            except Exception as e:
                print(f"Error getting system metrics: {e}")
                self.win_error = True
        return 1920, 1080

    def close(self):
        """
        Close the video window.
        """
        cv2.destroyWindow(self.window_name)

    async def start(self):
        print("     Starting video display 1.")
        """
        Start the video display window.
        """
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        print("       Video window created.")
        # start the process_frames coroutine
        tasks = asyncio.gather(self.process_frames(), self.display_frame())
        print("       Process frames and display frame tasks started.")

        # start the tasks
        await tasks


class DisplayFrame:
    print("DisplayFrame class loaded.")

    def __init__(self, window_name="Video"):
        self.video_window = VideoWindow(window_name)

    async def send_frame(self, frame):
        # print("     Sending frame to video window.")
        """
        Send a frame to the VideoWindow for display.
        """
        should_close = await self.video_window.add_frame_queue(frame)
        if should_close:
            print("Quitting video display.")

    async def send_frame_threadsafe(self, frame):
        await self.video_window.add_frame_queue(frame)

    async def start(self):
        print("     Starting video display 2.")
        """
        Start the video display window.
        """
        await self.video_window.start()


class DummyVideoTrack(VideoStreamTrack):
    print("DummyVideoTrack class loaded.")
    """
    A dummy video track that generates black frames.
    """
    kind = "video"

    def __init__(self):
        super().__init__()
        self._frame_count = 0

    async def recv(self):
        """
        A coroutine that produces video frames.
        Generates a new frame every time it's called.
        """
        pts, time_base = await self.next_timestamp()
        width, height = 640, 480
        frame = np.ones((height, width, 3), np.uint8) * 255
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame
