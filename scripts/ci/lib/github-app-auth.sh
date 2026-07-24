#!/usr/bin/env bash
# github-app-auth.sh — mint a short-lived GitHub App installation token.
# Usage: TOKEN=$(./scripts/ci/lib/github-app-auth.sh)
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
