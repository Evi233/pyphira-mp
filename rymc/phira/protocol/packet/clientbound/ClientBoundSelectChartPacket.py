"""Client-bound packet conveying the result of a select chart request.

There are two nested variants: ``Failed`` containing a reason string and
``Success`` which simply writes a success status. The outer class is
abstract and not meant to be instantiated.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundSelectChartPacket(ClientBoundPacket):
    """Base type for select chart responses.

    The base class carries no payload.  Two variants are defined below
    and attached to this class: ``Failed`` and ``Success``.
    """

    pass


class _ClientBoundSelectChartPacketFailed(ClientBoundSelectChartPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundSelectChartPacketSuccess(ClientBoundSelectChartPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants
ClientBoundSelectChartPacket.Failed = _ClientBoundSelectChartPacketFailed  # type: ignore[attr-defined]
ClientBoundSelectChartPacket.Success = _ClientBoundSelectChartPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundSelectChartPacket"]