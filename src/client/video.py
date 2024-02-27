import cv2
from aiortc import MediaStreamTrack
from av import VideoFrame
import numpy as np

class VideoWindow:
    def __init__(self, window_name="Video"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def display_frame(self, image):
        """
        Display a single video frame.
        """
        cv2.imshow(self.window_name, image)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Wait for 'q' key to quit
            self.close()
            return True  # Indicate that the window should close
        return False  # Indicate that the window should not close

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
