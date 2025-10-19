"""Server-bound authenticate packet containing an authentication token."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from ...util import NettyPacketUtil
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundAuthenticatePacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.token: str | None = None

    def decode(self, buf) -> None:
        # The token is a VarInt-prefaced string up to 32 bytes
        self.token = NettyPacketUtil.readString(buf, 32)

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleAuthenticate(self)