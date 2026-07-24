# Automation Principles

**Status:** Canonical policy for all Plizent repositories
**Owner:** Core Maintainer
**Applies to:** Every workflow, script, and bot under `plizent/*`

## 1. Why this exists

Marketplace Actions, SaaS bots (Dependabot's hosted resolver, Renovate Cloud,
third-party PR-labeler bots, etc.) introduce three failure modes we refuse to
depend on:

| Risk | Example | Consequence |
|---|---|---|
| Vendor outage | `actions/dependency-review-action` API backend down | CI blocked org-wide, no fallback |
| Silent abandonment | Unmaintained marketplace action pinned to old Node runtime | Security holes, deprecation breakage |
| Supply-chain injection | Compromised marketplace action (see `tj-actions/changed-files` 2025 incident) | Secrets exfiltration across every repo using it |
| Auth misuse | Long-lived PAT stored as an org secret | Credential is over-scoped, doesn't expire, hard to audit, survives employee/collaborator turnover |

The fix isn't "audit every action carefully" — it's **own the logic and
minimize the trust surface.**

## 2. The four rules

### Rule 1 — No hosted third-party bots
No Dependabot (hosted resolution), no Renovate Cloud, no marketplace
PR-triage/labeler/stale bots. If you need dependency-update detection,
CVE scanning, or stale-issue handling, it's a **script you own**, triggered
by a scheduled workflow.

**Allowed exceptions** (per your existing memory context): `actions/checkout`
and `actions/setup-java` — these are GitHub-maintained, source-available,
narrowly scoped (file checkout / toolchain install), and have no network
egress or secret access of their own. Everything beyond that is suspect.

### Rule 2 — No Personal Access Tokens
PATs are user-scoped, long-lived by default, and over-privileged (they carry
*all* of your personal repo permissions, not just what one workflow needs).
Replace every PAT with a **GitHub App installation token**, scoped to:
- Only the repos/orgs it needs
- Only the permissions it needs (e.g. `contents: write`, `workflows: write`)
- Short-lived (1 hour, auto-refreshed per run)
- Auditable as its own identity in the audit log (not "acting as you")

This directly covers your `sync-health-files.yml` case: `GITHUB_TOKEN`
cannot push to `.github/workflows/*` by design (GitHub blocks this to prevent
privilege escalation via workflow self-modification) — a GitHub App token
with `workflows: write` is the correct, least-privilege fix, not a PAT.

### Rule 3 — Workflows call scripts, not inline logic or Actions
A workflow YAML file should contain almost no logic — just triggers, checkout,
runtime setup, and a call to a script in `scripts/`. This gives you:
- **Portability** — run it locally: `./scripts/validate-repository.sh`
- **Testability** — unit-test the script itself, independent of CI
- **Diffability** — logic changes show up as script diffs, not YAML soup
- **No vendor coupling** — the script only depends on the language runtime and standard CLIs (`gh`, `jq`, `curl`, `git`), all first-party

### Rule 4 — Own token minting, don't outsource it
Use GitHub's official `actions/create-github-app-token` action (GitHub-maintained,
narrow single purpose: exchange App credentials for an installation token) —
or replicate the JWT exchange yourself in a script if you want zero marketplace
dependency at all. Below is the fully self-owned version.

## 3. Reference implementation

### 3.1 Repo layout

```
.github/
  workflows/
    validate-repository.yml       # trigger + script invocation only
    dependency-update.yml
    sync-health-files.yml
scripts/
  ci/
    validate-repository.sh
    check-dependency-updates.py
    sync-health-files.sh
    lib/
      github-app-auth.sh          # shared token-minting logic
```

### 3.2 Self-owned GitHub App token minting (`scripts/ci/lib/github-app-auth.sh`)

No marketplace action. Pure `openssl` + `curl` + `jq` — all pre-installed on
GitHub-hosted runners, no external service beyond GitHub's own REST API.

