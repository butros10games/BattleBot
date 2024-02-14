import gpiod
from gpiod.line import Direction, Value
import time
import threading

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
        self.pwm_controllers = {
            'pwm1': PWMController(self.lines_request['pwm1'], self.pins['pwm1']),
            'pwm2': PWMController(self.lines_request['pwm2'], self.pins['pwm2']),
        }
        
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
        pwm_controller = self.pwm_controllers[f'pwm{motor[-1]}']
        pwm_controller.update_speed(speed)
                
    def motor_data(self, motor, direction, speed):
        self.set_motor_direction(motor, direction)
        self.set_motor_speed(motor, speed)
        
    def action(self, action, value):
        if action == 'forward':
            self.motor_data('motor1', 'forward', value)
            self.motor_data('motor2', 'forward', value)
        elif action == 'backward':
            self.motor_data('motor1', 'backward', value)
            self.motor_data('motor2', 'backward', value)
        elif action == 'left':
            self.motor_data('motor1', 'forward', value)
            self.motor_data('motor2', 'backward', value)
        elif action == 'right':
            self.motor_data('motor1', 'backward', value)
            self.motor_data('motor2', 'forward', value)
        elif action == 'curve_left':
            self.motor_data('motor1', 'forward', (value/4))
            self.motor_data('motor2', 'forward', value)
        elif action == 'curve_right':
            self.motor_data('motor1', 'forward', value)
            self.motor_data('motor2', 'forward', (value/4))
        elif action == 'curve_left_back':
            self.motor_data('motor1', 'backward', (value/4))
            self.motor_data('motor2', 'backward', value)
        elif action == 'curve_right_back':
            self.motor_data('motor1', 'backward', value)
            self.motor_data('motor2', 'backward', (value/4))
        elif action == 'stop':
            self.motor_data('motor1', 'forward', 0)
            self.motor_data('motor2', 'forward', 0)
            
    def cleanup(self):
        for pwm_key in self.pwm_controllers:
            self.pwm_controllers[pwm_key].stop()
        super().cleanup()


class PWMController:
    def __init__(self, pwm_line_request, pin_line):
        self.pwm_line_request = pwm_line_request
        self.pin_line = pin_line
        self.on_time = 0
        self.off_time = 0
        self.running = False
        self.thread = None

    def update_speed(self, speed):
        if speed <= 0:
            self.stop()
            self.pwm_line_request.set_value(self.pin_line, Value.INACTIVE)
        elif speed >= 1:
            self.stop()
            self.pwm_line_request.set_value(self.pin_line, Value.ACTIVE)
        else:
            self.on_time = speed / 10.0
            self.off_time = (1 - speed) / 10.0
            if not self.running:
                self.start()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run_pwm)
        self.thread.start()

    def run_pwm(self):
        while self.running:
            self.pwm_line_request.set_value(self.pin_line, Value.ACTIVE)
            time.sleep(self.on_time)
            self.pwm_line_request.set_value(self.pin_line, Value.INACTIVE)
            time.sleep(self.off_time)

    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()