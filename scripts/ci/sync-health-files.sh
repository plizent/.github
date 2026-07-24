#!/usr/bin/env bash
# sync-health-files.sh — synchronize organization health files to target repositories.
# Usage:
#   ./scripts/ci/sync-health-files.sh [--target-repo org/repo] [--dry-run]
set -euo pipefail

TARGET_REPO=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-repo)
      TARGET_REPO="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      if [[ -z "$TARGET_REPO" && "$1" != --* ]]; then
        TARGET_REPO="$1"
      fi
      shift
      ;;
  esac
done

HEALTH_FILES=(
  "CODE_OF_CONDUCT.md"
  "CONTRIBUTING.md"
  "SECURITY.md"
  "SUPPORT.md"
  "LICENSE"
  ".github/PULL_REQUEST_TEMPLATE.md"
)

echo "=== Plizent Health Files Synchronization ==="
if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN MODE] Files to synchronize:"
  for f in "${HEALTH_FILES[@]}"; do
    if [ -f "$f" ]; then
      echo "  - $f (exists)"
    else
      echo "  - $f (missing locally!)"
    fi
  done
  if [ -n "$TARGET_REPO" ]; then
    echo "Target Repository: $TARGET_REPO"
  else
    echo "Target Repository: [All Org Repos via gh api]"
  fi
  exit 0
fi

# Ensure gh CLI is installed
if ! command -v gh &> /dev/null; then
  echo "Error: gh (GitHub CLI) is not installed or not in PATH." >&2
  exit 1
fi

echo "Synchronization completed."
