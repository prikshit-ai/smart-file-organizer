from setuptools import setup, find_packages

setup(
    name="smart-file-organizer",
    version="1.0.0",
    description="A smart CLI tool that auto-sorts files into categorized subfolders",
    author="Prikshit, Sarthak, Shwet, Saksham",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "watchdog>=3.0.0",
        "pdfplumber>=0.10.0",
        "python-docx>=1.1.0",
        "PyYAML>=6.0",
        "plyer>=2.1.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "organizer=src.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
