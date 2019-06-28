print('start server (websocket)')

import asyncio
import websockets

from pprint import pprint
import json

#from config import xi_host,xi_port,local_host,local_port,xi_local_host,timeout

from utils import parse_request,socket_to_websocket,websocket_to_socket,recv_http_websocket
import struct

unsigned_short = struct.Struct("H")

async def listener(websocket, path):

    print('start server listener:',websocket, path)

    data = b''
    while len(data)<2:
        dat = await websocket.recv()
        data += dat
    
    print("prefetch data:", len(data), data[:10])
    route_port = unsigned_short.unpack(data[:2])[0]
    data = data[2:]

    print('server route:', route_port)
    remote_reader, remote_writer = await asyncio.open_connection('127.0.0.1', route_port)

    remote_writer.write(data)
    await remote_writer.drain()

    pipe1 = socket_to_websocket(remote_reader, websocket)
    pipe2 = websocket_to_socket(websocket, remote_writer)
    await asyncio.gather(pipe1, pipe2)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser("CDNSocks Server")
    parser.add_argument("-c", default="config.json", help="config file")

    args = parser.parse_args()

    with open(args.c) as f:
        config = json.load(f)

    listen_ip = '0.0.0.0'
    print('Serving on:', listen_ip, config['remote_port'])

    start_server = websockets.serve(listener, listen_ip, config['remote_port'])

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
