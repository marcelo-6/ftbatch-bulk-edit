"""
Command-line interface for the Batch Bulk Editor.
"""

from __future__ import annotations

import logging
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Annotated, Callable, TypeVar

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from core.exporter import ExcelExporter
from core.importer import ExcelImporter
from core.parser import XMLParser
from core.writer import XMLWriter
from utils.errors import ValidationError
from utils.logging_cfg import configure_logging

logger = logging.getLogger(__name__)
console = Console(stderr=True)

T = TypeVar("T")


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
        pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
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
        return sys.stderr.isatty()
    return progress


def _run_steps(steps: list[tuple[str, Callable[[], T]]], show_progress: bool) -> list[T]:
    results: list[T] = []
    if show_progress:
        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task("[cyan]Starting...[/cyan]", total=len(steps))
            for description, callback in steps:
                progress.update(task_id, description=f"[cyan]{description}[/cyan]")
                results.append(callback())
                progress.advance(task_id)
        return results

    for description, callback in steps:
        console.print(f"[cyan]• {description}[/cyan]")
        results.append(callback())
    return results


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
    configure_logging(debug)
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
        trees: list | None = None

        def parse_step() -> list:
            nonlocal trees
            trees = parser.parse(str(xml))
            return trees

        def export_step() -> None:
            if trees is None:
                raise RuntimeError("XML parse step did not produce trees.")
            exporter.export(trees, str(excel))

        _run_steps(
            [
                ("Parsing XML files", parse_step),
                ("Writing Excel workbook", export_step),
            ],
            show_progress=show_progress,
        )
        console.print(f"[bold green]Excel written to:[/bold green] {excel}")
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

        trees: list | None = None
        stats: dict[str, int] | None = None
        output_dir: str | None = None

        def parse_step() -> list:
            nonlocal trees
            trees = parser.parse(str(xml))
            return trees

        def import_step() -> dict[str, int]:
            nonlocal stats
            if trees is None:
                raise RuntimeError("XML parse step did not produce trees.")
            stats = importer.import_changes(str(excel), trees)
            return stats

        def write_step() -> str:
            nonlocal output_dir
            if trees is None:
                raise RuntimeError("XML parse step did not produce trees.")
            output_dir = writer.write(trees)
            return output_dir

        _run_steps(
            [
                ("Parsing XML files", parse_step),
                ("Applying workbook edits", import_step),
                ("Writing updated XML files", write_step),
            ],
            show_progress=show_progress,
        )

        if stats is not None:
            console.print(
                "[bold green]Import summary:[/bold green] "
                f"created={stats['created']}, updated={stats['updated']}, deleted={stats['deleted']}"
            )
        if output_dir is not None:
            console.print(f"[bold green]XML written to:[/bold green] {output_dir}")
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
