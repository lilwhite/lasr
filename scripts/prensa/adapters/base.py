from typing import Dict, List

from urllib.error import HTTPError, URLError

from core.fetch import fetch_bytes, fetch_json
from core.parser import parse_feed_items
from core.types import AdapterResult, RawNewsItem
from helpers import strip_html


def _to_raw_item(entry: Dict[str, str], source: Dict) -> RawNewsItem | None:
    title = (entry.get("title") or "").strip()
    url = (entry.get("url") or "").strip()
    if not title or not url:
        return None

    return RawNewsItem(
        title=strip_html(title),
        url=url,
        date=entry.get("date", ""),
        published_at=entry.get("published_at", ""),
        excerpt=entry.get("excerpt", ""),
        raw_category=entry.get("raw_category", ""),
        source=source["name"],
        source_type=source.get("source_type", "provincial"),
        related_to=source.get("related_to", []),
    )


def fetch_feed_items(source: Dict, timeout: int, max_per_source: int) -> AdapterResult:
    output: List[RawNewsItem] = []
    warnings: List[str] = []

    for feed_url in source.get("feeds", []):
        try:
            payload = fetch_bytes(feed_url, timeout)
        except URLError as exc:
            warnings.append(
                f"[warn] {source['name']} feed no disponible: {feed_url} ({exc})"
            )
            continue

        parsed_items = parse_feed_items(payload)
        if not parsed_items:
            warnings.append(f"[warn] {source['name']} sin items parseables: {feed_url}")
            continue

        for parsed in parsed_items:
            item = _to_raw_item(parsed, source)
            if item:
                output.append(item)
                if len(output) >= max_per_source:
                    return AdapterResult(items=output, warnings=warnings)

    return AdapterResult(items=output, warnings=warnings)


def fetch_wordpress_history(source: Dict, timeout: int) -> AdapterResult:
    endpoint = source.get("wp_endpoint")
    searches = source.get("historical_searches", [])
    if not endpoint or not searches:
        return AdapterResult(items=[], warnings=[])

    output: List[RawNewsItem] = []
    warnings: List[str] = []
    per_page = min(int(source.get("wp_per_page", 100)), 100)

    for term in searches:
        if not term or not str(term).strip():
            continue

        page = 1
        total_pages = 1
        from urllib.parse import quote

        encoded_term = quote(str(term).strip())

        while page <= total_pages:
            wp_url = (
                f"{endpoint}?search={encoded_term}&per_page={per_page}&page={page}"
                "&_fields=link,slug,date,date_gmt,title,excerpt"
            )
            try:
                headers, payload = fetch_json(wp_url, timeout)
            except HTTPError as exc:
                if exc.code != 400:
                    warnings.append(
                        f"[warn] {source['name']} error WP ({exc.code}): {wp_url}"
                    )
                break
            except (URLError, TimeoutError, ValueError) as exc:
                warnings.append(
                    f"[warn] {source['name']} histórico no disponible: {wp_url} ({exc})"
                )
                break

            if not isinstance(payload, list) or not payload:
                break

            try:
                total_pages = int(headers.get("x-wp-totalpages", "") or "1")
            except ValueError:
                total_pages = 1

            for post in payload:
                title = strip_html(
                    ((post.get("title") or {}).get("rendered") or "").strip()
                )
                link = (post.get("link") or "").strip()
                if not title or not link:
                    continue

                output.append(
                    RawNewsItem(
                        title=title,
                        url=link,
                        date=(post.get("date_gmt") or post.get("date") or "").strip(),
                        published_at=(post.get("date") or "").strip(),
                        excerpt=strip_html(
                            (post.get("excerpt") or {}).get("rendered") or ""
                        ),
                        raw_category="",
                        source=source["name"],
                        source_type=source.get("source_type", "provincial"),
                        related_to=source.get("related_to", []),
                    )
                )

            page += 1

    return AdapterResult(items=output, warnings=warnings)
