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
from .state.GameState import GameState
from .UserProfile import UserProfile


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

        The fields are encoded in the order they appear in the constructor.
        After writing all fixed fields, the counts and entries for users and
        monitors are appended. Each profile is followed by a boolean flag
        indicating whether it is a monitor (``True``) or a normal user
        (``False``).

        :param buf: buffer to write into
        """
        PacketWriter.write(buf, self.roomId)
        PacketWriter.write(buf, self.state)
        PacketWriter.write(buf, self.live)
        PacketWriter.write(buf, self.locked)
        PacketWriter.write(buf, self.cycle)
        PacketWriter.write(buf, self.isHost)
        PacketWriter.write(buf, self.isReady)
        # Write total number of participants as a single byte
        total = len(self.users) + len(self.monitors)
        PacketWriter.writeByte(buf, total)
        # Encode users first with monitor flag = False
        for user in self.users:
            PacketWriter.write(buf, user)
            PacketWriter.write(buf, False)
        # Encode monitors with monitor flag = True
        for monitor in self.monitors:
            PacketWriter.write(buf, monitor)
            PacketWriter.write(buf, True)


__all__ = ["RoomInfo"]