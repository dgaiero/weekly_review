"""Local commands; no network access or Git mutations."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from .models import Effort, WeeklyReport, WeekMetadata, validate_week
from .reports.email import email_html, email_markdown
from .reports.slides import slides_markdown
from .reports.summary import build_report
from .repository import load_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate efforts and compile weekly status")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build-week", "schema"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        if name != "schema":
            command.add_argument(
                "--week",
                default=os.environ.get("REPORT_WEEK") or datetime.now(UTC).strftime("%G-W%V"),
            )
        if name == "build-week":
            command.add_argument(
                "--output", type=Path, help="Output directory (default: ROOT/build)"
            )
    args = parser.parse_args()
    try:
        if args.command == "schema":
            destination = args.root / "schema"
            destination.mkdir(parents=True, exist_ok=True)
            for name, model, mode in (
                ("effort", Effort, "validation"),
                ("weekly-status", WeekMetadata, "validation"),
                ("weekly-report", WeeklyReport, "serialization"),
            ):
                (destination / f"{name}.schema.json").write_text(
                    json.dumps(model.model_json_schema(mode=mode), indent=2) + "\n",
                    encoding="utf-8",
                )
            print(f"Schemas written to {destination}")
            return 0
        week = validate_week(args.week)
        repo = load_repository(args.root, week)
        for warning in repo.warnings:
            print(f"WARNING: {warning}")
        if repo.errors:
            for error in repo.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if args.command == "build-week":
            report = build_report(repo, week)
            email = email_markdown(report)
            artifacts = {
                "report.json": report.model_dump_json(indent=2) + "\n",
                "email.md": email,
                "email.html": email_html(email),
                "slides.md": slides_markdown(report),
            }
            destination = (args.output or args.root / "build") / week
            destination.mkdir(parents=True, exist_ok=True)
            for name, content in artifacts.items():
                (destination / name).write_text(content, encoding="utf-8")
            print(f"Report artifacts written to {destination}")
        else:
            print(f"Validated {len(repo.efforts)} efforts for {week}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
