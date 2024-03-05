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
        # Capture a frame from each camera
        frame1 = self.picamera1.capture_array("main")
        frame2 = self.picamera2.capture_array("main")
        
        print("Captured frames")

        # Convert the frames to OpenCV images
        if self.depth_map:
            img1 = cv2.cvtColor(np.array(frame1), cv2.COLOR_RGB2BGR)
            img2 = cv2.cvtColor(np.array(frame2), cv2.COLOR_RGB2BGR)
            
            img1_gray = cv2.cvtColor(np.array(frame1), cv2.COLOR_RGB2GRAY)
            img2_gray = cv2.cvtColor(np.array(frame2), cv2.COLOR_RGB2GRAY)
        else:
            img1 = cv2.cvtColor(np.array(frame1), cv2.COLOR_RGB2BGR)
            img2 = cv2.cvtColor(np.array(frame2), cv2.COLOR_RGB2BGR)
            
        print("Converted frames to OpenCV images")

        # Stitch the images together
        stitcher = cv2.Stitcher_create()
        status, wide_img = stitcher.stitch([img1, img2])
        
        print("Stitched images")

        if status != cv2.Stitcher_OK:
            print("Error during stitching images")
            return None

        if self.depth_map:
            # Calculate the disparity map
            stereo = cv2.StereoBM_create(numDisparities=8, blockSize=15)
            disparity = stereo.compute(img1_gray, img2_gray)

            # Normalize the disparity map to the range 0-255 and convert it to uint8
            disparity = cv2.normalize(disparity, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

            # Convert the wide image and the disparity map to RGBA
            wide_frame_rgba = cv2.cvtColor(wide_img, cv2.COLOR_RGB2RGBA)
            disparity_rgba = cv2.cvtColor(disparity, cv2.COLOR_GRAY2RGBA)
            
            # Resize the disparity map to match the size of the wide image
            disparity_rgba = cv2.resize(disparity_rgba, (wide_frame_rgba.shape[1], wide_frame_rgba.shape[0]))

            # Embed the disparity map in the alpha channel of the wide image
            wide_frame_rgba[:, :, 3] = disparity_rgba[:, :, 0]
        else:
            wide_frame_rgba = cv2.cvtColor(wide_img, cv2.COLOR_BGR2RGB)

        print("Converted images to RGBA")

        return wide_frame_rgba

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
