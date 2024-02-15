import sys


def main():
    if len(sys.argv) > 1:
        script_mode = sys.argv[1]
        
        if script_mode == 'server':
            from src.server.server import Server
            
            server = Server()
            server.start()
                                           
        elif script_mode == 'client':
            from src.client.client import Client
            
            client = Client()
            client.start()
            
        elif script_mode == 'test':
            pass
    else:
        print('script mode is not specified, options are: server, client, test')

if __name__ == "__main__":
    main()
