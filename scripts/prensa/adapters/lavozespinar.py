from typing import Dict

from .base import fetch_feed_items, fetch_wordpress_history


def collect(source: Dict, timeout: int, max_per_source: int):
    base = fetch_feed_items(source, timeout, max_per_source)
    historical = fetch_wordpress_history(source, timeout)
    return {
        "items": [*base.items, *historical.items],
        "warnings": [*base.warnings, *historical.warnings],
        "fetched_count": base.fetched_count + historical.fetched_count,
        "parsed_count": base.parsed_count + historical.parsed_count,
    }
