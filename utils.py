import asyncio
#import h11
#from config import timeout

timeout = 5


async def socket_to_websocket(reader, websocket):
    try:
        while not reader.at_eof():
            data = await reader.read(2048)
            print('browser_to_xi read:', len(data), data[:10])
            await websocket.send(data)
    finally:
        websocket.close()

async def websocket_to_socket(websocket, writer):
    while True:
        data = await websocket.recv() # default size? A pdb.set_trace to check will be useful.
        print('xi_to_browser recv:', len(data), data[:10])
        writer.write(data)
        await writer.drain()
