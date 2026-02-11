"""A composite user profile carrying monitor status.

This class mirrors the Java ``FullUserProfile`` record introduced in
``jphira-mp-protocol`` version 1.2.1 and later.  It encapsulates a
``UserProfile`` alongside a boolean indicating whether that user is a
monitor of the room.  The ``encode`` implementation writes the
underlying ``UserProfile`` followed by the monitor flag into the
provided :class:`ByteBuf`.

The class also includes a convenience method ``from_lists`` which
combines separate lists of normal users and monitor users into a single
sequence of ``FullUserProfile`` instances.  This mirrors the static
``fromLists`` factory on the Java version and simplifies building
room-member lists when encoding packets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..codec.Encodeable import Encodeable
from .UserProfile import UserProfile
from ..util.ByteBuf import ByteBuf
from ..util.PacketWriter import PacketWriter


@dataclass
class FullUserProfile(Encodeable):
    """Represents a user profile with an associated monitor flag."""

    userProfile: UserProfile
    monitor: bool

    def __init__(self, userProfile: UserProfile | int, monitor: bool | str | None = False, username: str | None = None) -> None:
        """Initialise a ``FullUserProfile``.

        Parameters
        ----------
        userProfile: ``UserProfile`` or ``int``
            Either an existing ``UserProfile`` instance or the user identifier.  If an integer
            is provided, the ``username`` argument must also be supplied.
        monitor: ``bool`` or ``str`` or ``None``
            When ``userProfile`` is a ``UserProfile`` instance, this flag indicates whether
            the user is a monitor.  When ``userProfile`` is an ``int``, this argument is
            instead treated as the boolean monitor flag and the ``username`` argument must
            be provided.
        username: ``str``, optional
            Required only when ``userProfile`` is provided as an ``int``.  Specifies the
            username associated with the identifier.
        """
        # Accept either a UserProfile instance or (userId, monitor, username) triple
        if isinstance(userProfile, UserProfile):
            self.userProfile = userProfile
            # monitor may come in as a positional argument when username=None
            self.monitor = bool(monitor)
        else:
            # Construct a new UserProfile from the provided id and name
            if username is None:
                raise ValueError("username must be provided when constructing from an id")
            self.userProfile = UserProfile(int(userProfile), str(username))
            self.monitor = bool(monitor)

    @property
    def userId(self) -> int:
        """Return the user identifier from the underlying profile."""
        return self.userProfile.userId

    @property
    def userName(self) -> str:
        """Return the username from the underlying profile."""
        return self.userProfile.username

    def encode(self, buf: ByteBuf) -> None:
        """Encode this profile into ``buf``.

        The underlying ``UserProfile`` is encoded first, followed by the
        monitor flag as a single byte.  This mirrors the Java implementation.

        Parameters
        ----------
        buf: :class:`ByteBuf`
            The buffer to encode into.
        """
        PacketWriter.write(buf, self.userProfile)
        PacketWriter.write(buf, self.monitor)

    @staticmethod
    def from_lists(users: Iterable[UserProfile], monitors: Iterable[UserProfile]) -> List["FullUserProfile"]:
        """Create a combined list of ``FullUserProfile`` instances.

        Given separate iterables of normal users and monitor users, this
        helper will produce a single list of ``FullUserProfile`` objects
        preserving the ordering: all users first, followed by monitors.

        Parameters
        ----------
        users: Iterable[UserProfile]
            The non-monitor participants.
        monitors: Iterable[UserProfile]
            The monitor participants.

        Returns
        -------
        List[FullUserProfile]
            A combined list containing ``FullUserProfile`` instances for
            both users and monitors.
        """
        full_profiles: List[FullUserProfile] = []
        for user in users:
            full_profiles.append(FullUserProfile(user, False))
        for monitor in monitors:
            full_profiles.append(FullUserProfile(monitor, True))
        return full_profiles


__all__ = ["FullUserProfile"]