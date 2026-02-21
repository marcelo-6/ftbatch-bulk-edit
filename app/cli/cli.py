"""
Command-line interface for the Batch Bulk Editor.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from cli.ui import CLIRuntimeUI
from core.exporter import ExcelExporter
from core.importer import ExcelImporter
from core.parser import XMLParser
from core.writer import XMLWriter
from utils.errors import ValidationError
from utils.logging_cfg import configure_logging

logger = logging.getLogger(__name__)
console = Console(stderr=True)


@dataclass(slots=True)
class CLIState:
    debug: bool
    progress: bool | None


app = typer.Typer(
    name="batch_bulk_editor",
    help="Bulk edit FactoryTalk Batch recipes by round-tripping XML and Excel.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)


def _project_version() -> str:
    try:
        return metadata.version("ftbatch-bulk-edit")
    except metadata.PackageNotFoundError:
        repo_root = Path(__file__).resolve().parents[2]
        version_script = repo_root / "scripts" / "versioning.py"
        if version_script.exists():
            try:
                completed = subprocess.run(
                    [sys.executable, str(version_script), "--mode", "current"],
                    cwd=str(repo_root),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                resolved = completed.stdout.strip()
                if resolved:
                    return resolved
            except (OSError, subprocess.CalledProcessError):
                pass

        pyproject_path = repo_root / "pyproject.toml"
        if pyproject_path.exists():
            project = tomllib.loads(pyproject_path.read_text(encoding="utf-8")).get(
                "project", {}
            )
            return str(project.get("version", "unknown"))
    return "unknown"


def _version_callback(value: bool) -> None:
    if not value:
        return
    console.print(
        f"[bold cyan]ftbatch-bulk-edit[/bold cyan] [green]{_project_version()}[/green]"
    )
    raise typer.Exit()


def _state(ctx: typer.Context) -> CLIState:
    if isinstance(ctx.obj, CLIState):
        return ctx.obj
    return CLIState(debug=False, progress=None)


def _progress_enabled(progress: bool | None) -> bool:
    if progress is None:
        return console.is_terminal and sys.stderr.isatty()
    return progress


def _validate_input_file(path: Path, option_name: str) -> None:
    if not path.exists():
        raise typer.BadParameter(
            f"File not found: {path}",
            param_hint=option_name,
        )
    if not path.is_file():
        raise typer.BadParameter(
            f"Expected a file path: {path}",
            param_hint=option_name,
        )


@app.callback()
def common_options(
    ctx: typer.Context,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging and write details to `batch_bulk_editor.log`.",
            rich_help_panel="Global Options",
        ),
    ] = False,
    progress: Annotated[
        bool | None,
        typer.Option(
            "--progress/--no-progress",
            help="Show/hide progress bars. Default: auto (enabled on interactive terminals).",
            rich_help_panel="Global Options",
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
            rich_help_panel="Global Options",
        ),
    ] = False,
) -> None:
    """
    Global CLI options.
    """
    _ = version
    configure_logging(debug, console=console)
    ctx.obj = CLIState(debug=debug, progress=progress)


@app.command(
    "xml2excel",
    help="Export a parent XML recipe (and child references) into one Excel workbook.",
    rich_help_panel="Commands",
)
def xml2excel_command(
    ctx: typer.Context,
    xml: Annotated[
        Path,
        typer.Option(
            "--xml",
            help="Parent recipe XML file (.pxml/.uxml/.oxml).",
            resolve_path=True,
            rich_help_panel="Command Options",
        ),
    ],
    excel: Annotated[
        Path,
        typer.Option(
            "--excel",
            help="Output Excel path (.xlsx).",
            resolve_path=True,
            rich_help_panel="Command Options",
        ),
    ],
) -> None:
    _validate_input_file(xml, "--xml")
    state = _state(ctx)
    show_progress = _progress_enabled(state.progress)

    try:
        parser = XMLParser()
        exporter = ExcelExporter()
        with CLIRuntimeUI(console=console, enable_progress=show_progress) as ui:
            trees = parser.parse(str(xml), progress_cb=ui.on_parse_progress)
            ui.ensure_task("export", "Writing Excel workbook", total=1)
            exporter.export(trees, str(excel))
            ui.complete_task("export", description="Wrote Excel workbook (1/1)")
            ui.success(f"Excel written to: {excel}")
    except ValidationError as exc:
        console.print(f"[bold red]Validation error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        logger.exception("Unexpected error")
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command(
    "excel2xml",
    help="Import an edited Excel workbook and write updated XML files.",
    rich_help_panel="Commands",
)
def excel2xml_command(
    ctx: typer.Context,
    xml: Annotated[
        Path,
        typer.Option(
            "--xml",
            help="Parent recipe XML file (.pxml/.uxml/.oxml).",
            resolve_path=True,
            rich_help_panel="Command Options",
        ),
    ],
    excel: Annotated[
        Path,
        typer.Option(
            "--excel",
            help="Edited Excel path (.xlsx).",
            resolve_path=True,
            rich_help_panel="Command Options",
        ),
    ],
) -> None:
    _validate_input_file(xml, "--xml")
    _validate_input_file(excel, "--excel")
    state = _state(ctx)
    show_progress = _progress_enabled(state.progress)

    try:
        parser = XMLParser()
        importer = ExcelImporter()
        writer = XMLWriter()
        with CLIRuntimeUI(console=console, enable_progress=show_progress) as ui:
            trees = parser.parse(str(xml), progress_cb=ui.on_parse_progress)
            stats = importer.import_changes(
                str(excel),
                trees,
                progress_cb=ui.on_import_progress,
            )
            output_dir = writer.write(
                trees,
                progress_cb=ui.on_write_progress,
            )
            ui.success(
                f"Import summary: created={stats['created']}, updated={stats['updated']}, deleted={stats['deleted']}"
            )
            ui.success(f"XML written to: {output_dir}")
    except ValidationError as exc:
        console.print(f"[bold red]Validation error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        logger.exception("Unexpected error")
        console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


def main() -> None:
    app()


if __name__ == "__main__":
    main()
