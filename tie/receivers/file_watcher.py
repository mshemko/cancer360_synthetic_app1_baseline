"""Polling file watcher to avoid external dependencies."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path


class PollingFileWatcher:
    def __init__(self, directories: list[Path], poll_seconds: float, handler: Callable[[Path], Awaitable[None]]):
        self.directories = directories
        self.poll_seconds = poll_seconds
        self.handler = handler
        self._seen: set[str] = set()

    async def start(self) -> None:
        while True:
            for directory in self.directories:
                directory.mkdir(parents=True, exist_ok=True)
                for child in sorted(directory.glob("*.csv")):
                    key = str(child.resolve())
                    if key in self._seen:
                        continue
                    self._seen.add(key)
                    await self.handler(child)
            await asyncio.sleep(self.poll_seconds)
