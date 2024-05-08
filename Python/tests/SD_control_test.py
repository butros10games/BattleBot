import pygame

class JoystickController:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()  # Initialize the joystick module
        self.joystick = pygame.joystick.Joystick(0)  # Initialize the first joystick
        self.joystick.init()
        self.prev_x = None
        self.prev_y = None
        self.prev_speed = None

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
        trigger_value = self.joystick.get_axis(5)  # Adjust if necessary for your controller
        corrected_trigger_value = (trigger_value + 1) / 2  # Normalize trigger value from -1 to 1 to 0 to 1

        # Speed handling remains the same
        if corrected_trigger_value < 0.1:
            speed = 0
        else:
            speed = round(0.4 + ((trigger_value + 1) / 2) * 0.6, 4)  # Map trigger value to range 0.4 to 1

        return x_axis, y_axis, speed
    
    def get_input(self):
        x, y, speed = self.get_joystick_position_and_speed()
        return x, y, speed
    
    def start(self):
        pass

    def close(self):
        pygame.quit()

def main():
    controller = JoystickController()
    try:
        while True:
            x, y, speed = controller.get_input()
            if x != controller.prev_x or y != controller.prev_y or speed != controller.prev_speed:
                print(f"Joystick Position: ({x}, {y}), Trigger Position: {speed}")
                controller.prev_x = x
                controller.prev_y = y
                controller.prev_speed = speed
    except KeyboardInterrupt:
        controller.close()

if __name__ == "__main__":
    main()
