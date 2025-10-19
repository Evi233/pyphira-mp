"""Encodes high-level client-bound packets into binary form.

The ``PacketEncoder`` wraps a :class:`ClientBoundPacket` into a
``ByteBuf`` containing the packet ID followed by the encoded payload.
It relies on :class:`PacketRegistry` to obtain the correct identifier
based on the runtime type of the packet. The resulting buffer can then
be further processed by the :class:`FrameEncoder` to add a length
prefix.
"""

from __future__ import annotations

from ...PacketRegistry import PacketRegistry
from ...packet.ClientBoundPacket import ClientBoundPacket
from ...util.ByteBuf import ByteBuf


class PacketEncoder:
    """Encodes client-bound packets using the registry."""

    @staticmethod
    def encode(packet: ClientBoundPacket) -> ByteBuf:
        """Encode the given packet into a new buffer containing its ID and payload.

        :param packet: the client-bound packet to encode
        :return: a read-only :class:`ByteBuf` containing the encoded packet
        """
        return PacketRegistry.encode(packet)


__all__ = ["PacketEncoder"]