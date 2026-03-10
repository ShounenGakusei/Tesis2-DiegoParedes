import logging
from pathlib import Path

def setup_logging(log_file: str, level: str = "INFO"):

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ],
    )

    logging.getLogger("dlgoes").setLevel(getattr(logging, level))