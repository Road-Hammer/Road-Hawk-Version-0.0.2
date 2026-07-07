#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ "$#" -lt 1 ]; then
  echo "Usage: run-with-node.sh [dev|build|start|lint]"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Install from https://nodejs.org"
  exit 1
fi

exec node "./node_modules/next/dist/bin/next" "$@"