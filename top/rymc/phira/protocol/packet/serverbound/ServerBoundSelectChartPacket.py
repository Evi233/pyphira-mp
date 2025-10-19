"""Server-bound packet selecting a chart by its ID."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundSelectChartPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.id: int | None = None

    def decode(self, buf) -> None:
        # Read an int in little-endian order
        self.id = buf.readIntLE()

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleSelectChart(self)