"""Client-bound packet communicating the result of a lock room request.

The ``Failed`` variant includes a human-readable reason, whereas the
``OK`` variant signals success without further payload. The outer class
itself is not meant to be instantiated.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundLockRoomPacket(ClientBoundPacket):
    """Base type for lock room responses.

    The outer class provides no direct ``encode`` implementation.  Two
    variant classes are defined below:

    * ``Failed`` — includes a failure reason.
    * ``OK`` — indicates a successful lock room operation.
    """

    pass


class _ClientBoundLockRoomPacketFailed(ClientBoundLockRoomPacket):
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundLockRoomPacketSuccess(ClientBoundLockRoomPacket):
    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Bind variants
ClientBoundLockRoomPacket.Failed = _ClientBoundLockRoomPacketFailed  # type: ignore[attr-defined]
ClientBoundLockRoomPacket.Success = _ClientBoundLockRoomPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundLockRoomPacket"]