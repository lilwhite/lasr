from typing import Dict, List

from helpers import canonicalize_url, parse_date, stable_id, strip_html

from .scorer import compute_score
from .types import NormalizedNewsItem, RawNewsItem


def classify(item_text: str, categories: Dict) -> str:
    lowered = item_text.lower()
    winner = "contexto_municipal"
    winner_score = 0

    for category, keywords in categories.items():
        hits = sum(1 for keyword in keywords if keyword in lowered)
        if hits > winner_score:
            winner = category
            winner_score = hits

    return winner


def normalize_item(
    raw: RawNewsItem,
    categories: Dict,
    scoring: Dict,
    relevance_threshold: int,
    featured_lookup: Dict[str, bool],
) -> NormalizedNewsItem | None:
    title = strip_html((raw.title or "").strip())
    url = canonicalize_url((raw.url or "").strip())
    if not title or not url:
        return None

    summary = strip_html(raw.excerpt or "")[:260].strip()
    date = parse_date(raw.date or "")
    published_at = (raw.published_at or "").strip() or date

    item_text = " ".join([title, summary, raw.raw_category or ""])
    score_result = compute_score(item_text, scoring)
    category = classify(item_text.lower(), categories)
    canonical_url = canonicalize_url(url)

    return NormalizedNewsItem(
        id=stable_id(url, title),
        feed_guid=(raw.guid or "").strip(),
        title=title,
        date=date,
        source=raw.source,
        source_type=raw.source_type,
        url=url,
        summary=summary,
        tags=score_result.tags,
        related_to=list(raw.related_to or []),
        score=score_result.score,
        is_relevant=score_result.score >= relevance_threshold,
        category=category,
        published_at=published_at,
        canonical_url=canonical_url,
        featured=featured_lookup.get(canonical_url, False),
    )


def sort_items(items: List[NormalizedNewsItem]) -> List[NormalizedNewsItem]:
    def sort_key(item: NormalizedNewsItem):
        date_value = item.date or "0000-00-00"
        return (date_value, item.score)

    return sorted(items, key=sort_key, reverse=True)
