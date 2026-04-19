"""
test_organizer.py - Unit tests for the Organizer class.
"""

import json
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.organizer import Organizer
from organizer.undo import HISTORY_FILE, load_run_snapshot


@pytest.fixture
def tmp_folder(tmp_path):
    """Provide a temporary watch folder."""
    folder = tmp_path / "watch"
    folder.mkdir()
    return folder


@pytest.fixture
def organizer(tmp_folder):
    return Organizer(tmp_folder, silent=True)


def make_file(folder: Path, name: str, content: str = "test") -> Path:
    f = folder / name
    f.write_text(content)
    return f


class TestOrganizeFile:
    def test_moves_image_to_images_folder(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify"):
            organizer.organize_file(f)
        assert (tmp_folder / "Images" / "photo.jpg").exists()
        assert not f.exists()

    def test_moves_pdf_to_pdfs_folder(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "doc.pdf")
        with patch("src.organizer.notify"), \
             patch("src.categorizer._extract_pdf_text", return_value=""):
            organizer.organize_file(f)
        assert (tmp_folder / "PDFs" / "General" / "doc.pdf").exists()

    def test_dry_run_does_not_move(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        organizer.organize_file(f, dry_run=True)
        assert f.exists()
        assert not (tmp_folder / "Images" / "photo.jpg").exists()

    def test_resolves_filename_collision(self, organizer, tmp_folder):
        f1 = make_file(tmp_folder, "photo.jpg", "first")
        dest_dir = tmp_folder / "Images"
        dest_dir.mkdir(parents=True)
        (dest_dir / "photo.jpg").write_text("existing")
        with patch("src.organizer.notify"):
            organizer.organize_file(f1)
        assert (dest_dir / "photo_1.jpg").exists()

    def test_refuses_file_outside_watch_folder(self, organizer, tmp_path):
        outside = tmp_path / "outside.jpg"
        outside.write_text("hi")
        result = organizer.organize_file(outside)
        assert result is None
        assert outside.exists()  # untouched

    def test_skips_log_file(self, organizer, tmp_folder):
        log = make_file(tmp_folder, "organizer_log.json", "{}")
        result = organizer.organize_file(log)
        assert result is None

    def test_log_entry_written(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify"):
            organizer.organize_file(f)
        log = json.loads((tmp_folder / "organizer_log.json").read_text())
        assert len(log) == 1
        assert log[0]["filename"] == "photo.jpg"
        assert log[0]["category"] == "Images"

    def test_retries_move_until_success(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        dest = tmp_folder / "Images" / "photo.jpg"

        with patch("src.organizer.time.sleep") as mock_sleep, \
             patch("src.organizer.notify"), \
             patch("src.organizer.shutil.move", side_effect=[
                 OSError("locked"),
                 OSError("still locked"),
                 None,
             ]) as mock_move:
            organizer.organize_file(f)

        assert mock_move.call_count == 3
        mock_sleep.assert_called_with(0.5)
        assert mock_move.call_args_list[-1].args == (str(f), str(dest))

    def test_raises_after_exhausting_move_retries(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")

        with patch("src.organizer.time.sleep") as mock_sleep, \
             patch("src.organizer.notify"), \
             patch("src.organizer.shutil.move", side_effect=OSError("locked")) as mock_move:
            with pytest.raises(OSError, match="locked"):
                organizer.organize_file(f)

        assert mock_move.call_count == 3
        assert mock_sleep.call_count == 2


class TestOrganizeAll:
    def test_organizes_multiple_files(self, organizer, tmp_folder):
        make_file(tmp_folder, "a.jpg")
        make_file(tmp_folder, "b.mp4")
        make_file(tmp_folder, "c.zip")
        with patch("src.organizer.notify"):
            results = organizer.organize_all()
        assert len(results) == 3
        assert (tmp_folder / HISTORY_FILE).exists()
        snap = load_run_snapshot(tmp_folder)
        assert set(snap.keys()) == {"a.jpg", "b.mp4", "c.zip"}
        for name in snap:
            assert "from" in snap[name] and "to" in snap[name]

    def test_empty_folder_returns_empty(self, organizer, tmp_folder):
        results = organizer.organize_all()
        assert results == []


class TestSessionUndo:
    def test_undo_restores_full_run_via_snapshot(self, organizer, tmp_folder):
        make_file(tmp_folder, "a.jpg")
        make_file(tmp_folder, "b.mp4")
        with patch("src.organizer.notify"):
            organizer.organize_all()
        assert load_run_snapshot(tmp_folder)
        n = organizer.undo(steps=1)
        assert n == 2
        assert (tmp_folder / "a.jpg").exists()
        assert (tmp_folder / "b.mp4").exists()
        assert not (tmp_folder / HISTORY_FILE).exists()

    def test_organize_all_dry_run_does_not_write_snapshot(self, organizer, tmp_folder):
        make_file(tmp_folder, "x.jpg")
        with patch("src.organizer.notify"):
            organizer.organize_all(dry_run=True)
        assert not (tmp_folder / HISTORY_FILE).exists()

    def test_single_organize_file_does_not_write_snapshot(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify"):
            organizer.organize_file(f)
        assert not (tmp_folder / HISTORY_FILE).exists()


class TestUndo:
    def test_undo_restores_file(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify"):
            organizer.organize_file(f)
        assert not f.exists()
        organizer.undo(steps=1)
        assert f.exists()

    def test_undo_updates_log(self, organizer, tmp_folder):
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify"):
            organizer.organize_file(f)
        organizer.undo(steps=1)
        log = organizer._load_log()
        assert len(log) == 0

    def test_undo_nothing_graceful(self, organizer):
        count = organizer.undo(steps=1)
        assert count == 0

    def test_undo_multiple_steps(self, organizer, tmp_folder):
        for name in ["a.jpg", "b.jpg"]:
            f = make_file(tmp_folder, name)
            with patch("src.organizer.notify"):
                organizer.organize_file(f)
        organizer.undo(steps=2)
        assert (tmp_folder / "a.jpg").exists()
        assert (tmp_folder / "b.jpg").exists()


class TestNotifications:
    def test_organize_continues_when_notify_raises(self, tmp_folder):
        cfg = tmp_folder / "cfg.yaml"
        cfg.write_text("notifications: true\n")
        org = Organizer(tmp_folder, config_path=str(cfg), silent=False)
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify", side_effect=RuntimeError("notify boom")):
            entry = org.organize_file(f)
        assert entry is not None
        assert (tmp_folder / "Images" / "photo.jpg").exists()

    def test_config_notifications_false_skips_notify(self, tmp_folder):
        cfg = tmp_folder / "cfg.yaml"
        cfg.write_text("notifications: false\n")
        org = Organizer(tmp_folder, config_path=str(cfg), silent=False)
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify") as mock_notify:
            org.organize_file(f)
        mock_notify.assert_not_called()

    def test_config_silent_skips_notify(self, tmp_folder):
        cfg = tmp_folder / "cfg.yaml"
        cfg.write_text("silent: true\n")
        org = Organizer(tmp_folder, config_path=str(cfg), silent=False)
        f = make_file(tmp_folder, "photo.jpg")
        with patch("src.organizer.notify") as mock_notify:
            org.organize_file(f)
        mock_notify.assert_not_called()


class TestReport:
    def test_report_empty(self, organizer):
        r = organizer.report()
        assert r["total"] == 0

    def test_report_counts_correctly(self, organizer, tmp_folder):
        for name in ["a.jpg", "b.jpg", "c.mp4"]:
            f = make_file(tmp_folder, name)
            with patch("src.organizer.notify"):
                organizer.organize_file(f)
        r = organizer.report()
        assert r["total"] == 3
        assert r["categories"]["Images"]["count"] == 2
        assert r["categories"]["Videos"]["count"] == 1
