#!/usr/bin/env python3

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.error import URLError
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
USER_AGENT = "LASR-PressFetcher/1.0 (+https://lasr-info.es)"


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    date: str
    excerpt: str
    category: str
    relevance_score: int
    is_relevant: bool
    tags: List[str]


def fetch_feed(url: str, timeout: int) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        return response.read()


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

        atom_items.append(
            {
                "title": text_of(entry, f"{atom_ns}title"),
                "url": link,
                "date": text_of(entry, f"{atom_ns}updated")
                or text_of(entry, f"{atom_ns}published"),
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


def dedupe(items: Iterable[Candidate]) -> List[Candidate]:
    seen_urls = set()
    seen_titles = set()
    result = []

    for item in items:
        url_key = canonicalize_url(item.url)
        title_key = normalize_title_key(item.title)

        if url_key and url_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue

        if url_key:
            seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)

        result.append(item)

    return result


def sort_candidates(items: Iterable[Candidate]) -> List[Candidate]:
    def sort_key(item: Candidate):
        date_value = item.date or "0000-00-00"
        return (date_value, item.relevance_score)

    return sorted(items, key=sort_key, reverse=True)


def run(config_path: Path, output_path: Path, timeout: int):
    config = load_json(config_path)
    candidates: List[Candidate] = []

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
                title = (raw.get("title") or "").strip()
                url = canonicalize_url((raw.get("url") or "").strip())
                if not title or not url:
                    continue

                excerpt = strip_html(raw.get("excerpt") or "")
                excerpt = excerpt[:220].strip()
                date = parse_date(raw.get("date") or "")

                text = normalize_text(
                    " ".join([title, excerpt, raw.get("raw_category", "")])
                )
                relevance_score, tags = score_relevance(text, config)
                category = classify(text, config)
                is_relevant = relevance_score >= int(config["relevance"]["min_score"])

                candidates.append(
                    Candidate(
                        title=title,
                        url=url,
                        source=source["name"],
                        date=date,
                        excerpt=excerpt,
                        category=category,
                        relevance_score=relevance_score,
                        is_relevant=is_relevant,
                        tags=tags,
                    )
                )

                source_count += 1
                if source_count >= int(config.get("max_per_source", 40)):
                    break

            if source_count >= int(config.get("max_per_source", 40)):
                break

    deduped = dedupe(candidates)
    ordered = sort_candidates(deduped)
    limited = ordered[: int(config.get("max_items", 120))]

    output = [
        {
            "id": stable_id(item.url, item.title),
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "date": item.date,
            "excerpt": item.excerpt,
            "category": item.category,
            "relevanceScore": item.relevance_score,
            "isRelevant": item.is_relevant,
            "tags": item.tags,
        }
        for item in limited
    ]

    write_json(output_path, output)

    relevant_count = sum(1 for item in output if item["isRelevant"])
    print(f"[ok] Total candidatas: {len(output)} | Relevantes: {relevant_count}")
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
        "--timeout", type=int, default=12, help="Timeout HTTP por feed en segundos"
    )
    return parser.parse_args(argv)


def main(argv: List[str]):
    args = parse_args(argv)
    run(Path(args.config), Path(args.output), timeout=args.timeout)


if __name__ == "__main__":
    main(sys.argv[1:])
