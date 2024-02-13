import asyncio
import websockets
import json
from pynput import keyboard

# Global flags to track key states
key_flags = {
    'w': False,
    's': False,
    'a': False,
    'd': False
}

async def send_command(uri, motor, action, value):
    command = json.dumps({"motor": motor, "action": action, "value": value})
    async with websockets.connect(uri) as websocket:
        await websocket.send(command)
        response = await websocket.recv()
        print(response)

async def control_loop(uri):
    state_old = ""
    while True:
        if key_flags['w']:
            state = 'w'
        elif key_flags['s']:
            state = 's'
        elif key_flags['a']:
            state = 'a'
        elif key_flags['d']:
            state = 'd'
        else:
            state = 'x'
            
        if state_old != state:
            await state_change(state)
            state_old = state

        await asyncio.sleep(0.1)  # Adjust for responsiveness

async def state_change(state):
    if state == 'w':
        await send_command(uri, "motor1", "direction", "forward")
        await send_command(uri, "motor2", "direction", "forward")
        await send_command(uri, "motor1", "speed", "1")
        await send_command(uri, "motor2", "speed", "1")
    elif state == 's':
        await send_command(uri, "motor1", "direction", "backward")
        await send_command(uri, "motor2", "direction", "backward")
        await send_command(uri, "motor1", "speed", "1")
        await send_command(uri, "motor2", "speed", "1")
    elif state == 'a':
        await send_command(uri, "motor1", "direction", "backward")
        await send_command(uri, "motor2", "direction", "forward")
        await send_command(uri, "motor1", "speed", "1")
        await send_command(uri, "motor2", "speed", "1")
    elif state == 'd':
        await send_command(uri, "motor1", "direction", "forward")
        await send_command(uri, "motor2", "direction", "backward")
        await send_command(uri, "motor1", "speed", "1")
        await send_command(uri, "motor2", "speed", "1")
    elif state == 'x':
        await send_command(uri, "motor1", "speed", "0")
        await send_command(uri, "motor2", "speed", "0")
    

def on_press(key):
    try:
        if key.char in key_flags:
            key_flags[key.char] = True
    except AttributeError:
        pass

def on_release(key):
    try:
        if key.char in key_flags:
            key_flags[key.char] = False
    except AttributeError:
        pass

if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    uri = "ws://172.20.10.11:8765"
    asyncio.run(control_loop(uri))
