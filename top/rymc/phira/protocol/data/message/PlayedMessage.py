"""Message containing the results of a player's performance.

Carries the user ID, score, accuracy and a boolean indicating a full
combo. The message ID is ``0x0B``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class PlayedMessage(Message):
    """Represents a player's performance at the end of a song."""

    user: int
    score: int
    accuracy: float
    fullCombo: bool

    def getMessageId(self) -> int:
        return 0x0B

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)
        PacketWriter.write(buf, self.score)
        PacketWriter.write(buf, self.accuracy)
        PacketWriter.write(buf, self.fullCombo)