from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

from utils.connection import Connection
from utils.asyncioutil import *


logger = logging.getLogger(__name__)


SUPPORTED_VERSIONS = [1]

class Server:

    def __init__(self, host, port, handler, *, security_store: Any = None):
        self.host = host
        self.port = port
        self.handler = handler
        self.security_store = security_store

        self._server: Optional[asyncio.base_events.Server] = None
        self._serve_task: Optional[asyncio.Task] = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        # addr: (ip, port)
        ip = None
        try:
            ip = addr[0] if isinstance(addr, (tuple, list)) and addr else None
        except Exception:
            ip = None

        # Security: blacklist/ban by IP (best-effort)
        try:
            if ip and self.security_store is not None:
                if getattr(self.security_store, "is_blacklisted_ip", None) and self.security_store.is_blacklisted_ip(ip):
                    logger.warning("Rejected blacklisted IP: %s", ip)
                    writer.close()
                    await writer.wait_closed()
                    return
                if getattr(self.security_store, "is_banned", None):
                    rec = self.security_store.is_banned("ip", str(ip))
                    if rec is not None:
                        logger.warning("Rejected banned IP: %s", ip)
                        writer.close()
                        await writer.wait_closed()
                        return
        except Exception:
            logger.exception("Security check failed (ip)")

        client_version = (await reader.readexactly(1))[0]
        logger.info(f"Connected client from {addr}")
        logger.info(f"Client version: {client_version}")

        if client_version not in SUPPORTED_VERSIONS:
            logger.warning(f"Unsupported protocol version: {client_version} from {addr}")
            writer.close()
            await writer.wait_closed()
            return

        connection = Connection(writer)

        try:
            self.handler(connection)
            while True:
                connection.on_receive(await receive_message(reader))
        except (asyncio.IncompleteReadError, ConnectionResetError):
            logger.info(f"Client disconnected from {addr}")
        finally:
            connection.close()

    async def start(self):
        # start_server returns immediately, but serve_forever blocks, so we run it in a task.
        self._server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addrs = ', '.join(str(sock.getsockname()) for sock in (self._server.sockets or []))
        logger.info(f"Server listening on {addrs}")

        async def _serve() -> None:
            assert self._server is not None
            async with self._server:
                await self._server.serve_forever()

        self._serve_task = asyncio.create_task(_serve())

    async def stop(self) -> None:
        if self._serve_task:
            self._serve_task.cancel()
            try:
                await self._serve_task
            except Exception:
                pass
            self._serve_task = None

        if self._server:
            try:
                self._server.close()
                await self._server.wait_closed()
            except Exception:
                logger.exception("Server stop failed")
            finally:
                self._server = None
