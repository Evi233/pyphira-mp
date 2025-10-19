"""Client-bound packet conveying the result of a ready request.

There are two nested variants: ``Failed`` with a reason string and
``Success`` with no payload other than the status byte. The outer class
is abstract and not directly instantiated.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundReadyPacket(ClientBoundPacket):
    """Base type for ready request results.

    This outer class is abstract; instantiate one of the variants below
    depending on whether the ready request was accepted or not.
    """

    pass


class _ClientBoundReadyPacketFailed(ClientBoundReadyPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundReadyPacketSuccess(ClientBoundReadyPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants
ClientBoundReadyPacket.Failed = _ClientBoundReadyPacketFailed  # type: ignore[attr-defined]
ClientBoundReadyPacket.Success = _ClientBoundReadyPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundReadyPacket"]