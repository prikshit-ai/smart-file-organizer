"""
categorizer.py - Smart file categorization.
Enhanced with content-aware detection for PDF, DOCX, and TXT.
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
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio", ".aac": "Audio",

    # Documents
    ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
    ".md": "Documents", ".pdf": "Documents",

    # Code
    ".py": "Code", ".js": "Code", ".ts": "Code", ".java": "Code", ".cpp": "Code",

    # Spreadsheets
    ".xlsx": "Spreadsheets", ".csv": "Spreadsheets", ".xls": "Spreadsheets",

    # Presentations
    ".pptx": "Presentations", ".ppt": "Presentations",

    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives", ".tar": "Archives",
}

# -------------------- CONTENT RULES --------------------

CONTENT_KEYWORDS = {
    "Invoices": ["invoice", "bill", "amount due", "total", "payment"],
    "Resumes": ["resume", "cv", "curriculum vitae", "experience", "skills"],
    "Notes": ["notes", "meeting notes", "summary", "points"],
}

PDF_CONTENT_RULES = [
    ("Documents/Resumes", CONTENT_KEYWORDS["Resumes"]),
    ("Documents/Invoices", CONTENT_KEYWORDS["Invoices"]),
    ("Documents/Notes", CONTENT_KEYWORDS["Notes"]),
]

DOC_CONTENT_RULES = [
    ("Documents/Resumes", CONTENT_KEYWORDS["Resumes"]),
    ("Documents/Invoices", CONTENT_KEYWORDS["Invoices"]),
    ("Documents/Notes", CONTENT_KEYWORDS["Notes"]),
]

TXT_CONTENT_RULES = [
    ("Documents/Resumes", CONTENT_KEYWORDS["Resumes"]),
    ("Documents/Invoices", CONTENT_KEYWORDS["Invoices"]),
    ("Documents/Notes", CONTENT_KEYWORDS["Notes"]),
]

# -------------------- TEXT EXTRACTION --------------------

def _extract_pdf_text(path: Path, max_chars: int = 500) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            text = ""
            for page in pdf.pages[:2]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                if len(text) >= max_chars:
                    break
            return text[:max_chars].lower()
    except Exception:
        # fallback
        try:
            return path.read_text(errors="ignore")[:max_chars].lower()
        except Exception:
            return ""


def _extract_docx_text(path: Path, max_chars: int = 500) -> str:
    try:
        import docx
        doc = docx.Document(str(path))
        text = " ".join(p.text for p in doc.paragraphs[:20])
        return text[:max_chars].lower()
    except Exception:
        return ""


def _extract_txt_text(path: Path, max_chars: int = 500) -> str:
    try:
        return path.read_text(errors="ignore")[:max_chars].lower()
    except Exception:
        return ""

# -------------------- KEYWORD MATCHER --------------------

def _match_content_rules(text: str, rules: list) -> str | None:
    for folder, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return folder
    return None

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

    # ---------------- PDF ----------------
    if suffix == ".pdf":
        text = _extract_pdf_text(path)
        if text:
            folder = _match_content_rules(text, PDF_CONTENT_RULES)
            if folder:
                logger.info(f"{path.name} → {folder} (content-based)")
                return folder
        return "Documents"

    # ---------------- DOC/DOCX ----------------
    if suffix in [".doc", ".docx"]:
        text = _extract_docx_text(path)
        if text:
            folder = _match_content_rules(text, DOC_CONTENT_RULES)
            if folder:
                logger.info(f"{path.name} → {folder} (content-based)")
                return folder
        return "Documents"

    # ---------------- TXT ----------------
    if suffix == ".txt":
        text = _extract_txt_text(path)
        if text:
            folder = _match_content_rules(text, TXT_CONTENT_RULES)
            if folder:
                logger.info(f"{path.name} → {folder} (content-based)")
                return folder
        return "Documents"

    # ---------------- EXTENSION RULE ----------------
    if suffix in rules:
        return rules[suffix]

    # ---------------- FALLBACK ----------------
    logger.info(f"{path.name} → Others (fallback)")
    return "Others"