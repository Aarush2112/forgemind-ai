"""
Lightweight callbacks fired after Pinecone indexing from Computer Vision.
Avoids circular imports between main.py and detect.py.
"""

from __future__ import annotations

import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

_index_callbacks: List[Callable[[], None]] = []


def register_index_callback(callback: Callable[[], None]) -> None:
    """Register a function to run after CV documents are indexed."""
    if callback not in _index_callbacks:
        _index_callbacks.append(callback)


def notify_index_updated() -> None:
    """Notify registered listeners that the vector index was updated."""
    for callback in _index_callbacks:
        try:
            callback()
        except Exception:
            logger.exception("Index update callback failed")
