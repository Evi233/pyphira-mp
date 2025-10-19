"""State classes representing the different phases of a game.

Game state objects are used both when transmitting room information and
when informing clients of state transitions. Each concrete state is
responsible for writing a unique type identifier byte (0x00–0x02) into
the buffer, mirroring the Java implementation. Additional fields may
follow depending on the state.
"""

from __future__ import annotations

from .GameState import GameState  # noqa: F401
from .SelectChart import SelectChart  # noqa: F401
from .Playing import Playing  # noqa: F401
from .WaitForReady import WaitForReady  # noqa: F401

__all__ = [
    "GameState",
    "SelectChart",
    "Playing",
    "WaitForReady",
]