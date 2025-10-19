"""Message indicating that a user has cancelled their ready state.

This uses message ID ``0x08`` and carries only the user ID.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class CancelReadyMessage(Message):
    """Indicates that a previously ready user is no longer ready."""

    user: int

    def getMessageId(self) -> int:
        return 0x08

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)