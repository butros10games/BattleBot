import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np
import asyncio


class VideoWindow:
    def __init__(self, window_name="Video"):
        self.window_name = window_name
        self.win_error = False
        self.depth_map = False
        self.frame_queue = asyncio.Queue()
        # cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    async def display_frame(self, frame):
        await self.frame_queue.put(frame)
        
    async def display_frames(self):
        while True:
            frame = await self.frame_queue.get()
            # Convert the av.VideoFrame to a numpy array in YUV420P format
            img_yuv = frame.to_ndarray(format="yuv420p")

            # Convert the YUV image to BGR for display with OpenCV
            img_bgr = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR_I420)

            # Flip the image and resize it
            img_bgr_flipped = cv2.flip(img_bgr, -1)
            scale_percent = 50  # percent of original size
            width = int(img_bgr.shape[1] * scale_percent / 100)
            height = int(img_bgr.shape[0] * scale_percent / 100)
            dim = (width, height)
            img_bgr = cv2.resize(img_bgr_flipped, dim, interpolation=cv2.INTER_AREA)

            # Display the image in a separate thread
            cv2.imshow(self.window_name, img_bgr)

            # Center the window on the screen
            screen_width, screen_height = self._get_system_metrics()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            cv2.moveWindow(self.window_name, x, y)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                return True  # Indicate that the window should close
    
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
        
    async def start(self):
        """
        Start the video display window.
        """
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # start the display_frames coroutine
        await self.display_frames()

class DisplayFrame:
    def __init__(self, window_name="Video"):
        self.video_window = VideoWindow(window_name)

    async def send_frame(self, frame):
        """
        Send a frame to the VideoWindow for display.
        """
        should_close = await self.video_window.display_frame(frame)
        if should_close:
            print("Quitting video display.")
            
    async def start(self):
        """
        Start the video display window.
        """
        await self.video_window.start()


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
