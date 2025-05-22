PYPROJECT     = pyproject.toml
VERSION_FILE  = version_info.txt
SRC           = app/main.py

# # Get the project name from pyproject.toml
PKG_NAME := $(shell uv run python3 -c "import toml; print(toml.load('$(PYPROJECT)')['project']['name'])")
PKG_VERSION := $(shell uv run python3 -c "import toml; print(toml.load('$(PYPROJECT)')['project']['version'])")
# Name the bundle
BUILD_DIR   := bundle-$(PKG_NAME)
ZIPFILE     := $(PKG_NAME)-$(PKG_VERSION)-source.zip

.PHONY: help all check-uv install meta version build clean test

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo "  help               Show this help message"
	@echo "  test               Runs pytests to confirm changes to code have basic regression testing"
	@echo "  all                Runs all in the following order check-uv install meta version build clean"
	@echo "  check-uv           Ensure 'uv' is installed (via pip if needed)"
	@echo "  install            Initialize uv and install project dependencies"
	@echo "  meta               Print name/version/description from pyproject.toml"
	@echo "  version            Generate version_info.txt from pyproject.toml"
	@echo "  build              Create a .zip of source + version_info.txt for Windows, you then need to run pyinstaller from a windows machine"
	@echo "  clean              Remove build artifacts (build/, dist/, *.spec, version_info.txt)"
	@echo ""
	@echo "Examples:"
	@echo "  make all           # runs all in the following order check-uv install meta version build clean"
	@echo "  make install       # set up uv venv + deps"
	@echo "  make version       # generate version_info.txt"
	@echo "  make clean         # wipe all artifacts"

test:
	@echo "Starting Pytests"
	pytest --disable-warnings -q

.ONESHELL:

.PHONY: all check-uv install meta version build clean
# version build clean

# Default target: run everything
all: check-uv install meta version build clean

# 1) Ensure 'uv' is installed
check-uv:
	@echo "🔍 [1/6] Checking if uv is installed..."
	@command -v uv >/dev/null 2>&1 || (echo "⚠️ uv not found; install it via installing..." && curl -LsSf https://astral.sh/uv/install.sh | sh)

# 2) Initialize & install Python deps via uv
install: check-uv
	@echo "🔧 [2/6] creating virtual enviroment and activating it..."
	uv venv --python 3.12
	. .venv/bin/activate
	uv sync

# 3) Print project metadata for verification
meta:
	@echo "🔍 [3/6] Project metadata from $(PYPROJECT):"
	uv run python3 - << 'EOF'
	import toml
	m = toml.load("$(PYPROJECT)")["project"]
	print("  Name       :", m["name"])
	print("  Version    :", m["version"])
	print("  Description:", m.get("description","<none>"))
	EOF

# 4) Generate version_info.txt for embedding into the EXE
version: install
	@echo "📄 [4/6] Generating $(VERSION_FILE)…"
	uv run python3 - << 'EOF'
	import toml
	from pathlib import Path
	# Load TOML
	meta = toml.load("$(PYPROJECT)")["project"]
	name = meta["name"]
	ver = meta["version"]
	maj, mino, pat = (ver.split(".") + ["0"])[:3]
	# build 0 for full 4-tuple
	filevers = f"({maj}, {mino}, {pat}, 0)"
	prodvers = filevers

	description = meta.get("description", "").replace('"','\\"')
	exe_name = f"{name}.exe"
	translation = "[1033, 1200]"

	# Now write out the exact VSVersionInfo block
	content = f"""# UTF-8
	#
	# For more details about fixed file info 'ffi' see:
	# http://msdn.microsoft.com/en-us/library/ms646997.aspx
	VSVersionInfo(
	ffi=FixedFileInfo(
		# filevers and prodvers should be a tuple with four items
		filevers={filevers},
		prodvers={prodvers},
		# valid fields bitmask
		mask=0x3f,
		# Boolean file attributes
		flags=0x0,
		# OS=0x4 means Windows NT
		OS=0x4,
		# 0x1 = application
		fileType=0x1,
		# subtype=0x0 for apps
		subtype=0x0,
		# date=(major,minor) – typically zeroed
		date=(0, 0)
	),
	kids=[
		StringFileInfo(
		[
			StringTable(
			u'040904B0',
			[
				StringStruct(u'FileDescription',    u'{description}'),
				StringStruct(u'FileVersion',        u'{ver}'),
				StringStruct(u'InternalName',       u'{exe_name}'),
				StringStruct(u'OriginalFilename',   u'{exe_name}'),
				StringStruct(u'ProductName',        u'{name}'),
				StringStruct(u'ProductVersion',     u'{ver}'),
				StringStruct(u'Copyright',          u'MIT')
			]
			)
		]
		),
		VarFileInfo([VarStruct(u'Translation', {translation})])
	]
	)
	"""
	Path("$(VERSION_FILE)").write_text(content, encoding="utf-8")
	print("✔ Generated $(VERSION_FILE)")
	EOF

# 5) Build the standalone EXE with PyInstaller
build: version
	@echo "📦 [5/6] Bundling source for Windows build…"
	@echo "         cleaning out old bundle directory"
	rm -rf $(BUILD_DIR)

	@echo "         gathering just the files we need"
	echo "Make sure you have python 3.12+ and pyinstaller, then run this on windows:\npython -m PyInstaller --onefile --name $(PKG_NAME).exe $(SRC) --version-file=$(VERSION_FILE)" > readme.txt
	mkdir -p $(BUILD_DIR)

	cp -r app $(VERSION_FILE) $(BUILD_DIR)/
	mv readme.txt $(BUILD_DIR)/
	@echo "         zip it up"
	@echo "         you might need sudo apt-get install zip if not already installed"
	zip -r $(ZIPFILE) $(BUILD_DIR)
	@echo "         clean up"
	rm -rf $(BUILD_DIR)
	@echo "✔ Source bundled into $(ZIPFILE)"
	@echo
	@echo "🚀 [6/6] On Windows, unzip $(ZIPFILE) then run:"
	@echo "    python -m PyInstaller --onefile --name $(PKG_NAME).exe $(SRC) --version-file=$(VERSION_FILE)"

clean:
	@echo "🧹 Cleaning up…"
	rm -rf build dist __pycache__ *.spec $(VERSION_FILE)
	@echo "✔ Clean complete."