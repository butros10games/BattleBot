import cv2
from av import VideoFrame

class VideoWindow:
    def __init__(self, window_name="Video"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    async def display_video_from_track(self, track):
        """
        Display video frames from a given track.
        """
        try:
            while True:
                frame = await track.recv()
                image = frame.to_ndarray(format="bgr24")
                cv2.imshow(self.window_name, image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except Exception as e:
            print(f"Error displaying video: {e}")
        finally:
            self.close()

    def close(self):
        """
        Close the video window.
        """
        cv2.destroyWindow(self.window_name)
