"""
categorizer.py - Smart file categorization.
Categorizes files by extension first, then by content for PDFs and documents.
"""

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default extension-to-folder mapping
DEFAULT_RULES: dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".bmp": "Images", ".svg": "Images", ".webp": "Images", ".tiff": "Images",
    ".ico": "Images", ".heic": "Images", ".raw": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos", ".mov": "Videos",
    ".wmv": "Videos", ".flv": "Videos", ".webm": "Videos", ".m4v": "Videos",
    ".3gp": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio", ".aac": "Audio",
    ".ogg": "Audio", ".m4a": "Audio", ".wma": "Audio",
    # Documents (non-PDF)
    ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
    ".odt": "Documents", ".rtf": "Documents", ".md": "Documents",
    ".pages": "Documents",
    # Spreadsheets
    ".xls": "Spreadsheets", ".xlsx": "Spreadsheets", ".csv": "Spreadsheets",
    ".ods": "Spreadsheets", ".numbers": "Spreadsheets",
    # Presentations
    ".ppt": "Presentations", ".pptx": "Presentations", ".odp": "Presentations",
    ".key": "Presentations",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives", ".bz2": "Archives",
    ".xz": "Archives", ".tar.gz": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".ts": "Code", ".html": "Code",
    ".css": "Code", ".java": "Code", ".cpp": "Code", ".c": "Code",
    ".h": "Code", ".go": "Code", ".rs": "Code", ".rb": "Code",
    ".php": "Code", ".swift": "Code", ".kt": "Code", ".sh": "Code",
    # Executables / installers
    ".exe": "Executables", ".msi": "Executables", ".dmg": "Executables",
    ".pkg": "Executables", ".deb": "Executables", ".rpm": "Executables",
    ".appimage": "Executables",
    # Fonts
    ".ttf": "Fonts", ".otf": "Fonts", ".woff": "Fonts", ".woff2": "Fonts",
    # Ebooks
    ".epub": "Ebooks", ".mobi": "Ebooks", ".azw": "Ebooks",
}

# PDF content-based subcategory keyword maps
PDF_CONTENT_RULES: list[tuple[str, list[str]]] = [
    ("PDFs/Resumes",   ["resume", "curriculum vitae", "cv", "work experience",
                        "professional summary", "skills", "objective", "references"]),
    ("PDFs/Invoices",  ["invoice", "bill to", "amount due", "payment", "total amount",
                        "tax", "subtotal", "due date", "invoice number"]),
    ("PDFs/Research",  ["abstract", "introduction", "methodology", "references",
                        "conclusion", "journal", "doi", "published", "arxiv"]),
    ("PDFs/Reports",   ["executive summary", "table of contents", "prepared by",
                        "report", "quarterly", "annual report", "findings"]),
    ("PDFs/Tickets",   ["booking", "confirmation", "ticket", "seat", "flight",
                        "boarding pass", "reservation", "itinerary"]),
]


def _extract_pdf_text(path: Path, max_chars: int = 3000) -> str:
    """Extract text from a PDF file for content analysis."""
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            text = ""
            for page in pdf.pages[:3]:  # scan first 3 pages only
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
                if len(text) >= max_chars:
                    break
            return text.lower()
    except Exception as e:
        logger.debug(f"PDF text extraction failed for {path.name}: {e}")
        return ""


def _extract_docx_text(path: Path, max_chars: int = 3000) -> str:
    """Extract text from a .docx file."""
    try:
        import docx
        doc = docx.Document(str(path))
        text = " ".join(p.text for p in doc.paragraphs[:50])
        return text[:max_chars].lower()
    except Exception as e:
        logger.debug(f"DOCX text extraction failed for {path.name}: {e}")
        return ""


def categorize(path: Path, custom_rules: dict = None) -> str:
    """
    Determine the destination subfolder for a file.

    Args:
        path: Path to the file
        custom_rules: Optional dict of {'.ext': 'FolderName'} overrides

    Returns:
        Subfolder name (e.g. 'Images', 'PDFs/Resumes', 'Others')
    """
    suffix = path.suffix.lower()
    rules = {**DEFAULT_RULES}
    if custom_rules:
        rules.update(custom_rules)

    # Check custom rules first (user overrides take priority)
    if custom_rules and suffix in custom_rules:
        return custom_rules[suffix]

    # Smart content-based detection for PDFs
    if suffix == ".pdf":
        text = _extract_pdf_text(path)
        if text:
            for folder, keywords in PDF_CONTENT_RULES:
                if any(kw in text for kw in keywords):
                    logger.debug(f"Content-matched '{path.name}' → {folder}")
                    return folder
        return "PDFs/General"

    # Smart content-based detection for DOCX
    if suffix in (".docx", ".doc"):
        text = _extract_docx_text(path)
        if text:
            if any(kw in text for kw in ["resume", "curriculum vitae", "work experience"]):
                return "Documents/Resumes"
            if any(kw in text for kw in ["invoice", "amount due", "bill to"]):
                return "Documents/Invoices"
        return "Documents"

    # Extension-based fallback
    if suffix in rules:
        return rules[suffix]

    return "Others"
