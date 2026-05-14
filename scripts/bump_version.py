"""Bump version in manifest.json."""

import json
import sys
from pathlib import Path


def bump_version(bump_type: str) -> str:
    """Bump semver version. Returns the new version string."""
    manifest_path = Path("custom_components/elite_climate/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    current = manifest["version"]

    major, minor, patch = map(int, current.split("."))
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"Unknown bump type: {bump_type}", file=sys.stderr)
        sys.exit(1)

    new_version = f"{major}.{minor}.{patch}"

    manifest["version"] = new_version
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(new_version)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <major|minor|patch>", file=sys.stderr)
        sys.exit(1)
    bump_version(sys.argv[1])
