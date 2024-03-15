# Importing all modules
import cv2
import numpy as np
class AimAssist:
    def __init__(self, camera):
        self.steering_angle = 180 # Max steering angle of tank based steering
        self.camera_angle = 66 # Pi V.3 camera angle
        self.aim_assist_range = 0.3 # Range in which aim assist takes control
        self.position_ratio = 0 # Variable for calculating the position
        self.x_range = 2
        self.contour_detected = False
        self.untracked_frames = 0

        # Specifying upper and lower ranges of color to detect in hsv (Hue, Saturation, Value) format
        self.lower = np.array([15, 180, 120])
        self.upper = np.array([35, 255, 255])  # (These ranges will detect Yellow)

        self.camera = camera.video_window

    async def start(self):
        while True:
            full_video = await self.camera.get_frame() # Get frames from video code
            
            # Choose video format
            # video = full_video[:, :full_video.shape[1] // 2, :]  # Crop the input video to its left half (For 2 cameras stitched together)
            midpoint = full_video.shape[1] // 2
            video_r = full_video[:, :midpoint, :]
            video_l = full_video[:, midpoint:, :]  # Crop the input video to its right half
            # video = full_video # For full camera feed (if you have 2 cameras without merging the overlap it wont track correctly)

            mask = cv2.inRange(video_l, self.lower, self.upper)  # Masking the image to find the set color

            mask_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Finding contours in the mask image

            biggest_contour = max(mask_contours, key=cv2.contourArea, default=None) # Get the biggest contour

            # Drawing the biggest contour
            if biggest_contour is not None and cv2.contourArea(biggest_contour) > 500:
                self.untracked_frames = 0
                self.contour_detected = True
                x, y, w, h = cv2.boundingRect(biggest_contour)

                # Calculate the position of the contour in the video
                self.position_ratio = (x + w / 2) / video_l.shape[1]  # Width = Horizontal

                roi_width = int(video_l.shape[1] * 0.05)  # 5% of the full video width

                if self.position_ratio < 0.5: # Check position ratio
                    side = slice(None, roi_width) # Set side to the left
                else:
                    side = slice(-roi_width, None) # Set side to the right

                red_ratio = self.position_ratio - 0.5  # Shifting the position ratio to be centered at 0
                if red_ratio < 0:
                    red_ratio = -red_ratio  # Making red ratio positive

                video_l[:, side, 2] = np.clip(video_l[:, side, 2] + int(255 * red_ratio), 0, 255)  # Displaying a red transparency effect based on distance from center
                # Add a bar 5% of the video with to the closest side, then change the transparancy of the red overlay based on the red_ratio (based on distance from center)

                cv2.rectangle(video_l, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Add a detection rectangle showing the detected object

            else:
                self.untracked_frames += 1
                if self.untracked_frames > 10:
                    self.contour_detected = False
                    
            video = np.hstack((video_l, video_r))

            await self.camera.add_tracking_frame(video)
            
    def get_aim_assist(self, x_angle):
        # Divide the steering range by angle and project the camera angle centered around the center
        x_camera = (self.x_range / self.steering_angle) * ( ((self.steering_angle - self.camera_angle) / 2) + (self.camera_angle  * self.position_ratio)) - 1
        if (x_camera <= (x_angle + self.aim_assist_range)) and (x_camera >= (x_angle - self.aim_assist_range) and (self.contour_detected == True)):
            x_angle = x_camera # if the aim assist is 0.1 off from either side of the steering angle then adjust it

        return x_angle