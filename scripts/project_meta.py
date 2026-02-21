#!/usr/bin/env python3
"""Read project metadata from pyproject.toml."""

from __future__ import annotations

import argparse
from pathlib import Path

from versioning import load_project_metadata, resolve_current_version, resolve_next_version


def main() -> int:
    parser = argparse.ArgumentParser(description="Read metadata from pyproject.toml")
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml",
    )
    parser.add_argument(
        "--field",
        choices=["name", "version", "description"],
        help="Print only one field value",
    )
    parser.add_argument(
        "--version-mode",
        choices=["current", "next"],
        default="current",
        help="Version resolution mode when reading the version field",
    )
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)
    metadata = load_project_metadata(pyproject_path)
    version = (
        resolve_next_version(pyproject_path)
        if args.version_mode == "next"
        else resolve_current_version(pyproject_path)
    )

    if args.field:
        if args.field == "version":
            print(version)
            return 0
        value = metadata.get(args.field, "")
        print(value)
        return 0

    print(f"Name       : {metadata.get('name', '')}")
    print(f"Version    : {version}")
    print(f"Description: {metadata.get('description', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
