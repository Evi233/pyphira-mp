"""Server-bound packet cancelling a previous ready state."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundCancelReadyPacket(ServerBoundPacket):
    def decode(self, buf) -> None:
        # No payload
        return None

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleCancelReady(self)