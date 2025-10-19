"""Message indicating that the game has been cancelled.

This uses message ID ``0x09`` and includes the user who cancelled.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class CancelGameMessage(Message):
    """Indicates that a user has cancelled the game."""

    user: int

    def getMessageId(self) -> int:
        return 0x09

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)