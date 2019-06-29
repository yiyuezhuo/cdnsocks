print("start client 0.3(socket)")

import asyncio

#from config import xi_host,xi_port,local_host,local_port
import json
with open("config_client.json") as f:
    config = json.load(f)
xi_host,xi_port,local_host,local_port = config['xi_host'], config['xi_port'], config['local_host'], config['local_port']

#from utils import socket_to_websocket,websocket_to_socket
from utils import pipe

#import websockets

#xi_addr = 'ws://' + xi_host + ':' + str(xi_port) # i.e. 'ws://localhost:8765'

#print('target server addr', xi_addr)

async def listener(reader, writer):
    try:
        
        #async with websockets.connect(xi_addr) as websocket:
        remote_reader, remote_writer = await asyncio.open_connection(
            xi_host, xi_port) 
        pipe1 = pipe(reader, remote_writer)
        pipe2 = pipe(remote_reader, writer)
        await asyncio.gather(pipe1, pipe2)
    finally:
        print("writer.close()")
        writer.close()

loop = asyncio.get_event_loop()
coro = asyncio.start_server(listener, local_host, local_port, loop = loop)
server = loop.run_until_complete(coro)

print('Serving on',server.sockets[0].getsockname())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()