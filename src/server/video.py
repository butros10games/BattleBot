from aiortc import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2
import asyncio

class Camera:
    def __init__(self):
        self.picamera2 = Picamera2()
        # Create a video configuration. Adjust the configuration as per your needs.
        video_config = self.picamera2.create_video_configuration(main={"size": (1080, 1920), "format": "RGB888"})
        self.picamera2.configure(video_config)

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

    async def recv(self):
        # Ensure this doesn't block the event loop
        frame = await asyncio.get_event_loop().run_in_executor(None, self.camera.get_frame)
        
        format_type = ""
        
        if frame.shape[0] == frame.shape[1] * 3 // 2:
            # YUV420 image, reshape to 2D array
            frame = frame.reshape((frame.shape[1], frame.shape[0]))
            format_type = "yuv420p"
        elif len(frame.shape) == 3 and frame.shape[2] == 3:
            # RGB image
            format_type = "rgb24"
        
        # Create video frame
        video_frame = VideoFrame.from_ndarray(frame, format=format_type)
        video_frame.pts, video_frame.time_base = await self.next_timestamp()

        return video_frame