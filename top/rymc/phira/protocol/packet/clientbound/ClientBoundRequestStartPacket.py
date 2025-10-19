"""Client-bound packet conveying the result of a request to start the game.

There are two nested variants: ``Failed`` with a reason string and
``Success`` which simply indicates the request was accepted. The outer
class is not meant to be instantiated directly.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundRequestStartPacket(ClientBoundPacket):
    """Base type for start request results.

    The outer class is abstract; use one of the variants defined below to
    represent a failed or successful request to start the game.
    """

    pass


class _ClientBoundRequestStartPacketFailed(ClientBoundRequestStartPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundRequestStartPacketSuccess(ClientBoundRequestStartPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants
ClientBoundRequestStartPacket.Failed = _ClientBoundRequestStartPacketFailed  # type: ignore[attr-defined]
ClientBoundRequestStartPacket.Success = _ClientBoundRequestStartPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundRequestStartPacket"]