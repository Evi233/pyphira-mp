"""Base class for client-bound packets.

All packets that are sent from the server to the client inherit from this
abstract class. Concrete subclasses must implement the ``encode`` method to
write their payload into a ByteBuf. A packet instance can then be encoded
via ``PacketRegistry.encode`` to include the packet identifier.
"""

from __future__ import annotations

from ..codec import Encodeable


class ClientBoundPacket(Encodeable):
    """Abstract base class for packets sent from server to client."""

    def encode(self, buf):
        """
        Encode this packet into the provided ByteBuf. Subclasses must
        implement this method and should write only the packet body (i.e.
        excluding the length prefix and packet identifier).
        """
        raise NotImplementedError("ClientBoundPacket subclasses must implement encode()")