"""Abstract handler for all server-bound packets.

When a server-bound packet is received, the network layer will invoke
``handle`` on the packet, passing in an implementation of ``PacketHandler``.
The appropriate method corresponding to the packet type is then called.
Implementers should override each method to provide custom logic.
"""

from __future__ import annotations

from ..packet.serverbound.ServerBoundAbortPacket import ServerBoundAbortPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundAuthenticatePacket import ServerBoundAuthenticatePacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundCancelReadyPacket import ServerBoundCancelReadyPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundChatPacket import ServerBoundChatPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundCreateRoomPacket import ServerBoundCreateRoomPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundCycleRoomPacket import ServerBoundCycleRoomPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundJoinRoomPacket import ServerBoundJoinRoomPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundJudgesPacket import ServerBoundJudgesPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundLeaveRoomPacket import ServerBoundLeaveRoomPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundLockRoomPacket import ServerBoundLockRoomPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundPingPacket import ServerBoundPingPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundPlayedPacket import ServerBoundPlayedPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundReadyPacket import ServerBoundReadyPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundRequestStartPacket import ServerBoundRequestStartPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundSelectChartPacket import ServerBoundSelectChartPacket  # type: ignore circular import
from ..packet.serverbound.ServerBoundTouchesPacket import ServerBoundTouchesPacket  # type: ignore circular import


class PacketHandler:
    """Base class defining handlers for each server-bound packet type."""

    def handle(self, packet):
        """
        Generic entry point invoked by a server-bound packet. The packet
        implementation will call this method, passing itself, so we can
        dispatch onto the appropriate handler method by type.
        """
        # Dispatch based on the packet's class
        if isinstance(packet, ServerBoundPingPacket):
            return self.handlePing(packet)
        if isinstance(packet, ServerBoundAuthenticatePacket):
            return self.handleAuthenticate(packet)
        if isinstance(packet, ServerBoundChatPacket):
            return self.handleChat(packet)
        if isinstance(packet, ServerBoundTouchesPacket):
            return self.handleTouches(packet)
        if isinstance(packet, ServerBoundJudgesPacket):
            return self.handleJudges(packet)
        if isinstance(packet, ServerBoundCreateRoomPacket):
            return self.handleCreateRoom(packet)
        if isinstance(packet, ServerBoundJoinRoomPacket):
            return self.handleJoinRoom(packet)
        if isinstance(packet, ServerBoundLeaveRoomPacket):
            return self.handleLeaveRoom(packet)
        if isinstance(packet, ServerBoundLockRoomPacket):
            return self.handleLockRoom(packet)
        if isinstance(packet, ServerBoundCycleRoomPacket):
            return self.handleCycleRoom(packet)
        if isinstance(packet, ServerBoundSelectChartPacket):
            return self.handleSelectChart(packet)
        if isinstance(packet, ServerBoundRequestStartPacket):
            return self.handleRequestStart(packet)
        if isinstance(packet, ServerBoundReadyPacket):
            return self.handleReady(packet)
        if isinstance(packet, ServerBoundCancelReadyPacket):
            return self.handleCancelReady(packet)
        if isinstance(packet, ServerBoundPlayedPacket):
            return self.handlePlayed(packet)
        if isinstance(packet, ServerBoundAbortPacket):
            return self.handleAbort(packet)
        # Unknown packet: no-op by default
        return None

    # The methods below are intended to be overridden by subclasses.
    def handlePing(self, packet: ServerBoundPingPacket) -> None:
        raise NotImplementedError

    def handleAuthenticate(self, packet: ServerBoundAuthenticatePacket) -> None:
        raise NotImplementedError

    def handleChat(self, packet: ServerBoundChatPacket) -> None:
        raise NotImplementedError

    def handleTouches(self, packet: ServerBoundTouchesPacket) -> None:
        raise NotImplementedError

    def handleJudges(self, packet: ServerBoundJudgesPacket) -> None:
        raise NotImplementedError

    def handleCreateRoom(self, packet: ServerBoundCreateRoomPacket) -> None:
        raise NotImplementedError

    def handleJoinRoom(self, packet: ServerBoundJoinRoomPacket) -> None:
        raise NotImplementedError

    def handleLeaveRoom(self, packet: ServerBoundLeaveRoomPacket) -> None:
        raise NotImplementedError

    def handleLockRoom(self, packet: ServerBoundLockRoomPacket) -> None:
        raise NotImplementedError

    def handleCycleRoom(self, packet: ServerBoundCycleRoomPacket) -> None:
        raise NotImplementedError

    def handleSelectChart(self, packet: ServerBoundSelectChartPacket) -> None:
        raise NotImplementedError

    def handleRequestStart(self, packet: ServerBoundRequestStartPacket) -> None:
        raise NotImplementedError

    def handleReady(self, packet: ServerBoundReadyPacket) -> None:
        raise NotImplementedError

    def handleCancelReady(self, packet: ServerBoundCancelReadyPacket) -> None:
        raise NotImplementedError

    def handlePlayed(self, packet: ServerBoundPlayedPacket) -> None:
        raise NotImplementedError

    def handleAbort(self, packet: ServerBoundAbortPacket) -> None:
        raise NotImplementedError