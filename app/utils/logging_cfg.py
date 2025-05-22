"""
Configure logging: INFO->console, DEBUG->file.
"""

import logging


def configure_logging(debug_mode: bool) -> None:
    """
    If debug_mode is True:
      - root logger level = DEBUG
      - create file handler at DEBUG
      - console at INFO
    Otherwise:
      - root logger level = INFO
      - no file is created
      - console at INFO
    """
    logger = logging.getLogger()
    # Remove any existing handlers if re-run
    logger.handlers.clear()

    if debug_mode:
        logger.setLevel(logging.DEBUG)
        # File handler at DEBUG
        fh = logging.FileHandler("batch_bulk_editor.log", mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s\t[%(name)s.%(funcName)s:%(lineno)d]\t%(message)s",
            datefmt="%d-%b-%Y %H:%M:%S",
        )
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

        # Console at INFO
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%d-%b-%Y %H:%M:%S",
        )
        ch.setFormatter(console_formatter)
        logger.addHandler(ch)
    else:
        # No file handler, just console
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            fmt="[%(asctime)s]\t%(levelname)s:\t%(message)s",
            datefmt="%d-%b-%Y %H:%M:%S",
        )
        ch.setFormatter(console_formatter)
        logger.addHandler(ch)
