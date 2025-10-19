"""Message indicating that room cycling has been toggled.

Carries a boolean flag after the message ID ``0x0F`` signalling whether
cycling is enabled or disabled.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class CycleRoomMessage(Message):
    """Indicates whether the room should automatically cycle after each song."""

    cycle: bool

    def getMessageId(self) -> int:
        return 0x0F

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.cycle)