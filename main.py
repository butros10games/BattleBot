import sys
import threading
import asyncio
sys.path.insert(0, 'src/')

def main():
    if len(sys.argv) > 1:
        script_mode = sys.argv[1]
        
        if script_mode == 'server':
            from src.server.server import Server
            
            server = Server()
            server.start()

        elif script_mode == 'client':
            from src.client.client import Client
            from src.client.video import DisplayFrame

            gui = DisplayFrame()
            client = Client(gui)

            async def starting():
                task1 = asyncio.create_task(gui.start())
                task2 = asyncio.create_task(client.start())

                await asyncio.gather(task1, task2)

            asyncio.run(starting())
            
        elif script_mode == 'test':
            pass
    else:
        print('script mode is not specified, options are: server, client, test')

if __name__ == "__main__":
    main()
