"""Client-bound packet conveying the result of a create-room request."""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundCreateRoomPacket(ClientBoundPacket):
    """Client-bound packet conveying the result of a create-room request.

    The base type does not contain any payload.  Use either
    ``ClientBoundCreateRoomPacket.Failed`` or ``ClientBoundCreateRoomPacket.Success``
    to instantiate specific outcomes.  These variant classes are defined
    below and attached to this type as attributes.
    """

    pass


# Failed variant with a human-readable reason.
class _ClientBoundCreateRoomPacketFailed(ClientBoundCreateRoomPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


# Success variant carrying no additional data beyond the success flag.
class _ClientBoundCreateRoomPacketSuccess(ClientBoundCreateRoomPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Attach variants to the outer class
ClientBoundCreateRoomPacket.Failed = _ClientBoundCreateRoomPacketFailed  # type: ignore[attr-defined]
ClientBoundCreateRoomPacket.Success = _ClientBoundCreateRoomPacketSuccess  # type: ignore[attr-defined]