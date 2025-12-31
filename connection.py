# 修改 connection.py
import asyncio
import logging

from asyncioutil import write_message
from rymc.phira.protocol import PacketRegistry
from rymc.phira.protocol.util import ByteBuf

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer
        self.receiver = None
        self.closeHandler = None
        # 【新增】创建一个队列来管理发送任务
        self.write_queue = asyncio.Queue()
        # 【新增】启动一个后台任务专门负责发送
        self._sender_task = asyncio.create_task(self._send_loop())

    # 【新增】发送循环，确保同一时间只有一个包写入 Socket
    async def _send_loop(self):
        try:
            while True:
                # 等待队列中有数据
                data = await self.write_queue.get()
                # 写数据 (此时是串行的，不会冲突)
                try:
                    await write_message(self.writer, data)
                except Exception as e:
                    logger.error(f"Error writing to socket: {e}")
                    self.close()
                    break
                finally:
                    self.write_queue.task_done()
        except asyncio.CancelledError:
            pass  # 任务被取消，正常退出

    def send(self, packet):
        try:
            data = PacketRegistry.encode(packet).toBytes()
            if data[0] != 0x00:
                logger.debug(f"Send packet: {data.hex()}")
            
            # 【修改】不再创建新任务，而是放入队列
            self.write_queue.put_nowait(data)
        except Exception as e:
            logger.error(f"Failed to enqueue packet: {e}")

    def set_receiver(self, receiver):
        self.receiver = receiver

    def on_receive(self, data):
        if data[0] != 0x00:
            logger.debug(f"Receive packet: {data.hex()}")
        if self.receiver is None:
            return
        self.receiver(PacketRegistry.decode(ByteBuf(data)))

    def is_closed(self):
        return self.writer.is_closing()

    def close(self):
        # 【新增】关闭连接时取消发送任务
        if self._sender_task:
            self._sender_task.cancel()
        asyncio.create_task(self.close_and_wait())

    async def close_and_wait(self, writer_timeout: float = 2) -> None:
        if self.writer is None:
            return
        try:
            if not self.is_closed():
                await asyncio.wait_for(self.writer.drain(), timeout=writer_timeout)
        except Exception:
            pass
        try:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), timeout=writer_timeout)
        except Exception:
            pass
        self.writer = None
        if self.closeHandler:
            try:
                self.closeHandler()
            except Exception as e:
                logger.error(f'[Connection] closeHandler exception: {e}')

    def on_close(self, close_handler):
        self.closeHandler = close_handler