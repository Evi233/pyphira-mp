"""Registry of packet identifiers and their corresponding classes.

This module is a Python translation of the Java ``PacketRegistry``. It
provides functionality for decoding server-bound packets from a
:class:`ByteBuf` and encoding client-bound packets into a new buffer.
Internally it maintains two dictionaries: one mapping numeric packet
identifiers to the appropriate server-bound packet class, and the other
mapping client-bound packet classes to their identifier.

When adding new packet types, ensure that they are registered in the
appropriate dictionary. The ordering of class checks when encoding is
important: Python's ``issubclass`` is used to account for inheritance.
"""

from __future__ import annotations

from typing import Callable, Dict, Type, TypeVar

from .codec import Decodeable
from .exception.CodecException import CodecException
from .util.ByteBuf import ByteBuf

from .packet.ServerBoundPacket import ServerBoundPacket
from .packet.ClientBoundPacket import ClientBoundPacket

from .packet.serverbound import (
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

from .packet.clientbound import (
    ClientBoundPongPacket,
    ClientBoundAuthenticatePacket,
    ClientBoundChatPacket,
    ClientBoundTouchesPacket,
    ClientBoundJudgesPacket,
    ClientBoundMessagePacket,
    ClientBoundChangeStatePacket,
    ClientBoundChangeHostPacket,
    ClientBoundCreateRoomPacket,
    ClientBoundJoinRoomPacket,
    ClientBoundOnJoinRoomPacket,
    ClientBoundLeaveRoomPacket,
    ClientBoundLockRoomPacket,
    ClientBoundCycleRoomPacket,
    ClientBoundSelectChartPacket,
    ClientBoundRequestStartPacket,
    ClientBoundReadyPacket,
    ClientBoundCancelReadyPacket,
    ClientBoundPlayedPacket,
    ClientBoundAbortPacket,
)


class PacketRegistry:
    """Utility class for encoding and decoding packets."""

    # Mapping from packet ID to a constructor function for server-bound packets.
    _client_bound_packet_map: Dict[int, Type[ServerBoundPacket]] = {
        0x00: ServerBoundPingPacket,
        0x01: ServerBoundAuthenticatePacket,
        0x02: ServerBoundChatPacket,
        0x03: ServerBoundTouchesPacket,
        0x04: ServerBoundJudgesPacket,
        0x05: ServerBoundCreateRoomPacket,
        0x06: ServerBoundJoinRoomPacket,
        0x07: ServerBoundLeaveRoomPacket,
        0x08: ServerBoundLockRoomPacket,
        0x09: ServerBoundCycleRoomPacket,
        0x0A: ServerBoundSelectChartPacket,
        0x0B: ServerBoundRequestStartPacket,
        0x0C: ServerBoundReadyPacket,
        0x0D: ServerBoundCancelReadyPacket,
        0x0E: ServerBoundPlayedPacket,
        0x0F: ServerBoundAbortPacket,
    }

    # Mapping from client-bound packet classes to packet IDs.
    _server_bound_packet_map: Dict[Type[ClientBoundPacket], int] = {
        ClientBoundPongPacket: 0x00,
        ClientBoundAuthenticatePacket: 0x01,
        ClientBoundChatPacket: 0x02,
        ClientBoundTouchesPacket: 0x03,
        ClientBoundJudgesPacket: 0x04,
        ClientBoundMessagePacket: 0x05,
        ClientBoundChangeStatePacket: 0x06,
        ClientBoundChangeHostPacket: 0x07,
        ClientBoundCreateRoomPacket: 0x08,
        ClientBoundJoinRoomPacket: 0x09,
        ClientBoundOnJoinRoomPacket: 0x0A,
        ClientBoundLeaveRoomPacket: 0x0B,
        ClientBoundLockRoomPacket: 0x0C,
        ClientBoundCycleRoomPacket: 0x0D,
        ClientBoundSelectChartPacket: 0x0E,
        ClientBoundRequestStartPacket: 0x0F,
        ClientBoundReadyPacket: 0x10,
        ClientBoundCancelReadyPacket: 0x11,
        ClientBoundPlayedPacket: 0x12,
        ClientBoundAbortPacket: 0x13,
    }

    @staticmethod
    def decode(buf: ByteBuf) -> ServerBoundPacket:
        """Decode a server-bound packet from the given buffer.

        The first byte read from the buffer is treated as the packet ID. If
        the ID is unknown a :class:`CodecException` is raised. Otherwise a
        new instance of the corresponding packet class is created and its
        ``decode`` method is invoked with the buffer. The fully populated
        packet is then returned.

        :param buf: buffer containing the packet body
        :raises CodecException: if the packet ID is not registered
        :return: a new instance of the appropriate :class:`ServerBoundPacket`
        """
        if not buf.isReadable():
            raise CodecException("Empty buffer provided for packet decoding")
        packet_id = buf.readUnsignedByte()
        packet_class = PacketRegistry._client_bound_packet_map.get(packet_id)
        if packet_class is None:
            raise CodecException(f"Unknown ServerBound packet id: {packet_id}")
        packet = packet_class()  # type: ignore[call-arg]
        packet.decode(buf)
        return packet

    @staticmethod
    def encode(packet: ClientBoundPacket) -> ByteBuf:
        """Encode a client-bound packet into a new read-only buffer.

        This method looks up the packet's class (or a superclass) in the
        ``_server_bound_packet_map``. The first mapping entry where the
        registered class is a superclass of the packet's class is chosen.
        The resulting buffer contains the packet ID byte followed by the
        encoded payload.

        :param packet: the packet to encode
        :raises CodecException: if the packet class is not registered
        :return: a read-only :class:`ByteBuf` containing the encoded packet
        """
        packet_cls = packet.__class__
        packet_id: int | None = None
        for registered_cls, pid in PacketRegistry._server_bound_packet_map.items():
            if issubclass(packet_cls, registered_cls):
                packet_id = pid
                break
        if packet_id is None:
            raise CodecException(f"Unknown ClientBound packet class: {packet_cls.__name__}")
        buf = ByteBuf()
        buf.writeByte(packet_id)
        packet.encode(buf)
        return buf.asReadOnly()


__all__ = ["PacketRegistry"]