"""Message indicating that the current session has been aborted.

This message uses ID ``0x0D`` and carries the user ID of the aborting
player.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class AbortMessage(Message):
    """Represents a user aborting the current session."""

    user: int

    def getMessageId(self) -> int:
        return 0x0D

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)