import cv2
import numpy as np
import time
import yaml
import os
from ultralytics import YOLO
import asyncio
import socket
import struct


class AimAssist:
    def __init__(self):
        self.initialize_paths()
        self.load_config()
        self.initialize_model()
        self.initialize_state_variables()
        self.load_aim_assist_config()
        self.initialize_tracker()
        self.frame_queue = asyncio.Queue()

    def initialize_paths(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        while os.path.basename(self.current_dir) != "BattleBot":
            self.current_dir = os.path.dirname(self.current_dir)

        self.config_file_path = os.path.join(self.current_dir, "docs", "config.yaml")
        self.model_file_path = os.path.join(self.current_dir, "Models", "BotModel.pt")

    def load_config(self):
        with open(self.config_file_path, "r") as f:
            self.aim_config = yaml.load(f, Loader=yaml.FullLoader)["aim_assist"]

    def initialize_model(self):
        self.model = YOLO(self.model_file_path)

    def initialize_state_variables(self):
        self.tracking_started = False
        self.tracking_box = None
        self.tracker_frames = 0
        self.steering_angle = 180
        self.x_range = 2
        self.position_ratio = 0
        self.start_time = time.time()
        self.fps_counter = 0
        self.average_fps = 0
        self.biggest_contour = None
        self.steering_activated = False
        self.object_detected = False

    def load_aim_assist_config(self):
        config = self.aim_config
        self.tracked_frames = config["tracked_frames"]
        self.lost_frames = config["lost_frames"]
        self.camera_angle = config["camera_angle"]
        self.aim_assist_range = config["range"]
        self.lower = np.array(config["lower_color"], dtype=np.uint8)
        self.upper = np.array(config["upper_color"], dtype=np.uint8)
        self.contour_tracking_size = config["color_tracking_size"]
        self.detection_confidence = config["detection_confidence"]

    def initialize_tracker(self):
        params = cv2.TrackerNano_Params()
        params.backbone = os.path.join(
            self.current_dir, "docs", "nanotrack_backbone.onnx"
        )
        params.neckhead = os.path.join(self.current_dir, "docs", "nanotrack_head.onnx")

        if self.aim_config["tracker"] == "Nano":
            self.tracker = cv2.TrackerNano_create(params)
        else:
            self.tracker = getattr(
                cv2.legacy, f"Tracker{self.aim_config['tracker']}_create"
            )()

    async def init_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False)
        self.server_socket.bind(("0.0.0.0", 65432))
        self.server_socket.listen(1)
        await self.accept_client()

    async def accept_client(self):
        while True:
            try:
                self.client_socket, _ = await self.loop.sock_accept(self.server_socket)
                break
            except BlockingIOError:
                await asyncio.sleep(0.1)
        asyncio.create_task(self.receive_frames())

    async def receive_frames(self):
        while True:
            data = await self.loop.sock_recv(self.client_socket, 4)
            if not data:
                break
            frame_length = struct.unpack("!I", data)[0]
            frame_data = b""
            while len(frame_data) < frame_length:
                packet = await self.loop.sock_recv(
                    self.client_socket, frame_length - len(frame_data)
                )
                if not packet:
                    break
                frame_data += packet
            np_frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            await self.frame_queue.put(frame)

    async def send_frame(self, frame):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        result, encoded_frame = cv2.imencode(".jpg", frame, encode_param)
        data = encoded_frame.tobytes()
        frame_length = struct.pack("!I", len(data))
        await self.loop.sock_sendall(self.client_socket, frame_length + data)

    async def start(self):
        self.loop = asyncio.get_event_loop()
        await asyncio.gather(self.process_loop(), self.init_socket())

    async def process_loop(self):
        print("Starting the aim assist.")

        while True:
            frame = await self.frame_queue.get()
            if frame is not None:
                self.main_video = frame
                detection = await getattr(
                    self, f"{self.aim_config['detection']}_detection"
                )()
                x, y, w, h = detection

                if not self.tracking_started and self.object_detected:
                    self.start_tracking(x, y, w, h)
                elif self.tracking_started and self.object_detected:
                    await self.update_tracking()
                else:
                    self.tracker_frames += 1
                    if self.tracker_frames > self.lost_frames:
                        self.steering_activated = False

                self.update_position_ratio(x, w)

                # Send the processed frame
                await self.send_frame(self.main_video)

    def process_video_frames(self, full_video):
        midpoint = full_video.shape[1] // 2
        self.main_video = full_video[:, :midpoint, :]

    def start_tracking(self, x, y, w, h):
        self.tracking_box = (x, y, w, h)
        self.tracker.init(self.main_video, self.tracking_box)
        self.tracking_started = True
        self.tracker_frames = 0
        self.steering_activated = True
        cv2.rectangle(self.main_video, (x, y), (x + w, y + h), (0, 0, 255), 2)

    async def update_tracking(self):
        success, self.tracking_box = self.tracker.update(self.main_video)
        if success:
            self.tracker_frames -= 1
            self.draw_tracking_box()
            if self.tracker_frames < -self.tracked_frames:
                self.reset_tracking()
        else:
            self.reset_tracking()

    def draw_tracking_box(self):
        x, y, w, h = map(int, self.tracking_box)
        cv2.rectangle(self.main_video, (x, y), (x + w, y + h), (0, 255, 0), 2)

    def reset_tracking(self):
        self.tracking_started = False
        self.object_detected = False

    def update_position_ratio(self, x, w):
        if self.tracking_started or self.object_detected:
            self.position_ratio = (x + (w / 2)) / self.main_video.shape[1]
            roi_width = int(self.main_video.shape[1] * 0.05)
            side = (
                slice(None, roi_width)
                if self.position_ratio < 0.5
                else slice(-roi_width, None)
            )
            red_ratio = abs(self.position_ratio - 0.5)
            self.main_video[:, side, 2] = np.clip(
                self.main_video[:, side, 2] + int(255 * red_ratio), 0, 255
            )

    async def color_detection(self):
        img = cv2.cvtColor(self.main_video, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(img, self.lower, self.upper)
        mask_contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if mask_contours:
            biggest_contour = max(mask_contours, key=cv2.contourArea, default=None)
            if cv2.contourArea(biggest_contour) > self.contour_tracking_size:
                x, y, w, h = cv2.boundingRect(biggest_contour)
                self.object_detected = True
                return x, y, w, h
        self.object_detected = False
        return 0, 0, 0, 0

    async def trained_detection(self):
        results = self.model(self.main_video, verbose=False)
        box = results[0].boxes if results[0].boxes is not None else None

        if box and len(box.xywh) > 0 and box.conf[0] > self.detection_confidence:
            x_center, y_center, w, h = map(int, map(round, box.xywh.tolist()[0]))
            x, y = x_center - w // 2, y_center - h // 2
            self.object_detected = True
            return x, y, w, h
        else:
            self.object_detected = False
            return 0, 0, 0, 0

    def get_aim_assist(self, x_angle):
        x_camera = (self.x_range / self.steering_angle) * (
            ((self.steering_angle - self.camera_angle) / 2)
            + (self.camera_angle * self.position_ratio)
        ) - 1
        if self.steering_activated and (
            x_angle - self.aim_assist_range
        ) <= x_camera <= (x_angle + self.aim_assist_range):
            x_angle = x_camera
        return x_angle


# main start
if __name__ == "__main__":
    print("Starting the aim assist.")
    aim_assist = AimAssist()
    print("Class initialized.")
    asyncio.run(aim_assist.start())
