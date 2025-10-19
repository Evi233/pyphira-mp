import asyncio


async def read_varint(reader: asyncio.StreamReader) -> int:
    result = 0
    num_read = 0
    while True:
        byte = await reader.readexactly(1)
        value = byte[0]
        result |= (value & 0x7F) << (7 * num_read)
        num_read += 1
        if num_read > 5:
            raise ValueError("VarInt too big")
        if (value & 0x80) == 0:
            break
    return result


def write_varint(writer: asyncio.StreamWriter, value: int):
    result = bytearray()
    while True:
        temp = value & 0x7F
        value >>= 7
        if value != 0:
            temp |= 0x80
        result.append(temp)
        if value == 0:
            break
    writer.write(bytes(result))


async def write_message(writer: asyncio.StreamWriter, data: bytes):
    write_varint(writer, len(data))
    writer.write(data)
    await writer.drain()


async def receive_message(reader: asyncio.StreamReader) -> bytes:
    length = await read_varint(reader)
    data = await reader.readexactly(length)
    return data