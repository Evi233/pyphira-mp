"""High-level packet decoder for server-bound packets.

This class accepts complete frames (with the length prefix removed) and
uses :class:`PacketRegistry` to turn them into instances of
``ServerBoundPacket``. It mimics the behaviour of the Java ``PacketDecoder``
class but does not interact with Netty channel handlers.
"""

from __future__ import annotations

from ...util.ByteBuf import ByteBuf
from ...PacketRegistry import PacketRegistry
from ...exception.CodecException import CodecException
from ...packet.ServerBoundPacket import ServerBoundPacket


class PacketDecoder:
    """Decode frames into server-bound packet instances."""

    @staticmethod
    def decode(frame: ByteBuf) -> ServerBoundPacket:
        """Decode a single frame into a :class:`ServerBoundPacket`.

        Delegates to :func:`PacketRegistry.decode`. The provided frame
        should contain only the packet body (length prefix removed).

        :param frame: the frame to decode
        :raises CodecException: if an unknown packet ID is encountered
        :return: a new instance of the decoded packet
        """
        return PacketRegistry.decode(frame)


__all__ = ["PacketDecoder"]