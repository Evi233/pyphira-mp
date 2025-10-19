"""Provides a simple interface for objects that can encode themselves into a ByteBuf.

This mirrors the original Java Encodeable interface from the Phira protocol but
is adapted for Python. Subclasses should implement the ``encode`` method which
accepts a ByteBuf and writes their representation into it.
"""

from __future__ import annotations
from typing import Protocol


class Encodeable:
    """Interface for objects that can encode themselves into a ByteBuf."""

    def encode(self, buf: 'ByteBuf') -> None:
        """
        Encode the contents of this object into the provided ByteBuf.

        Subclasses must override this method. It is analogous to the Java
        ``encode`` method defined on Encodeable.

        :param buf: the ByteBuf into which this object should be encoded
        """
        raise NotImplementedError("Encodeable subclasses must implement encode()")