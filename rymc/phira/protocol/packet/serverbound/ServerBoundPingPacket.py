"""Server-bound ping packet.

This packet contains no payload. When received the server should respond
immediately with a pong packet.
"""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundPingPacket(ServerBoundPacket):
    # Singleton instance, mirroring the Java code
    INSTANCE = None  # type: ServerBoundPingPacket | None

    def __new__(cls) -> 'ServerBoundPingPacket':
        # Ensure only one instance exists
        if cls.INSTANCE is None:
            cls.INSTANCE = super().__new__(cls)
        return cls.INSTANCE

    def decode(self, buf) -> None:
        # No payload to decode
        return None

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handlePing(self)