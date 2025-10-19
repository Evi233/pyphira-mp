"""Message signalling that the room has been locked or unlocked.

Encodes the boolean lock flag after the message ID ``0x0E``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class LockRoomMessage(Message):
    """Indicates whether the room has been locked (``True``) or unlocked.
    """

    lock: bool

    def getMessageId(self) -> int:
        return 0x0E

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.lock)