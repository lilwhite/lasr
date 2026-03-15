#!/usr/bin/env python3

import argparse
import importlib
import sys
from pathlib import Path
from typing import Dict, List

from core.dedupe import dedupe_items
from core.normalize import normalize_item, sort_items
from core.types import NormalizedNewsItem, RawNewsItem
from helpers import canonicalize_url, load_json, write_json


DEFAULT_CONFIG = Path("docs/data/prensa/sources.json")
DEFAULT_OUTPUT = Path("docs/data/prensa/curated_news.json")


def _load_adapter(module_name: str):
    return importlib.import_module(f"adapters.{module_name}")


def _collect_from_source(source: Dict, timeout: int, max_per_source: int):
    adapter_name = source.get("adapter")
    if not adapter_name:
        return {
            "items": [],
            "warnings": [f"[warn] {source.get('name', 'Fuente')} sin adapter"],
        }

    try:
        adapter = _load_adapter(adapter_name)
    except ModuleNotFoundError:
        return {
            "items": [],
            "warnings": [
                f"[warn] Adapter no encontrado para {source.get('name', 'Fuente')}: {adapter_name}"
            ],
        }

    return adapter.collect(source, timeout=timeout, max_per_source=max_per_source)


def _existing_featured(output_path: Path) -> Dict[str, bool]:
    featured = {}
    if not output_path.exists():
        return featured
    try:
        payload = load_json(output_path)
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue
                key = canonicalize_url(item.get("canonicalUrl") or item.get("url", ""))
                if key:
                    featured[key] = bool(item.get("featured", False))
    except Exception:
        return {}
    return featured


def run(config_path: Path, output_path: Path, timeout: int):
    config = load_json(config_path)
    max_per_source = int(config.get("max_per_source", 50))
    max_items = int(config.get("max_items", 300))
    relevance_threshold = int(config.get("relevance_threshold", 10))
    categories = config.get("categories", {})
    scoring = config.get("scoring", {})

    featured_lookup = _existing_featured(output_path)

    collected: List[RawNewsItem] = []
    warnings: List[str] = []
    source_stats: Dict[str, Dict[str, int]] = {}
    for source in config.get("sources", []):
        source_name = source.get("name", "Fuente")
        result = _collect_from_source(source, timeout, max_per_source)
        source_items = result.get("items", [])
        collected.extend(source_items)
        warnings.extend(result.get("warnings", []))
        source_stats[source_name] = {
            "fetched": int(result.get("fetched_count", 0)),
            "parsed": int(result.get("parsed_count", 0)),
            "normalized": 0,
            "relevant": 0,
            "deduped": 0,
            "final": 0,
            "raw_items": len(source_items),
        }

    normalized: List[NormalizedNewsItem] = []
    for raw in collected:
        item = normalize_item(
            raw,
            categories=categories,
            scoring=scoring,
            relevance_threshold=relevance_threshold,
            featured_lookup=featured_lookup,
        )
        if item:
            normalized.append(item)
            stats = source_stats.get(item.source)
            if stats is not None:
                stats["normalized"] += 1
                if item.is_relevant:
                    stats["relevant"] += 1

    deduped = dedupe_items(normalized)
    deduped_ids = {item.id for item in deduped}
    for item in normalized:
        stats = source_stats.get(item.source)
        if stats is None:
            continue
        if item.id not in deduped_ids:
            stats["deduped"] += 1

    ordered = sort_items(deduped)
    limited = ordered[:max_items]
    for item in limited:
        stats = source_stats.get(item.source)
        if stats is not None:
            stats["final"] += 1

    output = []
    for item in limited:
        output.append(
            {
                "id": item.id,
                "feedGuid": item.feed_guid,
                "title": item.title,
                "date": item.date,
                "source": item.source,
                "sourceType": item.source_type,
                "url": item.url,
                "summary": item.summary,
                "excerpt": item.summary,
                "tags": item.tags,
                "relatedTo": item.related_to,
                "score": item.score,
                "relevanceScore": item.score,
                "isRelevant": item.is_relevant,
                "category": item.category,
                "publishedAt": item.published_at,
                "year": int(item.date[:4])
                if item.date and len(item.date) >= 4
                else None,
                "canonicalUrl": item.canonical_url,
                "featured": item.featured,
            }
        )

    write_json(output_path, output)

    relevant = [item for item in output if item.get("isRelevant")]
    years = sorted(
        {item.get("year") for item in relevant if isinstance(item.get("year"), int)}
    )
    year_info = f"{years[0]}-{years[-1]}" if years else "sin rango"

    for warning in warnings:
        print(warning)
    for source_name, stats in source_stats.items():
        print(
            f"[{source_name}] fetched={stats['fetched']} parsed={stats['parsed']} "
            f"normalized={stats['normalized']} relevant={stats['relevant']} "
            f"deduped={stats['deduped']} final={stats['final']}"
        )
    print(f"[ok] Total candidatas: {len(output)} | Relevantes: {len(relevant)}")
    print(f"[ok] Rango histórico relevante: {year_info}")
    print(f"[ok] JSON generado: {output_path}")


def parse_args(argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Recopila y cura noticias para la sección Prensa (multifuente)."
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
