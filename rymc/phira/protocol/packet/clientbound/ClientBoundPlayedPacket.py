"""Client-bound packet indicating the result of a play request.

Like many other packets, this type has ``Failed`` and ``Success``
variants. ``Failed`` includes a reason string; ``Success`` carries no
payload beyond the status byte. The outer class is not intended for
direct instantiation.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundPlayedPacket(ClientBoundPacket):
    """Base type for play request results.

    The outer type is abstract; instantiate one of its variants below.
    """

    pass


class _ClientBoundPlayedPacketFailed(ClientBoundPlayedPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundPlayedPacketSuccess(ClientBoundPlayedPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants
ClientBoundPlayedPacket.Failed = _ClientBoundPlayedPacketFailed  # type: ignore[attr-defined]
ClientBoundPlayedPacket.Success = _ClientBoundPlayedPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundPlayedPacket"]