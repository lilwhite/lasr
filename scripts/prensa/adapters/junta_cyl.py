from typing import Dict


def collect(source: Dict, timeout: int, max_per_source: int):
    return {
        "items": [],
        "fetched_count": 0,
        "parsed_count": 0,
        "warnings": [
            "[warn] Junta de Castilla y León sin feed estable detectado para este ámbito temático."
        ],
    }
