import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np
import asyncio
import time

print("Video module loaded.")
class VideoWindow:
    print ("VideoWindow class loaded.")
    def __init__(self, window_name="Video"):
        self.window_name = window_name
        self.win_error = False
        self.depth_map = False
        self.pre_frame_queue = asyncio.Queue()
        self.post_frame_queue = asyncio.Queue()
        self.tracking_frame_queue = asyncio.Queue()
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame2 = None
        self.width = 1280

    async def add_frame_queue(self, frame):
        print("       Adding frame to pre_frame_queue.")
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
            # Convert the av.VideoFrame to a numpy array in YUV420P format
            img_yuv = frame.to_ndarray(format="yuv420p")

            # Convert the YUV image to RGB for display with OpenCV
            img_rgb = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB_I420)

            # Check if this is a double frame
            if img_rgb.shape[1] == self.width * 2:
                # Split the double frame into two frames
                frame2 = img_rgb[:, self.width:]

                # Use the first frame for display
                self.last_frame2 = frame2
            elif self.last_frame2 is not None:
                img_rgb = cv2.hconcat([img_rgb, self.last_frame2])

            # Flip the image and resize it
            img_rgb_flipped = cv2.flip(img_rgb, -1)
            scale_percent = 50  # percent of original size
            width = int(img_rgb.shape[1] * scale_percent / 100)
            height = int(img_rgb.shape[0] * scale_percent / 100)
            dim = (width, height)
            img_rgb = cv2.resize(img_rgb_flipped, dim, interpolation=cv2.INTER_AREA)
            
            await self.post_frame_queue.put(img_rgb)
            
    async def get_frame(self):
        print("       Getting frame from post_frame_queue.")
        """
        Get a frame from the frame queue.
        """
        return await self.post_frame_queue.get()
    
    async def add_tracking_frame(self, frame):
        await self.tracking_frame_queue.put(frame)
    
    async def display_frame(self):
        print("       Displaying frame.")
        """
        Display the video frame inside of a window.
        """
        while True:
            frame = await self.tracking_frame_queue.get()
            
            # Display the image in a separate thread
            cv2.imshow(self.window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                return True  # Indicate that the window should close
    
    def _get_system_metrics(self):
        print ("       _get_system_metrics function loaded.")
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
        print("     Starting video display 1.")
        """
        Start the video display window.
        """
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        print("       Video window created.")
        # start the process_frames coroutine
        tasks = asyncio.gather(
            self.process_frames(),
            self.display_frame()
        )
        print("       Process frames and display frame tasks started.") 
        
        # start the tasks
        await tasks
        

class DisplayFrame:
    print ("DisplayFrame class loaded.")
    def __init__(self, window_name="Video"):
        self.video_window = VideoWindow(window_name)

    async def send_frame(self, frame):
        print("     Sending frame to video window.")
        """
        Send a frame to the VideoWindow for display.
        """
        should_close = await self.video_window.add_frame_queue(frame)
        if should_close:
            print("Quitting video display.")
            
    async def start(self):
        print("     Starting video display 2.")
        """
        Start the video display window.
        """
        await self.video_window.start()


class DummyVideoTrack(VideoStreamTrack):
    print ("DummyVideoTrack class loaded.")
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
