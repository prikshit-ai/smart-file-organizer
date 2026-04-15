"""
test_categorizer.py - Unit tests for the categorizer module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.categorizer import categorize, DEFAULT_RULES


class TestExtensionBasedCategorization:
    def test_image_extensions(self):
        for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Images", f"Expected Images for {ext}"

    def test_video_extensions(self):
        for ext in [".mp4", ".mkv", ".avi", ".mov"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Videos"

    def test_audio_extensions(self):
        for ext in [".mp3", ".wav", ".flac", ".aac"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Audio"

    def test_archive_extensions(self):
        for ext in [".zip", ".rar", ".7z", ".tar"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Archives"

    def test_code_extensions(self):
        for ext in [".py", ".js", ".ts", ".java", ".cpp"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Code"

    def test_spreadsheet_extensions(self):
        for ext in [".xlsx", ".csv", ".xls"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Spreadsheets"

    def test_presentation_extensions(self):
        for ext in [".pptx", ".ppt"]:
            p = Path(f"file{ext}")
            assert categorize(p) == "Presentations"

    def test_unknown_extension_goes_to_others(self):
        p = Path("file.xyz123")
        assert categorize(p) == "Others"

    def test_no_extension_goes_to_others(self):
        p = Path("Makefile")
        assert categorize(p) == "Others"

    def test_case_insensitive_extension(self):
        assert categorize(Path("photo.JPG")) == "Images"
        assert categorize(Path("video.MP4")) == "Videos"


class TestCustomRules:
    def test_custom_rule_overrides_default(self):
        custom = {".mp4": "Videos/Work"}
        assert categorize(Path("video.mp4"), custom_rules=custom) == "Videos/Work"

    def test_custom_rule_new_extension(self):
        custom = {".blend": "3DFiles"}
        assert categorize(Path("scene.blend"), custom_rules=custom) == "3DFiles"

    def test_custom_rules_do_not_affect_other_extensions(self):
        custom = {".mp4": "Videos/Work"}
        assert categorize(Path("photo.jpg"), custom_rules=custom) == "Images"


class TestPDFCategorization:
    def _make_pdf(self, name="file.pdf"):
        return Path(name)

    def test_pdf_resume_detection(self):
        with patch("src.categorizer._extract_pdf_text") as mock_extract:
            mock_extract.return_value = "john doe resume work experience skills objective"
            result = categorize(self._make_pdf("john_resume.pdf"))
            assert result == "PDFs/Resumes"

    def test_pdf_invoice_detection(self):
        with patch("src.categorizer._extract_pdf_text") as mock_extract:
            mock_extract.return_value = "invoice number 1234 amount due payment tax subtotal"
            result = categorize(self._make_pdf("invoice.pdf"))
            assert result == "PDFs/Invoices"

    def test_pdf_research_detection(self):
        with patch("src.categorizer._extract_pdf_text") as mock_extract:
            mock_extract.return_value = "abstract introduction methodology conclusion doi arxiv"
            result = categorize(self._make_pdf("paper.pdf"))
            assert result == "PDFs/Research"

    def test_pdf_generic_when_no_keywords(self):
        with patch("src.categorizer._extract_pdf_text") as mock_extract:
            mock_extract.return_value = "some random text with no matching keywords"
            result = categorize(self._make_pdf("random.pdf"))
            assert result == "PDFs/General"

    def test_pdf_general_when_extraction_fails(self):
        with patch("src.categorizer._extract_pdf_text") as mock_extract:
            mock_extract.return_value = ""
            result = categorize(self._make_pdf("empty.pdf"))
            assert result == "PDFs/General"
