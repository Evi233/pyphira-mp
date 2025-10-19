"""Client-bound packet used to reply to ping requests.

This packet carries no payload. In the Java version a singleton
``INSTANCE`` is exposed to avoid repeated allocations; we adopt the same
pattern here.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket


class ClientBoundPongPacket(ClientBoundPacket):
    """Singleton packet used to respond to ``ServerBoundPingPacket``."""

    # Expose a singleton instance similar to the Java ``INSTANCE`` field
    INSTANCE: "ClientBoundPongPacket"

    def encode(self, buf) -> None:
        # Pong packets have no payload beyond their identifier byte
        pass


# Instantiate the singleton instance
ClientBoundPongPacket.INSTANCE = ClientBoundPongPacket()  # type: ignore[attr-defined]


__all__ = ["ClientBoundPongPacket"]