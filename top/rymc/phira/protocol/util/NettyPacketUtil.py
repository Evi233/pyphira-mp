"""Utility functions for encoding and decoding VarInt values and strings.

This module provides functions equivalent to the Netty-based helpers used in
the original Phira protocol. It includes a VarInt implementation and simple
UTF-8 string read/write routines that prepend the string length as a VarInt.
"""

from __future__ import annotations

from typing import Optional

from ..exception import BadVarintException, NeedMoreDataException
from .ByteBuf import ByteBuf


MAXIMUM_VARINT_SIZE = 5


def decodeVarInt(buf: ByteBuf) -> int:
    """Decode a variable-length integer from the provided ByteBuf.

    The encoding matches that of the Java implementation: each byte of the
    value uses the lower 7 bits to store payload data and the highest bit
    to indicate whether more bytes follow. If the first byte's highest bit is
    clear, it is the entire value. Otherwise subsequent bytes are read until
    a terminating byte (with the high bit clear) is encountered.

    :param buf: the ByteBuf to read from
    :raises NeedMoreDataException: if insufficient data is present to decode a full VarInt
    :raises BadVarintException: if more than 5 bytes are used to encode the value
    :return: the decoded integer
    """
    if not buf.isReadable():
        raise NeedMoreDataException()

    # Read the first byte. If the high bit is zero then this is the entire value.
    b = buf.readByte()
    if (b & 0x80) == 0:
        return b

    value = b & 0x7F
    shift = 7

    for i in range(1, MAXIMUM_VARINT_SIZE):
        if not buf.isReadable():
            raise NeedMoreDataException()
        b = buf.readByte()
        value |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return value
        shift += 7
    raise BadVarintException()


def encodeVarInt(buf: ByteBuf, value: int) -> None:
    """Encode an integer into the provided ByteBuf using the VarInt format.

    Negative values are supported by encoding the two's complement representation.
    This implementation mirrors the Java version where the integer is broken
    into 7-bit chunks. For performance reasons the Java version unrolls the
    cases for up to five bytes; here we implement the general loop version.

    :param buf: the ByteBuf to write into
    :param value: the integer to encode
    """
    # Convert Python's potentially unbounded ints into 32-bit two's complement
    value &= 0xFFFFFFFF
    while True:
        # Extract the lower 7 bits
        temp = value & 0x7F
        value >>= 7
        if value != 0:
            buf.writeByte(temp | 0x80)
        else:
            buf.writeByte(temp)
            break


def writeString(buf: ByteBuf, string: str) -> None:
    """Write a UTF-8 string prefaced by its VarInt length."""
    encoded = string.encode('utf-8')
    encodeVarInt(buf, len(encoded))
    buf.writeBytes(encoded)


def readString(buf: ByteBuf, maxLength: int) -> str:
    """Read a UTF-8 string prefaced by a VarInt length and enforce a maximum length.

    :param buf: the ByteBuf to read from
    :param maxLength: the maximum allowable string length
    :raises ValueError: if the decoded length is negative or exceeds maxLength
    :raises NeedMoreDataException: if the buffer does not contain enough bytes
    :return: the decoded string
    """
    length = decodeVarInt(buf)
    if length < 0 or length > maxLength:
        raise ValueError(f"Bad string length: {length} (max: {maxLength})")
    if not buf.isReadable(length):
        raise NeedMoreDataException()
    # Use readBytes to advance the reader index
    data = buf.readBytes(length)
    return data.decode('utf-8')