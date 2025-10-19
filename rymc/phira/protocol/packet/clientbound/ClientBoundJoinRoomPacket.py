"""Client-bound packet indicating the result of a join room request.

This packet reports whether joining a room failed or succeeded. On
success it carries the current :class:`GameState`, lists of
participants and monitors, and a live flag. The structure parallels the
Java implementation.
"""

from __future__ import annotations

from typing import List

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter
from ...data.state.GameState import GameState
from ...data.UserProfile import UserProfile


class ClientBoundJoinRoomPacket(ClientBoundPacket):
    """Base type for join room responses.

    The outer class represents the general form of a join room result but
    carries no data itself.  Use either the ``Failed`` or ``Success`` variant
    attached to this type to construct concrete responses.
    """

    pass


# Failure variant including a reason.
class _ClientBoundJoinRoomPacketFailed(ClientBoundJoinRoomPacket):
    """Represents a failed join room attempt with a reason."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


# Success variant carrying state, participants and live flag.
class _ClientBoundJoinRoomPacketSuccess(ClientBoundJoinRoomPacket):
    """Represents a successful join room response."""

    def __init__(
        self,
        gameState: GameState,
        users: List[UserProfile],
        monitors: List[UserProfile],
        isLive: bool,
    ) -> None:
        self.gameState = gameState
        self.users = users
        self.monitors = monitors
        self.isLive = isLive

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)
        PacketWriter.write(buf, self.gameState)
        # Write total number of participants as a byte
        total = len(self.users) + len(self.monitors)
        PacketWriter.writeByte(buf, total)
        # Encode users with monitor flag False
        for user in self.users:
            PacketWriter.write(buf, user)
            PacketWriter.write(buf, False)
        # Encode monitors with monitor flag True
        for monitor in self.monitors:
            PacketWriter.write(buf, monitor)
            PacketWriter.write(buf, True)
        PacketWriter.write(buf, self.isLive)


# Bind variants to the outer class
ClientBoundJoinRoomPacket.Failed = _ClientBoundJoinRoomPacketFailed  # type: ignore[attr-defined]
ClientBoundJoinRoomPacket.Success = _ClientBoundJoinRoomPacketSuccess  # type: ignore[attr-defined]


__all__ = ["ClientBoundJoinRoomPacket"]