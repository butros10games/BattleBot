import asyncio
import sys
import threading

from src.client.communications import WebRTCClient, WebSocketClient
from src.client.inputs import JoystickController, KeyboardController


class ApplicationController:
    def __init__(self, uri, communication_type, gui):
        self.communication_type = communication_type
        self.gui = gui

        self.old_data = ""

        self.get_control_input()
        self.set_net_client(uri)

    def get_control_input(self):
        if len(sys.argv) > 4:
            self.control_type = sys.argv[4]
        else:
            self.control_type = input(
                "Enter the type of control you want to use (joystick/keyboard): "
            )

        if self.control_type == "joystick":
            self.controller = JoystickController()
        elif self.control_type == "keyboard":
            self.controller = KeyboardController()
        else:
            raise ValueError("Invalid control type.")

    def set_net_client(self, uri):
        if self.communication_type == "webrtc":
            self.net_client = WebRTCClient(uri, self.gui)
        elif self.communication_type == "websocket":
            self.net_client = WebSocketClient(uri)
        else:
            raise ValueError("Invalid communication type.")

    async def run(self):
        print("Starting the application.")

        connect_thread = threading.Thread(
            target=asyncio.run, args=(self.net_client.connect(),)
        )
        connect_thread.daemon = True  # Set the thread as a daemon thread
        connect_thread.start()

        # Wait for the connection to be established
        while not self.net_client.connected:
            await asyncio.sleep(0.1)

        print("Connected to the server.")

        self.controller.start()
        while True:
            x, y, speed, weapon_speed = self.controller.get_input()

            # x = self.fly_by_wire.get_aim_assist(x)

            data = f"{x}, {y}, {speed}, {weapon_speed}"

            if self.old_data != data:
                print(f"Sending data: {x}, {y}, {speed}, {weapon_speed}")

                await self.net_client.send_command(
                    {"x": x, "y": y, "speed": speed, "weapon_speed": weapon_speed}
                )
                self.old_data = data
            await asyncio.sleep(0.01)
