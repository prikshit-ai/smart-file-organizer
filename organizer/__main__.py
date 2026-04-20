"""
Allow: python -m organizer undo <folder>  (and other CLI subcommands).
"""

import sys


def main() -> None:
    sys.argv[0] = "organizer"
    from src.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
