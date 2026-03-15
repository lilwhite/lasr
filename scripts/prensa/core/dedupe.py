from typing import Iterable, List

from helpers import canonicalize_url, normalize_text, normalize_title_key

from .types import NormalizedNewsItem


def _slug_from_url(url: str) -> str:
    cleaned = canonicalize_url(url)
    if not cleaned:
        return ""
    path = cleaned.split("?", 1)[0].rstrip("/")
    if "/" not in path:
        return path
    return path.rsplit("/", 1)[-1]


def dedupe_items(items: Iterable[NormalizedNewsItem]) -> List[NormalizedNewsItem]:
    seen_urls = set()
    seen_titles = set()
    seen_source_date = set()
    result = []

    for item in items:
        canonical_key = item.canonical_url or canonicalize_url(item.url)
        title_key = normalize_title_key(item.title)
        source_date_key = (
            f"{normalize_text(item.source)}::{item.date}::{_slug_from_url(item.url)}"
        )

        if canonical_key and canonical_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        if source_date_key in seen_source_date:
            continue

        if canonical_key:
            seen_urls.add(canonical_key)
        if title_key:
            seen_titles.add(title_key)
        seen_source_date.add(source_date_key)

        result.append(item)

    return result
