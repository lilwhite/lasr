#!/usr/bin/env python3

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from helpers import (
    canonicalize_url,
    load_json,
    normalize_text,
    normalize_title_key,
    parse_date,
    stable_id,
    strip_html,
    write_json,
)


DEFAULT_CONFIG = Path("docs/data/prensa/sources.json")
DEFAULT_OUTPUT = Path("docs/data/prensa/curated_news.json")
USER_AGENT = "LASR-PressFetcher/1.1 (+https://lasr-info.es)"


@dataclass
class Candidate:
    title: str
    url: str
    canonical_url: str
    source: str
    date: str
    published_at: str
    excerpt: str
    category: str
    relevance_score: int
    is_relevant: bool
    tags: List[str]


def fetch_bytes(url: str, timeout: int) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_feed(url: str, timeout: int) -> bytes:
    return fetch_bytes(url, timeout)


def fetch_json(url: str, timeout: int) -> Tuple[Dict[str, str], object]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        headers = {
            "x-wp-total": response.headers.get("X-WP-Total", ""),
            "x-wp-totalpages": response.headers.get("X-WP-TotalPages", ""),
        }
        payload = json.loads(response.read().decode("utf-8"))
        return headers, payload


def parse_feed_items(payload: bytes) -> List[Dict[str, str]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    rss_items = []
    for item in root.findall(".//item"):
        rss_items.append(
            {
                "title": text_of(item, "title"),
                "url": text_of(item, "link"),
                "date": text_of(item, "pubDate"),
                "published_at": text_of(item, "pubDate"),
                "excerpt": text_of(item, "description"),
                "raw_category": text_of(item, "category"),
            }
        )

    if rss_items:
        return rss_items

    atom_ns = "{http://www.w3.org/2005/Atom}"
    atom_items = []
    for entry in root.findall(f".//{atom_ns}entry"):
        link = ""
        link_el = entry.find(f"{atom_ns}link")
        if link_el is not None:
            link = link_el.attrib.get("href", "")

        published = text_of(entry, f"{atom_ns}published") or text_of(
            entry, f"{atom_ns}updated"
        )
        atom_items.append(
            {
                "title": text_of(entry, f"{atom_ns}title"),
                "url": link,
                "date": published,
                "published_at": published,
                "excerpt": text_of(entry, f"{atom_ns}summary")
                or text_of(entry, f"{atom_ns}content"),
                "raw_category": "",
            }
        )

    return atom_items


def text_of(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def score_relevance(item_text: str, config: Dict) -> Tuple[int, List[str]]:
    score = 0
    tags = []

    for keyword, weight in config["relevance"]["include"].items():
        if keyword in item_text:
            score += int(weight)
            tags.append(keyword)

    for keyword, weight in config["relevance"].get("priority_phrase", {}).items():
        if keyword in item_text:
            score += int(weight)
            tags.append(keyword)

    for keyword, penalty in config["relevance"]["exclude"].items():
        if keyword in item_text:
            score -= int(penalty)

    return score, sorted(set(tags))


def classify(item_text: str, config: Dict) -> str:
    winner = "contexto_municipal"
    winner_score = 0

    for category, keywords in config["categories"].items():
        hits = sum(1 for keyword in keywords if keyword in item_text)
        if hits > winner_score:
            winner = category
            winner_score = hits

    return winner


def slug_from_url(url: str) -> str:
    cleaned = canonicalize_url(url)
    if not cleaned:
        return ""
    path = cleaned.split("?", 1)[0].rstrip("/")
    if "/" not in path:
        return path
    return path.rsplit("/", 1)[-1]


def dedupe(items: Iterable[Candidate]) -> List[Candidate]:
    seen_urls = set()
    seen_titles = set()
    seen_source_slugs = set()
    result = []

    for item in items:
        canonical_key = item.canonical_url or canonicalize_url(item.url)
        title_key = normalize_title_key(item.title)
        slug_key = slug_from_url(item.url)
        source_slug_key = (
            f"{normalize_text(item.source)}::{slug_key}" if slug_key else ""
        )

        if canonical_key and canonical_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        if source_slug_key and source_slug_key in seen_source_slugs:
            continue

        if canonical_key:
            seen_urls.add(canonical_key)
        if title_key:
            seen_titles.add(title_key)
        if source_slug_key:
            seen_source_slugs.add(source_slug_key)

        result.append(item)

    return result


def sort_candidates(items: Iterable[Candidate]) -> List[Candidate]:
    def sort_key(item: Candidate):
        date_value = item.date or "0000-00-00"
        return (date_value, item.relevance_score)

    return sorted(items, key=sort_key, reverse=True)


def build_candidate(
    raw: Dict[str, str], source_name: str, config: Dict
) -> Candidate | None:
    title = strip_html((raw.get("title") or "").strip())
    url = canonicalize_url((raw.get("url") or "").strip())
    if not title or not url:
        return None

    excerpt = strip_html(raw.get("excerpt") or "")
    excerpt = excerpt[:220].strip()
    date = parse_date(raw.get("date") or "")
    published_at = (raw.get("published_at") or "").strip()
    if not published_at:
        published_at = date

    text = normalize_text(" ".join([title, excerpt, raw.get("raw_category", "")]))
    relevance_score, tags = score_relevance(text, config)
    category = classify(text, config)
    is_relevant = relevance_score >= int(config["relevance"]["min_score"])

    return Candidate(
        title=title,
        url=url,
        canonical_url=canonicalize_url(url),
        source=source_name,
        date=date,
        published_at=published_at,
        excerpt=excerpt,
        category=category,
        relevance_score=relevance_score,
        is_relevant=is_relevant,
        tags=tags,
    )


def fetch_wordpress_history(source: Dict, timeout: int) -> List[Dict[str, str]]:
    endpoint = source.get("wp_endpoint")
    searches = source.get("historical_searches", [])
    if not endpoint or not searches:
        return []

    output: List[Dict[str, str]] = []
    per_page = min(int(source.get("wp_per_page", 100)), 100)

    for term in searches:
        if not term or not str(term).strip():
            continue

        page = 1
        total_pages = 1
        encoded_term = quote(str(term).strip())

        while page <= total_pages:
            wp_url = (
                f"{endpoint}?search={encoded_term}&per_page={per_page}&page={page}"
                "&_fields=link,slug,date,date_gmt,title,excerpt"
            )

            try:
                headers, payload = fetch_json(wp_url, timeout=timeout)
            except HTTPError as exc:
                if exc.code == 400:
                    break
                print(f"[warn] {source['name']} error WP ({exc.code}): {wp_url}")
                break
            except (URLError, TimeoutError, ValueError) as exc:
                print(
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

                excerpt = strip_html((post.get("excerpt") or {}).get("rendered") or "")
                published_at = (post.get("date_gmt") or post.get("date") or "").strip()

                output.append(
                    {
                        "title": title,
                        "url": link,
                        "date": published_at,
                        "published_at": (post.get("date") or published_at),
                        "excerpt": excerpt,
                        "raw_category": "",
                    }
                )

            page += 1

    return output


def run(config_path: Path, output_path: Path, timeout: int):
    config = load_json(config_path)
    candidates: List[Candidate] = []
    existing_featured = {}

    if output_path.exists():
        try:
            existing_items = load_json(output_path)
            if isinstance(existing_items, list):
                for item in existing_items:
                    if not isinstance(item, dict):
                        continue
                    key = canonicalize_url(
                        item.get("canonicalUrl") or item.get("url", "")
                    )
                    if key:
                        existing_featured[key] = bool(item.get("featured", False))
        except (ValueError, OSError, TypeError):
            existing_featured = {}

    max_per_source = int(config.get("max_per_source", 40))

    for source in config["sources"]:
        source_count = 0

        for feed_url in source.get("feeds", []):
            try:
                payload = fetch_feed(feed_url, timeout=timeout)
            except URLError as exc:
                print(f"[warn] {source['name']} feed no disponible: {feed_url} ({exc})")
                continue

            items = parse_feed_items(payload)
            if not items:
                print(f"[warn] {source['name']} sin items parseables: {feed_url}")
                continue

            for raw in items:
                candidate = build_candidate(raw, source["name"], config)
                if not candidate:
                    continue

                candidates.append(candidate)
                source_count += 1
                if source_count >= max_per_source:
                    break

            if source_count >= max_per_source:
                break

        historical_items = fetch_wordpress_history(source, timeout=timeout)
        for raw in historical_items:
            candidate = build_candidate(raw, source["name"], config)
            if candidate:
                candidates.append(candidate)

    deduped = dedupe(candidates)
    ordered = sort_candidates(deduped)
    limited = ordered[: int(config.get("max_items", 120))]

    output = []
    for item in limited:
        canonical_key = canonicalize_url(item.canonical_url or item.url)
        output.append(
            {
                "id": stable_id(item.url, item.title),
                "title": item.title,
                "url": item.url,
                "canonicalUrl": canonical_key,
                "source": item.source,
                "date": item.date,
                "publishedAt": item.published_at,
                "year": int(item.date[:4])
                if item.date and len(item.date) >= 4
                else None,
                "excerpt": item.excerpt,
                "category": item.category,
                "relevanceScore": item.relevance_score,
                "isRelevant": item.is_relevant,
                "featured": existing_featured.get(canonical_key, False),
                "tags": item.tags,
            }
        )

    write_json(output_path, output)

    relevant_count = sum(1 for item in output if item["isRelevant"])
    years = sorted(
        {
            item.get("year")
            for item in output
            if isinstance(item.get("year"), int) and item.get("isRelevant")
        }
    )
    year_info = f"{years[0]}-{years[-1]}" if years else "sin rango"
    print(f"[ok] Total candidatas: {len(output)} | Relevantes: {relevant_count}")
    print(f"[ok] Rango histórico relevante: {year_info}")
    print(f"[ok] JSON generado: {output_path}")


def parse_args(argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Recopila y cura noticias para la sección Prensa."
    )
    parser.add_argument(
        "--config", default=str(DEFAULT_CONFIG), help="Ruta a sources.json"
    )
    parser.add_argument(
        "--output", default=str(DEFAULT_OUTPUT), help="Ruta de salida curated_news.json"
    )
    parser.add_argument(
        "--timeout", type=int, default=12, help="Timeout HTTP por feed/API en segundos"
    )
    return parser.parse_args(argv)


def main(argv: List[str]):
    args = parse_args(argv)
    run(Path(args.config), Path(args.output), timeout=args.timeout)


if __name__ == "__main__":
    main(sys.argv[1:])
