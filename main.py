import sys

from src.server.server import Server
from src.client.client import Client


def main():
    if len(sys.argv) > 1:
        script_mode = sys.argv[1]
        
        if script_mode == 'server':
            server = Server()
            server.start()
                                           
        elif script_mode == 'client':
            client = Client()
            client.start()
            
        elif script_mode == 'test':
            pass
    else:
        print('script mode is not specified, options are: server, client, test')

if __name__ == "__main__":
    main()
