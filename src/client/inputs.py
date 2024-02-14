from pynput import keyboard

class KeyboardController:
    def __init__(self):
        self.key_flags = {'w': False, 's': False, 'a': False, 'd': False}
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

    def on_press(self, key):
        try:
            if key.char in self.key_flags:
                self.key_flags[key.char] = True
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key.char in self.key_flags:
                self.key_flags[key.char] = False
        except AttributeError:
            pass

    def start(self):
        self.listener.start()
