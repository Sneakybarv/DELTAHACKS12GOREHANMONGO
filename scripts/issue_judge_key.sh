#!/usr/bin/env bash
set -e

API_URL=${API_URL:-http://localhost:8000}
ADMIN_KEY=${ADMIN_KEY:-$ADMIN_KEY}
OWNER=${1:-judge}
HOURS=${2:-24}

if [ -z "$ADMIN_KEY" ]; then
  echo "ERROR: ADMIN_KEY environment variable is required."
  echo "Set it like: export ADMIN_KEY=\"...\""
  exit 1
fi

resp=$(curl -s -X POST "$API_URL/api/admin/issue-key?owner=$OWNER&expires_hours=$HOURS" -H "X-Admin-Key: $ADMIN_KEY")

# Try to pretty-print token if JSON
echo "$resp" | python3 - <<'PY'
import sys, json
try:
    r = json.load(sys.stdin)
    if isinstance(r, dict) and 'token' in r:
        print('Token:', r['token'])
        print('Expires (hours):', r.get('expires_in_hours'))
        print('ID:', r.get('id'))
    else:
        print(json.dumps(r, indent=2))
except Exception:
    print(sys.stdin.read())
PY

echo "Keep the token secret; it will expire and will not be shown again."
