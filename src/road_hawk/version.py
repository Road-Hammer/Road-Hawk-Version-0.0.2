"""Package version resolution for Road Hawk."""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def package_version() -> str:
    try:
        from importlib.metadata import version

        return version("road-hawk")
    except Exception:
        pass

    pyproject = _repo_root() / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if match:
            return match.group(1)

    return "0.0.0-dev"


@lru_cache(maxsize=1)
def git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    revision = result.stdout.strip()
    return revision or None


def version_info() -> dict[str, str | None]:
    return {
        "version": package_version(),
        "git_revision": git_revision(),
    }