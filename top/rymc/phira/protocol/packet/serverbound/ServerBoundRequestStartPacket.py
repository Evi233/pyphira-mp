"""Server-bound packet requesting to start the game."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundRequestStartPacket(ServerBoundPacket):
    def decode(self, buf) -> None:
        # No payload
        return None

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleRequestStart(self)