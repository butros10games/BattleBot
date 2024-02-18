import asyncio
import threading

from src.client.communications import WebSocketClient, WebRTCClient
from src.client.inputs import KeyboardController


class ApplicationController:
    def __init__(self, uri, comunication_type):
        self.comunication_type = comunication_type    
        self.keyboard_controller = KeyboardController()
        self.old_data = ""
        
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
        
        # Wait for the connection to be established
        while not self.net_client.connected:
            await asyncio.sleep(0.1)
        
        print("Connected to the server.")
        
        self.keyboard_controller.start()
        while True:
            x, y, speed = self.keyboard_controller.get_input()
            
            data = f"{x}, {y}, {speed}"
            
            if self.old_data != data:
                print(f"Sending data: {x}, {y}, {speed}")
                await self.net_client.send_command({"x": x, "y": y, 'speed': speed})
                self.old_data = data
            await asyncio.sleep(0.01)
