"""Server-bound packet containing raw touch data."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundTouchesPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.data: bytes | None = None

    def decode(self, buf) -> None:
        # Copy all remaining bytes in the buffer as raw data
        length = buf.readableBytes()
        self.data = buf.readBytes(length) if length > 0 else b''

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleTouches(self)