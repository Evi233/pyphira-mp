"""Enumeration representing the result of an operation for client-bound packets.

In the Java implementation ``PacketResult`` is an enum with two values,
``SUCCESS`` and ``FAILED``, each associated with a single byte value. It
implements the ``Encodeable`` interface so that it can be directly written
to a buffer. The Python version uses a simple class with class attributes
representing the two possible values. Instances of :class:`PacketResult`
store the byte code used when encoding.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..codec.Encodeable import Encodeable
from ..util.ByteBuf import ByteBuf


@dataclass(frozen=True)
class PacketResult(Encodeable):
    """Represents the result of a packet operation.

    Each ``PacketResult`` has an associated integer code which is written as
    a single byte during encoding. Do not instantiate new values directly;
    use the predefined constants :data:`PacketResult.SUCCESS` and
    :data:`PacketResult.FAILED` instead.
    """

    code: int

    def encode(self, buf: ByteBuf) -> None:
        """Write the result code to the provided buffer as a single byte."""
        buf.writeByte(self.code)


# Predefined instances corresponding to the Java enum values
PacketResult.SUCCESS = PacketResult(0x01)  # type: ignore[attr-defined]
PacketResult.FAILED = PacketResult(0x00)  # type: ignore[attr-defined]


__all__ = ["PacketResult"]