import websockets
import asyncio
import random

ws = None
count = 0
randoms = 'cat rat hat shat bat'.split()

async def consumer_handler(websocket, path):
    global ws, count
    count += 1
    ws =  websocket
    print('Got connections from ', websocket)
        #when i get the new connectino i createa new task for sending
        #Unique message to the client
    task = websocket.loop.create_task(handle_sending(websocket, count))
    task = websocket.loop.create_task(handle_recv(websocket, count))
    while True:
        await asyncio.sleep(0)
    #await websocket.send('hi')


async def handle_sending(websocket=None, val=None):
    while True:
    #	msg = await websocket.recv()
    #	print('got', msg)
        await websocket.send('hi there')
        await asyncio.sleep(2)

async def handle_recv(websocket, count):
    while True:
        msg = await websocket.recv()
        print('got the msg', msg)
        
loop = asyncio.get_event_loop()
server = websockets.serve(consumer_handler, '', 5000)

loop.run_until_complete(server)
loop.run_forever()

