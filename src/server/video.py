from aiortc import VideoStreamTrack
from av import VideoFrame
from picamera2 import Picamera2, Preview

class Camera():
    def __init__(self):
        self.picamera2 = Picamera2()
        self.preview = None

    def start_preview(self):
        if self.preview is None:
            self.preview = Preview(self.picamera2)
        self.picamera2.start_preview(self.preview)

    def stop_preview(self):
        if self.preview is not None:
            self.picamera2.stop_preview()
            self.preview = None

    def get_frame(self):
        # Configure the camera
        self.picamera2.start()
        # Capture the frame
        frame = self.picamera2.capture_array()
        self.picamera2.stop()
        return frame

    def is_camera_available(self):
        """Check if the camera is available."""
        try:
            self.picamera2.start()
            self.picamera2.stop()
            return True
        except Exception as e:
            print(f"Camera availability check failed: {e}")
            return False

    def __del__(self):
        """Ensure the camera is properly closed if it's open."""
        self.stop_preview()

class CameraStreamTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, device_id=0):
        super().__init__()  # Initialize base class
        self.device_id = device_id
        self.cap = cv2.VideoCapture(self.device_id)
        self.camera = Camera(self.device_id)

    async def recv(self):
        frame = self.camera.get_frame()

        # Convert the image format from BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        av_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        av_frame.pts, av_frame.time_base = await self.next_timestamp()

        return av_frame

    def __del__(self):
        """Ensure the capture is released properly."""
        self.cap.release()