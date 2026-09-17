#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <instance-name> <profile-id>" >&2
    exit 2
fi

NAME="$1"
PROFILE="$2"

source /opt/fleet/env.sh

API="${FLEET_API:-http://localhost:8000}"

echo "[provision] ${NAME} profile=${PROFILE}"
curl -fsS -X POST "${API}/instances" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"${NAME}\",\"profile\":\"${PROFILE}\"}"

echo "[verify] ${NAME}"
RESULT=$(curl -fsS "${API}/instances/${NAME}/attestation")
echo "${RESULT}"

if echo "${RESULT}" | grep -q '"passed":true'; then
    echo "PASS ${NAME}"
    exit 0
fi

echo "FAIL ${NAME}"
curl -fsS -X DELETE "${API}/instances/${NAME}" || true
exit 1
