# Prensa multifuente — Guía rápida

Este documento explica cómo ampliar el sistema de prensa sin romper el flujo actual.

## 1) Arquitectura

El agregador vive en `scripts/prensa` y separa:

- **Adapters** (`adapters/`): conexión por fuente.
- **Core** (`core/`): parsing, scoring, normalización, dedupe.
- **Orquestador** (`fetch_press.py`): ejecuta todo y genera `curated_news.json`.

## 2) Contrato de un adapter

Cada adapter debe exponer:

```python
def collect(source: Dict, timeout: int, max_per_source: int) -> Dict:
    return {
      "items": [...],
      "warnings": [...]
    }
```

`items` debe incluir `RawNewsItem` compatibles con `core/normalize.py`.

## 3) Añadir una fuente

1. Crear archivo `scripts/prensa/adapters/<nombre>.py`.
2. Definir `collect(...)`.
3. Registrar la fuente en `docs/data/prensa/sources.json`:
   - `name`
   - `adapter`
   - `source_type` (`local`, `provincial`, `institucional`)
   - `feeds` o configuración propia
4. Ejecutar:

```bash
python3 scripts/prensa/fetch_press.py
```

5. Revisar warnings y validar `/prensa/`.

## 4) Criterios recomendados

- Evitar scraping HTML frágil.
- Priorizar RSS/Atom o API estable.
- Mantener logs útiles y no romper ejecución por una fuente caída.
- Reforzar términos LASR en scoring cuando se añada una nueva fuente generalista.
