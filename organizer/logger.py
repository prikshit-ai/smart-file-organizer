"""Human-readable timestamped audit log for file moves (organizer.log)."""

from datetime import datetime
from pathlib import Path

_DEFAULT_LOG_NAME = "organizer.log"


def resolve_audit_log_path(watch_folder: Path, config: dict) -> Path:
    """
    Resolve the audit log path from config.

    If ``organizer_log`` is unset, defaults to ``<watch_folder>/organizer.log``.
    Relative paths are resolved against ``watch_folder``; absolute paths are used as-is.
    """
    watch_folder = Path(watch_folder).resolve()
    raw = config.get("organizer_log")
    if raw is None or raw == "":
        return watch_folder / _DEFAULT_LOG_NAME
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (watch_folder / path).resolve()


def format_moved_line(watch_folder: Path, source_file: Path, dest_file: Path) -> str:
    """Build ``name → relative/dest`` detail for a MOVED line."""
    watch_folder = Path(watch_folder).resolve()
    dest_file = Path(dest_file).resolve()
    try:
        rel_dest = dest_file.relative_to(watch_folder).as_posix()
    except ValueError:
        rel_dest = dest_file.as_posix()
    return f"{Path(source_file).name} → {rel_dest}"


def append_audit_line(log_path: Path, kind: str, detail: str) -> None:
    """
    Append one line: ``[YYYY-MM-DD HH:MM:SS] KIND: detail``.

    ``kind`` must be one of ``MOVED``, ``ERROR``, ``SKIP``.
    """
    log_path = Path(log_path)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {kind}: {detail}\n"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line)
