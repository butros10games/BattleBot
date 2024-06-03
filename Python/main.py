import sys
import subprocess
import asyncio
import atexit
import time
sys.path.insert(0, 'src/')

def main():
    p = None  # subprocess reference
    try:
        if len(sys.argv) > 1:
            script_mode = sys.argv[1]

            if script_mode == 'server':
                from src.server.server import Server
                
                server = Server()
                server.start()

            elif script_mode == 'client':
                from src.client.client import Client
                from src.client.video import DisplayFrame

                print("Starting the client...")
                # start a python program as a subprocess
                p = subprocess.Popen(["python", "src/client/aim_assist.py"])
                atexit.register(p.terminate)  # register the terminate function to be called on exit
                
                time.sleep(4)
                
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
    except Exception as e:
        # kill the subprocess if an error occurred
        if p is not None:
            p.terminate()
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()