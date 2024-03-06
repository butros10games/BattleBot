from aiortc import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2
import asyncio
import cv2
import time

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
            self.frame_counter = 0
            self.last_frame2 = None
            self.frame_times = []
            
        except Exception as e:
            print(f"Camera initialization failed: {e}")

    def start(self):
        # Start the camera
        pass

    def stop(self):
        # Stop the camera
        self.picamera1.stop()
        self.picamera2.stop()

    def capture_frame(self, camera):
        return camera.capture_array("main")

    def get_frame(self):
        start_time = time.perf_counter()

        # Capture frame from the first camera
        frame1 = self.capture_frame(self.picamera1)
        img1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2BGR)  # Convert immediately to reduce conversions

        # Update frame counter
        self.frame_counter += 1

        # Capture and convert frame from the second camera only when needed
        if self.frame_counter % 10 == 0:
            frame2 = self.capture_frame(self.picamera2)
            self.last_frame2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2BGR)
        elif self.last_frame2 is None:
            # If no second frame has been captured yet, avoid redundant conversion
            self.last_frame2 = img1

        # Concatenate the images horizontally only if last_frame2 exists to save processing time
        if self.last_frame2 is not None:
            combined_img = cv2.hconcat([img1, self.last_frame2])
        else:
            combined_img = img1

        elapsed_time_ms = (time.perf_counter() - start_time) * 1000
        self.frame_times.append(elapsed_time_ms)

        # Calculate and print the average frame time every 50 frames efficiently
        if self.frame_counter % 50 == 0:
            avg_time_ms = sum(self.frame_times) / 50
            print(f"Average time to get frame in ms: {avg_time_ms}")
            self.frame_times.clear()  # More efficient reset of the list

        return combined_img

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
