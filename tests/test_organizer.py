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


class TestOrganizeAll:
    def test_organizes_multiple_files(self, organizer, tmp_folder):
        make_file(tmp_folder, "a.jpg")
        make_file(tmp_folder, "b.mp4")
        make_file(tmp_folder, "c.zip")
        with patch("src.organizer.notify"):
            results = organizer.organize_all()
        assert len(results) == 3

    def test_empty_folder_returns_empty(self, organizer, tmp_folder):
        results = organizer.organize_all()
        assert results == []


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
