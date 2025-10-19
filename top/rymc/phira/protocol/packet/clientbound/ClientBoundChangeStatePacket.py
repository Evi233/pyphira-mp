"""Client-bound packet instructing the client to change game state."""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.state.GameState import GameState
from ...util.PacketWriter import PacketWriter


class ClientBoundChangeStatePacket(ClientBoundPacket):
    def __init__(self, gameState: GameState) -> None:
        self.gameState = gameState

    def encode(self, buf) -> None:
        PacketWriter.write(buf, self.gameState)