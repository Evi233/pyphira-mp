"""Client-bound packet communicating the result of a leave room request.

This packet has two variants: ``Failed``, which carries a reason, and
``Success``, which simply indicates success. The outer class is not
intended to be encoded directly.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundLeaveRoomPacket(ClientBoundPacket):
    """Base type for leave room responses.

    The outer class itself does not implement an ``encode`` method.  Use
    the attached ``Failed`` or ``Success`` variants instead.
    """

    pass


class _ClientBoundLeaveRoomPacketFailed(ClientBoundLeaveRoomPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundLeaveRoomPacketSuccess(ClientBoundLeaveRoomPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants
ClientBoundLeaveRoomPacket.Failed = _ClientBoundLeaveRoomPacketFailed  # type: ignore[attr-defined]
ClientBoundLeaveRoomPacket.Success = _ClientBoundLeaveRoomPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundLeaveRoomPacket"]