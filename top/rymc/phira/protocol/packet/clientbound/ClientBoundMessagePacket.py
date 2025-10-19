"""Client-bound packet carrying an arbitrary message.

This packet wraps a :class:`~top.rymc.phira.protocol.data.message.Message`
instance and encodes it using :class:`PacketWriter`. The Java
``ClientBoundMessagePacket`` simply writes the message to the buffer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ClientBoundPacket import ClientBoundPacket
from ...data.message.Message import Message
from ...util.PacketWriter import PacketWriter


@dataclass
class ClientBoundMessagePacket(ClientBoundPacket):
    """Wraps a message that the client should display or act upon."""

    message: Message

    def encode(self, buf) -> None:
        PacketWriter.write(buf, self.message)


__all__ = ["ClientBoundMessagePacket"]