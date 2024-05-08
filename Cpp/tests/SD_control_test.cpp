#include <iostream>
#include <SDL2/SDL.h>

class JoystickController {
private:
    SDL_Joystick* joystick;
    int prev_x;
    int prev_y;
    int prev_speed;

public:
    JoystickController() {
        SDL_Init(SDL_INIT_JOYSTICK);
        joystick = SDL_JoystickOpen(0);
        prev_x = 0;
        prev_y = 0;
        prev_speed = 0;
    }

    std::tuple<int, int, int> get_joystick_position_and_speed() {
        SDL_Event event;
        SDL_PumpEvents();

        // Get the position of the joystick
        int x_axis = SDL_JoystickGetAxis(joystick, 0);
        int y_axis = SDL_JoystickGetAxis(joystick, 1);

        // Apply deadzone
        if (abs(x_axis) < 3000) {
            x_axis = 0;
        }

        if (abs(y_axis) < 3000) {
            y_axis = 0;
        }

        // Get the value of the right trigger
        int trigger_value = SDL_JoystickGetAxis(joystick, 5);
        int corrected_trigger_value = (trigger_value + 32767) / 2;

        int speed;
        if (corrected_trigger_value < 10000) {
            speed = 0;
        } else {
            speed = 0.4 + ((trigger_value + 32767) / 65535.0) * 0.6;
        }

        return std::make_tuple(x_axis, y_axis, speed);
    }

    void start() {
        // Not needed for this example
    }

    void close() {
        SDL_JoystickClose(joystick);
        SDL_Quit();
    }
};

int main() {
    JoystickController controller;

    try {
        while (true) {
            auto [x, y, speed] = controller.get_joystick_position_and_speed();
            if (x != controller.prev_x || y != controller.prev_y || speed != controller.prev_speed) {
                std::cout << "Joystick Position: (" << x << ", " << y << "), Trigger Position: " << speed << std::endl;
                controller.prev_x = x;
                controller.prev_y = y;
                controller.prev_speed = speed;
            }
        }
    } catch (...) {
        controller.close();
    }

    return 0;
}
