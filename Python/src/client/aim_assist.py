import cv2
import numpy as np
import time
import yaml
import os
import asyncio
from ultralytics import YOLO

class AimAssist:
    def __init__(self, camera):     

        self.loop = asyncio.get_event_loop()
        # Start the async operations
        self.loop.create_task(self.start())

        current_dir = os.path.dirname(os.path.abspath(__file__))
        while not os.path.basename(current_dir) == "BattleBot":
            current_dir = os.path.dirname(current_dir)

        config_file_path = os.path.join(current_dir, 'docs', 'config.yaml')
        model_file_path = os.path.join(current_dir, 'Models', 'BotModel.pt')

        with open(config_file_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.aim_config = config['aim_assist']

        self.model = YOLO(model_file_path)  # Load the YOLO model
        
        self.tracking_started = False
        self.tracking_box = None
        self.tracker_frames = 0

        self.steering_angle = 180  # Max steering angle of tank-based steering
        self.x_range = 2  # Range of steering on the x-axis -1 to 1

        self.position_ratio = 0
        self.start_time = time.time()
        self.fps_counter = 0
        self.average_fps = 0

        self.biggest_contour = None
        self.steering_activated = False
        self.object_detected = False

        self.last_processed_frame = None  # Store the last processed frame

        # Load the aim assist configuration
        self.tracked_frames = self.aim_config['tracked_frames']
        self.lost_frames = self.aim_config['lost_frames']

        self.camera_angle = self.aim_config['camera_angle']
        self.aim_assist_range = self.aim_config['range']

        self.lower = np.array(self.aim_config['lower_color'])  # Lower range of the color to detect
        self.upper = np.array(self.aim_config['upper_color'])  # Upper range of the color to detect

        self.contour_tracking_size = self.aim_config['color_tracking_size']

        self.detection_confidence = self.aim_config['detection_confidence']

        self.camera = camera.video_window  # Get the video window from the camera class

        params = cv2.TrackerNano_Params()
        params.backbone = os.path.join(current_dir, 'docs', 'nanotrack_backbone.onnx')  # an onnx file downloaded from the url displayed in (your doc)[https://docs.opencv.org/4.7.0/d8/d69/classcv_1_1TrackerNano.html]
        params.neckhead = os.path.join(current_dir, 'docs', 'nanotrack_head.onnx')  # an onnx file downloaded from the url displayed in (your doc)[https://docs.opencv.org/4.7.0/d8/d69/classcv_1_1TrackerNano.html]

         # 
        if self.aim_config['tracker'] == 'Nano':
            self.tracker = cv2.TrackerNano_create(params)
        else:
            self.tracker = getattr(cv2.legacy, f"Tracker{(self.aim_config['tracker'])}_create")()

    async def start(self):
        while True:
            start_loop_time = time.time()
            full_video = await self.camera.get_frame()  # Get frames from video code
            
            if self.last_processed_frame is not None and np.array_equal(full_video, self.last_processed_frame):
                # If the current frame is the same as the last processed frame, wait for a new frame
                print("Dupe")
                continue
            
            # Store the current frame as the last processed frame
            self.last_processed_frame = full_video.copy()
        
            midpoint = full_video.shape[1] // 2
            video_r = full_video[:, :midpoint, :]
            video_l = full_video[:, midpoint:, :]  # Crop the input video to its right half
            self.main_video = video_r

            if not self.tracking_started and not self.object_detected:
                # detection = self.color_detection()  
                detection = getattr(self, f"{self.aim_config['detection']}_detection")()
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
                    if self.tracker_frames < - self.tracked_frames:
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
                if self.tracker_frames > self.lost_frames:
                    print("Steering deactivated")
                    self.steering_activated = False

            if self.tracking_started or self.object_detected:
                self.position_ratio = (x + (w / 2)) / self.main_video.shape[1]  # Width = Horizontal

                roi_width = int(self.main_video.shape[1] * 0.05)  # 5% of the full video width

                if self.position_ratio < 0.5:  # Check position ratio
                    side = slice(None, roi_width)  # Set side to the left
                else:
                    side = slice(-roi_width, None)  # Set side to the right

                red_ratio = self.position_ratio - 0.5  # Shifting the position ratio to be centered at 0
                if red_ratio < 0:
                    red_ratio = -red_ratio  # Making red ratio positive

                self.main_video[:, side, 2] = np.clip(self.main_video[:, side, 2] + int(255 * red_ratio), 0, 255)  # Add a bar 5% of the video width to the closest side, then change the transparency of the red overlay based on the red_ratio (based on distance from center)

            # Calculate FPS
            self.fps_counter += 1
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 1:
                self.average_fps = self.fps_counter / elapsed_time
                self.start_time = time.time()
                self.fps_counter = 0

            # Display FPS
            cv2.putText(self.main_video, f"FPS: {self.average_fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            video_r = self.main_video        
            video = np.hstack((video_l, video_r))

            end_loop_time = time.time()
            # print(f"Loop time: {end_loop_time - start_loop_time:.2f} seconds")

            await self.camera.add_tracking_frame(video)
            await asyncio.sleep(0.01)

    async def color_detection(self):
        img = cv2.cvtColor(self.main_video, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(img, self.lower, self.upper)
        mask_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find the largest contour
        biggest_contour = max(mask_contours, key=cv2.contourArea, default=None)
        if biggest_contour is not None and cv2.contourArea(biggest_contour) > self.contour_tracking_size:
            self.object_detected = True
            x, y, w, h = cv2.boundingRect(biggest_contour)
            return x, y, w, h
        else:
            self.object_detected = False
            return 0, 0, 0, 0  # Return default values when no contour is detected  

    async def trained_detection(self):
        # Perform object detection using YOLO
        results = self.model(self.main_video, verbose=False)
        
        # Get the highest confidence detection
        if results[0].boxes is not None:
            box = results[0].boxes
        else:
            box = None

        if box is not None and len(box.xywh) > 0 and box.conf[0] > self.detection_confidence:
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
            x_angle = x_camera  # if the aim assist is (self.aim_assist_range) off from either side of the steering angle then adjust it

        return x_angle
