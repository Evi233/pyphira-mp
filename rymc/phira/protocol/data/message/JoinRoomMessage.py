"""Message indicating that a user has joined a room.

The Java ``JoinRoomMessage`` carries the user's ID and their chosen
username. It writes the message ID ``0x02`` followed by those fields.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class JoinRoomMessage(Message):
    """Represents a user joining a room."""

    user: int
    name: str

    def getMessageId(self) -> int:
        return 0x02

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)
        PacketWriter.write(buf, self.name)