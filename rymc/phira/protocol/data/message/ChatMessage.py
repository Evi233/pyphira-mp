"""A chat message broadcast to participants in a room.

This corresponds to the Java ``ChatMessage`` class. It carries the
identifier of the user who sent the message along with the message
contents. The message ID for chat messages is ``0x00``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class ChatMessage(Message):
    """Represents a textual chat message sent by a user."""

    user: int
    content: str

    def getMessageId(self) -> int:
        return 0x00

    def encode(self, buf: ByteBuf) -> None:
        # First write message ID, then the user ID and content
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)
        PacketWriter.write(buf, self.content)