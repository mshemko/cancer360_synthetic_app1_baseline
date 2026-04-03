"""File drop receiver — watches directories for incoming data files (CSV, XML, JSON)."""

import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Awaitable, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

logger = logging.getLogger(__name__)


class FileDropHandler(FileSystemEventHandler):
    """Watchdog handler that queues new files for async processing."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.queue = queue
        self.loop = loop

    def on_created(self, event: FileCreatedEvent):
        if not event.is_directory:
            asyncio.run_coroutine_threadsafe(
                self.queue.put(Path(event.src_path)), self.loop
            )


class FileDropReceiver:
    """Watches incoming directories for new files and routes them to handlers."""

    def __init__(self, watch_dirs: Dict[str, str], processed_dir: str = "processed", error_dir: str = "error"):
        """
        Args:
            watch_dirs: Mapping of directory path → file type identifier.
                        e.g. {"/data/incoming/somerset": "somerset_xml",
                              "/data/incoming/sact": "sact_csv"}
            processed_dir: Subdirectory name for successfully processed files.
            error_dir: Subdirectory name for failed files.
        """
        self.watch_dirs = watch_dirs
        self.processed_dir = processed_dir
        self.error_dir = error_dir
        self._handlers: Dict[str, Callable[[Path, str], Awaitable[None]]] = {}
        self._queue = None
        self._observer = None

    def on_file(self, file_type: str, handler: Callable[[Path, str], Awaitable[None]]):
        """Register a handler for a specific file type."""
        self._handlers[file_type] = handler

    async def start(self):
        """Start watching directories."""
        loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue()

        self._observer = Observer()
        for dir_path, file_type in self.watch_dirs.items():
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            (path / self.processed_dir).mkdir(exist_ok=True)
            (path / self.error_dir).mkdir(exist_ok=True)

            handler = FileDropHandler(self._queue, loop)
            self._observer.schedule(handler, str(path), recursive=False)
            logger.info(f"Watching {path} for {file_type} files")

        self._observer.start()

        # Process queue
        while True:
            file_path = await self._queue.get()
            await self._process_file(file_path)

    async def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()

    async def _process_file(self, file_path: Path):
        """Route a file to the appropriate handler based on its parent directory."""
        parent = str(file_path.parent)
        file_type = None
        for dir_path, ft in self.watch_dirs.items():
            if parent.startswith(dir_path):
                file_type = ft
                break

        if not file_type:
            logger.warning(f"No handler registered for file: {file_path}")
            return

        handler = self._handlers.get(file_type)
        if not handler:
            logger.warning(f"No handler for file type: {file_type}")
            return

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8-sig")  # Handle BOM in NHS CSV exports
            logger.info(f"Processing {file_type} file: {file_path.name} ({len(content)} bytes)")

            await handler(file_path, content)

            # Move to processed
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = file_path.parent / self.processed_dir / f"{ts}_{file_path.name}"
            shutil.move(str(file_path), str(dest))
            logger.info(f"Processed: {file_path.name} → {dest}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            # Move to error directory
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = file_path.parent / self.error_dir / f"{ts}_{file_path.name}"
            shutil.move(str(file_path), str(dest))

            # Write error log alongside
            error_log = dest.with_suffix(dest.suffix + ".error")
            error_log.write_text(f"Error: {e}\nTimestamp: {ts}\nFile: {file_path.name}\n")


async def process_existing_files(directory: str, file_type: str, handler):
    """Process any existing files in a directory (for initial load / replay)."""
    path = Path(directory)
    if not path.exists():
        return

    files = sorted(path.glob("*"))
    for f in files:
        if f.is_file() and f.suffix in (".csv", ".xml", ".json", ".txt"):
            try:
                content = f.read_text(encoding="utf-8-sig")
                await handler(f, content)
                logger.info(f"Processed existing file: {f.name}")
            except Exception as e:
                logger.error(f"Error processing existing file {f.name}: {e}")
