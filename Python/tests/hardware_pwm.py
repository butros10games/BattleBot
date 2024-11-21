import time
from rpi_hardware_pwm import HardwarePWM

# Define the PWM settings
PWM_PIN = 18  # GPIO pin to output PWM
PWM_FREQUENCY = 1000  # Frequency in Hz
PWM_DUTY_CYCLE = 50  # Duty cycle in percentage


def main():
    # Initialize the Hardware PWM on the specified pin
    pwm = HardwarePWM(pwm_channel=0, hz=PWM_FREQUENCY)

    # Start PWM with the specified duty cycle
    pwm.start(PWM_DUTY_CYCLE)

    try:
        # Run PWM for a certain duration
        duration = 10  # Duration in seconds
        print(
            f"Starting PWM on GPIO {PWM_PIN} with frequency {PWM_FREQUENCY}Hz and duty cycle {PWM_DUTY_CYCLE}% for {duration} seconds."
        )
        time.sleep(duration)
    except KeyboardInterrupt:
        # Handle the user interrupt
        print("PWM interrupted by user.")
    finally:
        # Stop the PWM
        pwm.stop()
        print("PWM stopped.")


if __name__ == "__main__":
    main()
