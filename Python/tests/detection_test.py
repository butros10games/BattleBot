import cv2
import numpy as np
import time 
import asyncio
import yaml
import os
from ultralytics import YOLO

current_dir = os.path.dirname(os.path.abspath(__file__))

while not os.path.basename(current_dir) == "BattleBot":
    current_dir = os.path.dirname(current_dir)

config_file_path = os.path.join(current_dir, 'docs', 'config.yaml')
model_file_path = os.path.join(current_dir, 'Models', 'BotModel.pt')

with open(config_file_path, "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
aim_config = config['aim_assist']

def load_config():
    with open(config_file_path, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

model = YOLO(model_file_path) # Load the YOLO model

class AimAssist:
    def __init__(self):
        # Initialization for tracking
        self.tracking_started = False
        self.tracking_box = None
        self.tracker_frames = 0

        self.x_range = 2 # Range of steering on the x-axis -1 to 1
        self.steering_angle = 180

        self.position_ratio = 0
        self.start_time = time.time()
        self.fps_counter = 0
        self.average_fps = 0

        self.biggest_contour = None
        self.steering_activated = False
        self.object_detected = False

        # Load the aim assist configuration
        self.tracked_frames = aim_config['tracked_frames']
        self.lost_frames = aim_config['lost_frames']

        self.camera_angle = aim_config['camera_angle']
        self.aim_assist_range = aim_config['range']

        self.lower = np.array(aim_config['lower_color'])  # Lower range of the color to detect
        self.upper = np.array(aim_config['upper_color'])  # Upper range of the color to detect

        self.contour_tracking_size = aim_config['color_tracking_size']

        self.detection_confidence = aim_config['detection_confidence']

        self.camera = cv2.VideoCapture((aim_config['camera']), cv2.CAP_DSHOW)

        self.tracker =  getattr(cv2.legacy, f"Tracker{(aim_config['tracker'])}_create")()

    async def start(self):
        while True:
            ret, full_video = self.camera.read()  # Capture frame
            if not ret:  # Check if frame is captured successfully
                print("Error: Frame not captured")
                continue  # Skip processing if frame is not captured
            
            self.video = full_video.copy()  # Create a copy for 
            
            if not self.tracking_started and not self.object_detected:
                detection = getattr(self, f"{aim_config['detection']}_detection")()
                x, y, w, h = await detection

            elif not self.tracking_started and self.object_detected:
                self.steering_activated = True
                self.tracker_frames = 0
                self.tracking_box = (x, y, w, h)
                print("Tracking started")
                self.tracker.init(self.video, self.tracking_box)
                self.tracking_started = True
                # Draw red bounding box for detection
                cv2.rectangle(self.video, (x, y), (x + w, y + h), aim_config['detection_box']['color'], aim_config['detection_box']['thickness'])
            elif self.tracking_started and self.object_detected:
                # Update the tracker
                success, self.tracking_box = self.tracker.update(self.video)
                if success:
                    self.tracker_frames -= 1
                    print("Tracking successful")
                    # Tracking successful, draw green bounding box
                    x, y, w, h = [int(coord) for coord in self.tracking_box]
                    cv2.rectangle(self.video, (x, y), (x + w, y + h), aim_config['tracking_box']['color'], aim_config['tracking_box']['thickness'])
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
                self.position_ratio = (x + (w / 2)) / self.video.shape[1]  # Width = Horizontal

                roi_width = int(self.video.shape[1] * aim_config['aim_line'])  # 5% of the full video width

                if self.position_ratio < 0.5: # Check position ratio
                    side = slice(None, roi_width) # Set side to the left
                else:
                    side = slice(-roi_width, None) # Set side to the right

                red_ratio = self.position_ratio - 0.5  # Shifting the position ratio to be centered at 0
                if red_ratio < 0:
                    red_ratio = -red_ratio  # Making red ratio positive

                self.video[:, side, 2] = np.clip(self.video[:, side, 2] + int(255 * red_ratio), 0, 255) # Add a bar 5% of the video with to the closest side, then change the transparancy of the red overlay based on the red_ratio (based on distance from center)

            # Calculate FPS
            self.fps_counter += 1
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 1:
                self.average_fps = self.fps_counter / elapsed_time
                self.start_time = time.time()
                self.fps_counter = 0

            # Display FPS
            cv2.putText(self.video, f"FPS: {self.average_fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, aim_config['fps_text']['color'], aim_config['fps_text']['thickness'])

            # Display video
            cv2.imshow("window", self.video)

            # Check for key press to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if cv2.waitKey(1) & 0xFF == ord('r'):
                new_config = load_config()  # Reload config
                aim_config.update(new_config['aim_assist'])  # Update aim_config with reloaded configuration

        # Release resources
        self.camera.release()
        cv2.destroyAllWindows()

    async def color_detection(self):
        img = cv2.cvtColor(self.video, cv2.COLOR_BGR2HSV)
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
        results = model(self.video)
        
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
            x_angle = x_camera # if the aim assist is 0.1 off from either side of the steering angle then adjust it

        return x_angle


if __name__ == "__main__":
    print("Starting the program")
    aim_assist = AimAssist()
    print("Starting AimAssist")
    asyncio.run(aim_assist.start())
