"""Client-bound packet conveying the result of sending a chat message."""

from __future__ import annotations

from ..ClientBoundPacket import ClientBoundPacket
from ...data.PacketResult import PacketResult
from ...util.PacketWriter import PacketWriter


class ClientBoundChatPacket(ClientBoundPacket):
    """Client-bound packet conveying the result of sending a chat message.

    Use the attached ``Failed`` or ``Success`` variants to create actual
    instances.  The base type does not itself implement ``encode``.
    """

    pass


class _ClientBoundChatPacketFailed(ClientBoundChatPacket):
    """Represents a failed chat message send with a reason."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.FAILED)
        PacketWriter.write(buf, self.reason)


class _ClientBoundChatPacketSuccess(ClientBoundChatPacket):
    """Represents a successful chat message send."""

    def encode(self, buf) -> None:
        PacketWriter.write(buf, PacketResult.SUCCESS)


# Attach variants
ClientBoundChatPacket.Failed = _ClientBoundChatPacketFailed  # type: ignore[attr-defined]
ClientBoundChatPacket.Success = _ClientBoundChatPacketSuccess  # type: ignore[attr-defined]