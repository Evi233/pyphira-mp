"""Client-bound packet conveying the result of an authentication request."""

from __future__ import annotations

from typing import Optional

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...data.UserProfile import UserProfile
from ...data.RoomInfo import RoomInfo
from ...data.FullUserProfile import FullUserProfile
from ...util.PacketWriter import PacketWriter


class ClientBoundAuthenticatePacket(ClientBoundPacket):
    """Client-bound packet conveying the result of an authentication request.

    The outer class itself carries no payload.  Instead, use one of the
    variants defined below: ``Failed`` for failed authentication attempts
    and ``Success`` for successful logins.  These variants are attached as
    attributes on this class to emulate Java-style nested classes.
    """

    pass


# ``Failed`` variant carrying a failure reason.
class _ClientBoundAuthenticatePacketFailed(ClientBoundAuthenticatePacket):
    """Represents a failed authentication attempt."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


# ``Success`` variant containing user profile, monitor flag and optional room info.
class _ClientBoundAuthenticatePacketSuccess(ClientBoundAuthenticatePacket):
    """Represents a successful authentication response.

    In the latest protocol the monitor flag is incorporated into the
    ``FullUserProfile``.  When encoding, the provided ``UserProfile`` and
    ``isMonitor`` flag are wrapped into a single ``FullUserProfile``
    instance and written to the buffer.  A subsequent boolean indicates
    whether room information is present, followed by the ``RoomInfo`` if
    provided.
    """

    def __init__(self, userProfile: UserProfile, isMonitor: bool, roomInfo: Optional[RoomInfo] = None) -> None:
        self.userProfile = userProfile
        self.isMonitor = isMonitor
        self.roomInfo = roomInfo

    def encode(self, buf) -> None:
        # Success flag
        PacketWriter.write(buf, PacketResult.SUCCESS)
        # Compose a FullUserProfile to include the monitor flag in the user encoding
        full_profile = FullUserProfile(self.userProfile, self.isMonitor)
        PacketWriter.write(buf, full_profile)
        # Indicate and write optional room info
        hasRoomInfo = self.roomInfo is not None
        PacketWriter.write(buf, hasRoomInfo)
        if hasRoomInfo:
            PacketWriter.write(buf, self.roomInfo)


# Bind variants to the outer class
ClientBoundAuthenticatePacket.Failed = _ClientBoundAuthenticatePacketFailed  # type: ignore[attr-defined]
ClientBoundAuthenticatePacket.Success = _ClientBoundAuthenticatePacketSuccess  # type: ignore[attr-defined]