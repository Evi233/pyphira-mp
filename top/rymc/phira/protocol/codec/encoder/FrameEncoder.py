"""Low-level frame encoder that prepends a length prefix to packet bodies.

This class mirrors the behaviour of the Java ``FrameEncoder``. It takes a
:class:`ByteBuf` containing a packet body (without identifier or length),
writes its length as a VarInt into a new buffer, and then writes the
packet body bytes. The resulting buffer can be sent directly over the
network. A ``FrameEncoder`` does not know about packet identifiers; it
only deals with length-prefixing.
"""

from __future__ import annotations

from ...util.ByteBuf import ByteBuf
from ...util.NettyPacketUtil import encodeVarInt


class FrameEncoder:
    """Encodes a packet body with a VarInt length prefix."""

    @staticmethod
    def encode(body: ByteBuf) -> ByteBuf:
        """Return a new buffer containing a VarInt length prefix and body bytes.

        :param body: a buffer containing the packet body
        :return: a new :class:`ByteBuf` with the length prefix and body
        """
        length = body.readableBytes()
        out = ByteBuf()
        # Write the length using VarInt encoding
        encodeVarInt(out, length)
        # Write the packet body bytes
        out.writeBytes(body.toBytes())
        return out


__all__ = ["FrameEncoder"]