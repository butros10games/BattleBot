import gpiod
from gpiod.line import Direction, Value
from rpi_hardware_pwm import HardwarePWM

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
            'motor1': StepController(self, 'motor1', pwm_channel=0),
            'motor2': StepController(self, 'motor2', pwm_channel=1),
        }

    def get_raspberry_pi_version(self):
        with open('/proc/cpuinfo', 'r') as cpuinfo:
            for line in cpuinfo:
                if 'Revision' in line:
                    return line.split(':')[-1].strip()
        return None

    def _init_lines(self):
        try:
            self._release_lines()  # Ensure any previously held lines are released
            self.lines_request['motor1_dir'] = gpiod.request_lines(
                self.CHIP_NAME, consumer="motor1_dir",
                config={self.pins['motor1_dir']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)}
            )
            self.lines_request['motor2_dir'] = gpiod.request_lines(
                self.CHIP_NAME, consumer="motor2_dir",
                config={self.pins['motor2_dir']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)}
            )

            if 'motor1_en' in self.pins:
                self.lines_request['motor1_en'] = gpiod.request_lines(
                    self.CHIP_NAME, consumer="motor1_en",
                    config={self.pins['motor1_en']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}
                )
            if 'motor2_en' in self.pins:
                self.lines_request['motor2_en'] = gpiod.request_lines(
                    self.CHIP_NAME, consumer="motor2_en",
                    config={self.pins['motor2_en']: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}
                )
        except OSError as e:
            print(f"Error requesting GPIO lines: {e}")
            self.cleanup()
            raise

    def _release_lines(self):
        for key, line in self.lines_request.items():
            try:
                line.release()
            except gpiod.exception.RequestReleasedError:
                print(f"GPIO line {key} already released")
            except Exception as e:
                print(f"Error releasing GPIO line {key}: {e}")

    def _reinit_lines(self):
        try:
            self._release_lines()  # Release all lines before reinitializing
            self._init_lines()
        except Exception as e:
            print(f"Error reinitializing GPIO lines: {e}")

    def set_motor_direction(self, motor, direction):
        try:
            request_dir = self.lines_request[f'{motor}_dir']
            pin_dir = self.pins[f'{motor}_dir']
            if direction == "forward":
                request_dir.set_value(pin_dir, Value.INACTIVE)
            elif direction == "backward":
                request_dir.set_value(pin_dir, Value.ACTIVE)
        except gpiod.exception.RequestReleasedError:
            print(f"GPIO lines for {motor}_dir have been released, re-requesting...")
            self._reinit_lines()  # Re-request the GPIO lines
            self.set_motor_direction(motor, direction)  # Retry setting the direction

    def enable_motor(self, motor, enable):
        try:
            if f'{motor}_en' in self.lines_request:
                request_en = self.lines_request[f'{motor}_en']
                pin_en = self.pins[f'{motor}_en']
                if enable:
                    request_en.set_value(pin_en, Value.INACTIVE)  # Active low
                else:
                    request_en.set_value(pin_en, Value.ACTIVE)
        except gpiod.exception.RequestReleasedError:
            print(f"GPIO lines for {motor}_en have been released, re-requesting...")
            self._reinit_lines()  # Re-request the GPIO lines
            self.enable_motor(motor, enable)  # Retry enabling the motor

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
        self.step_controllers['motor1'].stop()
        self.step_controllers['motor2'].stop()

    def cleanup(self):
        self._release_lines()

class StepController:
    def __init__(self, motor_controller, motor_name, pwm_channel):
        self.motor_controller = motor_controller
        self.motor_name = motor_name
        self.pwm = HardwarePWM(pwm_channel=pwm_channel, hz=1000, chip=2)
        self.pwm.start(0)  # Start with 50% duty cycle (stopped)
        self.dir_line_request = motor_controller.lines_request[f'{motor_name}_dir']
        self.dir_pin = motor_controller.pins[f'{motor_name}_dir']
        self.en_line_request = motor_controller.lines_request.get(f'{motor_name}_en')
        self.en_pin = motor_controller.pins.get(f'{motor_name}_en')

    def update_speed(self, speed):
        frequency = min(max(300000 * speed, 0), 1) # 30 kHz frequency max speed between 0 and 1 (0% and 100%)
        self.pwm.change_frequency(frequency)
        duty_cycle = 50 # set the duty cycle to 50%
        self.pwm.change_duty_cycle(duty_cycle)
        
        if duty_cycle > 0:
            self.en_line_request.set_value(self.en_pin, Value.INACTIVE)
            return
        
        print(f"Motor {self.motor_name} duty_cycle set to {duty_cycle}%")
        
    def stop(self):
        self.pwm.change_duty_cycle(0)
        if self.en_line_request:
            self.en_line_request.set_value(self.en_pin, Value.ACTIVE)