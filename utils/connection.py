import asyncio
import logging
import time
from typing import Optional

from utils.asyncioutil import write_message
from rymc.phira.protocol import PacketRegistry
from rymc.phira.protocol.util import ByteBuf

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, writer: asyncio.StreamWriter):
        self.writer = writer
        self.receiver = None
        self.closeHandler = None
        self.write_queue = asyncio.Queue()
        self.created_at = time.monotonic()
        self.last_seen = self.created_at
        self._closing = False
        self._closed = False
        self._close_task: Optional[asyncio.Task] = None
        self._sender_task = asyncio.create_task(self._send_loop())

    async def _send_loop(self):
        try:
            while True:
                data = await self.write_queue.get()
                try:
                    await write_message(self.writer, data)
                except Exception as e:
                    logger.error(f"Error writing to socket: {e}")
                    self.close()
                    break
                finally:
                    self.write_queue.task_done()
        except asyncio.CancelledError:
            pass

    def mark_seen(self):
        self.last_seen = time.monotonic()

    def idle_for(self, now=None):
        if now is None:
            now = time.monotonic()
        return now - self.last_seen

    def is_stale(self, max_idle_seconds: float, now=None) -> bool:
        if max_idle_seconds <= 0:
            return False
        return self.idle_for(now) > max_idle_seconds

    def send(self, packet):
        if self._closing or self._closed:
            return
        try:
            data = PacketRegistry.encode(packet).toBytes()
            if data[0] != 0x00:
                logger.debug(f"Send packet: {data.hex()}")
            self.write_queue.put_nowait(data)
        except Exception as e:
            logger.error(f"Failed to enqueue packet: {e}")

    def set_receiver(self, receiver):
        self.receiver = receiver

    def on_receive(self, data):
        self.mark_seen()
        if data[0] != 0x00:
            logger.debug(f"Receive packet: {data.hex()}")
        if self.receiver is None:
            return
        self.receiver(PacketRegistry.decode(ByteBuf(data)))

    def is_closed(self):
        if self._closed:
            return True
        if self.writer is None:
            return True
        try:
            return self.writer.is_closing()
        except Exception:
            return True

    def is_closing(self):
        return self._closing or self.is_closed()

    def close(self):
        if self._closing or self._closed:
            return
        self._closing = True
        if self._sender_task:
            self._sender_task.cancel()
        self._close_task = asyncio.create_task(self.close_and_wait())

    async def close_and_wait(self, writer_timeout: float = 2) -> None:
        if self._closed:
            return
        writer = self.writer
        try:
            if writer is not None and not writer.is_closing():
                await asyncio.wait_for(writer.drain(), timeout=writer_timeout)
        except Exception:
            pass
        try:
            if writer is not None:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=writer_timeout)
        except Exception:
            pass
        self.writer = None
        self._closed = True
        if self.closeHandler:
            try:
                self.closeHandler()
            except Exception as e:
                logger.error(f"[Connection] closeHandler exception: {e}")

    def on_close(self, close_handler):
        self.closeHandler = close_handler
