set shell := ["bash", "-eu", "-o", "pipefail", "-c"]
set windows-shell := ["C:\\Program Files\\Git\\bin\\bash.exe", "-eu", "-o", "pipefail", "-c"]

# -----------------------------
# Global config
# -----------------------------
python_version := "3.14"
uv_cache_dir := "/tmp/uv-cache"
coverage_threshold := "70"
pyproject_file := "pyproject.toml"
entrypoint := "app/main.py"

# -----------------------------
# Versioning / metadata
# -----------------------------
version_info_file := "build/version_info.txt"
version_script := "scripts/versioning.py"
project_meta_script := "scripts/project_meta.py"
cliff_config := "cliff.toml"
semver_tag_pattern := "^v?[0-9]+\\.[0-9]+\\.[0-9]+$"

# -----------------------------
# Packaging (TestPyPI)
# -----------------------------
dist_dir := "dist"
smoke_test_script := "tests/smoke_test.py"
testpypi_publish_url := "https://test.pypi.org/legacy/"
testpypi_check_url := "https://test.pypi.org/simple/"

# -----------------------------
# Defaults / discovery
# -----------------------------
# List available recipes.
default: help

# List available recipes.
help:
    @just --list

# -----------------------------
# Tool checks (internal)
# -----------------------------
[private]
check-uv:
    @command -v uv >/dev/null 2>&1 || { echo "uv is required. Install: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }

[private]
check-git-cliff:
    @command -v git-cliff >/dev/null 2>&1 || { echo "git-cliff is required. Install: https://git-cliff.org/docs/installation/"; exit 1; }

# Check if all needed dev tools are available
doctor:
    @echo "Checking local tools..."
    @command -v just >/dev/null 2>&1 && echo "  just: ok" || echo "  just: missing"
    @command -v git >/dev/null 2>&1 && echo "  git: ok" || echo "  git: missing"
    @command -v cargo >/dev/null 2>&1 && echo "  cargo: ok" || echo "  cargo: missing"
    @command -v git-cliff >/dev/null 2>&1 && echo "  git-cliff: ok" || echo "  git-cliff: missing"
    @command -v pre-commit >/dev/null 2>&1 && echo "  pre-commit: ok" || echo "  pre-commit: missing"
    @command -v yamllint >/dev/null 2>&1 && echo "  yamllint: ok" || echo "  yamllint: missing"

# -----------------------------
# Python / deps (uv)
# -----------------------------
[private]
python: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv python install {{python_version}}

# Sync project dependencies for Python 3.14.
sync: check-uv python
    UV_CACHE_DIR={{uv_cache_dir}} uv sync --python {{python_version}}

# Sync all dependency groups (used by CI and packaging/build workflows).
sync-all: check-uv python
    UV_CACHE_DIR={{uv_cache_dir}} uv sync --python {{python_version}} --all-groups

# Alias to uv sync to install all project dependencies
install: sync

# -----------------------------
# Project metadata / version-info
# -----------------------------

# Print project metadata from pyproject.toml using current/tag-derived version.
meta: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --version-mode current

# Print project metadata using the bumped (next) version.
meta-next: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --version-mode next

# Generate version metadata file used by PyInstaller on Windows.
[private]
version-info output=version_info_file: check-uv
    mkdir -p "$(dirname {{output}})"
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/generate_version_info.py --pyproject {{pyproject_file}} --output {{output}} --version-mode current

# Generate version metadata file using the bumped (next) version.
[private]
version-info-next output=version_info_file: check-uv
    mkdir -p "$(dirname {{output}})"
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/generate_version_info.py --pyproject {{pyproject_file}} --output {{output}} --version-mode next

# -----------------------------
# Quality: test / lint / format / typecheck / CI parity
# -----------------------------

# Run the test suite.
test: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run pytest --disable-warnings -q

# Run tests with coverage and enforce a minimum threshold.
cov threshold=coverage_threshold: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with coverage coverage run -m pytest --disable-warnings -q
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with coverage coverage report --fail-under {{threshold}}

# Run static type checks.
typecheck: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run mypy app

# Format source files with Ruff.
fmt: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with ruff ruff format app tests scripts

# Lint source files with Ruff.
lint: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with ruff ruff check app tests scripts

# CI parity target used by GitHub Actions (lint + tests + coverage threshold).
ci-check threshold=coverage_threshold: sync-all
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync ruff check app tests scripts
    just cov {{threshold}}

# Common developer flow.
all: sync meta test build

# -----------------------------
# Build artifact (PyInstaller)
# -----------------------------

# Build a one-file executable with PyInstaller (needs windows).
build: check-uv
    just version-info
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with pyinstaller pyinstaller \
      --onefile \
      --name "$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --field name).exe" \
      {{entrypoint}} \
      --version-file version_info.txt \
      --distpath dist \
      --workpath build/pyinstaller \
      --specpath build

# -----------------------------
# Cleanup
# -----------------------------

# Remove local build and cache artifacts.
clean:
    @echo "Removing local build and cache artifacts...."
    rm -rf build dist __pycache__ .pytest_cache .mypy_cache .ruff_cache
    rm -f *.spec {{version_info_file}} batch_bulk_editor.log

# -----------------------------
# Changelog / release helpers
# -----------------------------

# Generate the full changelog from tags into CHANGELOG.md.
changelog: check-git-cliff
    git-cliff --config {{cliff_config}} --tag-pattern '{{semver_tag_pattern}}' --output CHANGELOG.md

# Preview the unreleased changelog section rendered with the next semantic version.
changelog-dry-run: check-git-cliff
    next="$(git-cliff --config {{cliff_config}} --bumped-version --unreleased --tag-pattern '{{semver_tag_pattern}}')"; git-cliff --config {{cliff_config}} --unreleased --tag "${next}" --tag-pattern '{{semver_tag_pattern}}'

# Print the next semantic version from unreleased commits.
bump-dry-run: check-git-cliff
    git-cliff --config {{cliff_config}} --bumped-version --unreleased --tag-pattern '{{semver_tag_pattern}}'

# Show a local release simulation: current version, next version, and release notes preview.
release-dry-run: check-uv check-git-cliff
    current="$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{version_script}} --pyproject {{pyproject_file}} --mode current)"; \
    next="$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{version_script}} --pyproject {{pyproject_file}} --mode next --tag-pattern '{{semver_tag_pattern}}')"; \
    echo "Current version: ${current}"; \
    echo "Next version:    ${next}"; \
    echo; \
    echo "Release notes preview:"; \
    git-cliff --config {{cliff_config}} --unreleased --tag "${next}" --tag-pattern '{{semver_tag_pattern}}'

# -----------------------------
# TestPyPI: local pipeline parity
# -----------------------------

# Delete dist directory
[private]
dist-clean:
    rm -rf {{dist_dir}}/

# Check if pypi token is in env vars
[private]
check-testpypi-token:
    @token="${UV_PUBLISH_TOKEN:-${TEST_PYPI_API_TOKEN:-}}"; \
    if [[ -z "$token" ]]; then \
      echo "Missing TestPyPI token. Set UV_PUBLISH_TOKEN (preferred) or TEST_PYPI_API_TOKEN."; \
      exit 1; \
    fi

# Build + validate + smoke-test like the GitHub workflow.
package version="": check-uv python
    just dist-clean
    semver_tag="$(git tag --points-at HEAD | grep -E -m1 '{{semver_tag_pattern}}' || true)"; \
    if [[ -n "$semver_tag" ]]; then \
      echo "On release tag: $semver_tag (using SCM version)"; \
    else \
      if [[ -n "{{version}}" ]]; then \
        export PDM_BUILD_SCM_VERSION="{{version}}"; \
      else \
        suffix="${GITHUB_RUN_ID:-$(date +%Y%m%d%H%M%S)}${GITHUB_RUN_ATTEMPT:-0}${BASHPID:-$$}"; \
        export PDM_BUILD_SCM_VERSION="0.0.0.dev${suffix}"; \
      fi; \
      echo "Using PDM_BUILD_SCM_VERSION=${PDM_BUILD_SCM_VERSION}"; \
    fi; \
    UV_CACHE_DIR={{uv_cache_dir}} uv build; \
    UV_CACHE_DIR={{uv_cache_dir}} uvx twine check --strict dist/*; \
    UV_CACHE_DIR={{uv_cache_dir}} uv run --isolated --no-project --with dist/*.whl {{smoke_test_script}}; \
    UV_CACHE_DIR={{uv_cache_dir}} uv run --isolated --no-project --with dist/*.tar.gz {{smoke_test_script}}

# Validate auth/connectivity without uploading.
publish-testpypi-dry version="": check-testpypi-token
    just package "{{version}}"
    token="${UV_PUBLISH_TOKEN:-${TEST_PYPI_API_TOKEN:-}}"; \
    UV_PUBLISH_TOKEN="$token" UV_CACHE_DIR={{uv_cache_dir}} uv publish \
      --dry-run \
      --publish-url {{testpypi_publish_url}} \
      --check-url {{testpypi_check_url}}

# Actually upload to TestPyPI.
publish-testpypi version="": check-testpypi-token
    just package "{{version}}"
    token="${UV_PUBLISH_TOKEN:-${TEST_PYPI_API_TOKEN:-}}"; \
    UV_PUBLISH_TOKEN="$token" UV_CACHE_DIR={{uv_cache_dir}} uv publish \
      --publish-url {{testpypi_publish_url}} \
#   --check-url {{testpypi_check_url}}

# Install from TestPyPI (falls back to PyPI for dependencies) and run smoke test.
verify-install-testpypi:
    python -m pip install \
      --upgrade \
      --force-reinstall \
      --no-cache-dir \
      --index-url {{testpypi_check_url}} \
      --extra-index-url https://pypi.org/simple/ \
      ftbatch-bulk-edit
    python {{smoke_test_script}}