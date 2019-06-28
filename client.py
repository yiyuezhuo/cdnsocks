print("start client 0.3(websocket)")

import asyncio
import json
import struct

from utils import socket_to_websocket,websocket_to_socket
import websockets

unsigned_short = struct.Struct("H")

def listener_factory(remote_ip, remote_port, route_port):
    addr = 'ws://' + remote_ip + ':' + str(remote_port) # i.e. 'ws://localhost:8765'

    async def listener(reader, writer):
        try:
            
            async with websockets.connect(addr) as websocket:

                assert 0 <= route_port <= 65535
                print("client route_port:", route_port)
                await websocket.send(unsigned_short.pack(route_port))
                
                pipe1 = socket_to_websocket(reader, websocket)
                pipe2 = websocket_to_socket(websocket, writer)
                await asyncio.gather(pipe1, pipe2)
        finally:
            print("writer.close()")
            writer.close()
    
    return listener

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser("CDNSocks client")
    parser.add_argument("-c", default="config.json", help="config file")

    args = parser.parse_args()

    with open(args.c) as f:
        config = json.load(f)

    local_ip = config['local_ip']
    remote_ip = config['remote_ip']
    remote_port = config['remote_port']
    routes = config['routes']

    loop = asyncio.get_event_loop()
    server_list = []

    for idx,route in enumerate(routes):

        listener = listener_factory(remote_ip, remote_port, route['route_port'])
        coro = asyncio.start_server(listener, local_ip, route['local_port'], loop = loop)
        server = loop.run_until_complete(coro)
        server_list.append(server)
        
        print('Serving {} on {}'.format(route['name'] if route['name'] else idx, 
            server.sockets[0].getsockname()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    for server in server_list:
        server.close()
        loop.run_until_complete(server.wait_closed())

    loop.close()