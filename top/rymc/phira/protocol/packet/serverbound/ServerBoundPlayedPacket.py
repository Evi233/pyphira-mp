"""Server-bound packet indicating a song was played with a chart ID."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundPlayedPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.id: int | None = None

    def decode(self, buf) -> None:
        self.id = buf.readIntLE()

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handlePlayed(self)