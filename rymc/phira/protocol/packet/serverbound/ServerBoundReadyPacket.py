"""Server-bound packet indicating the player is ready."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundReadyPacket(ServerBoundPacket):
    def decode(self, buf) -> None:
        # No payload
        return None

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleReady(self)