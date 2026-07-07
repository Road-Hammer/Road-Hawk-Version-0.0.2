#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../web"
if command -v npm >/dev/null 2>&1; then
  npm run dev
else
  sh bin/run-with-node.sh dev
fi