"""Simple record containing a user's identifier and display name.

This class corresponds to the Java ``record`` ``UserProfile(int userId, String
username)`` found under ``top/rymc/phira/protocol/data``. It stores a user
identifier and a username and implements the :class:`Encodeable` interface so
that it can be written directly into a :class:`ByteBuf` for transmission.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..codec.Encodeable import Encodeable
from ..util.ByteBuf import ByteBuf
from ..util import NettyPacketUtil, PacketWriter


@dataclass
class UserProfile(Encodeable):
    """Represents a user's identity within the protocol."""

    userId: int
    username: str

    def encode(self, buf: ByteBuf) -> None:
        """Encode this user profile into the provided buffer.

        The user ID is written as a 32-bit little-endian integer and the
        username is written as a VarInt-prefixed UTF-8 string.

        :param buf: buffer to write into
        """
        PacketWriter.write(buf, self.userId)
        PacketWriter.write(buf, self.username)


__all__ = ["UserProfile"]