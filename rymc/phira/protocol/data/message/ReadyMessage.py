"""Message indicating that a user is ready.

Uses message ID ``0x07`` followed by the user ID.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class ReadyMessage(Message):
    """Represents a user signalling readiness to start playing."""

    user: int

    def getMessageId(self) -> int:
        return 0x07

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)