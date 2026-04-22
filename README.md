# Smart File Organizer

A Python-based command-line tool that automatically organizes files into structured folders using both file extensions and content-aware analysis.

---

## Overview

Smart File Organizer is designed to simplify file management by categorizing files based on their type and content. It supports both one-time organization and real-time monitoring of directories. The system also provides undo functionality and detailed logging for traceability.

---

## Features

* Automatic file sorting into categorized folders such as Images, Videos, Documents, etc.
* Content-aware classification using keyword detection in files (PDF, DOCX, TXT)
* Undo functionality to revert previous operations
* Real-time folder monitoring (watch mode)
* Logging system for tracking file movements
* Configurable rules using a YAML configuration file
* Automated testing using pytest

---

## Project Structure

```
smart-file-organizer/
│
├── src/
│   ├── organizer.py      # Core file organization logic
│   ├── categorizer.py    # File classification logic
│   ├── cli.py            # Command-line interface
│   ├── watcher.py        # Real-time monitoring
│   ├── config.py         # Configuration handling
│   └── notifier.py       # Notification system
│
├── tests/
│   └── test_sorter.py    # Automated test cases
│
├── config.yaml
├── requirements.txt
└── README.md
```

---

## Installation

1. Clone the repository:

```
git clone https://github.com/your-username/smart-file-organizer.git
cd smart-file-organizer
```

2. Install dependencies:

```
pip install -r requirements.txt
```

---

## Usage

### Organize Files Once

```
python -m src.cli run <folder_path>
```

### Watch Folder in Real-Time

```
python -m src.cli watch <folder_path>
```

### Undo Last Operation

```
python -m src.cli undo <folder_path>
```

### Generate Report

```
python -m src.cli report <folder_path>
```

---

## How It Works

1. Scans the target directory recursively using `rglob()`
2. Classifies files using:

   * Extension-based rules
   * Content-based keyword matching
3. Moves files into appropriate directories
4. Logs all operations for undo and reporting

---

## Content-Aware Classification

The system reads the first 500 characters of supported files and matches keywords to determine subcategories.

| Category | Keywords                         | Output Directory   |
| -------- | -------------------------------- | ------------------ |
| Invoices | invoice, bill, amount due, total | Documents/Invoices |
| Resumes  | resume, cv, experience, skills   | Documents/Resumes  |
| Notes    | notes, summary, points           | Documents/Notes    |

---

## Testing

Run automated tests using:

```
PYTHONPATH=. pytest tests/test_sorter.py -v
```

The tests use pytest's `tmp_path` fixture to ensure that no real files are modified during execution.

---

## Technologies Used

* Python 3
* pathlib, shutil, logging, json
* pdfplumber (PDF parsing)
* python-docx (DOCX parsing)
* PyYAML (configuration management)
* pytest (testing framework)
* watchdog (real-time monitoring)

---

## Key Design Aspects

* Modular architecture with clear separation of responsibilities
* Combination of rule-based and content-based classification
* Efficient processing by reading only partial file content
* Safe operations with logging and undo support

---

## Future Enhancements

* Graphical user interface
* Improved content classification using NLP techniques
* Cloud integration for remote file management
* Advanced filtering and rule customization

---

## Author

Prikshit Gaur
Symbiosis Institute of Technology

---

## License

This project is intended for academic and educational purposes.
