set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

python_version := "3.14"
uv_cache_dir := "/tmp/uv-cache"
coverage_threshold := "70"
pyproject_file := "pyproject.toml"
entrypoint := "app/main.py"
version_info_file := "build/version_info.txt"
version_script := "scripts/versioning.py"
project_meta_script := "scripts/project_meta.py"
cliff_config := "cliff.toml"
semver_tag_pattern := "^v?[0-9]+\\.[0-9]+\\.[0-9]+$"

default: help

# List available recipes.
help:
    @just --list

# Ensure uv is installed.
check-uv:
    @command -v uv >/dev/null 2>&1 || { echo "uv is required. Install: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }

# Sync project dependencies for Python 3.14.
sync: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv sync --python {{python_version}}

# Alias used by teams that prefer install terminology.
install: sync

# Print project metadata from pyproject.toml using current/tag-derived version.
meta: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --version-mode current

# Print project metadata using the bumped (next) version.
meta-next: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --version-mode next

# Generate version metadata file used by PyInstaller on Windows.
version-info output=version_info_file: check-uv
    mkdir -p "$(dirname {{output}})"
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/generate_version_info.py --pyproject {{pyproject_file}} --output {{output}} --version-mode current

# Generate version metadata file using the bumped (next) version.
version-info-next output=version_info_file: check-uv
    mkdir -p "$(dirname {{output}})"
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/generate_version_info.py --pyproject {{pyproject_file}} --output {{output}} --version-mode next

# Backward-compatible alias.
version: version-info

# Build a one-file executable with PyInstaller.
# Intended to run on Windows for production artifacts.
build: check-uv
    just version-info
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with pyinstaller pyinstaller \
      --onefile \
      --name "$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --field name).exe" \
      {{entrypoint}} \
      --version-file {{version_info_file}} \
      --distpath dist \
      --workpath build/pyinstaller \
      --specpath build

# Build a one-file executable stamped with the bumped (next) version.
build-next: check-uv
    just version-info-next
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with pyinstaller pyinstaller \
      --onefile \
      --name "$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{project_meta_script}} --pyproject {{pyproject_file}} --field name).exe" \
      {{entrypoint}} \
      --version-file {{version_info_file}} \
      --distpath dist \
      --workpath build/pyinstaller \
      --specpath build

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

# Local quality gate.
ci: lint typecheck test

# Common developer flow.
all: sync meta test build

# Ensure git-cliff is installed.
check-git-cliff:
    @command -v git-cliff >/dev/null 2>&1 || { echo "git-cliff is required. Install: https://git-cliff.org/docs/installation/"; exit 1; }

# Remove local build and cache artifacts.
clean:
    rm -rf build dist __pycache__ .pytest_cache .mypy_cache .ruff_cache
    rm -f *.spec {{version_info_file}} batch_bulk_editor.log

doctor:
    @echo "Checking local tools..."
    @command -v just >/dev/null 2>&1 && echo "  just: ok" || echo "  just: missing"
    @command -v git >/dev/null 2>&1 && echo "  git: ok" || echo "  git: missing"
    @command -v cargo >/dev/null 2>&1 && echo "  cargo: ok" || echo "  cargo: missing"
    @command -v git-cliff >/dev/null 2>&1 && echo "  git-cliff: ok" || echo "  git-cliff: missing"
    @command -v pre-commit >/dev/null 2>&1 && echo "  pre-commit: ok" || echo "  pre-commit: missing"
    @command -v yamllint >/dev/null 2>&1 && echo "  yamllint: ok" || echo "  yamllint: missing"

# Generate the full changelog from tags into CHANGELOG.md.
changelog: check-git-cliff
    git-cliff --config {{cliff_config}} --tag-pattern '{{semver_tag_pattern}}' --output CHANGELOG.md

# Preview changelog content for unreleased commits.
changelog-unreleased: check-git-cliff
    git-cliff --config {{cliff_config}} --unreleased --tag-pattern '{{semver_tag_pattern}}'

# Print the next semantic version from unreleased commits.
bump-dry-run: check-git-cliff
    git-cliff --config {{cliff_config}} --bumped-version --unreleased --tag-pattern '{{semver_tag_pattern}}'

# Preview the unreleased changelog section rendered with the next semantic version.
changelog-dry-run: check-git-cliff
    next="$(git-cliff --config {{cliff_config}} --bumped-version --unreleased --tag-pattern '{{semver_tag_pattern}}')"; git-cliff --config {{cliff_config}} --unreleased --tag "${next}" --tag-pattern '{{semver_tag_pattern}}'

# Show a local release simulation: current version, next version, and release notes preview.
release-dry-run: check-uv check-git-cliff
    current="$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{version_script}} --pyproject {{pyproject_file}} --mode current)"; \
    next="$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python {{version_script}} --pyproject {{pyproject_file}} --mode next --tag-pattern '{{semver_tag_pattern}}')"; \
    echo "Current version: ${current}"; \
    echo "Next version:    ${next}"; \
    echo; \
    echo "Release notes preview:"; \
    git-cliff --config {{cliff_config}} --unreleased --tag "${next}" --tag-pattern '{{semver_tag_pattern}}'

# Backward-compatible alias.
bump: bump-dry-run
