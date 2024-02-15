import asyncio

from src.client.logic import ApplicationController


class Client:
    def get_conmunication_type(self):
        return input("Enter the type of communication you want to use (websocket/webrtc): ")


    def get_battlebot_name(self):
        return input("Enter the name of the battlebot: ")


    def get_connection_string(self, comunication_type):
        if comunication_type == "webrtc":
            bot_name = self.get_battlebot_name()
            return f"wss://butrosgroot.com/ws/battle_bot/signal/{bot_name}"
        elif comunication_type == "websocket":
            host, port = input("Enter the ip and port of the server (ip:port): ").split(":")
        
            return f"ws://{host}:{port}"
        else:
            return None


    def start(self):
        comunication_type = self.get_conmunication_type()
        uri = self.get_connection_string(comunication_type)
        
        if uri is not None:
            controller = ApplicationController(uri, comunication_type)
            asyncio.run(controller.run())
        else:
            print("Invalid communication type.")
