"""Message indicating that playing should commence immediately.

This message uses identifier ``0x0A`` and has no payload beyond the ID.
"""

from __future__ import annotations

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


class StartPlayingMessage(Message):
    """Signals that the gameplay should start now."""

    def getMessageId(self) -> int:
        return 0x0A

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())