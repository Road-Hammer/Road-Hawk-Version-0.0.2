#!/usr/bin/env python3
"""Sync package version from pyproject.toml into web metadata."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
WEB_PACKAGE = ROOT / "web" / "package.json"
WEB_BRANDING = ROOT / "web" / "lib" / "branding.ts"


def read_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("Could not find version in pyproject.toml")
    return match.group(1)


def sync_package_json(version: str) -> None:
    text = WEB_PACKAGE.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'("version"\s*:\s*")[^"]+(")',
        rf'\g<1>{version}\2',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("Could not update version in web/package.json")
    WEB_PACKAGE.write_text(updated, encoding="utf-8", newline="\n")


def sync_branding_ts(version: str) -> None:
    text = WEB_BRANDING.read_text(encoding="utf-8")
    if "export const PACKAGE_VERSION" in text:
        updated, count = re.subn(
            r'export const PACKAGE_VERSION = "[^"]+";',
            f'export const PACKAGE_VERSION = "{version}";',
            text,
            count=1,
        )
        if count != 1:
            raise SystemExit("Could not update PACKAGE_VERSION in web/lib/branding.ts")
    else:
        marker = 'export const PRODUCT = "Road Hawk";\n'
        if marker not in text:
            raise SystemExit("Could not locate PRODUCT export in web/lib/branding.ts")
        updated = text.replace(
            marker,
            f'{marker}export const PACKAGE_VERSION = "{version}";\n',
            1,
        )
    WEB_BRANDING.write_text(updated, encoding="utf-8", newline="\n")


def main() -> int:
    version = read_pyproject_version()
    sync_package_json(version)
    sync_branding_ts(version)
    print(f"Synced Road Hawk version {version} to web metadata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())