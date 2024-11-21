import asyncio
import sys

from src.server.communications import MotorWebRTCClient, MotorWebSocketServer
from src.server.motor_controller import MotorController


class Server:
    def get_conmunication_type(self):
        if len(sys.argv) > 2:
            return sys.argv[2]

        return input(
            "Enter the type of communication you want to use (websocket/webrtc): "
        )

    def get_battlebot_name(self):
        if len(sys.argv) > 3:
            return sys.argv[3]

        return input("Enter the name of the battlebot: ")

    def get_server_ip_port(self):
        if len(sys.argv) > 3:
            return sys.argv[3].split(":")

        return input("Enter the ip and port of the server (ip:port): ").split(":")

    def start(self):
        motor_controller = MotorController(
            motor1_step=13,
            motor1_dir=17,
            motor2_step=12,
            motor2_dir=20,
            motor1_en=27,
            motor2_en=1,
            weapon_speed=18,
        )

        # motor callibration
        motor_controller.calibrate()

        comunication_type = self.get_conmunication_type()

        if comunication_type == "webrtc":
            websocket_server = MotorWebRTCClient(
                motor_controller, self.get_battlebot_name(), 0
            )
        elif comunication_type == "websocket":
            ip, port = self.get_server_ip_port()
            websocket_server = MotorWebSocketServer(motor_controller, ip, port)

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(websocket_server.run())
        except KeyboardInterrupt:
            print("WebSocket server shutting down.")
        finally:
            motor_controller.cleanup()
