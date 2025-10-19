"""Represents the state where players are getting ready to play.

This state is encoded as a single byte ``0x01`` according to the Java
implementation. No additional data follows the identifier.
"""

from __future__ import annotations

from ...util.ByteBuf import ByteBuf
from .GameState import GameState


class WaitForReady(GameState):
    """Game is waiting for all players to signal readiness."""

    def encode(self, buf: ByteBuf) -> None:
        # Type discriminator for WaitForReady is 0x01
        buf.writeByte(0x01)

    def __str__(self) -> str:  # pragma: no cover
        return "WaitForReady"