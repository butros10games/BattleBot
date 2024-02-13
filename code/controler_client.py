import asyncio
import websockets
import json
from pynput import keyboard

class WebSocketController:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.key_flags = {'w': False, 's': False, 'a': False, 'd': False}
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            print("Connected to the WebSocket server.")
        except Exception as e:
            print(f"Failed to connect to WebSocket server: {e}")

    async def send_command(self, action, value):
        command = json.dumps({"action": action, "value": value})
        try:
            await self.websocket.send(command)
            response = await self.websocket.recv()
            # print(f"Server response: {response}")
        except Exception as e:
            print(f"Error sending command: {e}")

    async def control_loop(self):
        state_old = ""
        while True:
            state = self.get_state()
            if state_old != state:
                print(f"State changed to: {state}")
                await self.state_change(state)
                state_old = state
            await asyncio.sleep(0.01)

    def get_state(self):
        if self.key_flags['w'] and self.key_flags['a']:
            return 'moving_left_forward'
        elif self.key_flags['w'] and self.key_flags['d']:
            return 'moving_right_forward'
        elif self.key_flags['s'] and self.key_flags['a']:
            return 'moving_left_backward'
        elif self.key_flags['s'] and self.key_flags['d']:
            return 'moving_right_backward'
        for key, pressed in self.key_flags.items():
            if pressed:
                return f"moving_{key}"
        return 'stopped'

    async def state_change(self, state):
        action_map = {
            'moving_w': ("forward", 1),
            'moving_s': ("backward", 1),
            'moving_a': ("left", 1),
            'moving_d': ("right", 1),
            'moving_left_forward': ("curve_left", 1),
            'moving_right_forward': ("curve_right", 1),
            'moving_left_backward': ("curve_left_back", 1),
            'moving_right_backward': ("curve_right_back", 1),
            'stopped': ("stop", 0)
        }
        action, value = action_map.get(state, ("stop", 0))
        await self.send_command(action, value)

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

    async def run(self):
        self.listener.start()
        await self.connect()
        await self.control_loop()

if __name__ == "__main__":
    uri = "ws://172.20.10.11:8765"
    controller = WebSocketController(uri)
    asyncio.run(controller.run())
