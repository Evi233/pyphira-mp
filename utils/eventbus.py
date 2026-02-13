from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


Callback = Callable[..., Any]


@dataclass(frozen=True)
class Subscription:
    event: str
    callback: Callback
    owner: Any
    once: bool = False


class EventBus:
    """A small event bus.

    - Supports sync and async callbacks.
    - Async callbacks are scheduled via asyncio.create_task.
    - Exceptions are caught and logged, never leaking into core logic.
    """

    def __init__(self) -> None:
        self._subs: Dict[str, List[Subscription]] = {}

    def on(self, event: str, callback: Callback, *, owner: Any = None) -> Subscription:
        sub = Subscription(event=event, callback=callback, owner=owner, once=False)
        self._subs.setdefault(event, []).append(sub)
        return sub

    def once(self, event: str, callback: Callback, *, owner: Any = None) -> Subscription:
        sub = Subscription(event=event, callback=callback, owner=owner, once=True)
        self._subs.setdefault(event, []).append(sub)
        return sub

    def off(self, sub: Subscription) -> None:
        items = self._subs.get(sub.event)
        if not items:
            return
        self._subs[sub.event] = [s for s in items if s != sub]
        if not self._subs[sub.event]:
            self._subs.pop(sub.event, None)

    def off_owner(self, owner: Any) -> None:
        if owner is None:
            return
        for event in list(self._subs.keys()):
            self._subs[event] = [s for s in self._subs[event] if s.owner != owner]
            if not self._subs[event]:
                self._subs.pop(event, None)

    def emit(self, event: str, **payload: Any) -> None:
        subs = list(self._subs.get(event, []))
        if not subs:
            return

        for sub in subs:
            if sub.once:
                # remove first to prevent re-entrance duplications
                self.off(sub)
            self._safe_invoke(sub, payload)

    def _safe_invoke(self, sub: Subscription, payload: Dict[str, Any]) -> None:
        try:
            result = sub.callback(**payload)

            # If callback is async def, result is a coroutine
            if inspect.isawaitable(result):
                asyncio.create_task(self._await_and_log(result, sub))
        except Exception:
            logger.exception("[EventBus] Error in handler for event=%s callback=%r", sub.event, sub.callback)

    async def _await_and_log(self, aw: Awaitable[Any], sub: Subscription) -> None:
        try:
            await aw
        except Exception:
            logger.exception("[EventBus] Async handler failed for event=%s callback=%r", sub.event, sub.callback)
