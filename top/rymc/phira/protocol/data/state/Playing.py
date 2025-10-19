"""Represents the state where the game is actively being played.

When encoded this state writes a single byte ``0x02``. No additional
information follows the discriminator.
"""

from __future__ import annotations

from ...util.ByteBuf import ByteBuf
from .GameState import GameState


class Playing(GameState):
    """Game is currently in progress."""

    def encode(self, buf: ByteBuf) -> None:
        # Discriminator for Playing is 0x02
        buf.writeByte(0x02)

    def __str__(self) -> str:  # pragma: no cover
        return "Playing"