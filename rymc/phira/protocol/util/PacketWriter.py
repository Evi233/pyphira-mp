"""Helper functions to simplify writing various types into a ByteBuf.

The original Java version provided several overloaded static methods on
``PacketWriter``. In Python we implement a single polymorphic ``write``
function which dispatches based on the type of the value supplied. Specific
helpers such as ``writeByte`` are also provided for clarity.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from ..codec.Encodeable import Encodeable
from ..exception import NeedMoreDataException
from .ByteBuf import ByteBuf
from .NettyPacketUtil import writeString


class PacketWriter:
    """Utility class for writing typed values into a ByteBuf."""

    @staticmethod
    def writeByte(buf: ByteBuf, value: int) -> None:
        buf.writeByte(value)

    @staticmethod
    def write(buf: ByteBuf, value) -> None:
        """
        Write a value into the provided ByteBuf using the appropriate encoding.

        The encoding rules mirror those defined in the original Java
        ``PacketWriter``:

          * ``int`` values are written as little-endian 32-bit integers.
          * ``float`` values are written as little-endian 32-bit floats.
          * ``bool`` values are written as a single byte (1 or 0).
          * ``str`` values are written as a VarInt length followed by the UTF-8 bytes.
          * ``Encodeable`` values delegate to their ``encode`` method.
          * ``Sequence`` of ``Encodeable`` values are written with a length byte
            followed by each element encoded in sequence.

        :param buf: the ByteBuf to write into
        :param value: the value to encode
        :raises TypeError: if the value type is unsupported
        """
        # Order of type checks matters: bool is also an int, so check it first
        if isinstance(value, bool):
            buf.writeBoolean(value)
        elif isinstance(value, int):
            buf.writeIntLE(value)
        elif isinstance(value, float):
            buf.writeFloatLE(value)
        elif isinstance(value, str):
            writeString(buf, value)
        elif isinstance(value, Encodeable):
            value.encode(buf)
        elif isinstance(value, Sequence):
            # Write the number of elements as a single byte
            buf.writeByte(len(value) & 0xFF)
            for element in value:
                if not isinstance(element, Encodeable):
                    raise TypeError(f"List element {element!r} does not implement Encodeable")
                element.encode(buf)
        else:
            raise TypeError(f"Unsupported type for PacketWriter.write: {type(value).__name__}")