from pynput import keyboard

class KeyboardController:
    def __init__(self):
        self.key_flags = {'w': False, 's': False, 'a': False, 'd': False}
        self.active_keys = []
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

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
            if key == 'w':
                y = 1
                break
            if key == 's':
                y = -1
                break

        # Process horizontal keys
        for key in self.active_keys:
            if key == 'a':
                x = -1
                break
            if key == 'd':
                x = 1
                break

        return x, y, speed

    def start(self):
        self.listener.start()