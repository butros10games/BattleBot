import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np


class VideoWindow:
    def __init__(self, window_name="Video"):
        self.window_name = window_name
        self.win_error = False
        self.depth_map = False
        # cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def display_frame(self, frame):
        # Convert the av.VideoFrame to a numpy array
        img = frame.to_ndarray(format="bgr24")

        # Split the image into two
        img1 = img[:, :img.shape[1]//2, :]
        img2 = img[:, img.shape[1]//2:, :]

        # Stitch the images together
        stitcher = cv2.Stitcher_create()
        status, img_stitched = stitcher.stitch([img1, img2])

        if status != cv2.Stitcher_OK:
            print("Error during stitching images")
            return False

        img_stitched_flipped = cv2.flip(img_stitched, -1)
        
        # Set a fixed size for the window
        window_width = 800
        window_height = 600

        # Resize the stitched image to fit the window
        img_stitched = cv2.resize(img_stitched_flipped, (window_width, window_height), interpolation = cv2.INTER_AREA)
        
        # Create the window and set its size
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, window_width, window_height)

        cv2.imshow(self.window_name, img_stitched)
        
        # Get the screen size
        screen_width, screen_height = self._get_system_metrics()

        # Calculate the position to center the window
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Move the window to the center of the screen
        cv2.moveWindow(self.window_name, x, y)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True  # Indicate that the window should close
        return False  # Indicate that the window should not close
    
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
