"""Simplified frame decoder for the Phira protocol.

In Netty the ``FrameDecoder`` is responsible for handling the initial
protocol version handshake and then slicing incoming bytes into packet
frames using a VarInt length prefix. The Python implementation here
provides similar functionality without relying on Netty constructs such
as channel handlers. It can be used with a :class:`ByteBuf` containing
data from a network stream.
"""

from __future__ import annotations

from typing import List, Optional

from ...util.ByteBuf import ByteBuf
from ...util.NettyPacketUtil import decodeVarInt
from ...exception.BadVarintException import BadVarintException
from ...exception.NeedMoreDataException import NeedMoreDataException


class FrameDecoder:
    """Performs protocol version negotiation and frame slicing."""

    # The only supported protocol version
    SUPPORTED_VERSIONS = {0x01}

    def __init__(self) -> None:
        # Once the version handshake has completed this will be set
        self.client_protocol_version: Optional[int] = None
        # Internal state: have we consumed the version byte yet?
        self._handshake_done: bool = False

    def decode(self, buf: ByteBuf) -> List[ByteBuf]:
        """Decode one or more complete frames from the given buffer.

        If the handshake has not yet been completed, the first byte will
        be interpreted as the client protocol version. After handshake,
        frames are read by decoding a VarInt length and slicing the
        specified number of bytes. If insufficient data is available the
        reader index is reset and the method returns whatever frames were
        successfully extracted so far.

        :param buf: a buffer containing raw network data
        :return: a list of zero or more :class:`ByteBuf` frames
        :raises BadVarintException: if an invalid VarInt is encountered
        """
        frames: List[ByteBuf] = []

        # Perform version handshake if necessary
        if not self._handshake_done:
            if not buf.isReadable():
                return frames
            version = buf.readUnsignedByte()
            if version not in self.SUPPORTED_VERSIONS:
                raise RuntimeError(f"Unsupported protocol version: {version}")
            self.client_protocol_version = version
            self._handshake_done = True

        # Now decode length-prefixed frames until no more complete frames
        while True:
            buf.markReaderIndex()
            try:
                length = decodeVarInt(buf)
            except NeedMoreDataException:
                # Not enough bytes to decode length, reset to mark and exit
                buf.resetReaderIndex()
                break
            except BadVarintException:
                # Invalid VarInt encountered; this is a protocol error
                raise
            # If not enough bytes for the frame payload, reset and exit
            if not buf.isReadable(length):
                buf.resetReaderIndex()
                break
            # Read the frame body and append to frames list
            frame_bytes = buf.readBytes(length)
            frames.append(ByteBuf(frame_bytes))
        return frames


__all__ = ["FrameDecoder"]