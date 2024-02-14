import asyncio
import websockets
import json
import traceback
import socket

class MotorWebSocketServer:
    def __init__(self, motor_controller, host, port):
        self.motor_controller = motor_controller
        self.host = host
        self.port = port


    async def handle_client(self, websocket, path):
        async for message in websocket:
            try:
                command = json.loads(message)
                if 'action' in command and 'value' in command:
                    self.motor_controller.action(command['action'], command['value'])
                    await websocket.send(json.dumps({'status': 'success'}))
                else:
                    await websocket.send(json.dumps({'status': 'error', 'message': 'Invalid command format'}))
            except Exception as e:
                await websocket.send(json.dumps({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}))

        # Stop the motor controller when the connection is lost
        await self.motor_controller.stop()
    

    def print_server_info(self):
        # Determine the actual IP when the server is bound to '0.0.0.0'
        if self.host == "0.0.0.0":
            # Attempt to determine the "real" IP by connecting to a public DNS server
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))  # Google's DNS server
                    ip = s.getsockname()[0]
            except Exception:
                ip = "unable to determine IP"
            print(f"Server started at ws://{ip}:{self.port}")
        else:
            print(f"Server started at ws://{self.host}:{self.port}")


    def run(self):
        start_server = websockets.serve(self.handle_client, self.host, self.port)
        
        self.print_server_info()
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()