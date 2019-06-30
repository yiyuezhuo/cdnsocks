
import asyncio

import json
with open("config_client.json") as f:
    config = json.load(f)
expose_port, reverse_ip, reverse_port = config['expose_port'], config['reverse_ip'], config['reverse_port']

from utils import pipe, parse_data,unsigned_short

async def make_pipe(command, reverse_ip, reverse_port):
    
    reader_expose, writer_expose = await asyncio.open_connection("127.0.0.1", expose_port)
    reader_reverse, writer_reverse = await asyncio.open_connection(reverse_ip, reverse_port)

    writer_reverse.write(b"new"+unsigned_short.pack(command))
    await writer_reverse.drain()

    pipe1 = pipe(reader_reverse, writer_expose)
    pipe2 = pipe(reader_expose, writer_reverse)
    try:
        await asyncio.gather(pipe1, pipe2)
    finally:
        print("writer_reverse writer_expose close")
        writer_reverse.close()
        writer_expose.close()

async def main():
    reader, writer = await asyncio.open_connection(reverse_ip, reverse_port)
    writer.write(b"con")
    await writer.drain()
    print("Connection to {} {} is established, ready to reverse proxy.".format(reverse_ip, reverse_port))

    future_list = []
    data = b''
    while True:
        dat = await reader.read(2048)
        data += dat
        command_list, data = parse_data(data)
        for command in command_list:
            coro = make_pipe(command, reverse_ip, reverse_port)
            asyncio.ensure_future(coro)
            print("New future created")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()