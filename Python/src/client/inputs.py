import pygame
from pynput import keyboard


class KeyboardController:
    def __init__(self):
        self.key_flags = {"w": False, "s": False, "a": False, "d": False}
        self.active_keys = []
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )

    def on_press(self, key):
        try:
            key = key.char  # convert the Key object to a string
            if key in self.key_flags and not self.key_flags[key]:
                self.key_flags[key] = True
                self.active_keys.append(key)
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            key = key.char  # convert the Key object to a string
            if key in self.key_flags:
                self.key_flags[key] = False
                if key in self.active_keys:
                    self.active_keys.remove(key)
        except AttributeError:
            pass

    def get_input(self):
        x = 0
        y = 0
        speed = 1

        # Process vertical keys
        for key in self.active_keys:
            if key == "w":
                y = -1
                break
            if key == "s":
                y = 1
                break

        # Process horizontal keys
        for key in self.active_keys:
            if key == "a":
                x = -1
                break
            if key == "d":
                x = 1
                break

        return x, y, speed

    def start(self):
        self.listener.start()


class JoystickController:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()  # Initialize the joystick module
        self.joystick = pygame.joystick.Joystick(0)  # Initialize the first joystick
        self.joystick.init()

    def get_joystick_position_and_speed(self):
        pygame.event.pump()  # Process event queue

        # Get the position of the joystick
        x_axis = self.joystick.get_axis(0)
        y_axis = self.joystick.get_axis(1)

        # Apply a deadzone to the joystick to prevent drift for X-axis
        if abs(x_axis) < 0.3:
            x_axis = 0
        else:
            # Invert the x_axis value to correct the turning direction
            x_axis = round(-x_axis, 4)  # Invert the direction of the turn

        # Adjust Y-axis to be -1, 0, or 1 based on its direction or neutral position
        if abs(y_axis) < 0.3 or abs(x_axis) == 1 or abs(x_axis) == -1:
            y_axis = 0
        else:
            y_axis = round(y_axis / abs(y_axis))  # This will result in -1 or 1

        if 1 > x_axis > 0 and y_axis == 0:
            x_axis = 1

        if -1 < x_axis < 0 and y_axis == 0:
            x_axis = -1

        if x_axis == 1 and y_axis == 0:
            x_axis = -1
        elif x_axis == -1 and y_axis == 0:
            x_axis = 1

        # Get the value of the right trigger (RT on Xbox controller)
        trigger_value = self.joystick.get_axis(
            5
        )  # Adjust if necessary for your controller
        corrected_trigger_value = (
            trigger_value + 1
        ) / 2  # Normalize trigger value from -1 to 1 to 0 to 1

        # Speed handling remains the same
        if corrected_trigger_value < 0.1:
            speed = 0
        else:
            speed = round(
                0.4 + (corrected_trigger_value) * 0.6, 4
            )  # Map trigger value to range 0.4 to 1

        # Get the value of the left trigger (LT on Xbox controller)
        trigger_value_2 = self.joystick.get_axis(
            4
        )  # Adjust if necessary for your controller
        corrected_trigger_value_2 = (
            trigger_value_2 + 1
        ) / 2  # Normalize trigger value from -1 to 1 to 0 to 1

        # Speed handling remains the same
        if corrected_trigger_value_2 < 0.1:
            weapon_speed = 0
        else:
            weapon_speed = round(0.4 + (corrected_trigger_value_2) * 0.6, 4)

        return x_axis, y_axis, speed, weapon_speed

    def get_input(self):
        x, y, speed, weapon_speed = self.get_joystick_position_and_speed()
        return x, y, speed, weapon_speed

    def start(self):
        pass

    def close(self):
        pygame.quit()
