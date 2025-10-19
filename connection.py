import asyncio

from asyncioutil import write_message
from rymc.phira.protocol import PacketRegistry
from rymc.phira.protocol.util import ByteBuf


class Connection:

    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer
        self.receiver = None

    def send(self, packet):
        data = PacketRegistry.encode(packet).toBytes()
        print("Send", data.hex())
        asyncio.create_task(write_message(self.writer, data))

    def set_receiver(self, receiver):
        self.receiver = receiver

    def on_receive(self, data):
        print("Receive", data.hex())
        if self.receiver is None:
            return

        self.receiver(PacketRegistry.decode(ByteBuf(data)))

    def close(self):
        self.writer.close()
        asyncio.create_task(self._wait_closed())

    async def _wait_closed(self):
        await self.writer.wait_closed()
