import gpiod
from gpiod.line import Direction, Value
import time
import threading

class MotorController:
    def __init__(self, motor1_step, motor1_dir, motor2_step, motor2_dir, motor1_en=None, motor2_en=None):
        self.raspberry_pi_version = self.get_raspberry_pi_version()
        
        if self.raspberry_pi_version == 'c03115':
            self.CHIP_NAME = '/dev/gpiochip0'
        else:
            self.CHIP_NAME = '/dev/gpiochip4'
        self.chip = gpiod.Chip(self.CHIP_NAME)
        self.pins = {
            'motor1_step': motor1_step,
            'motor1_dir': motor1_dir,
            'motor2_step': motor2_step,
            'motor2_dir': motor2_dir,
        }
        if motor1_en is not None:
            self.pins['motor1_en'] = motor1_en
        if motor2_en is not None:
            self.pins['motor2_en'] = motor2_en
        
        self.lines_request = {}
        self._init_lines()
        self.step_controllers = {
            'motor1': StepController(self.lines_request['motor1_step'], self.lines_request['motor1_dir'], self.pins['motor1_step'], self.pins['motor1_dir'], self.lines_request.get('motor1_en'), self.pins.get('motor1_en')),
            'motor2': StepController(self.lines_request['motor2_step'], self.lines_request['motor2_dir'], self.pins['motor2_step'], self.pins['motor2_dir'], self.lines_request.get('motor2_en'), self.pins.get('motor2_en')),
        }
        
    def get_raspberry_pi_version(self):
        with open('/proc/cpuinfo', 'r') as cpuinfo:
            for line in cpuinfo:
                if 'Revision' in line:
                    return line.split(':')[-1].strip()
        return None
        
    def _init_lines(self):
        try:
            self.lines_request['motor1_step'] = gpiod.request_lines(self.CHIP_NAME, consumer="motor1_step", config={self.pins['motor1_step']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)})
            self.lines_request['motor1_dir'] = gpiod.request_lines(self.CHIP_NAME, consumer="motor1_dir", config={self.pins['motor1_dir']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)})
            self.lines_request['motor2_step'] = gpiod.request_lines(self.CHIP_NAME, consumer="motor2_step", config={self.pins['motor2_step']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)})
            self.lines_request['motor2_dir'] = gpiod.request_lines(self.CHIP_NAME, consumer="motor2_dir", config={self.pins['motor2_dir']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)})
            
            if 'motor1_en' in self.pins:
                self.lines_request['motor1_en'] = gpiod.request_lines(self.CHIP_NAME, consumer="motor1_en", config={self.pins['motor1_en']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)})
            if 'motor2_en' in self.pins:
                self.lines_request['motor2_en'] = gpiod.request_lines(self.CHIP_NAME, consumer="motor2_en", config={self.pins['motor2_en']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)})
        except OSError as e:
            print(f"Error requesting GPIO lines: {e}")
            self.cleanup()
            raise

    def set_motor_direction(self, motor, direction):
        request_dir = self.lines_request[f'{motor}_dir']
        pin_dir = self.pins[f'{motor}_dir']
        if direction == "forward":
            request_dir.set_value(pin_dir, Value.INACTIVE)
        elif direction == "backward":
            request_dir.set_value(pin_dir, Value.ACTIVE)
    
    def enable_motor(self, motor, enable):
        if f'{motor}_en' in self.lines_request:
            request_en = self.lines_request[f'{motor}_en']
            pin_en = self.pins[f'{motor}_en']
            if enable:
                request_en.set_value(pin_en, Value.INACTIVE)  # Active low
            else:
                request_en.set_value(pin_en, Value.ACTIVE)
            
    def set_motor_speed(self, motor, speed):
        step_controller = self.step_controllers[motor]
        step_controller.update_speed(speed)
                
    def motor_data(self, motor, direction, speed):
        self.set_motor_direction(motor, direction)
        self.set_motor_speed(motor, speed)
        
    def action(self, x, y, speed):
        # Normalize x and y to be between -1 and 1
        x = max(min(x, 1), -1)
        y = max(min(y, 1), -1)

        # Calculate the motor values
        left = y + x
        right = y - x

        # Scale the motor values to be between -speed and speed
        left = max(min(left, 1), -1) * speed
        right = max(min(right, 1), -1) * speed

        # Determine the direction of each motor
        left_direction = 'forward' if left >= 0 else 'backward'
        right_direction = 'forward' if right >= 0 else 'backward'

        # Send the motor commands
        self.motor_data('motor1', left_direction, abs(left))
        self.motor_data('motor2', right_direction, abs(right))
        
    def stop(self):
        self.motor_data('motor1', 'forward', 0)
        self.motor_data('motor2', 'forward', 0)
        self.cleanup()
            
    def cleanup(self):
        for key, line in self.lines_request.items():
            line.release()

class StepController:
    def __init__(self, step_line_request, dir_line_request, step_pin, dir_pin, en_line_request=None, en_pin=None):
        self.step_line_request = step_line_request
        self.dir_line_request = dir_line_request
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.en_line_request = en_line_request
        self.en_pin = en_pin
        self.step_delay = 1.0 / 30000  # 30 kHz frequency
        self.running = False
        self.thread = None

    def update_speed(self, speed):
        if speed <= 0:
            self.stop()
        else:
            self.step_delay = 1.0 / speed
            if not self.running:
                self.start()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run_stepper)
        self.thread.start()

    def run_stepper(self):
        if self.en_line_request:
            self.en_line_request.set_value(self.en_pin, Value.INACTIVE)  # Enable the motor
        while self.running:
            self.step_line_request.set_value(self.step_pin, Value.ACTIVE)
            time.sleep(0.0000019)  # Step pulse width, should be at least 1 microsecond
            self.step_line_request.set_value(self.step_pin, Value.INACTIVE)
            time.sleep(self.step_delay)
        if self.en_line_request:
            self.en_line_request.set_value(self.en_pin, Value.ACTIVE)  # Disable the motor when stopped

    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()