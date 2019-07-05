print('start server (socket)')

import asyncio
#import websockets

from pprint import pprint

#from config import xi_host,xi_port,local_host,local_port,xi_local_host,timeout
import json
with open("config_server.json") as f:
    config = json.load(f)
xi_local_host, xi_port, timeout = config['xi_local_host'], config['xi_port'], config['timeout']

import h11

#from utils import parse_request,socket_to_websocket,websocket_to_socket,recv_http_websocket
from utils import pipe,parse_request,recv_http_socket

#async def listener(websocket, path):
async def listener(reader, writer):
    print('start server listener:',reader, writer)

    event_list, data = await recv_http_socket(reader)
    print('recv_http_socket:', event_list, data)
    request = parse_request(event_list)

    remote_reader, remote_writer = await asyncio.open_connection(request['host'], request['port'])

    if request['method'] == b'CONNECT':
        #await writer.write(b'HTTP/1.0 200 Connection Established\r\nProxy-agent: Pyx\r\n\r\n')
        writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await writer.drain()
    else:
        remote_writer.write(data)
        await remote_writer.drain()

    pipe1 = pipe(remote_reader, writer)
    pipe2 = pipe(reader, remote_writer)
    await asyncio.gather(pipe1, pipe2)

print('Serving on:', xi_local_host, xi_port)

'''
start_server = websockets.serve(listener, xi_local_host, xi_port)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
'''

loop = asyncio.get_event_loop()
print('start server:',xi_local_host, xi_port)
coro = asyncio.start_server(listener, xi_local_host, xi_port, loop = loop)
server = loop.run_until_complete(coro)

print('Serving on',server.sockets[0].getsockname())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()