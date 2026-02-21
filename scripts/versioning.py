#!/usr/bin/env python3
"""Resolve project versions from git tags and git-cliff bump calculations."""

from __future__ import annotations

import argparse
import importlib.metadata as importlib_metadata
import re
import subprocess
from pathlib import Path
from typing import Any

import tomllib

SEMVER_TAG_RE = re.compile(r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
SEMVER_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
DEFAULT_TAG_PATTERN = r"^v?[0-9]+\.[0-9]+\.[0-9]+$"
FALLBACK_VERSION = "0.0.0"


def load_project_metadata(pyproject_path: Path) -> dict[str, Any]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError(f"Missing [project] table in {pyproject_path}")
    return project


def _run_command(command: list[str], *, cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    output = completed.stdout.strip()
    return output or None


def _normalize_tag(tag: str) -> str | None:
    match = SEMVER_TAG_RE.fullmatch(tag.strip())
    if not match:
        return None
    return f"{int(match.group('major'))}.{int(match.group('minor'))}.{int(match.group('patch'))}"


def _version_tuple(version: str) -> tuple[int, int, int] | None:
    match = SEMVER_RE.fullmatch(version)
    if not match:
        return None
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def latest_semver_tag(repo_root: Path) -> tuple[str, str] | None:
    tags_output = _run_command(["git", "tag", "--list"], cwd=repo_root)
    if not tags_output:
        return None

    best_tag: str | None = None
    best_version: str | None = None
    best_tuple: tuple[int, int, int] | None = None

    for tag in tags_output.splitlines():
        normalized = _normalize_tag(tag)
        if not normalized:
            continue
        version_tuple = _version_tuple(normalized)
        if version_tuple is None:
            continue
        if best_tuple is None or version_tuple > best_tuple:
            best_tag = tag.strip()
            best_version = normalized
            best_tuple = version_tuple

    if best_tag is None or best_version is None:
        return None
    return best_tag, best_version


def _version_from_pyproject(project: dict[str, Any]) -> str | None:
    value = project.get("version")
    if value is None:
        return None
    candidate = str(value).strip()
    return candidate or None


def resolve_current_version(pyproject_path: Path) -> str:
    project = load_project_metadata(pyproject_path)
    repo_root = pyproject_path.resolve().parent

    latest = latest_semver_tag(repo_root)
    if latest is not None:
        return latest[1]

    project_name = str(project.get("name", "")).strip()
    if project_name:
        try:
            installed_version = importlib_metadata.version(project_name).strip()
            if installed_version:
                return installed_version
        except importlib_metadata.PackageNotFoundError:
            pass

    static_version = _version_from_pyproject(project)
    if static_version:
        return static_version

    return FALLBACK_VERSION


def _bump_patch(version: str) -> str:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return "0.1.0"
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    return f"{major}.{minor}.{patch + 1}"


def resolve_next_version(
    pyproject_path: Path,
    *,
    tag_pattern: str = DEFAULT_TAG_PATTERN,
) -> str:
    repo_root = pyproject_path.resolve().parent
    cliff_config = repo_root / "cliff.toml"

    command = ["git-cliff"]
    if cliff_config.exists():
        command.extend(["--config", str(cliff_config)])
    command.extend(
        [
            "--bumped-version",
            "--unreleased",
            "--tag-pattern",
            tag_pattern,
        ]
    )
    bumped = _run_command(command, cwd=repo_root)
    if bumped:
        return bumped

    return _bump_patch(resolve_current_version(pyproject_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve project versions from git metadata")
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml",
    )
    parser.add_argument(
        "--mode",
        default="current",
        choices=["current", "next", "latest-tag"],
        help="Version resolution mode",
    )
    parser.add_argument(
        "--tag-pattern",
        default=DEFAULT_TAG_PATTERN,
        help="Regex pattern used by git-cliff for SemVer tags",
    )
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)
    repo_root = pyproject_path.resolve().parent

    if args.mode == "latest-tag":
        latest = latest_semver_tag(repo_root)
        print(latest[1] if latest else FALLBACK_VERSION)
        return 0

    if args.mode == "next":
        print(resolve_next_version(pyproject_path, tag_pattern=args.tag_pattern))
        return 0

    print(resolve_current_version(pyproject_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
