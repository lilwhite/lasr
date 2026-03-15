from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


SourceType = Literal["local", "provincial", "institucional"]


@dataclass
class RawNewsItem:
    guid: str
    title: str
    url: str
    date: str
    published_at: str
    excerpt: str
    raw_category: str
    source: str
    source_type: SourceType
    related_to: List[str]


@dataclass
class NormalizedNewsItem:
    id: str
    feed_guid: str
    title: str
    date: str
    source: str
    source_type: SourceType
    url: str
    summary: str
    tags: List[str]
    related_to: List[str]
    score: int
    is_relevant: bool
    category: str
    published_at: str
    canonical_url: str
    featured: bool


AdapterConfig = Dict


@dataclass
class AdapterResult:
    items: List[RawNewsItem]
    warnings: List[str]
