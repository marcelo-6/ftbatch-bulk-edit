from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import cli.cli as cli_module
from utils.errors import ValidationError

runner = CliRunner()


def test_help_includes_commands() -> None:
    result = runner.invoke(cli_module.app, ["--help"])
    assert result.exit_code == 0
    assert "xml2excel" in result.output
    assert "excel2xml" in result.output
    assert "--debug" in result.output
    assert "--progress" in result.output
    assert "--no-progress" in result.output


def test_version_flag_shows_project_version(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_project_version", lambda: "9.9.9")
    result = runner.invoke(cli_module.app, ["--version"])
    all_output = result.output + getattr(result, "stderr", "")
    assert result.exit_code == 0
    assert "9.9.9" in all_output


def test_xml2excel_invokes_parser_and_exporter(
    monkeypatch, tmp_path: Path
) -> None:
    xml_path = tmp_path / "in.pxml"
    xml_path.write_text("<RecipeElement/>", encoding="utf-8")
    excel_path = tmp_path / "out.xlsx"
    calls: dict[str, object] = {}

    class DummyParser:
        def parse(self, path: str):
            calls["parse"] = path
            return ["TREE"]

    class DummyExporter:
        def export(self, trees, excel: str):
            calls["export"] = (trees, excel)

    monkeypatch.setattr(cli_module, "XMLParser", DummyParser)
    monkeypatch.setattr(cli_module, "ExcelExporter", DummyExporter)

    result = runner.invoke(
        cli_module.app,
        [
            "--no-progress",
            "xml2excel",
            "--xml",
            str(xml_path),
            "--excel",
            str(excel_path),
        ],
    )

    assert result.exit_code == 0
    assert calls["parse"] == str(xml_path.resolve())
    assert calls["export"] == (["TREE"], str(excel_path.resolve()))


def test_excel2xml_invokes_parse_import_write(
    monkeypatch, tmp_path: Path
) -> None:
    xml_path = tmp_path / "in.pxml"
    xml_path.write_text("<RecipeElement/>", encoding="utf-8")
    excel_path = tmp_path / "edited.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")
    out_dir = tmp_path / "converted"
    calls: dict[str, object] = {}

    class DummyParser:
        def parse(self, path: str):
            calls["parse"] = path
            return ["TREE"]

    class DummyImporter:
        def import_changes(self, excel: str, trees):
            calls["import"] = (excel, trees)
            return {"created": 1, "updated": 2, "deleted": 3}

    class DummyWriter:
        def write(self, trees):
            calls["write"] = trees
            return str(out_dir)

    monkeypatch.setattr(cli_module, "XMLParser", DummyParser)
    monkeypatch.setattr(cli_module, "ExcelImporter", DummyImporter)
    monkeypatch.setattr(cli_module, "XMLWriter", DummyWriter)

    result = runner.invoke(
        cli_module.app,
        [
            "--no-progress",
            "excel2xml",
            "--xml",
            str(xml_path),
            "--excel",
            str(excel_path),
        ],
    )

    assert result.exit_code == 0
    assert calls["parse"] == str(xml_path.resolve())
    assert calls["import"] == (str(excel_path.resolve()), ["TREE"])
    assert calls["write"] == ["TREE"]


def test_excel2xml_validation_error_returns_exit_code_1(
    monkeypatch, tmp_path: Path
) -> None:
    xml_path = tmp_path / "in.pxml"
    xml_path.write_text("<RecipeElement/>", encoding="utf-8")
    excel_path = tmp_path / "edited.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")

    class DummyParser:
        def parse(self, path: str):
            return ["TREE"]

    class DummyImporter:
        def import_changes(self, excel: str, trees):
            raise ValidationError("invalid workbook")

    monkeypatch.setattr(cli_module, "XMLParser", DummyParser)
    monkeypatch.setattr(cli_module, "ExcelImporter", DummyImporter)

    result = runner.invoke(
        cli_module.app,
        [
            "--no-progress",
            "excel2xml",
            "--xml",
            str(xml_path),
            "--excel",
            str(excel_path),
        ],
    )

    assert result.exit_code == 1
