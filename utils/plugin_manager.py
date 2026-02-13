import asyncio
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Optional, Union

from utils.eventbus import EventBus


logger = logging.getLogger(__name__)


Teardown = Callable[[], Any]


@dataclass
class LoadedPlugin:
    name: str
    path: Path
    module_name: str
    module: ModuleType
    teardown: Optional[Teardown]
    mtime: float


class PluginContext:
    def __init__(self, bus: EventBus, plugin_name: str, owner: Any) -> None:
        self.bus = bus
        self.plugin_name = plugin_name
        self.logger = logging.getLogger(f"plugin.{plugin_name}")
        self._owner = owner

    def on(self, event: str, callback, *, owner: Any = None):
        # By default bind handlers to this plugin, so reload/unload can cleanly remove them.
        return self.bus.on(event, callback, owner=self._owner if owner is None else owner)

    def once(self, event: str, callback, *, owner: Any = None):
        return self.bus.once(event, callback, owner=self._owner if owner is None else owner)

    def emit(self, event: str, **payload):
        return self.bus.emit(event, **payload)


class PluginManager:
    def __init__(
        self,
        bus: EventBus,
        plugins_dir: Union[str, os.PathLike] = "plugins",
        *,
        poll_interval: float = 1.0,
    ) -> None:
        self.bus = bus
        self.plugins_dir = Path(plugins_dir)
        self.poll_interval = poll_interval

        self._loaded: Dict[Path, LoadedPlugin] = {}
        self._watch_task: Optional[asyncio.Task] = None

    def start(self) -> None:
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.load_all()
        if self._watch_task is None:
            logger.info(
                "[PluginManager] Hot-reload watcher started. dir=%s interval=%ss",
                str(self.plugins_dir),
                self.poll_interval,
            )
            self._watch_task = asyncio.create_task(self._watch_loop())

    def stop(self) -> None:
        if self._watch_task:
            self._watch_task.cancel()
            self._watch_task = None
        # unload all
        for path in list(self._loaded.keys()):
            self.unload(path)

    def load_all(self) -> None:
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.plugins_dir.glob("*.py")):
            self.load(path)

    def load(self, path: Path) -> None:
        path = path.resolve()
        if path in self._loaded:
            return

        try:
            mtime = path.stat().st_mtime
            module_name = f"pyphira_plugin_{path.stem}"
            module = self._import_from_path(module_name, path)

            teardown = None
            if hasattr(module, "setup"):
                # owner is module_name so off_owner can cleanly remove subscriptions
                ctx = PluginContext(self.bus, plugin_name=path.stem, owner=module_name)
                result = module.setup(ctx)
                if callable(result):
                    teardown = result

            self._loaded[path] = LoadedPlugin(
                name=path.stem,
                path=path,
                module_name=module_name,
                module=module,
                teardown=teardown,
                mtime=mtime,
            )
            logger.info("[PluginManager] Loaded plugin %s (%s)", path.stem, path)
        except Exception:
            logger.exception("[PluginManager] Failed to load plugin: %s", path)

    def unload(self, path: Path) -> None:
        path = path.resolve()
        plugin = self._loaded.pop(path, None)
        if not plugin:
            return
        try:
            # best-effort teardown
            if plugin.teardown:
                try:
                    plugin.teardown()
                except Exception:
                    logger.exception("[PluginManager] Teardown failed: %s", plugin.name)

            # remove event handlers owned by this module
            self.bus.off_owner(plugin.module_name)

            # remove module cache
            sys.modules.pop(plugin.module_name, None)
            logger.info("[PluginManager] Unloaded plugin %s", plugin.name)
        except Exception:
            logger.exception("[PluginManager] Failed to unload plugin: %s", plugin.name)

    def reload(self, path: Path) -> None:
        path = path.resolve()
        if path in self._loaded:
            self.unload(path)
        self.load(path)

    def _import_from_path(self, module_name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to create module spec for {path}")

        module = importlib.util.module_from_spec(spec)
        # ensure new import always wins
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    async def _watch_loop(self) -> None:
        """Poll mtime changes for hot reload (no external deps)."""
        try:
            while True:
                await asyncio.sleep(self.poll_interval)
                self._scan_once()
        except asyncio.CancelledError:
            return

    def _scan_once(self) -> None:
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        current = {p.resolve() for p in self.plugins_dir.glob("*.py")}

        # detect deletions
        for old in list(self._loaded.keys()):
            if old not in current:
                self.unload(old)

        # detect new/modified
        for path in current:
            try:
                mtime = path.stat().st_mtime
            except FileNotFoundError:
                continue

            loaded = self._loaded.get(path)
            if loaded is None:
                self.load(path)
            else:
                # mtime changed => reload
                if mtime != loaded.mtime:
                    logger.info("[PluginManager] Detected change, reloading: %s", path.name)
                    self.reload(path)
