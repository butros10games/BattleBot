import gpiod
from gpiod.line import Direction, Value
import time

# Define the chip and lines for motor control and PWM
CHIP_NAME = '/dev/gpiochip4'  # Adjust if your chip name is different
MOTOR1_FOR = 17  # Direction control for Motor 1
MOTOR1_BACK = 18  # Direction control for Motor 2
MOTOR2_FOR = 27  # Direction control for Motor 1
MOTOR2_BACK = 22  # Direction control for Motor 2
PWM1_PIN = 13  # PWM control for Motor 1
PWM2_PIN = 12  # PWM control for Motor 2

# Initialize gpiod chip and lines
chip = gpiod.Chip(CHIP_NAME)

MOTOR1_FOR_request = gpiod.request_lines("/dev/gpiochip4", consumer="blink-example", config={MOTOR1_FOR: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},)
MOTOR1_BACK_request = gpiod.request_lines("/dev/gpiochip4", consumer="blink-example", config={MOTOR1_BACK: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},)
MOTOR2_FOR_request = gpiod.request_lines("/dev/gpiochip4", consumer="blink-example", config={MOTOR2_FOR: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},)
MOTOR2_BACK_request = gpiod.request_lines("/dev/gpiochip4", consumer="blink-example", config={MOTOR2_BACK: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},)
MOTOR1_PWM_request = gpiod.request_lines("/dev/gpiochip4", consumer="blink-example", config={PWM1_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},)
MOTOR2_PWM_request = gpiod.request_lines("/dev/gpiochip4", consumer="blink-example", config={PWM2_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)},)
# Request lines as outputs
lines = [MOTOR1_FOR, MOTOR1_BACK, MOTOR2_FOR, MOTOR2_BACK, PWM1_PIN, PWM2_PIN]
lines_request = [MOTOR1_FOR_request, MOTOR1_BACK_request, MOTOR2_FOR_request, MOTOR2_BACK_request, MOTOR1_PWM_request, MOTOR2_PWM_request]

def set_motor_direction(request_for, request_back, forward, backward, direction):
    """Set the motor direction with a single line."""
    if direction == "forward":
        request_for.set_value(forward, Value.ACTIVE)  # Off (low) for forward
        request_back.set_value(backward, Value.INACTIVE)  # On (high) for backward
    elif direction == "backward":
        request_for.set_value(forward, Value.INACTIVE)  # Off (low) for forward
        request_back.set_value(backward, Value.ACTIVE)  # On (high) for backward

def set_motor_speed(request, pwm_line, speed):
    """Simulate PWM to control motor speed. Speed: 0 (off) to 1 (full speed)."""
    if speed <= 0:
        request.set_value(pwm_line, Value.INACTIVE)
    elif speed >= 1:
        request.set_value(pwm_line, Value.ACTIVE)
    else:
        # Simple PWM simulation - for real applications, consider using hardware PWM if available
        on_time = speed / 10.0
        off_time = (1 - speed) / 10.0
        for _ in range(10):  # 10 cycles to simulate PWM effect
            request.set_value(pwm_line, Value.ACTIVE)
            time.sleep(on_time)
            request.set_value(pwm_line, Value.INACTIVE)
            time.sleep(off_time)

try:
    # Example to control Motor 1
    set_motor_direction(MOTOR1_FOR_request, MOTOR1_BACK_request, MOTOR1_FOR, MOTOR1_BACK, "forward")
    set_motor_speed(MOTOR1_PWM_request, PWM1_PIN, 0.5)  # 50% speed
    time.sleep(20)

    # Example to control Motor 2
    set_motor_direction(MOTOR2_FOR_request, MOTOR2_BACK_request, MOTOR2_FOR, MOTOR2_BACK, "backward")
    set_motor_speed(MOTOR2_PWM_request, PWM2_PIN, 0.75)  # 75% speed
    time.sleep(5)

finally:
    # Cleanup - stop all motors
    for i, line in enumerate(lines):
        lines_request[i].set_value(line, Value.INACTIVE)
    chip.close()
