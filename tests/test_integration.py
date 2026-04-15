"""
test_integration.py - End-to-end integration tests simulating real usage.
"""

import time
import threading
import pytest
from pathlib import Path
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.organizer import Organizer


@pytest.fixture
def watch_folder(tmp_path):
    folder = tmp_path / "downloads"
    folder.mkdir()
    return folder


def make_file(folder, name, content="data"):
    f = folder / name
    f.write_text(content)
    return f


class TestFullWorkflow:
    def test_run_organize_then_report_then_undo(self, watch_folder):
        """Full cycle: run → report → undo."""
        files = {
            "image.png": "Images",
            "video.mp4": "Videos",
            "archive.zip": "Archives",
        }
        for name in files:
            make_file(watch_folder, name)

        organizer = Organizer(watch_folder, silent=True)
        with patch("src.organizer.notify"):
            results = organizer.organize_all()

        assert len(results) == 3

        # All files should be in their subfolders
        for name, cat in files.items():
            assert (watch_folder / cat / name).exists()

        # Report should reflect 3 moves
        report = organizer.report()
        assert report["total"] == 3

        # Undo all
        organizer.undo(steps=3)
        for name in files:
            assert (watch_folder / name).exists()

        # Log should be empty after undo
        assert organizer._load_log() == []

    def test_dry_run_leaves_files_intact(self, watch_folder):
        make_file(watch_folder, "photo.jpg")
        make_file(watch_folder, "doc.pdf")

        organizer = Organizer(watch_folder, silent=True)
        with patch("src.categorizer._extract_pdf_text", return_value=""):
            results = organizer.organize_all(dry_run=True)

        assert len(results) == 2
        assert (watch_folder / "photo.jpg").exists()
        assert (watch_folder / "doc.pdf").exists()
        assert not (watch_folder / "Images").exists()

    def test_custom_config_rules(self, watch_folder):
        """Custom rule overrides default categorization."""
        f = make_file(watch_folder, "work_meeting.mp4")
        config = {"rules": {".mp4": "Videos/Work"}}

        organizer = Organizer(watch_folder, silent=True)
        organizer.custom_rules = config["rules"]

        with patch("src.organizer.notify"):
            organizer.organize_file(f)

        assert (watch_folder / "Videos" / "Work" / "work_meeting.mp4").exists()

    def test_collision_handling(self, watch_folder):
        """Two files with same name go to same folder without overwriting."""
        (watch_folder / "Images").mkdir()
        existing = watch_folder / "Images" / "photo.jpg"
        existing.write_text("original")

        new_file = make_file(watch_folder, "photo.jpg", "new content")
        organizer = Organizer(watch_folder, silent=True)
        with patch("src.organizer.notify"):
            organizer.organize_file(new_file)

        assert existing.read_text() == "original"
        assert (watch_folder / "Images" / "photo_1.jpg").read_text() == "new content"
