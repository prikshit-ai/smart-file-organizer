"""
watcher.py - Real-time folder watcher using watchdog.
Monitors a target folder and triggers file organization on new file events.
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .organizer import Organizer

logger = logging.getLogger(__name__)

# Patterns to ignore (temp files, partial downloads, hidden files)
IGNORE_PATTERNS = {".tmp", ".part", ".crdownload", ".download", ".DS_Store", "Thumbs.db"}


class FileHandler(FileSystemEventHandler):
    def __init__(self, organizer: Organizer, dry_run: bool = False):
        self.organizer = organizer
        self.dry_run = dry_run
        self._processing = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self._should_ignore(path):
            return
        if path in self._processing:
            return
        self._processing.add(path)
        try:
            # Small delay to ensure file is fully written before acting
            time.sleep(0.5)
            if path.exists():
                logger.info(f"Detected new file: {path.name}")
                self.organizer.organize_file(path, dry_run=self.dry_run)
        finally:
            self._processing.discard(path)

    def _should_ignore(self, path: Path) -> bool:
        if path.suffix.lower() in IGNORE_PATTERNS:
            return True
        if path.name.startswith("."):
            return True
        if path.name in IGNORE_PATTERNS:
            return True
        return False


def watch(folder: str, config_path: str = None, dry_run: bool = False, silent: bool = False):
    """
    Start watching a folder for new files.
    
    Args:
        folder: Path to the folder to watch
        config_path: Optional path to config YAML
        dry_run: If True, preview moves without executing
        silent: If True, suppress desktop notifications
    """
    watch_path = Path(folder).resolve()
    if not watch_path.exists():
        raise FileNotFoundError(f"Watch folder does not exist: {watch_path}")
    if not watch_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {watch_path}")

    organizer = Organizer(watch_path, config_path=config_path, silent=silent)
    handler = FileHandler(organizer, dry_run=dry_run)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=False)
    observer.start()

    mode = "[DRY RUN] " if dry_run else ""
    logger.info(f"{mode}Watching folder: {watch_path}")
    print(f"  Watching: {watch_path}")
    if dry_run:
        print("  Mode: DRY RUN (no files will be moved)")
    print("  Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Stopping watcher...")
        observer.stop()
    observer.join()
    print("  Watcher stopped.")
