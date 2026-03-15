from dataclasses import dataclass
from typing import Dict, List

from helpers import normalize_text


@dataclass
class ScoreResult:
    score: int
    tags: List[str]


def compute_score(text: str, scoring: Dict) -> ScoreResult:
    normalized = normalize_text(text)
    score = 0
    tags: List[str] = []
    relation_hits = 0

    relation_terms = [
        normalize_text(term) for term in scoring.get("relation_terms", [])
    ]
    for term in relation_terms:
        if term and term in normalized:
            relation_hits += 1

    for rule in scoring.get("positive", []):
        term = normalize_text(rule.get("term", ""))
        if term and term in normalized:
            score += int(rule.get("weight", 0))
            tags.append(term)

    for rule in scoring.get("negative", []):
        term = normalize_text(rule.get("term", ""))
        if term and term in normalized:
            score -= int(rule.get("weight", 0))

    if relation_terms and relation_hits == 0:
        score -= int(scoring.get("unclear_relation_penalty", 10))

    return ScoreResult(score=score, tags=sorted(set(tags)))
