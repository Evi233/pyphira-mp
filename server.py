from connection import Connection
from asyncioutil import *

class Server:

    def __init__(self, host, port, handler):
        self.host = host
        self.port = port
        self.handler = handler

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        client_version = (await reader.readexactly(1))[0]
        print("Connected", addr)
        print("Version", client_version)

        try:
            connection = Connection(writer)
            self.handler(connection)
            while True:
                connection.on_receive(await receive_message(reader))
        except (asyncio.IncompleteReadError, ConnectionResetError):
            print("Client disconnected", addr)
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Listening on {addrs}")
        async with server:
            await server.serve_forever()
