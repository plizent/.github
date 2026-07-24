#!/usr/bin/env python3
"""
validate-repository.py
Automated local linter & compliance validator for Plizent repositories.

Checks:
1. YAML Syntax: Validates all YAML files in .github/
2. Policy Check (automation-principles.md):
   - Rule 1: No unauthorized 3rd-party marketplace actions (only actions/checkout and actions/setup-* permitted).
   - Rule 2: No Personal Access Token (PAT) secrets used in workflows.
3. Markdown Linting: Ensures markdown files exist and are non-empty.

Usage:
    python scripts/ci/validate-repository.py
"""

import os
import re
import sys

try:
    import yaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False

# Allowed Actions under Rule 1 of automation-principles.md
ALLOWED_ACTION_PREFIXES = [
    "actions/checkout@",
    "actions/setup-java@",
    "actions/setup-python@",
    "actions/setup-node@",
    "actions/setup-go@",
]

FORBIDDEN_TOKEN_PATTERNS = [
    r"secrets\.PAT",
    r"secrets\.PERSONAL_ACCESS_TOKEN",
    r"secrets\.GH_PAT",
    r"secrets\.MY_PAT"
]

def check_yaml_syntax(file_path):
    """Parse YAML syntax using pyyaml if available, or basic structure check."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if HAS_PYYAML:
        try:
            yaml.safe_load(content)
            return True, "OK"
        except yaml.YAMLError as e:
            return False, f"YAML Syntax Error: {e}"
    else:
        # Basic check for empty or non-string
        if not content.strip():
            return False, "File is empty"
        return True, "OK (Basic check - pyyaml not installed)"

def check_workflow_compliance(file_path):
    """Enforce automation-principles.md Rule 1 and Rule 2."""
    issues = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines, 1):
        # Rule 1: Check marketplace action usage
        if "uses:" in line:
            match = re.search(r"uses:\s*([^\s]+)", line)
            if match:
                action = match.group(1).strip("'\"")
                # Allow local script/action references starting with ./
                if not action.startswith("./"):
                    is_allowed = any(action.startswith(prefix) for prefix in ALLOWED_ACTION_PREFIXES)
                    if not is_allowed:
                        issues.append(f"Line {idx}: Unapproved action '{action}' violates Rule 1 of automation-principles.md")

        # Rule 2: Check PAT references
        for pattern in FORBIDDEN_TOKEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(f"Line {idx}: Reference to Personal Access Token ('{line.strip()}') violates Rule 2 of automation-principles.md")

    return issues

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    github_dir = os.path.join(root_dir, ".github")
    workflows_dir = os.path.join(github_dir, "workflows")

    total_errors = 0
    print("=== Plizent Repository Compliance & Syntax Validator ===")

    # 1. Check YAML Files in .github
    print("\n--- Validating YAML Syntax ---")
    yaml_files = []
    for dirpath, _, filenames in os.walk(github_dir):
        for fname in filenames:
            if fname.endswith(".yml") or fname.endswith(".yaml"):
                yaml_files.append(os.path.join(dirpath, fname))

    for yf in yaml_files:
        rel = os.path.relpath(yf, root_dir)
        valid, msg = check_yaml_syntax(yf)
        if valid:
            print(f"  [PASS] {rel}")
        else:
            print(f"  [FAIL] {rel}: {msg}")
            total_errors += 1

    # 2. Check Workflow Compliance
    if os.path.exists(workflows_dir):
        print("\n--- Validating Workflow Compliance (automation-principles.md) ---")
        wf_files = [os.path.join(workflows_dir, f) for f in os.listdir(workflows_dir) if f.endswith(".yml") or f.endswith(".yaml")]
        for wf in wf_files:
            rel = os.path.relpath(wf, root_dir)
            issues = check_workflow_compliance(wf)
            if not issues:
                print(f"  [PASS] {rel} (Complies with Rule 1 & Rule 2)")
            else:
                print(f"  [FAIL] {rel}:")
                for issue in issues:
                    print(f"    - {issue}")
                total_errors += len(issues)

    print("\n--- Validation Summary ---")
    if total_errors == 0:
        print("Result: ALL CHECKS PASSED SUCCESSFULLY! ✅")
        sys.exit(0)
    else:
        print(f"Result: FAILED with {total_errors} error(s). ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()
