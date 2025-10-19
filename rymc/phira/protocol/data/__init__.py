"""Data structures used by the Phira protocol.

This package contains simple value objects and enums which are encoded and
decoded as part of the protocol. The classes mirror those found in the
original Java implementation under ``top/rymc/phira/protocol/data``. Most
types implement the :class:`~top.rymc.phira.protocol.codec.Encodeable` interface
so they can be written directly to a :class:`~top.rymc.phira.protocol.util.ByteBuf`.
"""

from __future__ import annotations

# Expose common data classes at the package level for convenience
from .PacketResult import PacketResult  # noqa: F401
from .UserProfile import UserProfile  # noqa: F401
from .RoomInfo import RoomInfo  # noqa: F401

# The ``state`` and ``message`` subpackages are imported for their side
# effects (they register their classes with PacketWriter) and for ease of
# access. Importing them here allows consumers to write ``from
# top.rymc.phira.protocol.data import state``. If unused, these imports
# have no runtime cost beyond the initial import.
from . import state  # noqa: F401
from . import message  # noqa: F401

__all__ = [
    "PacketResult",
    "UserProfile",
    "RoomInfo",
    "state",
    "message",
]