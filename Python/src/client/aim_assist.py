# Importing all modules
import cv2
import numpy as np
import time
import asyncio
from ultralytics import YOLO

model = YOLO('../Models/BotModel.pt')  # load an official model

class AimAssist:
    def __init__(self, camera):
        
        # Specifying upper and lower ranges of color to detect in hsv (Hue, Saturation, Value) format
        self.lower = np.array([15, 100, 60])  # Lower range of the color to detect
        self.upper = np.array([35, 255, 255])  # Upper range of the color to detect

        # Initialize object tracker
        self.tracker = cv2.legacy.TrackerMedianFlow_create() 
        # self.tracker = cv2.legacy.TrackerMOSSE_create() # No resizing
        # self.tracker = cv2.TrackerCSRT_create() # Acurate but slower, especially when the tracking area gets big
        # self.tracker = cv2.TrackerKCF_create()
        # self.tracker = cv2.TrackerTLD_create()

        # Variables for tracking
        self.tracking_started = False
        self.tracking_box = None
        self.tracker_frames = 0

        self.tracked_frames_amount = 60 # The faster the tracker the higher this number should be
        self.lost_frames_amount = 6 # For color detection about 10 is good and for yolo around 6 because it is way slower

        self.steering_angle = 180 # Max steering angle of tank based steering
        self.x_range = 2 # Range of steering on the x-axis -1 to 1


        self.camera_angle = 66 # Pi V.3 camera angle
        self.aim_assist_range = 0.3 # Range in which aim assist takes control
        
        self.position_ratio = 0 # Variable for calculating the position
        self.untracked_frames = 0 # Counter for frames without a contour

        self.camera = camera.video_window # Get the video window from the camera class

        self.start_time = time.time()
        self.fps_counter = 0
        self.average_fps = 0

        self.biggest_contour = None
        self.steering_activated = False # Bool to check if a contour is detected
        self.object_detected = False


    async def start(self):
        while True:
            ret, full_video = await self.camera.get_frame() # Get frames from video code
            if not ret:  # Check if frame is captured successfully
                print("Error: Frame not captured")
                continue  # Skip processing if frame is not captured
            
            midpoint = full_video.shape[1] // 2
            video_r = full_video[:, :midpoint, :]
            video_l = full_video[:, midpoint:, :]  # Crop the input video to its right half
            # video = full_video # For full camera feed (if you have 2 cameras without merging the overlap it wont track correctly)
            self.main_video = video_r

            if not self.tracking_started and not self.object_detected:
                # detection = self.color_detection()  
                detection = self.trained_detection() 
                x, y, w, h = await detection

            elif not self.tracking_started and self.object_detected:
                self.steering_activated = True
                self.tracker_frames = 0
                self.tracking_box = (x, y, w, h)
                print("Tracking started")
                self.tracker.init(self.main_video, self.tracking_box)
                self.tracking_started = True
                # Draw red bounding box for detection
                cv2.rectangle(self.main_video, (x, y), (x + w, y + h), (0, 0, 255), 2)
            elif self.tracking_started and self.object_detected:
                # Update the tracker
                success, self.tracking_box = self.tracker.update(self.main_video)
                if success:
                    self.tracker_frames -= 1
                    print("Tracking successful")
                    # Tracking successful, draw green bounding box
                    x, y, w, h = [int(coord) for coord in self.tracking_box]
                    cv2.rectangle(self.main_video, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    if self.tracker_frames < - self.tracked_frames_amount:
                        self.tracking_started = False
                        self.object_detected = False
                else:
                    self.tracker_frames = 0
                    print("Tracking failed")    
                    # Tracking failed, reset detection and tracking
                    self.tracking_started = False
                    self.object_detected = False
            else:
                self.tracker_frames += 1
                if self.tracker_frames > self.lost_frames_amount:
                    print("Steering deactivated")
                    self.steering_activated = False

            if self.tracking_started or self.object_detected:
                self.position_ratio = (x + (w / 2)) / self.main_video.shape[1]  # Width = Horizontal

                roi_width = int(self.main_video.shape[1] * 0.05)  # 5% of the full video width

                if self.position_ratio < 0.5: # Check position ratio
                    side = slice(None, roi_width) # Set side to the left
                else:
                    side = slice(-roi_width, None) # Set side to the right

                red_ratio = self.position_ratio - 0.5  # Shifting the position ratio to be centered at 0
                if red_ratio < 0:
                    red_ratio = -red_ratio  # Making red ratio positive

                self.main_video[:, side, 2] = np.clip(self.main_video[:, side, 2] + int(255 * red_ratio), 0, 255) # Add a bar 5% of the video with to the closest side, then change the transparancy of the red overlay based on the red_ratio (based on distance from center)


            # Calculate FPS
            self.fps_counter += 1
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 1:
                self.average_fps = self.fps_counter / elapsed_time
                self.elapsed_time = time.time()
                self.fps_counter = 0

            video_r = self.main_video        
            video = np.hstack((video_l, video_r))

            await self.camera.add_tracking_frame(video)

    async def color_detection(self):
        img = cv2.cvtColor(self.main_video, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(img, self.lower, self.upper)
        mask_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find the largest contour
        biggest_contour = max(mask_contours, key=cv2.contourArea, default=None)
        if biggest_contour is not None and cv2.contourArea(biggest_contour) > 500:
            self.object_detected = True
            x, y, w, h = cv2.boundingRect(biggest_contour)
            return x, y, w, h
        else:
            self.object_detected = False
            return 0, 0, 0, 0  # Return default values when no contour is detected  


    async def trained_detection(self):
        # Perform object detection using YOLO
        results = model(self.main_video)
        
        # Get the highest confidence detection
        if results[0].boxes is not None:
            box = results[0].boxes
        else:
            box = None

        if box is not None and len(box.xywh) > 0 and box.conf[0] > 0.3:
            # Extract bounding box coordinates
            x_center, y_center, w, h = map(int, map(round, box.xywh.tolist()[0]))  

            # Calculate top-left coordinates
            x = round(x_center - int(w / 2))
            y = round(y_center - int(h / 2))

            self.object_detected = True
            return x, y, w, h
        else:
            self.object_detected = False
            return 0, 0, 0, 0
            
    def get_aim_assist(self, x_angle):
        # Divide the steering range by angle and project the camera angle centered around the center
        x_camera = (self.x_range / self.steering_angle) * ( ((self.steering_angle - self.camera_angle) / 2) + (self.camera_angle  * self.position_ratio)) - 1
        if (x_camera <= (x_angle + self.aim_assist_range)) and (x_camera >= (x_angle - self.aim_assist_range) and (self.steering_activated == True)):
            x_angle = x_camera # if the aim assist is 0.1 off from either side of the steering angle then adjust it

        return x_angle