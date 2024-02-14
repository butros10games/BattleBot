import asyncio

from logic import ApplicationController


class Client:
    def get_connection_string(self):
        host = input("Enter the server IP: ")
        port = input("Enter the server port: ")
        
        return f"ws://{host}:{port}"

    def start(self):
        uri = self.get_connection_string()
        controller = ApplicationController(uri)
        asyncio.run(controller.run())
