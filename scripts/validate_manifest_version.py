"""Validate manifest version and release tag alignment."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MANIFEST_PATH = Path("custom_components/p2000/manifest.json")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[abrc]\d+)?$")


def main() -> int:
    """Validate the integration manifest version."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    version = manifest.get("version")

    if not isinstance(version, str) or not VERSION_PATTERN.match(version):
        print(f"Invalid manifest version: {version!r}")
        return 1

    github_ref = os.environ.get("GITHUB_REF", "")
    if github_ref.startswith("refs/tags/"):
        tag = github_ref.rsplit("/", 1)[-1].removeprefix("v")
        if tag != version:
            print(
                f"Tag version {tag!r} does not match manifest version {version!r}"
            )
            return 1

    print(f"Manifest version {version} is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
