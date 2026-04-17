"""
organizer.py - Core file organization logic.
Handles moving files, collision resolution, logging, undo, and notifications.
"""

import json
import shutil
import logging
import time
from datetime import datetime
from pathlib import Path

from . import categorizer
from .config import load_config
from .notifier import notify

logger = logging.getLogger(__name__)

LOG_FILE = "organizer_log.json"


class Organizer:
    def __init__(self, watch_folder: Path, config_path: str = None, silent: bool = False):
        self.watch_folder = Path(watch_folder).resolve()
        self.config = load_config(config_path)

        cfg_silent = bool(self.config.get("silent", False))
        cfg_notify_off = self.config.get("notifications") is False

        self.silent = silent or cfg_silent or cfg_notify_off
        self.custom_rules = self.config.get("rules", {})
        self.log_path = self.watch_folder / LOG_FILE

    # ---------------- LOG HANDLING ----------------

    def _load_log(self) -> list:
        if self.log_path.exists():
            try:
                return json.loads(self.log_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_log(self, entries: list):
        self.log_path.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _append_log(self, entry: dict):
        entries = self._load_log()
        entries.append(entry)
        self._save_log(entries)

    # ---------------- FILE NAME COLLISION ----------------

    def _resolve_dest(self, dest: Path) -> Path:
        if not dest.exists():
            return dest

        stem = dest.stem
        suffix = dest.suffix
        parent = dest.parent
        counter = 1

        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    # ---------------- MAIN FILE ORGANIZATION ----------------

    def organize_file(self, file_path: Path, dry_run: bool = False) -> dict | None:
        file_path = Path(file_path).resolve()

        # Safety check
        try:
            file_path.relative_to(self.watch_folder)
        except ValueError:
            logger.warning(f"Refusing to move file outside watch folder: {file_path}")
            return None

        if not file_path.exists():
            logger.warning(f"File no longer exists: {file_path}")
            return None

        if file_path.name == LOG_FILE:
            return None

        subfolder = categorizer.categorize(file_path, self.custom_rules)
        dest_dir = self.watch_folder / subfolder
        dest_file = self._resolve_dest(dest_dir / file_path.name)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "filename": file_path.name,
            "source": str(file_path),
            "destination": str(dest_file),
            "category": subfolder,
            "dry_run": dry_run,
        }

        if dry_run:
            print(f"  [DRY RUN] {file_path.name!r}  →  {subfolder}/")
            return entry

        dest_dir.mkdir(parents=True, exist_ok=True)

        # 🔥 RETRY LOGIC (FIXED ISSUE)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                shutil.move(str(file_path), str(dest_file))
                break

            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"File '{file_path.name}' is in use. Retrying ({attempt+1}/{max_retries})..."
                    )
                    time.sleep(1)
                else:
                    logger.error(
                        f"Failed to move '{file_path.name}' after {max_retries} attempts: {e}"
                    )
                    print(f"  ⚠️ Skipped: '{file_path.name}' (file in use)")
                    return None

        # Log success
        self._append_log(entry)
        logger.info(f"Moved '{file_path.name}' → {subfolder}/")

        # Notification (safe)
        if not self.silent:
            try:
                notify(
                    title="File Organizer",
                    message=f"Moved {file_path.name} → {subfolder}/",
                )
            except Exception as e:
                logger.warning(f"Notification failed: {e}")

        print(f"  Moved: {file_path.name!r}  →  {subfolder}/")
        return entry

    # ---------------- ORGANIZE ALL ----------------

    def organize_all(self, dry_run: bool = False) -> list:
        results = []

        files = [
            f for f in self.watch_folder.iterdir()
            if f.is_file() and f.name != LOG_FILE
        ]

        if not files:
            print("  No files to organize.")
            return results

        print(f"  Found {len(files)} file(s) to organize.\n")

        for f in sorted(files):
            entry = self.organize_file(f, dry_run=dry_run)
            if entry:
                results.append(entry)

        print(f"\n  Done. {len(results)} file(s) moved.")
        return results

    # ---------------- UNDO ----------------

    def undo(self, steps: int = 1) -> int:
        entries = self._load_log()
        real_entries = [e for e in entries if not e.get("dry_run")]

        if not real_entries:
            print("  Nothing to undo.")
            return 0

        to_undo = real_entries[-steps:]
        restored = 0

        for entry in reversed(to_undo):
            src = Path(entry["destination"])
            dest = Path(entry["source"])

            if not src.exists():
                print(f"  Skipping (missing): {src.name}")
                continue

            if dest.exists():
                print(f"  Conflict detected for {dest.name}, resolving...")
                dest = self._resolve_dest(dest)

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))

            print(f"  Restored: {src.name!r}  →  {dest.parent.name}/")
            restored += 1

        remaining = real_entries[:-steps] if steps < len(real_entries) else []
        dry_entries = [e for e in entries if e.get("dry_run")]

        self._save_log(dry_entries + remaining)

        print(f"\n  Undo complete. {restored} file(s) restored.")
        return restored

    # ---------------- REPORT ----------------

    def report(self) -> dict:
        entries = [e for e in self._load_log() if not e.get("dry_run")]

        if not entries:
            return {"total": 0, "categories": {}}

        categories = {}

        for e in entries:
            cat = e["category"]
            categories.setdefault(cat, []).append(e["filename"])

        return {
            "total": len(entries),
            "categories": {
                k: {"count": len(v), "files": v}
                for k, v in sorted(categories.items())
            },
            "first_run": entries[0]["timestamp"],
            "last_run": entries[-1]["timestamp"],
        }