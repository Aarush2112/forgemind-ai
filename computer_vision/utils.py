import logging
from pathlib import Path

from .config import LOG_LEVEL


logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ForgeMind-CV")


def ensure_directory(path: Path) -> None:
    """
    Create directory if it does not exist.
    """

    path.mkdir(parents=True, exist_ok=True)


def file_exists(path: Path) -> bool:
    return path.exists()