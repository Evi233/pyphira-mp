"""Information about a game room used in the Phira protocol.

``RoomInfo`` corresponds to the Java class of the same name. It encapsulates
metadata about a room, including its identifier, the current game state,
various flags and lists of participants. The ``encode`` method writes all
fields into a :class:`ByteBuf` in the same order as defined in the Java
version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..codec.Encodeable import Encodeable
from ..util.ByteBuf import ByteBuf
from ..util.PacketWriter import PacketWriter
from ..util.NettyPacketUtil import encodeVarInt
from .state.GameState import GameState
from .UserProfile import UserProfile
from .FullUserProfile import FullUserProfile


@dataclass
class RoomInfo(Encodeable):
    """Represents the full state of a game room at a point in time."""

    roomId: str
    state: GameState
    live: bool
    locked: bool
    cycle: bool
    isHost: bool
    isReady: bool
    users: List[UserProfile] = field(default_factory=list)
    monitors: List[UserProfile] = field(default_factory=list)

    def encode(self, buf: ByteBuf) -> None:
        """Write this room's information into the provided buffer.

        The encoding closely follows the latest Java protocol (jphira-mp-protocol
        v1.3.0).  After the fixed fields are written, the participants are
        encoded as a VarInt-length-prefixed list of ``FullUserProfile``
        instances.  For each profile, the user identifier is written first
        as a 32-bit little-endian integer followed by the full profile
        encoding (which writes the embedded ``UserProfile`` and monitor flag).

        :param buf: buffer to write into
        """
        # Fixed room metadata
        PacketWriter.write(buf, self.roomId)
        PacketWriter.write(buf, self.state)
        PacketWriter.write(buf, self.live)
        PacketWriter.write(buf, self.locked)
        PacketWriter.write(buf, self.cycle)
        PacketWriter.write(buf, self.isHost)
        PacketWriter.write(buf, self.isReady)
        # Construct FullUserProfile list preserving user/monitor separation
        full_profiles = FullUserProfile.from_lists(self.users, self.monitors)
        # Write the number of participants using VarInt encoding
        encodeVarInt(buf, len(full_profiles))
        # Write each entry: first the userId (int32 little-endian), then the full profile
        for profile in full_profiles:
            PacketWriter.write(buf, profile.userId)
            PacketWriter.write(buf, profile)


__all__ = ["RoomInfo"]