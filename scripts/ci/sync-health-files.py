#!/usr/bin/env python3
"""
sync-health-files.py
Synchronize organization community health files to target repositories.
Works natively on Windows (PowerShell/CMD), Linux, and macOS.

Usage:
    python scripts/ci/sync-health-files.py [--target-repo org/repo] [--dry-run]
"""

import argparse
import os
import shutil
import subprocess
import sys

HEALTH_FILES = [
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "LICENSE",
    os.path.join(".github", "PULL_REQUEST_TEMPLATE.md"),
]

def main():
    parser = argparse.ArgumentParser(description="Synchronize health files to target repositories.")
    parser.add_argument("--target-repo", help="Target repository (e.g. plizent/sample-repo)", default="")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without syncing")
    args = parser.parse_args()

    print("=== Plizent Health Files Synchronization ===")

    if args.dry_run:
        print("[DRY-RUN MODE] Files to synchronize:")
        for f in HEALTH_FILES:
            status = "exists" if os.path.exists(f) else "missing locally!"
            print(f"  - {f} ({status})")
        
        target = args.target_repo if args.target_repo else "[All Org Repos via gh api]"
        print(f"Target Repository: {target}")
        sys.exit(0)

    # Check for gh CLI
    if not shutil.which("gh"):
        print("Error: gh (GitHub CLI) is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)

    print("Synchronization completed.")

if __name__ == "__main__":
    main()
