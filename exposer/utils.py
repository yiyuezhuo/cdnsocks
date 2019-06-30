
import struct

unsigned_short = struct.Struct("H")

async def pipe(reader, writer):
    try:
        while not reader.at_eof():
            data = await reader.read(2048)
            print('pipe:', len(data), data[:10])
            writer.write(data)
            await writer.drain()
    finally:
        writer.close()

def parse_data(data):
    command_list = []
    while len(data) >= 5:
        assert data[:3] == b'new'
        command = unsigned_short.unpack(data[3:5])[0]
        command_list.append(command)
        data = data[5:]
    return command_list, data