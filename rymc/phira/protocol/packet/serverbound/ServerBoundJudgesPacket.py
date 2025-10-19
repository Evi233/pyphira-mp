"""Server-bound packet carrying judge data as raw bytes."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundJudgesPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.data: bytes | None = None

    def decode(self, buf) -> None:
        length = buf.readableBytes()
        self.data = buf.readBytes(length) if length > 0 else b''

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleJudges(self)