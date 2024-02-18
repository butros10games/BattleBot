import asyncio
import threading

from src.client.communications import WebSocketClient, WebRTCClient
from src.client.inputs import KeyboardController


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
    def __init__(self, uri, comunication_type):
        self.comunication_type = comunication_type    
        self.keyboard_controller = KeyboardController()
        self.state_old = ""
        
        self.set_net_client(uri)
        
    def set_net_client(self, uri):
        if self.comunication_type == "webrtc":
            self.net_client = WebRTCClient(uri)
        elif self.comunication_type == "websocket":
            self.net_client = WebSocketClient(uri)
        else:
            raise ValueError("Invalid communication type.")

    async def run(self):
        print("Starting the application.")
        
        connect_thread = threading.Thread(target=asyncio.run, args=(self.net_client.connect(),))
        connect_thread.daemon = True  # Set the thread as a daemon thread
        connect_thread.start()
        
        print("Connected to the server.")
        
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
        
        await self.net_client.send_command({"action": action, "value": value})
