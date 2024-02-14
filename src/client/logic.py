import asyncio

from client.communications import WebSocketClient
from client.inputs import KeyboardController


class CommandGenerator:
    @staticmethod
    def get_command(key_flags):
        if key_flags['w'] and key_flags['a']:
            return 'moving_left_forward'
        elif key_flags['w'] and key_flags['d']:
            return 'moving_right_forward'
        elif key_flags['s'] and key_flags['a']:
            return 'moving_left_backward'
        elif key_flags['s'] and key_flags['d']:
            return 'moving_right_backward'
        for key, pressed in key_flags.items():
            if pressed:
                return f"moving_{key}"
        return 'stopped'


class ApplicationController:
    def __init__(self, uri):
        self.ws_client = WebSocketClient(uri)
        self.keyboard_controller = KeyboardController()
        self.state_old = ""

    async def control_loop(self):
        await self.ws_client.connect()
        self.keyboard_controller.start()
        while True:
            state = CommandGenerator.get_command(self.keyboard_controller.key_flags)
            if self.state_old != state:
                print(f"State changed to: {state}")
                await self.state_change(state)
                self.state_old = state
            await asyncio.sleep(0.01)

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
        await self.ws_client.send_command(action, value)
