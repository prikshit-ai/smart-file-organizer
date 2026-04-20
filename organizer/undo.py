"""
Session undo: snapshot written after each non–dry-run `organizer run` (organize_all).

Snapshot file: `.organizer_history.json` in the watch folder, mapping each moved
basename to ``{"from": original_path, "to": new_path}``.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

HISTORY_FILE = ".organizer_history.json"


def _norm_path(p: str | Path) -> str:
    return str(Path(p).resolve())


def _resolve_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def save_run_snapshot(watch_folder: Path, results: list[dict], *, dry_run: bool = False) -> None:
    """
    Persist the last batch run for one-shot session undo.

    Skipped for dry-run. Does not overwrite an existing snapshot when the run
    moved no files (e.g. empty folder), so a prior session remains undoable.
    """
    if dry_run:
        return

    moves: dict[str, dict[str, str]] = {}
    for e in results:
        if e.get("dry_run"):
            continue
        moves[e["filename"]] = {"from": e["source"], "to": e["destination"]}

    path = Path(watch_folder).resolve() / HISTORY_FILE
    if not moves:
        return

    path.write_text(json.dumps(moves, indent=2, ensure_ascii=False), encoding="utf-8")


def load_run_snapshot(watch_folder: Path) -> dict[str, dict[str, str]]:
    path = Path(watch_folder).resolve() / HISTORY_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read %s: %s", path, e)
        return {}
    if not isinstance(data, dict) or not data:
        return {}
    return data


def _trim_log(log_path: Path, destinations_restored: set[str]) -> None:
    if not log_path.exists() or not destinations_restored:
        return
    try:
        entries = json.loads(log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if not isinstance(entries, list):
        return

    kept = []
    for e in entries:
        dest = e.get("destination")
        if dest and _norm_path(dest) in destinations_restored:
            continue
        kept.append(e)

    log_path.write_text(json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8")


def undo_last_session(watch_folder: Path, log_path: Path | None = None) -> int:
    """
    Move every file from the last run snapshot back to its original path.

    Returns the number of files successfully restored.
    """
    watch_folder = Path(watch_folder).resolve()
    log_path = log_path or (watch_folder / "organizer_log.json")
    data = load_run_snapshot(watch_folder)

    if not data:
        print("  Nothing to undo (no saved organize session).")
        return 0

    destinations_restored: set[str] = set()
    restored = 0

    for filename, paths in data.items():
        if not isinstance(paths, dict):
            continue
        src = Path(paths["to"])
        dest = Path(paths["from"])

        if not src.exists():
            print(f"  Skipping (missing at destination): {filename}")
            continue

        dest_use = dest
        if dest.exists() and _norm_path(dest) != _norm_path(src):
            print(f"  Conflict detected for {dest.name}, resolving...")
            dest_use = _resolve_dest(dest)

        dest_use.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest_use))

        label = dest_use.parent.name if dest_use.parent != watch_folder else "."
        print(f"  Restored: {filename!r}  →  {label}/")
        destinations_restored.add(_norm_path(src))
        restored += 1

    _trim_log(log_path, destinations_restored)

    hist = watch_folder / HISTORY_FILE
    if hist.exists():
        hist.unlink()

    print(f"\n  Restored {restored} file(s) to original locations.")
    return restored
