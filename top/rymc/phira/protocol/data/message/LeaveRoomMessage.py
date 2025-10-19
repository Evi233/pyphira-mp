"""Message indicating that a user has left a room.

The Java ``LeaveRoomMessage`` encodes the message ID ``0x03`` followed by
the user ID and the user's name. We replicate that behaviour here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class LeaveRoomMessage(Message):
    """Represents a user leaving a room."""

    user: int
    name: str

    def getMessageId(self) -> int:
        return 0x03

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)
        PacketWriter.write(buf, self.name)