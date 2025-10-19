"""Represents the state where a chart is being selected.

When encoded, this state writes a discriminator byte ``0x00`` followed by
a boolean indicating whether a chart ID is present. If the boolean is
``True``, the chart ID (an integer) is written immediately afterwards in
little-endian form.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ...util.ByteBuf import ByteBuf
from ..state.GameState import GameState
# Using a relative import to reach the util.PacketWriter module. We are currently
# within ``top/rymc/phira/protocol/data/state``, so three dots climbs up to
# ``top/rymc/phira/protocol``. From there we import PacketWriter.
from ...util.PacketWriter import PacketWriter  # type: ignore


@dataclass
class SelectChart(GameState):
    """State indicating the chart selection phase of the game."""

    chartId: Optional[int] = None

    def encode(self, buf: ByteBuf) -> None:
        # Discriminator for SelectChart is 0x00
        buf.writeByte(0x00)
        has_id = self.chartId is not None
        # Write presence flag as boolean
        PacketWriter.write(buf, has_id)
        if has_id:
            # Write the integer chart ID in little-endian form
            PacketWriter.write(buf, self.chartId)

    def __str__(self) -> str:  # pragma: no cover
        return f"SelectChart(chartId={self.chartId!r})"