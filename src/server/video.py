from aiortc import VideoStreamTrack
from av import VideoFrame

from picamera2 import Picamera2
from libcamera import controls

class Camera():
    def __init__(self):
        try:
            self.picamera2 = Picamera2()
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            self.picamera2 = None
        
    def start(self):
        self.picamera2.start()
        self.picamera2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        
    def stop(self):
        self.picamera2.stop()

    def get_frame(self):
        # Capture the frame
        return self.picamera2.capture_array()

    def is_camera_available(self):
        """Check if the camera is available."""
        try:
            self.picamera2.start()
            self.picamera2.stop()
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
        frame = self.camera.get_frame()
        
        print('frame')

        # Convert the image format from BGR to RGB
        frame = VideoFrame.from_ndarray(frame, format="bgr24")
        frame.pts, frame.time_base = await self.next_timestamp()

        return frame