"""
Command-line interface for the Batch Bulk Editor.
"""

import argparse
import sys
import logging
from utils.logging_cfg import configure_logging
from core.parser import XMLParser
from core.exporter import ExcelExporter
from core.importer import ExcelImporter
from core.writer import XMLWriter
from utils.errors import ValidationError

logger = logging.getLogger(__name__)


def main():
    """
    Entrypoint: parse CLI arguments, set up logging, dispatch commands.
    """
    parser = argparse.ArgumentParser(
        prog="batch_bulk_editor", description="Bulk edit FactoryTalk Batch recipes"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        required=False,
        default=False,
        help="Enable debug logging",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("xml2excel", help="Export XML to Excel workbook")
    p1.add_argument(
        "--xml", required=True, help="Parent recipe XML file (.pxml/.uxml/.oxml)"
    )
    p1.add_argument("--excel", required=True, help="Output Excel path (.xlsx)")

    p2 = sub.add_parser("excel2xml", help="Import Excel and update XML")
    p2.add_argument(
        "--xml", required=True, help="Parent recipe XML file (.pxml/.uxml/.oxml)"
    )
    p2.add_argument("--excel", required=True, help="Edited Excel path (.xlsx)")

    args = parser.parse_args()
    configure_logging(getattr(args, "debug", False))

    try:
        if args.cmd == "xml2excel":
            tree = XMLParser().parse(args.xml)
            ExcelExporter().export(tree, args.excel)
        elif args.cmd == "excel2xml":
            tree = XMLParser().parse(args.xml)
            stats = ExcelImporter().import_changes(args.excel, tree)
            logger.info(f"{stats=}")
            out_dir = XMLWriter().write(tree)
            logger.info(f"Wrote updated XML files to {out_dir}")
        else:
            parser.print_help()
    except ValidationError as e:
        logger.error(f"Validation error: Aborted due to {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error :(")
        sys.exit(1)


if __name__ == "__main__":
    main()
