import time

from gpiozero import PWMOutputDevice

ESC_PIN = 18  # GPIO pin connected to the ESC signal wire

# Initialize PWM on the pin at 50Hz (20ms period)
esc = PWMOutputDevice(ESC_PIN, frequency=50)


def set_speed(pulse_width_us):
    """Sets the motor speed by changing the PWM pulse width.

    Args:
        pulse_width_us (float): Pulse width in microseconds.
    """
    esc.value = pulse_width_us / 20000.0  # Convert to fraction (0 to 1)


try:
    # Calibrate the ESC
    print("Calibrating ESC. Ensure the motor is powered on.")

    # Step 1: Send maximum throttle (2ms pulse width)
    set_speed(2000)  # 2000us pulse width
    print("Sending maximum throttle signal. Wait for beeps.")
    time.sleep(8)  # Wait for 6 seconds or until beeping stops

    # Step 2: Send minimum throttle (1ms pulse width)
    set_speed(200)  # 1000us pulse width
    print("Sending minimum throttle signal. Wait for beeps.")
    time.sleep(8)  # Wait for 6 seconds or until beeping stops

    # The ESC should now be calibrated
    print("ESC calibration complete.")

    # Arm the ESC with minimum throttle
    set_speed(200)  # Minimum throttle (1000us)
    print("Arming ESC with minimum throttle.")
    time.sleep(5)  # Wait for 2 seconds

    # Gradually increase the speed
    print("Increasing speed...")
    for duty_cycle in range(5, 101, 2):  # Increase duty cycle from 0% to 100%
        set_speed(duty_cycle * 20)  # Convert percentage to microseconds
        print(f"Set duty cycle to {duty_cycle}%")
        time.sleep(1)  # Wait for 1 second at each speed

    # Gradually decrease the speed
    print("Decreasing speed...")
    for duty_cycle in range(100, -1, -2):  # Decrease duty cycle from 100% to 0%
        set_speed(duty_cycle * 20)  # Convert percentage to microseconds
        print(f"Set duty cycle to {duty_cycle}%")
        time.sleep(1)  # Wait for 1 second at each speed

    # Stop the motor
    print("Stopping the motor.")
    set_speed(0)
    time.sleep(2)

except KeyboardInterrupt:
    print("Stopping the ESC calibration.")
    set_speed(0)  # Stop the motor
    esc.close()
    exit()

# Cleanup after calibration
set_speed(0)  # Stop the motor
esc.close()
