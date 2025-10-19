"""Server-bound chat packet carrying a message string."""

from __future__ import annotations

from ..ServerBoundPacket import ServerBoundPacket
from ...util import NettyPacketUtil
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ...handler.PacketHandler import PacketHandler


class ServerBoundChatPacket(ServerBoundPacket):
    def __init__(self) -> None:
        self.message: str | None = None

    def decode(self, buf) -> None:
        # Read up to 200 characters of UTF-8 text
        self.message = NettyPacketUtil.readString(buf, 200)

    def handle(self, handler: 'PacketHandler') -> None:
        handler.handleChat(self)