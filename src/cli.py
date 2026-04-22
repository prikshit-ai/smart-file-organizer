#!/usr/bin/env python3
"""
cli.py - Command-line interface for Smart File Organizer.

Commands:
  organizer watch <folder>   Watch a folder in real-time
  organizer run <folder>     Organize all files in a folder once
  organizer undo <folder>    Undo the last run session (or log steps if no snapshot)
  organizer report <folder>  Show an organization summary report
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from rich import print
from rich.box import ASCII
from rich.table import Table

from organizer.reporter import build_audit_summary

# Allow running as: python -m src.cli OR as installed command
try:
    from src.organizer import Organizer
    from src.watcher import watch
except ImportError:
    from organizer import Organizer
    from watcher import watch


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_watch(args):
    setup_logging(args.verbose)

    print("\n[bold cyan]Smart File Organizer - Watch Mode[/bold cyan]")
    print("[green]Watching for new files...[/green]\n")

    watch(
        folder=args.folder,
        config_path=args.config,
        dry_run=args.dry_run,
        silent=args.silent,
    )


def cmd_run(args):
    setup_logging(args.verbose)
    folder = Path(args.folder).resolve()

    print("\n[bold cyan]Smart File Organizer - Run Mode[/bold cyan]")
    print("-" * 40)

    if args.dry_run:
        print("[yellow]Mode: DRY RUN - no files will be moved[/yellow]\n")

    exclude_exts = []
    if args.exclude:
        exclude_exts = [f".{ext.strip().lower()}" for ext in args.exclude.split(",")]

    organizer = Organizer(folder, config_path=args.config, silent=args.silent)

    results = organizer.organize_all(dry_run=args.dry_run)

    if not results:
        print("[yellow]No files found.[/yellow]")
        return

    # 🔥 DRY RUN TABLE
    if args.dry_run:
        table = Table(title="Dry Run Preview")
        table.add_column("File", style="cyan")
        table.add_column("Current Location", style="yellow")
        table.add_column("Would Move To", style="green")

        for entry in results:
            table.add_row(
                entry["filename"],
                entry.get("current_location", "-"),
                entry.get("would_move_to", "-"),
            )

        print(table)
        print(f"\n[bold yellow]Preview: {len(results)} file(s) would be moved[/bold yellow]")

    # 🔥 NORMAL RUN TABLE
    else:
        table = Table(title="Organization Summary")
        table.add_column("File", style="cyan")
        table.add_column("Category", style="green")

        for entry in results:
            table.add_row(entry["filename"], entry["category"])

        print(table)
        print(f"\n[bold green]Organized {len(results)} file(s)[/bold green]")

def cmd_undo(args):
    setup_logging(args.verbose)
    folder = Path(args.folder).resolve()

    print("\n[bold cyan]Smart File Organizer - Undo[/bold cyan]")
    print("-" * 40)

    organizer = Organizer(folder, config_path=args.config)
    organizer.undo(steps=args.steps)


def cmd_report(args):
    setup_logging(args.verbose)
    folder = Path(args.folder).resolve()
    organizer = Organizer(folder, config_path=args.config)
    report = build_audit_summary(organizer.audit_log_path)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("\n[bold cyan]Smart File Organizer - Report[/bold cyan]")
    print("-" * 40)

    if report["total"] == 0:
        print(
            "[yellow]No MOVED entries found in the audit log "
            f"({organizer.audit_log_path}).[/yellow]\n"
        )
        return

    table = Table(box=ASCII, show_header=True, header_style="bold")
    table.add_column("Category", style="cyan", no_wrap=False)
    table.add_column("Files moved", justify="right", style="green")
    table.add_column("Last activity", style="yellow")

    for cat, info in report["categories"].items():
        table.add_row(cat, str(info["count"]), info["last_activity"])

    print(table)
    print(f"\n[bold]Total files organized (all sessions):[/bold] {report['total']}")
    print(
        f"[dim]First activity: {report.get('first_activity', 'N/A')}  "
        f"|  Last activity: {report.get('last_activity', 'N/A')}[/dim]\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="organizer",
        description="Smart File Organizer - auto-sort files into categorized subfolders.",
    )
    parser.add_argument("--version", action="version", version="1.0.0")

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # Shared arguments
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("folder", help="Target folder path")
    shared.add_argument("--config", "-c", metavar="FILE", help="Path to config.yaml")
    shared.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    # watch
    p_watch = subparsers.add_parser(
        "watch",
        parents=[shared],
        help="Watch a folder and organize files in real-time",
    )
    p_watch.add_argument("--dry-run", action="store_true", help="Preview moves without executing")
    p_watch.add_argument("--silent", action="store_true", help="Disable desktop notifications")
    p_watch.set_defaults(func=cmd_watch)

    # run
    p_run = subparsers.add_parser(
        "run",
        parents=[shared],
        help="Organize all existing files in a folder once",
    )
    p_run.add_argument("--dry-run", action="store_true", help="Preview moves without executing")
    p_run.add_argument("--silent", action="store_true", help="Disable desktop notifications")
    p_run.add_argument(
    "--exclude",
    type=str,
    help="Comma-separated file extensions to skip (e.g. pdf,mp4,dmg)",
)
    p_run.set_defaults(func=cmd_run)

    # undo
    p_undo = subparsers.add_parser(
        "undo",
        parents=[shared],
        help="Undo the last run session (snapshot), or log-based steps if none",
    )
    p_undo.add_argument(
        "--steps",
        "-n",
        type=int,
        default=1,
        metavar="N",
        help="With no run snapshot: undo this many last moves from the log (default: 1)",
    )
    p_undo.set_defaults(func=cmd_undo)

    # report
    p_report = subparsers.add_parser(
        "report",
        parents=[shared],
        help="Show an organization summary report",
    )
    p_report.add_argument("--json", action="store_true", help="Output report as JSON")
    p_report.set_defaults(func=cmd_report)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(f"\n[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()