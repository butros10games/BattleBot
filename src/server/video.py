from aiortc import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2
import asyncio
import cv2
import numpy as np

class Camera:
    def __init__(self):
        try:
            self.picamera1 = Picamera2(0)
            self.picamera2 = Picamera2(1)
            # Create a video configuration. Adjust the configuration as per your needs.
            video_config = self.picamera1.create_video_configuration(main={"size": (1920, 1080), "format": "RGB888"})
            self.picamera1.configure(video_config)
            self.picamera2.configure(video_config)
            
            self.depth_map = False
            
        except Exception as e:
            print(f"Camera initialization failed: {e}")

    def start(self):
        # Start the camera
        pass

    def stop(self):
        # Stop the camera
        self.picamera1.stop()
        self.picamera2.stop()

    def get_frame(self):
        # Capture frames from each camera
        frame1 = self.picamera1.capture_array("main")
        frame2 = self.picamera2.capture_array("main")

        # Convert the frames to OpenCV images
        img1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2BGR)
        img2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2BGR)

        # Concatenate the images horizontally
        combined_img = cv2.hconcat([img1, img2])

        # Convert the combined image back to the original format if necessary
        combined_frame = cv2.cvtColor(combined_img, cv2.COLOR_BGR2RGB)

        return combined_frame

    def is_camera_available(self):
        """Check if the camera is available."""
        try:
            self.picamera1.start()
            self.picamera2.start()
            return True
        except Exception as e:
            print(f"Camera availability check failed: {e}")
            return False


class CameraStreamTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, camera):
        super().__init__()  # Initialize base class
        self.camera = camera
        self.send_lock = asyncio.Lock()

    async def recv(self):
        async with self.send_lock:
            # Ensure this doesn't block the event loop
            frame = await asyncio.get_event_loop().run_in_executor(None, self.camera.get_frame)
            
            # Since your image is in RGBA format, specify "rgba" here
            if self.camera.depth_map:
                video_frame = VideoFrame.from_ndarray(frame, format="rgba")
            else:
                video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
                
            video_frame.pts, video_frame.time_base = await self.next_timestamp()

            return video_frame
