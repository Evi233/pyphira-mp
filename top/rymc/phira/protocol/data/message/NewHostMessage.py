"""Message indicating a change of host in a room.

The message ID for ``NewHostMessage`` is ``0x04``. It carries the user
ID of the new host. This mirrors the Java class with the same name.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class NewHostMessage(Message):
    """Indicates that hosting privileges have been transferred to a new user."""

    user: int

    def getMessageId(self) -> int:
        return 0x04

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)