from utils.connection import Connection
from utils.asyncioutil import *
import logging

logger = logging.getLogger(__name__)


SUPPORTED_VERSIONS = [1]

class Server:

    def __init__(self, host, port, handler):
        self.host = host
        self.port = port
        self.handler = handler

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
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
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logger.info(f"Server listening on {addrs}")
        async with server:
            await server.serve_forever()
