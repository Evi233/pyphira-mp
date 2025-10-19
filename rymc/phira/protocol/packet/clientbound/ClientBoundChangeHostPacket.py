"""Client-bound packet indicating the player's host status has changed."""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...util.PacketWriter import PacketWriter


class ClientBoundChangeHostPacket(ClientBoundPacket):
    def __init__(self, isHost: bool) -> None:
        self.isHost = isHost

    def encode(self, buf) -> None:
        PacketWriter.write(buf, self.isHost)