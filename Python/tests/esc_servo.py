#!/usr/bin/env python3

import pigpio
import time


class ServoController:
    def __init__(self, gpio_pin):
        self.pi = pigpio.pi()
        self.gpio_pin = gpio_pin

        # Servo configuration
        self.servo_min_pulsewidth = (
            1000  # Minimum pulse width for full anticlockwise rotation
        )
        self.servo_max_pulsewidth = (
            2000  # Maximum pulse width for full clockwise rotation
        )
        self.servo_frequency = 50  # Servo frequency in Hz

        # Set servo frequency
        self.pi.set_PWM_frequency(self.gpio_pin, self.servo_frequency)

    def set_angle(self, angle):
        # Convert angle to pulse width
        pulse_width = self.servo_min_pulsewidth + (angle / 180.0) * (
            self.servo_max_pulsewidth - self.servo_min_pulsewidth
        )
        self.pi.set_servo_pulsewidth(self.gpio_pin, pulse_width)
        print("Servo angle set to", angle, "degrees")

    def cleanup(self):
        self.pi.stop()
        print("GPIO cleanup complete")


if __name__ == "__main__":
    try:
        # GPIO pin connected to servo signal wire
        gpio_pin = 4

        servo = ServoController(gpio_pin)

        # Example: Set servo to 0 degrees (full anticlockwise)
        servo.set_angle(0)
        time.sleep(2)

        # Example: Set servo to 90 degrees (center position)
        servo.set_angle(90)
        time.sleep(2)

        # Example: Set servo to 180 degrees (full clockwise)
        # =======================================================================
        # Doesn't work untill this step. Only spins full speed at this step and not at the previous steps!
        # =======================================================================
        servo.set_angle(180)
        time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        servo.cleanup()
