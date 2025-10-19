"""Message indicating that the game has ended.

The Java ``GameEndMessage`` writes only the message ID ``0x0C`` and no
additional data. We follow the same pattern here.
"""

from __future__ import annotations

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


class GameEndMessage(Message):
    """Indicates that the current game session has ended."""

    def getMessageId(self) -> int:
        return 0x0C

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())