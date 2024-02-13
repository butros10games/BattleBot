import gpiod
from gpiod.line import Direction, Value
import time
import asyncio
import websockets
import json
import traceback


class MotorController:
    def __init__(self, motor1_for, motor1_back, motor2_for, motor2_back, pwm1_pin, pwm2_pin):
        self.CHIP_NAME = '/dev/gpiochip4'
        self.chip = gpiod.Chip(self.CHIP_NAME)
        self.pins = {
            'motor1_for': motor1_for,
            'motor1_back': motor1_back,
            'motor2_for': motor2_for,
            'motor2_back': motor2_back,
            'pwm1': pwm1_pin,
            'pwm2': pwm2_pin
        }
        self._init_lines()
        
    def _init_lines(self):
        self.lines_request = {
            'motor1_for': gpiod.request_lines(self.CHIP_NAME, consumer="motor1_for", config={self.pins['motor1_for']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}),
            'motor1_back': gpiod.request_lines(self.CHIP_NAME, consumer="motor1_back", config={self.pins['motor1_back']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}),
            'motor2_for': gpiod.request_lines(self.CHIP_NAME, consumer="motor2_for", config={self.pins['motor2_for']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}),
            'motor2_back': gpiod.request_lines(self.CHIP_NAME, consumer="motor2_back", config={self.pins['motor2_back']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}),
            'pwm1': gpiod.request_lines(self.CHIP_NAME, consumer="pwm1", config={self.pins['pwm1']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}),
            'pwm2': gpiod.request_lines(self.CHIP_NAME, consumer="pwm2", config={self.pins['pwm2']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}),
        }

    def set_motor_direction(self, motor, direction):
        request_for = self.lines_request[f'{motor}_for']
        pin_for = self.pins[f'{motor}_for']
        request_back = self.lines_request[f'{motor}_back']
        pin_back = self.pins[f'{motor}_back']
        if direction == "forward":
            request_for.set_value(pin_for, Value.ACTIVE)
            request_back.set_value(pin_back, Value.INACTIVE)
        elif direction == "backward":
            request_for.set_value(pin_for, Value.INACTIVE)
            request_back.set_value(pin_back, Value.ACTIVE)
            
    def set_motor_speed(self, motor, speed):
        pwm_line_request = self.lines_request[f'pwm{motor[-1]}']
        pin_line = self.pins[f'pwm{motor[-1]}']
        if speed <= 0:
            pwm_line_request.set_value(pin_line, Value.INACTIVE)
        elif speed >= 1:
            pwm_line_request.set_value(pin_line, Value.ACTIVE)
        else:
            on_time = speed / 10.0
            off_time = (1 - speed) / 10.0
            for _ in range(10):
                pwm_line_request.set_value(pin_line, Value.ACTIVE)
                time.sleep(on_time)
                pwm_line_request.set_value(pin_line, Value.INACTIVE)
                time.sleep(off_time)
                
    def motor_data(self, motor, direction, speed):
        self.set_motor_direction(motor, direction)
        self.set_motor_speed(motor, speed)

    def cleanup(self):
        for request_key in self.lines_request:
            request = self.lins_request[request_key]
            pin = self.pins[request_key]
            request.set_value(pin, Value.INACTIVE)
        self.chip.close()


class MotorWebSocketServer:
    def __init__(self, motor_controller, host, port):
        self.motor_controller = motor_controller
        self.host = host
        self.port = port

    async def handle_client(self, websocket, path):
        async for message in websocket:
            try:
                command = json.loads(message)
                if 'motor' in command and 'action' in command and 'value' in command:
                    if command['action'] == 'direction':
                        self.motor_controller.set_motor_direction(command['motor'], command['value'])
                    elif command['action'] == 'speed':
                        speed_value = float(command['value'])
                        self.motor_controller.set_motor_speed(command['motor'], speed_value)
                    await websocket.send(json.dumps({'status': 'success'}))
                else:
                    await websocket.send(json.dumps({'status': 'error', 'message': 'Invalid command format'}))
            except Exception as e:
                await websocket.send(json.dumps({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}))

    def run(self):
        start_server = websockets.serve(self.handle_client, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    motor_controller = MotorController(motor1_for=17, motor1_back=18, motor2_for=27, motor2_back=22, pwm1_pin=12, pwm2_pin=13)
    websocket_server = MotorWebSocketServer(motor_controller, '0.0.0.0', 8765)
    try:
        websocket_server.run()
    except KeyboardInterrupt:
        print("WebSocket server shutting down.")
    finally:
        motor_controller.cleanup()
