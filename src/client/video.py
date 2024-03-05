import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np


class VideoWindow:
    def __init__(self, window_name="Video"):
        self.window_name = window_name
        self.win_error = False
        self.depth_map = False
        self.cap = cv2.VideoCapture(0)
        # cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def display_frame(self, frame):
        ret, frame_e = self.cap.read()
        if not ret:
            print("Failed to grab a frame")
        
        cv2.imshow('frame', frame_e)
    
    def _get_system_metrics(self):
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
        
        # Set default values for screen width and height
        return 1920, 1080

    def close(self):
        """
        Close the video window.
        """
        cv2.destroyWindow(self.window_name)

class DisplayFrame:
    def __init__(self, window_name="Video"):
        self.video_window = VideoWindow(window_name)

    def send_frame(self, frame):
        """
        Send a frame to the VideoWindow for display.
        """
        should_close = self.video_window.display_frame(frame)
        if should_close:
            print("Quitting video display.")


class DummyVideoTrack(VideoStreamTrack):
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

        # Frame dimensions and format
        width, height = 640, 480
        frame = np.ones((height, width, 3), np.uint8) * 255  # Black frame

        # Optionally, modify the frame to add text, patterns, or increment a frame counter

        # Convert the numpy array to a video frame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame
