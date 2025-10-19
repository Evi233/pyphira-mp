"""A simple byte buffer implementation used for encoding and decoding packet data.

This class provides a minimal subset of the Netty ByteBuf API required by the
Phira protocol. It is backed by a Python ``bytearray`` and maintains a
reader index for decoding. Methods are provided for reading and writing
primitive types in little and big endian forms as required.
"""

from __future__ import annotations

import struct
from typing import Optional, Iterable


class ByteBuf:
    """A mutable buffer supporting sequential reads and writes of primitive values."""

    def __init__(self, initial: Optional[bytes] = None) -> None:
        # Underlying storage for bytes; convert initial to bytearray for mutability
        self.buffer = bytearray(initial if initial is not None else b'')
        # Reader index tracks where reads occur; writes append to the end
        self.reader_index: int = 0
        # Marker for resetting the reader index (used by FrameDecoder)
        self._mark: Optional[int] = None

    # === Read operations ===
    def isReadable(self, length: int = 1) -> bool:
        """Return True if at least ``length`` bytes are available to read."""
        return len(self.buffer) - self.reader_index >= length

    def readableBytes(self) -> int:
        """Return the number of bytes remaining to read."""
        return len(self.buffer) - self.reader_index

    def readByte(self) -> int:
        """Read a single byte and advance the reader index by one."""
        if not self.isReadable(1):
            raise IndexError("Not enough bytes to read a byte")
        value = self.buffer[self.reader_index]
        self.reader_index += 1
        return value

    def readUnsignedByte(self) -> int:
        """Read an unsigned byte (0-255)."""
        return self.readByte() & 0xFF

    def readBoolean(self) -> bool:
        """Read a boolean value (0 or 1)."""
        return bool(self.readByte())

    def readIntLE(self) -> int:
        """Read a 32-bit little-endian integer."""
        if not self.isReadable(4):
            raise IndexError("Not enough bytes to read an int32")
        start = self.reader_index
        self.reader_index += 4
        return struct.unpack_from('<i', self.buffer, start)[0]

    def readFloatLE(self) -> float:
        """Read a 32-bit little-endian floating point number."""
        if not self.isReadable(4):
            raise IndexError("Not enough bytes to read a float")
        start = self.reader_index
        self.reader_index += 4
        return struct.unpack_from('<f', self.buffer, start)[0]

    def readBytes(self, length: int) -> bytes:
        """Read ``length`` bytes and return them as an immutable bytes object."""
        if not self.isReadable(length):
            raise IndexError("Not enough bytes to read")
        start = self.reader_index
        self.reader_index += length
        return bytes(self.buffer[start:start + length])

    def readRetainedSlice(self, length: int) -> 'ByteBuf':
        """Return a new ByteBuf backed by a slice of this buffer and advance the reader index."""
        slice_bytes = self.readBytes(length)
        return ByteBuf(slice_bytes)

    # === Write operations ===
    def writeByte(self, value: int) -> None:
        """Write a single byte (lower 8 bits of value)."""
        self.buffer.append(value & 0xFF)

    def writeBoolean(self, value: bool) -> None:
        """Write a boolean as a single byte (1 for True, 0 for False)."""
        self.writeByte(1 if value else 0)

    def writeIntLE(self, value: int) -> None:
        """Write a 32-bit little-endian integer."""
        self.buffer.extend(struct.pack('<i', int(value)))

    def writeFloatLE(self, value: float) -> None:
        """Write a 32-bit little-endian float."""
        self.buffer.extend(struct.pack('<f', float(value)))

    def writeShort(self, value: int) -> None:
        """Write a 16-bit big-endian short."""
        self.buffer.extend(int(value).to_bytes(2, byteorder='big', signed=True))

    def writeMedium(self, value: int) -> None:
        """Write a 24-bit big-endian integer."""
        # Write the lower 3 bytes of the integer value. In Python, negative
        # values need special handling to produce the correct two's complement.
        if value < 0:
            # Convert to unsigned equivalent within 3 bytes
            value &= 0xFFFFFF
        self.buffer.extend(value.to_bytes(3, byteorder='big', signed=False))

    def writeInt(self, value: int) -> None:
        """Write a 32-bit big-endian integer."""
        self.buffer.extend(int(value).to_bytes(4, byteorder='big', signed=True))

    def writeBytes(self, data: Iterable[int] | bytes | bytearray) -> None:
        """Append a sequence of bytes to this buffer."""
        if isinstance(data, (bytes, bytearray)):
            self.buffer.extend(data)
        else:
            # Assume iterable of ints
            self.buffer.extend(int(b) & 0xFF for b in data)

    # === Utility methods ===
    def skipBytes(self, length: int) -> None:
        """Advance the reader index by ``length`` bytes without returning them."""
        if length < 0:
            raise ValueError("length must be non-negative")
        if self.reader_index + length > len(self.buffer):
            raise IndexError("Not enough bytes to skip")
        self.reader_index += length

    def getBytes(self, index: int, length: int) -> bytes:
        """Return a slice of bytes from an arbitrary index without modifying the reader index."""
        if index < 0 or index + length > len(self.buffer):
            raise IndexError("Index out of bounds")
        return bytes(self.buffer[index:index + length])

    def markReaderIndex(self) -> None:
        """Mark the current reader index so it can be restored later."""
        self._mark = self.reader_index

    def resetReaderIndex(self) -> None:
        """Reset the reader index to the last marked position."""
        if self._mark is None:
            raise RuntimeError("No reader index has been marked")
        self.reader_index = self._mark
        self._mark = None

    def asReadOnly(self) -> 'ByteBuf':
        """Return a new ByteBuf containing a copy of this buffer's bytes."""
        return ByteBuf(bytes(self.buffer))

    def toBytes(self) -> bytes:
        """Return the entire contents of this buffer as bytes."""
        return bytes(self.buffer)

    def __len__(self) -> int:
        return len(self.buffer)

    def __repr__(self) -> str:
        return f"ByteBuf(reader_index={self.reader_index}, buffer={self.buffer!r})"