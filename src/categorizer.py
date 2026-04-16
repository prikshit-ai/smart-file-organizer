"""
categorizer.py - Smart file categorization.
Enhanced with content-aware detection and improved structure.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# -------------------- DEFAULT RULES --------------------

DEFAULT_RULES: dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".bmp": "Images", ".svg": "Images", ".webp": "Images", ".tiff": "Images",
    ".ico": "Images", ".heic": "Images", ".raw": "Images",

    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos", ".mov": "Videos",

    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",

    # Documents
    ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
    ".md": "Documents",

    # Code
    ".py": "Code", ".js": "Code", ".java": "Code", ".cpp": "Code",

    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
}

# -------------------- CONTENT RULES --------------------

PDF_CONTENT_RULES = [
    ("PDFs/Resumes", ["resume", "cv", "curriculum vitae", "skills"]),
    ("PDFs/Invoices", ["invoice", "amount due", "bill to", "total"]),
    ("PDFs/Research", ["abstract", "introduction", "research", "paper"]),
    ("PDFs/Reports", ["report", "summary", "analysis"]),
]

DOC_CONTENT_RULES = [
    ("Documents/Resumes", ["resume", "cv", "experience"]),
    ("Documents/Invoices", ["invoice", "amount due"]),
]

# -------------------- TEXT EXTRACTION --------------------

def _extract_pdf_text(path: Path, max_chars: int = 2000) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            text = ""
            for page in pdf.pages[:2]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                if len(text) > max_chars:
                    break
            return text.lower()
    except Exception:
        # 🔥 fallback for fake/test PDFs
        try:
            return path.read_text(errors="ignore").lower()
        except:
            return ""


def _extract_docx_text(path: Path, max_chars: int = 2000) -> str:
    try:
        import docx
        doc = docx.Document(str(path))
        text = " ".join(p.text for p in doc.paragraphs[:30])
        return text[:max_chars].lower()
    except Exception:
        return ""

# -------------------- MAIN FUNCTION --------------------

def categorize(path: Path, custom_rules: dict = None) -> str:
    """
    Categorize a file based on extension and content.
    """

    suffix = path.suffix.lower()
    rules = {**DEFAULT_RULES}

    if custom_rules:
        rules.update(custom_rules)

    # ---------------- CUSTOM RULES ----------------
    if custom_rules and suffix in custom_rules:
        return custom_rules[suffix]

    # ---------------- PDF CONTENT ----------------
    if suffix == ".pdf":
        text = _extract_pdf_text(path)

        if text:
            for folder, keywords in PDF_CONTENT_RULES:
                if any(keyword in text for keyword in keywords):
                    logger.info(f"{path.name} → {folder} (content-based)")
                    return folder

        return "PDFs/General"

    # ---------------- DOC/DOCX CONTENT ----------------
    if suffix in [".doc", ".docx"]:
        text = _extract_docx_text(path)

        if text:
            for folder, keywords in DOC_CONTENT_RULES:
                if any(keyword in text for keyword in keywords):
                    logger.info(f"{path.name} → {folder} (content-based)")
                    return folder

        return "Documents"

    # ---------------- EXTENSION RULE ----------------
    if suffix in rules:
        return rules[suffix]

    # ---------------- FALLBACK ----------------
    logger.info(f"{path.name} → Others (fallback)")
    return "Others"