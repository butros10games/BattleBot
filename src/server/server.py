from src.server.motor_controller import MotorController
from src.server.communications import MotorWebSocketServer


class Server:
    def start(self):
        motor_controller = MotorController(motor1_for=17, motor1_back=18, motor2_for=27, motor2_back=22, pwm1_pin=12, pwm2_pin=13)
        websocket_server = MotorWebSocketServer(motor_controller, '0.0.0.0', 8765)
        try:
            websocket_server.run()
        except KeyboardInterrupt:
            print("WebSocket server shutting down.")
        finally:
            motor_controller.cleanup()
