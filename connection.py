import asyncio

from asyncioutil import write_message
from rymc.phira.protocol import PacketRegistry
from rymc.phira.protocol.util import ByteBuf


class Connection:

    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer
        self.receiver = None
        self.closeHandler = None

    def send(self, packet):
        data = PacketRegistry.encode(packet).toBytes()
        #如果是00，那么不print（防止诊断消息过多）
        if data[0] != 0x00:
            print("Send", data.hex())
        asyncio.create_task(write_message(self.writer, data))

    def set_receiver(self, receiver):
        self.receiver = receiver

    def on_receive(self, data):
        #如果接到00开头的包，那么不print（防止诊断消息过多）
        if data[0] != 0x00:
            print("Receive", data.hex())
        if self.receiver is None:
            return


        self.receiver(PacketRegistry.decode(ByteBuf(data)))

    def close(self):
        asyncio.create_task(self.close_and_wait())

    async def close_and_wait(self, writer_timeout=2):
        if self.writer:
            await asyncio.wait_for(self.writer.drain(), writer_timeout)

        self.writer.close()
        await self.writer.wait_closed()
        if self.closeHandler:
            try:
                self.closeHandler()          # 不需要任何参数
            except Exception as e:
                print('[Connection] closeHandler 异常:', e)

    def on_close(self, close_handler):
        self.closeHandler = close_handler

