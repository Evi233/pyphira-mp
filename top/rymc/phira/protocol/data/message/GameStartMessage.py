"""Message indicating that the game has started.

The game start message uses message ID ``0x06`` and encodes only the
ID of the user who initiated the start.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class GameStartMessage(Message):
    """Indicates that a user has started the game."""

    user: int

    def getMessageId(self) -> int:
        return 0x06

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)