```bash
#!/usr/bin/env bash
# github-app-auth.sh — mint a short-lived GitHub App installation token.
# Usage: TOKEN=$(github-app-auth.sh)
set -euo pipefail

: "${PLIZENT_APP_ID:?PLIZENT_APP_ID env var required}"
: "${PLIZENT_APP_PRIVATE_KEY:?PLIZENT_APP_PRIVATE_KEY env var required}"
: "${PLIZENT_APP_INSTALLATION_ID:?PLIZENT_APP_INSTALLATION_ID env var required}"

now=$(date +%s)
iat=$((now - 60))       # backdate 60s for clock drift
exp=$((now + 540))      # 9 min max (GitHub caps JWT at 10 min)

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
payload=$(printf '{"iat":%d,"exp":%d,"iss":"%s"}' "$iat" "$exp" "$PLIZENT_APP_ID" | b64url)
unsigned="${header}.${payload}"

signature=$(printf '%s' "$unsigned" \
  | openssl dgst -sha256 -sign <(printf '%s' "$PLIZENT_APP_PRIVATE_KEY") \
  | b64url)

jwt="${unsigned}.${signature}"

curl -s --fail -X POST \
  -H "Authorization: Bearer ${jwt}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/${PLIZENT_APP_INSTALLATION_ID}/access_tokens" \
  | jq -r '.token'
```

### 3.3 Workflow — thin invoker only

```yaml
# .github/workflows/sync-health-files.yml
name: Sync Health Files

on:
  schedule:
    - cron: "0 3 * * 1"     # weekly, Monday 03:00 UTC
  workflow_dispatch: {}

permissions:
  contents: read            # default token stays minimal; the App token does the real writes

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Mint installation token
        id: auth
        env:
          PLIZENT_APP_ID: ${{ secrets.PLIZENT_APP_ID }}
          PLIZENT_APP_PRIVATE_KEY: ${{ secrets.PLIZENT_APP_PRIVATE_KEY }}
          PLIZENT_APP_INSTALLATION_ID: ${{ secrets.PLIZENT_APP_INSTALLATION_ID }}
        run: echo "token=$(./scripts/ci/lib/github-app-auth.sh)" >> "$GITHUB_OUTPUT"

      - name: Run sync script
        env:
          GH_TOKEN: ${{ steps.auth.outputs.token }}
        run: ./scripts/ci/sync-health-files.sh
```

Note: `id: auth` output is masked as a secret by GitHub Actions automatically
when it matches a registered secret pattern — but to be safe, treat this as
sensitive and never `echo` the raw token elsewhere. `GITHUB_OUTPUT` values
aren't printed to logs by default.

### 3.4 Dependency updates — self-owned, no Dependabot

Instead of relying on GitHub's hosted Dependabot resolver, run your own scan
and open PRs yourself via `gh`:

```python
#!/usr/bin/env python3
# scripts/ci/check-dependency-updates.py
# Parses pom.xml / package.json / requirements.txt in-repo, queries
# public registries (Maven Central, npm registry, PyPI — all already
# allow-listed in your network config) for newer versions, and opens
# a PR via `gh pr create` if updates exist. No third-party service —
# just registry APIs you already trust as upstream sources of truth.
```

This is more work upfront than flipping on Dependabot, but it means:
- You control the PR format, labels, and grouping logic
- You control cadence and batching (one PR per ecosystem, not 40 individual ones)
- Nothing runs unless your own script runs it — no hidden hosted job

## 4. Required repo secrets (App-based, not PAT)

| Secret | Scope | Rotation |
|---|---|---|
| `PLIZENT_APP_ID` | Public, but stored as secret for consistency | Static |
| `PLIZENT_APP_PRIVATE_KEY` | GitHub App private key (PEM) | Rotate on suspicion of leak; GitHub allows multiple active keys during rotation |
| `PLIZENT_APP_INSTALLATION_ID` | Which org/repo installation to mint tokens for | Static per install |

Configure at **Settings → Environments → `plizent-automation` → Environment
secrets**, gated to the `sync-health-files`/`validate-repository` workflows
only (environment protection rules), rather than as repo-wide secrets.

## 5. Checklist for any new automation

- [ ] Is the logic in a script under `scripts/`, not inline YAML or a marketplace action?
- [ ] Does the workflow use a GitHub App token instead of a PAT?
- [ ] Can I run this script locally with the same inputs and get the same result?
- [ ] Does it depend only on `gh`, `curl`, `jq`, `openssl`, and the language runtime — no arbitrary npm/pip packages from unaudited sources?
- [ ] Is the token scoped to only what this specific job needs?