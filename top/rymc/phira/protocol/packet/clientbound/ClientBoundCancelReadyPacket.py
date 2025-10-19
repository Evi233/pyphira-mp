"""Client-bound packet conveying the result of a cancel-ready request."""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundCancelReadyPacket(ClientBoundPacket):
    """Client-bound packet conveying the result of a cancel-ready request.

    The base type carries no payload.  Two variant classes are defined
    below and attached as attributes to this type:

    * ``Failed`` — includes a reason string indicating why the cancel-ready
      request could not be processed.
    * ``Success`` — indicates that the cancel-ready operation completed
      successfully.
    """

    pass


# Variant representing failure with a reason.
class _ClientBoundCancelReadyPacketFailed(ClientBoundCancelReadyPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


# Variant representing success with no additional payload.
class _ClientBoundCancelReadyPacketSuccess(ClientBoundCancelReadyPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind the variants to the outer class
ClientBoundCancelReadyPacket.Failed = _ClientBoundCancelReadyPacketFailed  # type: ignore[attr-defined]
ClientBoundCancelReadyPacket.Success = _ClientBoundCancelReadyPacketSuccess  # type: ignore[attr-defined]