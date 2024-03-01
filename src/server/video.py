from aiortc import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2
import asyncio

class Camera:
    def __init__(self):
        try:
            self.picamera2 = Picamera2()
            # Create a video configuration. Adjust the configuration as per your needs.
            video_config = self.picamera2.create_video_configuration(main={"size": (1920, 1080), "format": "RGB888"})
            self.picamera2.configure(video_config)
        except Exception as e:
            print(f"Camera initialization failed: {e}")

    def start(self):
        # Start the camera
        pass

    def stop(self):
        # Stop the camera
        self.picamera2.stop()

    def get_frame(self):
        # This method captures a frame and returns it
        # Note: picamera2.capture_array() might need adjustments based on your setup.
        # Ensure it captures a single frame in a non-blocking manner if necessary.
        return self.picamera2.capture_array("main")

    def is_camera_available(self):
        """Check if the camera is available."""
        try:
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
            
            if frame.shape[2] == 4:
                frame = frame[:, :, :3]
            
            # Since your image is in RGB format, specify "rgb24" here
            video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            video_frame.pts, video_frame.time_base = await self.next_timestamp()

            return video_frame
