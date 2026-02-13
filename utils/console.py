from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional

from utils.commands import CommandContext, CommandRegistry


logger = logging.getLogger(__name__)


async def console_loop(
    registry: CommandRegistry,
    ctx: CommandContext,
    *,
    prompt: str = "",
) -> None:
    """Read commands from stdin and dispatch.

    - Runs in background without blocking asyncio loop.
    - Accepts only lines beginning with '/'. Other input is ignored.
    """

    if prompt:
        try:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        except Exception:
            pass

    while not ctx.shutdown_event.is_set():
        try:
            line = await asyncio.to_thread(sys.stdin.readline)
        except Exception:
            logger.exception("[Console] Failed reading stdin")
            await asyncio.sleep(0.2)
            continue

        if line == "":
            # EOF (stdin closed)
            logger.warning("[Console] stdin EOF, console loop stopped")
            return

        line = line.strip()
        if not line:
            continue

        handled = registry.dispatch(line, ctx)
        if not handled:
            # Ignore non-command input in server console.
            pass

        if prompt:
            try:
                sys.stdout.write(prompt)
                sys.stdout.flush()
            except Exception:
                pass
