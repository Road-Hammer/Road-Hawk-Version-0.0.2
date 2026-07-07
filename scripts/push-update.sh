#!/usr/bin/env sh
# Maintainer workflow: sync versions, test, commit, and push Road Hawk updates.
set -eu

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"commit message\" [--branch Road-Hawk] [--skip-tests] [--skip-web-build] [--dry-run]" >&2
  exit 1
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MESSAGE="$1"
shift

BRANCH="${ROAD_HAWK_GIT_BRANCH:-Road-Hawk}"
SKIP_TESTS=0
SKIP_WEB_BUILD=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --branch)
      shift
      BRANCH="${1:?branch name required}"
      ;;
    --skip-tests) SKIP_TESTS=1 ;;
    --skip-web-build) SKIP_WEB_BUILD=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

cd "$REPO"
echo "Road Hawk push-update"
echo "Target branch: $BRANCH"

echo "Syncing version metadata..."
python3 scripts/sync-version.py

if [ "$SKIP_TESTS" -eq 0 ]; then
  echo "Running pytest..."
  python3 -m pytest -q
fi

if [ "$SKIP_WEB_BUILD" -eq 0 ]; then
  echo "Building web dashboard..."
  cd web
  npm ci
  npm run build
  cd "$REPO"
fi

if [ -z "$(git status --porcelain)" ]; then
  echo "No changes to commit."
else
  echo "Staging changes..."
  if [ "$DRY_RUN" -eq 1 ]; then
    git status --short
    echo "Dry run: would commit with message: $MESSAGE"
  else
    git add -A
    git commit -m "$MESSAGE"
  fi
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry run: would push to origin/$BRANCH"
  exit 0
fi

echo "Pushing to origin/$BRANCH..."
git push origin "HEAD:$BRANCH"

python3 -c "from road_hawk.version import version_info; print('Push complete:', version_info())"
echo "GitHub Actions CI will run on the pushed commit."