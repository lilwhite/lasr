from typing import Dict


def collect(source: Dict, timeout: int, max_per_source: int):
    return {
        "items": [],
        "warnings": [
            "[warn] Diputación de Segovia sin feed estable detectado para automatización segura."
        ],
    }
