# 1) Create a clean temp workspace
tmpdir="$(mktemp -d)"
cd "$tmpdir"

# 2) Ensure the Python you want exists (optional if already installed)
uv python install 3.14

# 3) Create an isolated virtual environment
uv venv -p 3.14

# 4) Install package from TestPyPI, but allow deps from PyPI
VIRTUAL_ENV="$PWD/.venv" uv pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  ftbatch-bulk-edit

# 5) Confirm version + that the console script runs
"$PWD/.venv/bin/python" -c "import importlib.metadata as m; print(m.version('ftbatch-bulk-edit'))"
"$PWD/.venv/bin/ftbatch-bulk-edit" --help

# 6) Cleanup
cd /
rm -rf "$tmpdir"