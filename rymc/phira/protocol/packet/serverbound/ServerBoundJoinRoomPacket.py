"""Server-bound packet to join an existing room."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from ...util import NettyPacketUtil
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundJoinRoomPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.roomId: str | None = None
        self.monitor: bool | None = None

    def decode(self, buf) -> None:
        self.roomId = NettyPacketUtil.readString(buf, 20)
        self.monitor = buf.readBoolean()

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleJoinRoom(self)