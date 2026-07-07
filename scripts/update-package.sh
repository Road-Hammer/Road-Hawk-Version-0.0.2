#!/usr/bin/env sh
# Pull latest Road Hawk code and refresh local Python + web dependencies.
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BRANCH="${ROAD_HAWK_GIT_BRANCH:-Road-Hawk}"
SKIP_PULL=0
SKIP_TESTS=0
INCLUDE_OCR=0
PRODUCTION_WEB=0

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-pull) SKIP_PULL=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    --include-ocr) INCLUDE_OCR=1 ;;
    --production-web) PRODUCTION_WEB=1 ;;
    --branch)
      shift
      BRANCH="${1:?branch name required}"
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

cd "$REPO"
echo "Road Hawk package update"
echo "Repository: $REPO"

if [ "$SKIP_PULL" -eq 0 ]; then
  echo "Fetching and pulling origin/$BRANCH..."
  git fetch origin
  git pull origin "$BRANCH"
fi

echo "Syncing version metadata..."
python3 scripts/sync-version.py

EXTRAS="[dev]"
if [ "$INCLUDE_OCR" -eq 1 ]; then
  EXTRAS="[dev,ocr]"
fi

echo "Reinstalling Python package $EXTRAS..."
python3 -m pip install -e ".$EXTRAS"

echo "Refreshing web dependencies..."
cd web
if [ "$PRODUCTION_WEB" -eq 1 ]; then
  npm ci
  npm run build
else
  npm install
fi
cd "$REPO"

if [ "$SKIP_TESTS" -eq 0 ]; then
  echo "Running pytest..."
  python3 -m pytest -q
fi

python3 -c "from road_hawk.version import version_info; print('Update complete:', version_info())"
echo "Restart services if they are already running:"
echo "  API:  ./scripts/start-api.sh"
echo "  Web:  ./scripts/start-web.sh"
if [ "$PRODUCTION_WEB" -eq 1 ]; then
  echo "  Prod: cd web && npm run start"
fi