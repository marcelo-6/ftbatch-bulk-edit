set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

python_version := "3.14"
uv_cache_dir := "/tmp/uv-cache"
coverage_threshold := "70"
pyproject_file := "pyproject.toml"
entrypoint := "app/main.py"
version_info_file := "build/version_info.txt"

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

# Print project metadata from pyproject.toml.
meta: check-uv
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/project_meta.py --pyproject {{pyproject_file}}

# Generate version metadata file used by PyInstaller on Windows.
version-info output=version_info_file: check-uv
    mkdir -p "$(dirname {{output}})"
    UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/generate_version_info.py --pyproject {{pyproject_file}} --output {{output}}

# Backward-compatible alias.
version: version-info

# Build a one-file executable with PyInstaller.
# Intended to run on Windows for production artifacts.
build: version-info
    name="$$(UV_CACHE_DIR={{uv_cache_dir}} uv run --no-sync python scripts/project_meta.py --pyproject {{pyproject_file}} --field name)"
    UV_CACHE_DIR={{uv_cache_dir}} uv run --with pyinstaller pyinstaller \
      --onefile \
      --name "$${name}.exe" \
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

# Remove local build and cache artifacts.
clean:
    rm -rf build dist __pycache__ .pytest_cache .mypy_cache .ruff_cache
    rm -f *.spec version_info.txt batch_bulk_editor.log

doctor:
	@echo "Checking local tools..."
	@command -v just >/dev/null && echo "  just: ok" || echo "  just: missing"
	@command -v git >/dev/null && echo "  git: ok" || echo "  git: missing"
	@command -v cargo >/dev/null && echo "  cargo: ok" || echo "  cargo: missing"
	@command -v git-cliff >/dev/null && echo "  git-cliff: ok" || echo "  git-cliff: missing (run: just install-git-cliff)"
	@command -v yamllint -v >/dev/null && echo "  yamllint: ok" || echo "  yamllint: missing"
	@command -v pre-commit -V >/dev/null && echo "  pre-commit: ok" || echo "  pre-commit: missing"
	@command -v pre-commit install >/dev/null && echo "    all pre-commits: ok" || echo "  pre-commits: missing"

changelog:
	git cliff -o CHANGELOG.md

changelog-unreleased:
	git cliff --unreleased

bump:
	git cliff --bump --unreleased