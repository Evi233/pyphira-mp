"""Client-bound packet notifying others when a user joins a room.

This packet carries the new user's :class:`UserProfile` and a boolean
indicating whether they joined as a monitor. The Java version writes
these fields in that order.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ClientBoundPacket import ClientBoundPacket
from ...data.UserProfile import UserProfile
from ...data.FullUserProfile import FullUserProfile
from ...util.PacketWriter import PacketWriter


@dataclass
class ClientBoundOnJoinRoomPacket(ClientBoundPacket):
    """Informs clients that a new user has joined the room."""

    userProfile: UserProfile
    monitor: bool

    def encode(self, buf) -> None:
        """Encode this notification using a ``FullUserProfile`` wrapper.

        The updated protocol bundles the monitor flag within the profile,
        so construct a ``FullUserProfile`` and write it directly.
        """
        full_profile = FullUserProfile(self.userProfile, self.monitor)
        PacketWriter.write(buf, full_profile)


__all__ = ["ClientBoundOnJoinRoomPacket"]