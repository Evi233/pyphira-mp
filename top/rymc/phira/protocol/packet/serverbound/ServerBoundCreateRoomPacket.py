"""Server-bound packet to request creation of a new room."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from ...util import NettyPacketUtil
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundCreateRoomPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.roomId: str | None = None

    def decode(self, buf) -> None:
        # Room IDs are up to 20 characters in length
        self.roomId = NettyPacketUtil.readString(buf, 20)

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleCreateRoom(self)