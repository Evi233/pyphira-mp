"""Client-bound packet carrying judge data for a particular user.

This packet is sent by the server to deliver raw judging data back to a
client. It contains the player's ID and a byte string representing the
judging information. The Java implementation bypasses parsing and
forwards the data verbatim; we adopt the same strategy here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ClientBoundPacket import ClientBoundPacket
from ...util.PacketWriter import PacketWriter
from ...util.ByteBuf import ByteBuf


@dataclass
class ClientBoundJudgesPacket(ClientBoundPacket):
    """Transmits raw judge data back to a client."""

    id: int
    judges: bytes

    def encode(self, buf: ByteBuf) -> None:
        # Write the player identifier
        PacketWriter.write(buf, self.id)
        # Append the raw judge byte array directly to the buffer
        buf.writeBytes(self.judges)


__all__ = ["ClientBoundJudgesPacket"]