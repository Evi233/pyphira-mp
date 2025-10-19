"""Message sent when a user creates a room.

This carries only the user ID of the creator. The corresponding Java
class writes the message ID ``0x01`` followed by the 32-bit user ID.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class CreateRoomMessage(Message):
    """Indicates that a user has created a new room."""

    user: int

    def getMessageId(self) -> int:
        return 0x01

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)