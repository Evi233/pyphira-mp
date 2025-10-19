"""Message indicating a user has selected a chart.

This class corresponds to the Java ``SelectChartMessage``. It is encoded
with message ID ``0x05`` followed by the user ID, chart name and chart
identifier.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter
from .Message import Message


@dataclass
class SelectChartMessage(Message):
    """Represents a user selecting a chart to play."""

    user: int
    name: str
    id: int

    def getMessageId(self) -> int:
        return 0x05

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.writeByte(buf, self.getMessageId())
        PacketWriter.write(buf, self.user)
        PacketWriter.write(buf, self.name)
        PacketWriter.write(buf, self.id)