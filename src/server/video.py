from aiortc import VideoStreamTrack
from av import VideoFrame
import cv2


class Camera():
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.cap = cv2.VideoCapture(self.device_id)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Camera frame capture failed")
        return frame
    
    def is_camera_available(self):
        """Check if the camera is available."""
        cap = cv2.VideoCapture(self.device_id)
        if cap is None or not cap.isOpened():
            cap.release()
            return False
        cap.release()
        return True

    def __del__(self):
        """Ensure the capture is released properly."""
        self.cap.release()

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