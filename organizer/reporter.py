"""Summaries from human-readable organizer.log (MOVED audit lines)."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

MOVED_LINE_RE = re.compile(
    r"^\[(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})\] MOVED: (?P<detail>.+?)\s*$"
)


def _category_from_rel_dest(rel_dest: str) -> str:
    normalized = rel_dest.replace("\\", "/")
    parent = PurePosixPath(normalized).parent.as_posix()
    return "." if parent == "." else parent


def _split_moved_detail(detail: str) -> tuple[str, str] | None:
    sep = " → "
    if sep not in detail:
        return None
    name, rel = detail.split(sep, 1)
    name, rel = name.strip(), rel.strip()
    if not rel:
        return None
    return name, rel


def parse_audit_log_text(log_text: str) -> list[dict[str, str]]:
    """Return one dict per MOVED line (chronological order of appearance in the file)."""
    moves: list[dict[str, str]] = []
    for raw in log_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = MOVED_LINE_RE.match(line)
        if not m:
            continue
        parts = _split_moved_detail(m.group("detail"))
        if not parts:
            continue
        _name, rel_dest = parts
        date = m.group("date")
        time = m.group("time")
        moves.append(
            {
                "date": date,
                "time": time,
                "datetime": f"{date} {time}",
                "rel_dest": rel_dest,
                "category": _category_from_rel_dest(rel_dest),
            }
        )
    return moves


def summarize_moves(moves: list[dict[str, str]]) -> dict[str, Any]:
    """Group MOVED events by category; last activity is the calendar date of the latest move in that category."""
    if not moves:
        return {
            "total": 0,
            "categories": {},
            "first_activity": None,
            "last_activity": None,
        }

    chron = sorted(moves, key=lambda x: x["datetime"])
    by_cat: dict[str, dict[str, Any]] = {}
    for m in moves:
        cat = m["category"]
        if cat not in by_cat:
            by_cat[cat] = {"count": 0, "last_datetime": m["datetime"]}
        by_cat[cat]["count"] += 1
        if m["datetime"] > by_cat[cat]["last_datetime"]:
            by_cat[cat]["last_datetime"] = m["datetime"]

    categories = {
        cat: {
            "count": data["count"],
            "last_activity": data["last_datetime"][:10],
        }
        for cat, data in sorted(by_cat.items(), key=lambda kv: kv[0])
    }

    return {
        "total": len(moves),
        "categories": categories,
        "first_activity": chron[0]["datetime"][:10],
        "last_activity": chron[-1]["datetime"][:10],
    }


def build_audit_summary(audit_log_path: Path) -> dict[str, Any]:
    """Parse ``organizer.log`` at ``audit_log_path`` and return ``summarize_moves`` output."""
    path = Path(audit_log_path)
    if not path.is_file():
        return summarize_moves([])
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return summarize_moves([])
    return summarize_moves(parse_audit_log_text(text))
