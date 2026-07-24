#!/usr/bin/env python3
"""
generate-changelog.py
Automated local script to generate and insert a new release entry in CHANGELOG.md
following the Keep a Changelog (https://keepachangelog.com) format.

Usage:
    python scripts/ci/generate-changelog.py --tag v1.1.0 [--date 2026-07-23] [--changelog-path CHANGELOG.md] [--dry-run]
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

def get_git_commits(previous_tag=None):
    """Retrieve git commit messages since last tag or all commits if no tag."""
    try:
        if previous_tag:
            cmd = ["git", "log", f"{previous_tag}..HEAD", "--oneline"]
        else:
            # Try to find latest tag
            latest_tag_cmd = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True)
            if latest_tag_cmd.returncode == 0 and latest_tag_cmd.stdout.strip():
                tag = latest_tag_cmd.stdout.strip()
                cmd = ["git", "log", f"{tag}..HEAD", "--oneline"]
            else:
                cmd = ["git", "log", "-n", "20", "--oneline"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except Exception as e:
        print(f"Warning: Failed to fetch git log: {e}", file=sys.stderr)
        return []

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Security": [],
        "Maintenance": []
    }
    
    for commit in commits:
        # Strip commit hash
        parts = commit.split(" ", 1)
        msg = parts[1] if len(parts) > 1 else parts[0]
        
        lower = msg.lower()
        if lower.startswith("feat") or lower.startswith("add"):
            categories["Added"].append(msg)
        elif lower.startswith("fix"):
            categories["Fixed"].append(msg)
        elif lower.startswith("sec") or "vulnerability" in lower:
            categories["Security"].append(msg)
        elif lower.startswith("refactor") or lower.startswith("style") or lower.startswith("change"):
            categories["Changed"].append(msg)
        else:
            categories["Maintenance"].append(msg)
            
    return categories

def main():
    parser = argparse.ArgumentParser(description="Generate and prepend changelog entry.")
    parser.add_argument("--tag", required=True, help="Release tag/version (e.g. v1.1.0 or 1.1.0)")
    parser.add_argument("--date", help="Release date (YYYY-MM-DD)", required=False)
    parser.add_argument("--changelog-path", default="CHANGELOG.md", help="Path to CHANGELOG.md")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying file")
    args = parser.parse_args()

    changelog_path = os.path.abspath(args.changelog_path)
    if not os.path.exists(changelog_path):
        print(f"Error: {changelog_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    version_clean = re.sub(r"^v", "", args.tag)
    date_str = args.date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    commits = get_git_commits()
    categorized = categorize_commits(commits)

    # Format release section
    entry_lines = [f"## [{version_clean}] - {date_str}\n"]
    for cat_name, msgs in categorized.items():
        if msgs:
            entry_lines.append(f"### {cat_name}\n")
            for m in msgs:
                entry_lines.append(f"- {m}")
            entry_lines.append("")

    new_release_block = "\n".join(entry_lines) + "\n---\n\n"

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if version already exists
    if f"## [{version_clean}]" in content:
        print(f"Version [{version_clean}] already exists in {changelog_path}. Skipping modification.")
        sys.exit(0)

    # Insert after ## [Unreleased] section or before first release heading
    unreleased_pattern = r"(## \[Unreleased\].*?)(---\n\n## \[)"
    if re.search(unreleased_pattern, content, flags=re.DOTALL):
        updated_content = re.sub(
            unreleased_pattern,
            r"\1---\n\n" + new_release_block + r"## [",
            content,
            count=1,
            flags=re.DOTALL
        )
    else:
        # Fallback: insert before first release header
        first_release_pattern = r"(## \[\d+\.\d+\.\d+\])"
        updated_content = re.sub(
            first_release_pattern,
            new_release_block + r"\1",
            content,
            count=1
        )

    if args.dry_run:
        print(f"--- Dry Run: Generated Release Block for [{version_clean}] ---")
        print(new_release_block)
    else:
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Successfully added release [{version_clean}] - {date_str} to {changelog_path}")

if __name__ == "__main__":
    main()
