"""Server-bound packet to lock or unlock a room."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundLockRoomPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.lock: bool | None = None

    def decode(self, buf) -> None:
        # A single boolean value indicates the desired lock state
        self.lock = buf.readBoolean()

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleLockRoom(self)