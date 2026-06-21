"""
CLI tool — Add accepted Screen Reader controls to the whitelist.

Usage:
    python src/tools/accept_sr_control.py --name "Profile and preferences ..." --platform Windows
    python src/tools/accept_sr_control.py --name "control text" --sr-text "expected sr" --version 46.6.0
    python src/tools/accept_sr_control.py --list                      # list all accepted
    python src/tools/accept_sr_control.py --file controls.txt         # bulk insert from file
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.processor.accept_sr_processor import insert_accepted_control, get_accepted_controls


def main():
    parser = argparse.ArgumentParser(description="Manage accepted Screen Reader controls")
    parser.add_argument("--name", type=str, help="Control name / SR description to accept")
    parser.add_argument("--sr-text", type=str, default=None, help="Expected SR text (optional)")
    parser.add_argument("--platform", type=str, default="Windows")
    parser.add_argument("--version", type=str, default=None, help="App version")
    parser.add_argument("--language", type=str, default="en_US")
    parser.add_argument("--added-by", type=str, default="wrs")
    parser.add_argument("--list", action="store_true", help="List all accepted controls")
    parser.add_argument("--file", type=str, default=None, help="Bulk insert from file (one control name per line)")

    args = parser.parse_args()

    if args.list:
        accepted = get_accepted_controls(args.platform, args.language)
        if not accepted:
            print("No accepted controls found.")
            return
        print(f"{'#':<4} {'Control Name':<80} {'Expected SR Text'}")
        print("-" * 120)
        for i, (name, sr_text) in enumerate(accepted.items(), 1):
            print(f"{i:<4} {name:<80} {sr_text or '(any)'}")
        print(f"\nTotal: {len(accepted)}")
        return

    if args.file:
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        count = 0
        for line in lines:
            if insert_accepted_control(
                control_name=line,
                platform=args.platform,
                app_version=args.version,
                language=args.language,
                added_by=args.added_by,
            ):
                count += 1
        print(f"Inserted {count}/{len(lines)} controls.")
        return

    if not args.name:
        parser.print_help()
        sys.exit(1)

    ok = insert_accepted_control(
        control_name=args.name,
        expected_sr_text=args.sr_text,
        platform=args.platform,
        app_version=args.version,
        language=args.language,
        added_by=args.added_by,
    )
    if ok:
        print(f"✅ Accepted: {args.name}")
    else:
        print(f"⚠️  Not inserted (already exists or error)")


if __name__ == "__main__":
    main()
