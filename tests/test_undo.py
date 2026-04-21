"""
test_undo.py - Unit tests for organizer.undo module.
"""

import json
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from organizer.undo import HISTORY_FILE, undo_last_session


def _write_snapshot(folder: Path, filename: str, source: Path, destination: Path):
    snapshot = {
        filename: {
            "from": str(source),
            "to": str(destination),
        }
    }
    (folder / HISTORY_FILE).write_text(json.dumps(snapshot), encoding="utf-8")


class TestUndoModule:
    def test_undo_moves_file_back_to_original_path(self, tmp_path):
        watch_folder = tmp_path / "watch"
        watch_folder.mkdir()

        original = watch_folder / "photo.jpg"
        moved = watch_folder / "Images" / "photo.jpg"
        moved.parent.mkdir()
        moved.write_text("image data", encoding="utf-8")

        _write_snapshot(watch_folder, "photo.jpg", original, moved)

        restored = undo_last_session(watch_folder)

        assert restored == 1
        assert original.exists()
        assert original.read_text(encoding="utf-8") == "image data"
        assert not moved.exists()

    def test_undo_with_no_history_prints_friendly_message(self, tmp_path, capsys):
        watch_folder = tmp_path / "watch"
        watch_folder.mkdir()

        restored = undo_last_session(watch_folder)
        output = capsys.readouterr().out

        assert restored == 0
        assert "Nothing to undo" in output

    def test_history_file_is_cleared_after_undo(self, tmp_path):
        watch_folder = tmp_path / "watch"
        watch_folder.mkdir()

        original = watch_folder / "video.mp4"
        moved = watch_folder / "Videos" / "video.mp4"
        moved.parent.mkdir()
        moved.write_text("video data", encoding="utf-8")

        _write_snapshot(watch_folder, "video.mp4", original, moved)
        history_path = watch_folder / HISTORY_FILE
        assert history_path.exists()

        undo_last_session(watch_folder)

        assert not history_path.exists()
