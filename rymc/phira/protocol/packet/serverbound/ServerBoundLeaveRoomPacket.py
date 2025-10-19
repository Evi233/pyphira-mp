"""Server-bound packet to leave the current room."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundLeaveRoomPacket(ServerBoundPacket):
    def decode(self, buf) -> None:
        # No payload for leave room
        return None

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleLeaveRoom(self)