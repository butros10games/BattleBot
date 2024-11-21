import cv2
import numpy as np
import time
import asyncio
import yaml
import os
from ultralytics import YOLO
import cProfile
import pstats


class AimAssist:
    def __init__(self):

        current_dir = os.path.dirname(os.path.abspath(__file__))

        while not os.path.basename(current_dir) == "BattleBot":
            current_dir = os.path.dirname(current_dir)

        config_file_path = os.path.join(current_dir, "docs", "config.yaml")
        model_file_path = os.path.join(current_dir, "Models", "BotModel.pt")

        with open(config_file_path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.aim_config = config["aim_assist"]

        self.model = YOLO(model_file_path)

        # Initialization for tracking
        self.tracking_started = False
        self.tracking_box = None
        self.tracker_frames = 0

        self.x_range = 2  # Range of steering on the x-axis -1 to 1
        self.steering_angle = 180

        self.position_ratio = 0
        self.start_time = time.time()
        self.fps_counter = 0
        self.average_fps = 0

        self.biggest_contour = None
        self.steering_activated = False
        self.object_detected = False

        # Load the aim assist configuration
        self.tracked_frames = self.aim_config["tracked_frames"]
        self.lost_frames = self.aim_config["lost_frames"]

        self.camera_angle = self.aim_config["camera_angle"]
        self.aim_assist_range = self.aim_config["range"]

        self.lower = np.array(
            self.aim_config["lower_color"]
        )  # Lower range of the color to detect
        self.upper = np.array(
            self.aim_config["upper_color"]
        )  # Upper range of the color to detect

        self.contour_tracking_size = self.aim_config["color_tracking_size"]

        self.detection_confidence = self.aim_config["detection_confidence"]

        self.camera = cv2.VideoCapture(self.aim_config["camera"])

        params = cv2.TrackerNano_Params()
        params.backbone = os.path.join(
            current_dir, "docs", "nanotrack_backbone.onnx"
        )  # an onnx file downloaded from the url displayed in (your doc)[https://docs.opencv.org/4.7.0/d8/d69/classcv_1_1TrackerNano.html]
        params.neckhead = os.path.join(
            current_dir, "docs", "nanotrack_head.onnx"
        )  # an onnx file downloaded from the url displayed in (your doc)[https://docs.opencv.org/4.7.0/d8/d69/classcv_1_1TrackerNano.html]

        if self.aim_config["tracker"] == "Nano":
            self.tracker = cv2.TrackerNano_create(params)
        else:
            self.tracker = getattr(
                cv2.legacy, f"Tracker{(self.aim_config['tracker'])}_create"
            )()

        # Load the window width and height for use in screen capturing aim assist
        self.window_width = self.aim_config["window_width"]
        self.window_height = self.aim_config["window_height"]

    async def start(self):
        while True:
            start_loop_time = time.time()
            ret, full_video = self.camera.read()  # Capture frame
            if not ret:  # Check if frame is captured successfully
                print("Error: Frame not captured")
                continue  # Skip processing if frame is not captured

            self.video = full_video.copy()

            if not self.tracking_started and not self.object_detected:
                detection = getattr(self, f"{self.aim_config['detection']}_detection")()
                x, y, w, h = await detection

            elif not self.tracking_started and self.object_detected:
                self.steering_activated = True
                self.tracker_frames = 0
                self.tracking_box = (x, y, w, h)
                print("Tracking started")
                self.tracker.init(full_video, self.tracking_box)
                self.tracking_started = True
                # Draw red bounding box for detection
                cv2.rectangle(
                    self.video,
                    (x, y),
                    (x + w, y + h),
                    self.aim_config["detection_box"]["color"],
                    self.aim_config["detection_box"]["thickness"],
                )
            elif self.tracking_started and self.object_detected:
                # Update the tracker
                success, self.tracking_box = self.tracker.update(full_video)
                if success:
                    self.tracker_frames -= 1
                    print("Tracking successful")
                    # Tracking successful, draw green bounding box
                    x, y, w, h = [int(coord) for coord in self.tracking_box]
                    cv2.rectangle(
                        self.video,
                        (x, y),
                        (x + w, y + h),
                        self.aim_config["tracking_box"]["color"],
                        self.aim_config["tracking_box"]["thickness"],
                    )
                    if self.tracker_frames < -self.tracked_frames:
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
                self.position_ratio = (x + (w / 2)) / self.video.shape[
                    1
                ]  # Width = Horizontal

                roi_width = int(
                    self.video.shape[1] * self.aim_config["aim_line"]
                )  # 5% of the full video width

                if self.position_ratio < 0.5:  # Check position ratio
                    side = slice(None, roi_width)  # Set side to the left
                else:
                    side = slice(-roi_width, None)  # Set side to the right

                red_ratio = (
                    self.position_ratio - 0.5
                )  # Shifting the position ratio to be centered at 0
                if red_ratio < 0:
                    red_ratio = -red_ratio  # Making red ratio positive

                self.video[:, side, 2] = np.clip(
                    self.video[:, side, 2] + int(255 * red_ratio), 0, 255
                )  # Add a bar 5% of the video with to the closest side, then change the transparency of the red overlay based on the red_ratio (based on distance from center)

            # Calculate FPS
            self.fps_counter += 1
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 1:
                self.average_fps = self.fps_counter / elapsed_time
                self.start_time = time.time()
                self.fps_counter = 0

            # Display video
            display_video = cv2.resize(
                self.video, (self.window_width, self.window_height)
            )
            # Display FPS
            cv2.putText(
                display_video,
                f"FPS: {self.average_fps:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                self.aim_config["fps_text"]["color"],
                self.aim_config["fps_text"]["thickness"],
            )
            cv2.imshow("window", display_video)

            end_loop_time = time.time()
            print(f"Loop time: {end_loop_time - start_loop_time:.2f} seconds")

            # Check for key press to exit
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # Release resources
        self.camera.release()
        cv2.destroyAllWindows()

    async def color_detection(self):
        img = cv2.cvtColor(self.video, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(img, self.lower, self.upper)
        mask_contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Find the largest contour
        biggest_contour = max(mask_contours, key=cv2.contourArea, default=None)
        if (
            biggest_contour is not None
            and cv2.contourArea(biggest_contour) > self.contour_tracking_size
        ):
            self.object_detected = True
            x, y, w, h = cv2.boundingRect(biggest_contour)
            return x, y, w, h
        else:
            self.object_detected = False
            return 0, 0, 0, 0  # Return default values when no contour is detected

    async def trained_detection(self):
        # Perform object detection using YOLO
        results = self.model(self.video, verbose=False)

        # Get the highest confidence detection
        if results[0].boxes is not None:
            box = results[0].boxes
        else:
            box = None

        if (
            box is not None
            and len(box.xywh) > 0
            and box.conf[0] > self.detection_confidence
        ):
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
        x_camera = (self.x_range / self.steering_angle) * (
            ((self.steering_angle - self.camera_angle) / 2)
            + (self.camera_angle * self.position_ratio)
        ) - 1
        if (x_camera <= (x_angle + self.aim_assist_range)) and (
            x_camera >= (x_angle - self.aim_assist_range)
            and (self.steering_activated == True)
        ):
            x_angle = x_camera  # if the aim assist is 0.1 off from either side of the steering angle then adjust it

        return x_angle


if __name__ == "__main__":
    print("Starting the program")
    aim_assist = AimAssist()
    print("Starting AimAssist")
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        asyncio.run(aim_assist.start())
    finally:
        profiler.disable()

        # Get the statistics
        stats = pstats.Stats(profiler)

        # Sort the statistics by cumulative time
        stats.sort_stats(pstats.SortKey.CUMULATIVE)

        # Display the top 15 most time-consuming functions
        stats.print_stats(15)
