# Plizent Organization Health Files

<p align="center">

Files and policies used across all of Plizent's repositories whenever applicable. Includes community health files, organization governance, and local-first automation suite.

</p>

---

## Overview

This repository serves as the central source for GitHub organization standards used across all **Plizent** repositories.

> **Note**  
> This repository does **not** contain application source code or production services. It exists solely to manage organization-wide repository standards, governance policies, and self-owned automation tools.

---

## Repository Structure

```text
.github/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml          # Template for reporting bugs.
│   │   ├── config.yml              # Configures the issue template chooser and support links.
│   │   ├── documentation.yml       # Template for documentation improvements.
│   │   └── feature_request.yml     # Template for requesting new features.
│   ├── workflows/
│   │   ├── release-changelog.yml   # Triggers changelog auto-generation on release.
│   │   ├── sync-health-files.yml   # Triggers community health file sync.
│   │   ├── update-citation.yml     # Triggers CITATION.cff metadata update.
│   │   └── validate-repository.yml # Runs syntax & policy validation on push/PR.
│   ├── PULL_REQUEST_TEMPLATE.md    # Default pull request template.
│   └── release.yml                 # Configures automatic GitHub release notes.
│
├── profile/
│   └── README.md                   # Displays Plizent's public organization profile landing page.
│
├── scripts/
│   └── ci/
│       ├── lib/
│       │   └── github-app-auth.sh  # Mints short-lived GitHub App installation tokens.
│       ├── generate-changelog.py   # Generates release entries in CHANGELOG.md.
│       ├── sync-health-files.py    # Synchronizes health files across org repos (Python).
│       ├── sync-health-files.sh    # Synchronizes health files across org repos (Bash).
│       ├── update-citation.py      # Updates version & date in CITATION.cff.
│       └── validate-repository.py  # Local linter and automation policy validator.
│
├── .editorconfig                   # Consistent coding styles across editors.
├── .gitattributes                  # Git behavior and text normalization.
├── .gitignore                      # Specifies files ignored by Git.
├── automation-principles.md        # Canonical policy for all Plizent automation.
├── CHANGELOG.md                    # Records notable changes across releases.
├── CITATION.cff                    # Citation metadata for academic & GitHub citation.
├── CODE_OF_CONDUCT.md              # Community standards and expected behavior.
├── CODEOWNERS                      # Default code owners for pull request reviews.
├── CONTRIBUTING.md                 # Contribution guidelines and workflow.
├── FUNDING.yml                     # Organization-wide funding & sponsor links.
├── GOVERNANCE.md                   # Decision-making roles and governance model.
├── LICENSE                         # Apache 2.0 open-source license terms.
├── README.md                       # Overview of this repository.
├── SECURITY.md                     # Security policy and vulnerability disclosure.
└── SUPPORT.md                      # Support channels and help resources.
```

---

## Local Automation Usage

In accordance with [automation-principles.md](automation-principles.md), all repository automation scripts can be executed locally without depending on third-party SaaS services:

```bash
# Validate YAML, Markdown, and Automation Principles compliance
python scripts/ci/validate-repository.py

# Test CITATION.cff update (dry-run)
python scripts/ci/update-citation.py --version 1.1.0 --dry-run

# Test CHANGELOG.md generation (dry-run)
python scripts/ci/generate-changelog.py --tag v1.1.0 --dry-run

# Test health files synchronization (dry-run)
python scripts/ci/sync-health-files.py --dry-run
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [automation-principles.md](automation-principles.md) | Canonical automation policy enforcing self-owned scripts & zero hosted third-party bots |
| [CHANGELOG.md](CHANGELOG.md) | Records notable changes made to the repository across releases |
| [CITATION.cff](CITATION.cff) | Citation metadata for GitHub and academic software citation tools |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards and expected behavior |
| [CODEOWNERS](CODEOWNERS) | Defines default code owners responsible for reviewing changes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines and development workflow |
| [GOVERNANCE.md](GOVERNANCE.md) | Decision-making roles and governance model |
| [SECURITY.md](SECURITY.md) | Security policy and vulnerability reporting process |
| [SUPPORT.md](SUPPORT.md) | Support channels and how to get help |

---

## License

Distributed under the terms of the [LICENSE](LICENSE).

<p align="center">

Built and maintained by the **Plizent Foundation**

</p>