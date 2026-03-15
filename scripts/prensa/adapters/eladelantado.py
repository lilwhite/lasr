from typing import Dict

from .base import fetch_feed_items


def collect(source: Dict, timeout: int, max_per_source: int):
    result = fetch_feed_items(source, timeout, max_per_source)
    return {"items": result.items, "warnings": result.warnings}
