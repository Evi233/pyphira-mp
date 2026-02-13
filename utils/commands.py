from __future__ import annotations

import logging
import shlex
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence


logger = logging.getLogger(__name__)


CommandHandler = Callable[["CommandContext", List[str]], Any]


@dataclass(frozen=True)
class Command:
    name: str
    handler: CommandHandler
    help: str = ""
    usage: str = ""
    aliases: Sequence[str] = field(default_factory=tuple)
    hidden: bool = False
    owner: Any = None

    def all_names(self) -> List[str]:
        return [self.name, *list(self.aliases)]


@dataclass
class CommandContext:
    """Execution context passed to command handlers."""

    bus: Any
    plugin_manager: Any
    server_state: Any
    shutdown_event: Any
    logger: logging.Logger

    def println(self, msg: str) -> None:
        # Console command output should go to stdout; also log at INFO.
        try:
            print(msg)
        except Exception:
            # If stdout is broken, at least log.
            self.logger.info(msg)


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: Dict[str, Command] = {}
        # primary commands in registration order
        self._primary: Dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        """Register command under name and aliases.

        If a name already exists, it will be overwritten. This is useful for hot reload.
        """

        # track primary command order
        self._primary[cmd.name.lower()] = cmd

        for name in cmd.all_names():
            if not name:
                continue
            self._commands[name.lower()] = cmd

    def off_owner(self, owner: Any) -> None:
        if owner is None:
            return
        for k in list(self._commands.keys()):
            if self._commands[k].owner == owner:
                self._commands.pop(k, None)

        for k in list(self._primary.keys()):
            if self._primary[k].owner == owner:
                self._primary.pop(k, None)

    def unregister_by_owner_prefix(self, prefix: str) -> None:
        """Optional helper: allow plugins to remove commands by naming convention.

        Not used by core right now. For hot reload we typically re-register over same names.
        """

        prefix = prefix.lower()
        for k in list(self._commands.keys()):
            if k.startswith(prefix):
                self._commands.pop(k, None)

    def get(self, name: str) -> Optional[Command]:
        return self._commands.get(name.lower())

    def list_unique(self) -> List[Command]:
        # Primary commands in registration order.
        return list(self._primary.values())

    def parse(self, line: str) -> Optional[tuple[str, List[str]]]:
        line = (line or "").strip()
        if not line:
            return None
        if not line.startswith("/"):
            return None

        # Windows-friendly splitting; supports quoted strings.
        try:
            parts = shlex.split(line[1:], posix=False)
        except ValueError as e:
            raise ValueError(f"参数解析失败: {e}")

        if not parts:
            return None

        name = parts[0]
        args = parts[1:]
        return name, args

    def dispatch(self, line: str, ctx: CommandContext) -> bool:
        """Dispatch a command line.

        Returns True if the line was a command (started with '/') and was handled (even if failed).
        Returns False if the line is not a command.
        """

        parsed = self.parse(line)
        if parsed is None:
            return False

        name, args = parsed
        cmd = self.get(name)
        if not cmd:
            ctx.println(f"未知指令: /{name} (输入 /help 查看帮助)")
            return True

        try:
            result = cmd.handler(ctx, args)
            # If handler returns an awaitable, schedule it.
            try:
                import inspect

                if inspect.isawaitable(result):
                    asyncio = __import__("asyncio")
                    asyncio.create_task(result)  # type: ignore[attr-defined]
            except Exception:
                # best-effort
                pass
        except SystemExit:
            raise
        except Exception as e:
            logger.exception("Command failed: /%s args=%r", name, args)
            ctx.println(f"指令执行失败: /{name} - {e}")
        return True

    def format_help(self, *, title: str = "===== 服务器控制台帮助菜单 =====") -> str:
        lines: List[str] = [title]
        for cmd in self.list_unique():
            if cmd.hidden:
                continue
            usage = cmd.usage or f"/{cmd.name}"
            if cmd.help:
                lines.append(f"{usage} - {cmd.help}")
            else:
                lines.append(usage)
        lines.append("=============================")
        return "\n".join(lines)
