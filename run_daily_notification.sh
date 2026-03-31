#!/bin/zsh

set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

: "${LATITUDE:?LATITUDE is required}"
: "${LONGITUDE:?LONGITUDE is required}"

args=(
  --latitude "$LATITUDE"
  --longitude "$LONGITUDE"
  --notify
)

if [[ -n "${NTFY_TOPIC:-}" ]]; then
  args+=(--ntfy-topic "$NTFY_TOPIC")
fi

if [[ -n "${NTFY_SERVER:-}" ]]; then
  args+=(--ntfy-server "$NTFY_SERVER")
fi

python3 "$SCRIPT_DIR/clothing_app.py" "${args[@]}"
