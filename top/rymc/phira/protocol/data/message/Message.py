"""Base class for all message types sent to clients.

Each subclass must implement :meth:`getMessageId` to return the numeric
identifier associated with the message. The :meth:`encode` method is
responsible for writing the message ID and any additional fields into
the supplied :class:`ByteBuf`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ...codec.Encodeable import Encodeable
from ...util.ByteBuf import ByteBuf
from ...util.PacketWriter import PacketWriter


class Message(Encodeable, ABC):
    """Abstract base class for protocol messages."""

    @abstractmethod
    def getMessageId(self) -> int:
        """Return the message identifier for this message."""
        raise NotImplementedError

    def encode(self, buf: ByteBuf) -> None:
        """Encode the message into the provided buffer.

        Subclasses should override this method to write the message ID followed
        by any additional payload. This base implementation writes only the
        message ID; most subclasses will need to call into
        :func:`PacketWriter.write` for additional fields.

        :param buf: the buffer to write into
        """
        # Write the message identifier as a single byte
        PacketWriter.writeByte(buf, self.getMessageId())

    def __str__(self) -> str:  # pragma: no cover - simple helper
        return f"{self.__class__.__name__}(id=0x{self.getMessageId():02X})"