"""Client-bound packet instructing the client to abort.

This packet comes in two flavours: ``Failed``, which includes a reason for
the failure, and ``Success``, which indicates that the abort request
succeeded. Both nested classes inherit from this base and provide their
own ``encode`` implementations.
"""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundAbortPacket(ClientBoundPacket):
    """Client-bound packet instructing the client to abort.

    This packet comes in two flavours: ``Failed``, which includes a reason for
    the failure, and ``Success``, which indicates that the abort request
    succeeded. The outer class itself does not implement ``encode``; instead
    use one of its variants.  The variants are defined below and attached
    as attributes to this class.
    """

    # No direct payload for the base type. Actual variants are defined below.
    pass

# Define the ``Failed`` variant as a separate class inheriting from the outer
# class.  This avoids issues with referencing the outer class within its own
# body.  The class is subsequently bound to ``ClientBoundAbortPacket.Failed``.
class _ClientBoundAbortPacketFailed(ClientBoundAbortPacket):
    """Represents a failed abort request.

    Carries a human-readable reason explaining why the abort request failed.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


# Define the ``Success`` variant as a separate class inheriting from the outer
# class.  This variant carries no payload beyond the status byte.
class _ClientBoundAbortPacketSuccess(ClientBoundAbortPacket):
    """Represents a successful abort request response."""

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Attach the variant classes to the outer class to emulate Java-style nested
# classes.  Users can instantiate ``ClientBoundAbortPacket.Failed`` and
# ``ClientBoundAbortPacket.Success`` just like the original design.
ClientBoundAbortPacket.Failed = _ClientBoundAbortPacketFailed  # type: ignore[attr-defined]
ClientBoundAbortPacket.Success = _ClientBoundAbortPacketSuccess  # type: ignore[attr-defined]