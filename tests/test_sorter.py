import pytest
from pathlib import Path
from src.organizer import Organizer
from src import categorizer


# ---------------- CATEGORY TESTS ----------------

def test_extension_categorization():
    assert categorizer.categorize(Path("file.jpg")) == "Images"
    assert categorizer.categorize(Path("file.mp4")) == "Videos"
    assert categorizer.categorize(Path("file.py")) == "Code"
    assert categorizer.categorize(Path("file.zip")) == "Archives"
    assert categorizer.categorize(Path("file.pdf")) == "Documents"


def test_no_extension():
    assert categorizer.categorize(Path("file")) == "Others"


# ---------------- FILE MOVE TEST ----------------

def test_file_movement(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("invoice amount due")

    org = Organizer(tmp_path)
    org.organize_all()

    # check moved
    moved_file = tmp_path / "Documents" / "Invoices" / "test.txt"
    assert moved_file.exists()


# ---------------- DUPLICATE FILE TEST ----------------

def test_duplicate_file(tmp_path):
    # create two same files
    f1 = tmp_path / "file.txt"
    f2 = tmp_path / "file_copy.txt"

    f1.write_text("invoice data")
    f2.write_text("invoice data")

    org = Organizer(tmp_path)
    org.organize_all()

    dest = tmp_path / "Documents" / "Invoices"

    files = list(dest.glob("file*"))
    assert len(files) == 2  # both should exist


# ---------------- DRY RUN TEST ----------------

def test_dry_run(tmp_path):
    file = tmp_path / "dry.txt"
    file.write_text("invoice data")

    org = Organizer(tmp_path)
    org.organize_all(dry_run=True)

    # file should NOT move
    assert file.exists()
    dest = tmp_path / "Documents" / "Invoices" / "dry.txt"
    assert not dest.exists()