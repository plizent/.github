#!/usr/bin/env python3
"""
update-citation.py
Automated local script to update version and release date in CITATION.cff.
Usage:
    python scripts/ci/update-citation.py --version 1.1.0 --date 2026-07-23 [--cff-path CITATION.cff] [--dry-run]
"""

import argparse
import datetime
import os
import re
import sys

def main():
    parser = argparse.ArgumentParser(description="Update CITATION.cff metadata.")
    parser.add_argument("--version", help="Version tag/string (e.g. 1.1.0 or v1.1.0)", required=False)
    parser.add_argument("--date", help="Release date YYYY-MM-DD", required=False)
    parser.add_argument("--cff-path", default="CITATION.cff", help="Path to CITATION.cff file")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying file")
    args = parser.parse_args()

    cff_path = os.path.abspath(args.cff_path)
    if not os.path.exists(cff_path):
        print(f"Error: {cff_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    version_str = args.version
    if not version_str:
        # Try reading git tag or default
        version_str = os.environ.get("GITHUB_REF_NAME", "0.1.0")
    
    # Strip leading 'v' if present
    version_str = re.sub(r"^v", "", version_str)

    date_str = args.date
    if not date_str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    with open(cff_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update or add 'version:'
    if re.search(r"^version:\s*.*$", content, flags=re.MULTILINE):
        new_content = re.sub(r"^version:\s*.*$", f"version: {version_str}", content, flags=re.MULTILINE)
    else:
        new_content = content.rstrip() + f"\nversion: {version_str}\n"

    # Update or add 'date-released:'
    if re.search(r"^date-released:\s*.*$", new_content, flags=re.MULTILINE):
        new_content = re.sub(r"^date-released:\s*.*$", f"date-released: {date_str}", new_content, flags=re.MULTILINE)
    else:
        new_content = new_content.rstrip() + f"\ndate-released: {date_str}\n"

    if args.dry_run:
        print(f"--- Dry Run: Proposed {cff_path} Content ---")
        print(new_content)
    else:
        with open(cff_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully updated {cff_path} with version={version_str}, date-released={date_str}")

if __name__ == "__main__":
    main()
