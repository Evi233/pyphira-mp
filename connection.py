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

    def is_closed(self):
        return self.writer.is_closing()

    def close(self):
        asyncio.create_task(self.close_and_wait())

    async def close_and_wait(self, writer_timeout: float = 2) -> None:
        """
        优雅关闭：先尽力把缓存 drain 出去，再关闭 TCP 连接，
        最后回调 closeHandler。所有“连接已死”类异常都被静默消化。
        """
        if self.writer is None:  # 已经关过
            return

        # 1. 尽力 drain
        try:
            if not self.is_closed():
                await asyncio.wait_for(self.writer.drain(), timeout=writer_timeout)
        except (ConnectionResetError, BrokenPipeError, OSError, asyncio.TimeoutError):
            print("Drain skipped: connection already down or timeout")
        except Exception as e:
            print("Unexpected drain error:", e)

        # 2. 关闭 TCP 连接
        try:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), timeout=writer_timeout)
        except Exception:
            print("Error while closing writer, ignored")

        # 3. 清引用，防重复关闭
        self.writer = None

        # 4. 业务回调
        if self.closeHandler:
            try:
                self.closeHandler()
            except Exception as e:
                print('[Connection] closeHandler 异常:', e)

    def on_close(self, close_handler):
        self.closeHandler = close_handler

