"""Base class for server-bound packets.

Packets sent from the client to the server inherit from this abstract class.
Concrete subclasses must implement both ``decode`` and ``handle``. The
``decode`` method should populate the packet's fields from a ByteBuf. The
``handle`` method is invoked by the network layer with an instance of
``PacketHandler`` to perform any server-side logic.
"""

from __future__ import annotations

from ..codec import Decodeable
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    # Import only for type checking to avoid circular dependencies at runtime
    from ..handler.PacketHandler import PacketHandler


class ServerBoundPacket(Decodeable):
    """Abstract base class for packets sent from client to server."""

    def decode(self, buf):
        """
        Populate this packet's fields by reading from the provided ByteBuf.
        Subclasses must implement this method to decode their specific payload.
        """
        raise NotImplementedError("ServerBoundPacket subclasses must implement decode()")

    def handle(self, handler: 'PacketHandler') -> None:
        """
        Handle this packet using the supplied PacketHandler. Subclasses must
        implement this to dispatch themselves onto the appropriate handler
        method.
        """
        raise NotImplementedError("ServerBoundPacket subclasses must implement handle()")