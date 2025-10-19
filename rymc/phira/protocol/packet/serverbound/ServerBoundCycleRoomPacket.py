"""Server-bound packet toggling the cycle state of a room."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundCycleRoomPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.cycle: bool | None = None

    def decode(self, buf) -> None:
        self.cycle = buf.readBoolean()

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleCycleRoom(self)