"""Provides a simple interface for objects that can decode themselves from a ByteBuf.

This mirrors the original Java Decodeable interface from the Phira protocol but
is adapted for Python. Subclasses should implement the ``decode`` method which
takes a ByteBuf and populates the object's fields from it.
"""

from __future__ import annotations


class Decodeable:
    """Interface for objects that can decode themselves from a ByteBuf."""

    def decode(self, buf: 'ByteBuf') -> None:
        """
        Decode the contents of this object from the provided ByteBuf.

        Subclasses must override this method. It is analogous to the Java
        ``decode`` method defined on Decodeable.

        :param buf: the ByteBuf from which this object should be decoded
        """
        raise NotImplementedError("Decodeable subclasses must implement decode()")