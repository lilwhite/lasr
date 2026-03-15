from typing import Dict


def collect(source: Dict, timeout: int, max_per_source: int):
    return {
        "items": [],
        "warnings": [
            "[warn] Segovia Audaz no disponible actualmente (dominio/feed no resoluble)."
        ],
    }
