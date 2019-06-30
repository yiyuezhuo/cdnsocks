
print("exposer(reverse proxy) start")

import asyncio
import random
import json
with open('config_server.json') as f:
    config = json.load(f)
reverse_port, request_port = config['reverse_port'], config['request_port']

from utils import pipe,parse_data,unsigned_short

state_map = {
    'activated': False,
    'connected_reader': None,
    'connected_writer': None,
}

available_set = set(random.sample(range(256**2), 10)) # require complex maintaining
print('random available set', available_set)

'''
channel_map = { 
    # No key -> have not request
    # Have key and value is (reader, writer) pair -> request reader, writer 
}
'''
waiting_stack = []

async def reverse_listener(reader, writer):
    data = b''
    while len(data)<3:
        dat = await reader.read(2048)
        data += dat
    
    while len(data)>=3:
        print("data:", len(data), data[:10])
        if data[:3] == b'con':
            if not state_map['activated']:
                print("reverse proxy established")
            else:
                print("A new connect have been established, the old one is disconnected")
                state_map['connected_reader'].close()
                state_map['connected_writer'].close()

            state_map['activated'] = True
            state_map['connected_reader'] = reader
            state_map['connected_writer'] = writer
            # Can the reader and the writer still work after the function(coroutine) exit?

            data = data[3:]

        elif data[:3] == b'new':
            idx = unsigned_short.unpack(data[3:5])[0]
            print("reverse idx:", idx)
            if idx not in available_set:
                print("The idx is suspicious since it have not been considered as valid token")
                #reader.close() #AttributeError: 'StreamReader' object has no attribute 'close'
                writer.close()
                return
            if len(waiting_stack) ==0:
                print("Empty waiting stack, the verbose connection is rejected.")
                writer.close()
                return
            print("New channel connection have been established")
            reader_request, writer_request = waiting_stack.pop() #channel_map[idx]

            pipe1 = pipe(reader_request, writer)
            pipe2 = pipe(reader, writer_request)

            try:
                await asyncio.gather(pipe1, pipe2)
            finally:
                print("writer.close()")
                writer.close()

            #channel_map[idx] = (reader, writer)

            data = data[5:]

        else:
            print("Unknown command {}, exit".format(data[:3]))
            #reader.close()
            writer.close()
            return
    

async def request_listener(reader, writer):
    if not state_map['activated']:
        print("The reverse proxy have not been established, a request is rejected.")
        #reader.close()
        writer.close()
        return

    idx = random.sample(available_set, 1)[0]
    print("request idx", idx)
    #available_set.remove(idx)
    waiting_stack.append((reader, writer))
    state_map['connected_writer'].write(b'new'+unsigned_short.pack(idx))
    # Should we record the reader, writer in a map and wait reverse_listenr to pipe them?
    '''
    pipe1 = pipe(reader, state_map['connected_writer'])
    pipe2 = pipe(state_map['connected_reader'], writer)

    try:
        await asyncio.gather(pipe1, pipe2)
    finally:
        print("writer.close()")
        write.close()
    '''

loop = asyncio.get_event_loop()

async def config_server(listener, host, port, desc=None):
    server = await asyncio.start_server(listener, host, port, loop = loop)
    print('{}Serving {} on {}'.format(
        '' if desc is None else '{} :'.format(desc),
        (host, port), 
        server.sockets[0].getsockname())
    )
    return server

server_reverse = loop.run_until_complete(config_server(reverse_listener, '0.0.0.0', reverse_port, desc='exposer'))
server_request = loop.run_until_complete(config_server(request_listener, '0.0.0.0', request_port, desc='request'))

async def debug_coro(step=60):
    while True:
        await asyncio.sleep(step)
        print("DEBUG: Published by the headquarters")
        print("waiting_stack:", len(waiting_stack))

asyncio.ensure_future(debug_coro())

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server_reverse.close()
server_request.close()
loop.run_until_complete(server_reverse.wait_closed())
loop.run_until_complete(server_request.wait_closed())
loop.close()
