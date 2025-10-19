"""Base class for all game state representations.

In the Java version ``GameState`` is a sealed abstract class that
permits exactly three subclasses: ``Playing``, ``WaitForReady`` and
``SelectChart``. In Python we model this as a normal abstract base class
which implements the :class:`Encodeable` protocol. Subclasses must
override the :meth:`encode` method to write a unique type identifier
followed by any additional state-specific data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ...codec.Encodeable import Encodeable


class GameState(Encodeable, ABC):
    """Abstract base for all game state classes."""

    @abstractmethod
    def encode(self, buf) -> None:
        """Encode the state into the provided buffer."""
        raise NotImplementedError

    def __str__(self) -> str:  # pragma: no cover - simple helper
        return self.__class__.__name__