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
    """
    Dedupe con claves fuertes para preservar cobertura multi-fuente.

    Decisión de negocio:
    - La cobertura de distintos medios sobre el mismo tema se conserva intencionadamente.
    - NO se deduplica por similitud semántica global entre medios.
    - Solo se eliminan duplicados reales (misma URL canónica, mismo guid, o título casi exacto dentro del mismo medio).
    """
    seen_urls = set()
    seen_guids = set()
    seen_source_title = set()
    seen_source_date = set()
    result = []

    for item in items:
        canonical_key = item.canonical_url or canonicalize_url(item.url)
        source_key = normalize_text(item.source)
        title_key = normalize_title_key(item.title)
        guid_key = normalize_text(item.feed_guid)
        source_title_key = f"{source_key}::{title_key}" if title_key else ""
        source_date_key = f"{source_key}::{item.date}::{_slug_from_url(item.url)}"

        if canonical_key and canonical_key in seen_urls:
            continue
        if guid_key and guid_key in seen_guids:
            continue
        if source_title_key and source_title_key in seen_source_title:
            continue
        if source_date_key in seen_source_date:
            continue

        if canonical_key:
            seen_urls.add(canonical_key)
        if guid_key:
            seen_guids.add(guid_key)
        if source_title_key:
            seen_source_title.add(source_title_key)
        seen_source_date.add(source_date_key)

        result.append(item)

    return result
