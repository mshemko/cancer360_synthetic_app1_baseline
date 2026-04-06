"""Minimal MLLP server for HL7 traffic."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

MLLP_START = b"\x0b"
MLLP_END = b"\x1c\x0d"


class MLLPServer:
    def __init__(self, host: str, port: int, handler: Callable[[str], Awaitable[str]]):
        self.host = host
        self.port = port
        self.handler = handler
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_connection, self.host, self.port)
        async with self._server:
            await self._server.serve_forever()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        buffer = b""
        try:
            while True:
                chunk = await reader.read(65536)
                if not chunk:
                    break
                buffer += chunk
                while MLLP_START in buffer and MLLP_END in buffer:
                    start = buffer.index(MLLP_START) + 1
                    end = buffer.index(MLLP_END)
                    message = buffer[start:end].decode("utf-8", errors="replace")
                    buffer = buffer[end + len(MLLP_END):]
                    ack = await self.handler(message)
                    writer.write(MLLP_START + ack.encode("utf-8") + MLLP_END)
                    await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
