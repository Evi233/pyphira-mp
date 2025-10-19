"""Encoding helpers for the Phira protocol.

The classes in this package perform low-level encoding of packets into
binary form. ``FrameEncoder`` writes a VarInt length prefix followed by
the packet body, and ``PacketEncoder`` uses the registry to obtain the
correct packet ID before invoking the packet's ``encode`` method.
"""

from .FrameEncoder import FrameEncoder  # noqa: F401
from .PacketEncoder import PacketEncoder  # noqa: F401

__all__ = [
    "FrameEncoder",
    "PacketEncoder",
]