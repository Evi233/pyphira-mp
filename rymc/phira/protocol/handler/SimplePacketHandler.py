"""A simple PacketHandler that replies to pings and provides empty hooks for others.

This mirrors the Java ``SimplePacketHandler`` which automatically responded
to ping packets with a pong. In this Python adaptation the handler accepts a
``channel`` object which is expected to expose a ``write_and_flush`` method.
All other packet types are handled by no-op methods that can be overridden
by subclasses as needed.
"""

from __future__ import annotations

from connection import Connection
from ..packet.clientbound.ClientBoundPongPacket import ClientBoundPongPacket
from ..packet.serverbound import (
    ServerBoundPingPacket,
    ServerBoundAuthenticatePacket,
    ServerBoundChatPacket,
    ServerBoundTouchesPacket,
    ServerBoundJudgesPacket,
    ServerBoundCreateRoomPacket,
    ServerBoundJoinRoomPacket,
    ServerBoundLeaveRoomPacket,
    ServerBoundLockRoomPacket,
    ServerBoundCycleRoomPacket,
    ServerBoundSelectChartPacket,
    ServerBoundRequestStartPacket,
    ServerBoundReadyPacket,
    ServerBoundCancelReadyPacket,
    ServerBoundPlayedPacket,
    ServerBoundAbortPacket,
)
from .PacketHandler import PacketHandler


class SimplePacketHandler(PacketHandler):
    """PacketHandler implementation that sends a pong response to a ping."""

    def __init__(self, connection: Connection) -> None:
        # The channel object should provide a ``write_and_flush`` method. It is
        # intentionally kept generic so this handler can be used in different
        # networking contexts.
        self.connection = connection

    # Override only the ping handler to automatically reply with a pong
    def handlePing(self, packet: ServerBoundPingPacket) -> None:
        # Send back a singleton pong packet
        self.connection.send(ClientBoundPongPacket.INSTANCE)

    # The remaining handlers are provided as no-ops and can be overridden in
    # subclasses. They simply return without performing any action.
    def handleAuthenticate(self, packet: ServerBoundAuthenticatePacket) -> None:
        return None

    def handleChat(self, packet: ServerBoundChatPacket) -> None:
        return None

    def handleTouches(self, packet: ServerBoundTouchesPacket) -> None:
        return None

    def handleJudges(self, packet: ServerBoundJudgesPacket) -> None:
        return None

    def handleCreateRoom(self, packet: ServerBoundCreateRoomPacket) -> None:
        return None

    def handleJoinRoom(self, packet: ServerBoundJoinRoomPacket) -> None:
        return None

    def handleLeaveRoom(self, packet: ServerBoundLeaveRoomPacket) -> None:
        return None

    def handleLockRoom(self, packet: ServerBoundLockRoomPacket) -> None:
        return None

    def handleCycleRoom(self, packet: ServerBoundCycleRoomPacket) -> None:
        return None

    def handleSelectChart(self, packet: ServerBoundSelectChartPacket) -> None:
        return None

    def handleRequestStart(self, packet: ServerBoundRequestStartPacket) -> None:
        return None

    def handleReady(self, packet: ServerBoundReadyPacket) -> None:
        return None

    def handleCancelReady(self, packet: ServerBoundCancelReadyPacket) -> None:
        return None

    def handlePlayed(self, packet: ServerBoundPlayedPacket) -> None:
        return None

    def handleAbort(self, packet: ServerBoundAbortPacket) -> None:
        return None