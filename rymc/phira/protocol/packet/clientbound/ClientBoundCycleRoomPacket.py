"""Client-bound packet communicating the result of a cycle room request.

This packet has two variants:

* ``Failed``: includes a reason string explaining why the request failed.
* ``Success``: signifies that the cycle setting was successfully toggled.

The outer class does not itself implement ``encode``; use one of the
nested classes instead.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundCycleRoomPacket(ClientBoundPacket):
    """Base type for cycle room responses.

    This class defines the general type for cycle room responses but
    implements no encoding on its own.  Instead, use the attached
    ``Failed`` or ``Success`` variants defined below.
    """

    pass


class _ClientBoundCycleRoomPacketFailed(ClientBoundCycleRoomPacket):
    """Represents a failed cycle room attempt with a reason."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundCycleRoomPacketSuccess(ClientBoundCycleRoomPacket):
    """Represents a successful cycle room toggle."""

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants to the outer class
ClientBoundCycleRoomPacket.Failed = _ClientBoundCycleRoomPacketFailed  # type: ignore[attr-defined]
ClientBoundCycleRoomPacket.Success = _ClientBoundCycleRoomPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundCycleRoomPacket"]