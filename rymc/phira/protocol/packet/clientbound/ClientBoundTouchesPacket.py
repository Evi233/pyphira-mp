"""Client-bound packet carrying raw touch input data back to a user.

Analogous to :class:`ClientBoundJudgesPacket`, this packet contains a
player identifier and a byte array representing touch events. The Java
implementation forwards the data verbatim and we follow suit here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ClientBoundPacket import ClientBoundPacket
from ...util.PacketWriter import PacketWriter
from ...util.ByteBuf import ByteBuf


@dataclass
class ClientBoundTouchesPacket(ClientBoundPacket):
    """Transmits raw touch data back to a client."""

    id: int
    touches: bytes

    def encode(self, buf: ByteBuf) -> None:
        PacketWriter.write(buf, self.id)
        buf.writeBytes(self.touches)


__all__ = ["ClientBoundTouchesPacket"]