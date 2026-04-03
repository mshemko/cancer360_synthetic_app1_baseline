"""HL7 MLLP (Minimal Lower Layer Protocol) receiver for ICE pathology and RIS radiology messages."""

import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

MLLP_START = b"\x0b"
MLLP_END = b"\x1c\x0d"


class MLLPReceiver:
    """Async TCP server that receives HL7 v2 messages over MLLP framing."""

    def __init__(self, host: str = "0.0.0.0", port: int = 2575):
        self.host = host
        self.port = port
        self._handler: Callable[[str], Awaitable[str]] = None
        self._server = None

    def on_message(self, handler: Callable[[str], Awaitable[str]]):
        """Register message handler. Handler receives raw HL7 string, returns ACK string."""
        self._handler = handler

    async def start(self):
        """Start the MLLP TCP server."""
        self._server = await asyncio.start_server(
            self._handle_connection, self.host, self.port
        )
        addr = self._server.sockets[0].getsockname()
        logger.info(f"MLLP receiver listening on {addr[0]}:{addr[1]}")
        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a single MLLP connection — may receive multiple messages."""
        peer = writer.get_extra_info("peername")
        logger.info(f"MLLP connection from {peer}")

        buffer = b""
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break

                buffer += data

                while MLLP_START in buffer and MLLP_END in buffer:
                    start_idx = buffer.index(MLLP_START) + len(MLLP_START)
                    end_idx = buffer.index(MLLP_END)

                    if start_idx >= end_idx:
                        buffer = buffer[end_idx + len(MLLP_END):]
                        continue

                    raw_message = buffer[start_idx:end_idx].decode("utf-8", errors="replace")
                    buffer = buffer[end_idx + len(MLLP_END):]

                    logger.debug(f"Received HL7 message ({len(raw_message)} bytes)")

                    # Process and build ACK
                    try:
                        if self._handler:
                            ack = await self._handler(raw_message)
                        else:
                            ack = self._build_ack(raw_message, "AA")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        ack = self._build_ack(raw_message, "AE", str(e))

                    # Send ACK wrapped in MLLP framing
                    writer.write(MLLP_START + ack.encode("utf-8") + MLLP_END)
                    await writer.drain()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"MLLP connection error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"MLLP connection closed from {peer}")

    @staticmethod
    def _build_ack(raw_message: str, ack_code: str = "AA", error_msg: str = "") -> str:
        """Build an HL7 ACK response from the incoming message."""
        lines = raw_message.split("\r")
        msh = lines[0] if lines else ""
        fields = msh.split("|")

        # Extract key MSH fields
        sending_app = fields[2] if len(fields) > 2 else ""
        sending_fac = fields[3] if len(fields) > 3 else ""
        receiving_app = fields[4] if len(fields) > 4 else ""
        receiving_fac = fields[5] if len(fields) > 5 else ""
        msg_control_id = fields[9] if len(fields) > 9 else ""

        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d%H%M%S")

        ack = (
            f"MSH|^~\\&|{receiving_app}|{receiving_fac}|{sending_app}|{sending_fac}|{ts}||ACK|ACK{msg_control_id}|P|2.4\r"
            f"MSA|{ack_code}|{msg_control_id}|{error_msg}\r"
        )
        return ack


class MLLPSender:
    """Send HL7 messages over MLLP to a remote receiver."""

    def __init__(self, host: str, port: int, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    async def send(self, message: str) -> str:
        """Send an HL7 message and return the ACK response."""
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout,
        )

        try:
            # Send with MLLP framing
            writer.write(MLLP_START + message.encode("utf-8") + MLLP_END)
            await writer.drain()

            # Read ACK
            buffer = b""
            while MLLP_END not in buffer:
                data = await asyncio.wait_for(reader.read(4096), timeout=self.timeout)
                if not data:
                    raise ConnectionError("Connection closed before ACK received")
                buffer += data

            start = buffer.index(MLLP_START) + len(MLLP_START)
            end = buffer.index(MLLP_END)
            return buffer[start:end].decode("utf-8")

        finally:
            writer.close()
            await writer.wait_closed()
