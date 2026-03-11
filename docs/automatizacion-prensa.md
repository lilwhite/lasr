# Automatización de prensa (v1)

## Objetivo

Esta v1 implementa un flujo semiautomático y mantenible:

1. recopilar noticias candidatas desde feeds de medios
2. puntuar relevancia para Los Ángeles de San Rafael
3. categorizar y deduplicar
4. generar JSON reutilizable por la web

La actualización es manual (sin cron ni Actions en esta fase).

## Archivos

- `scripts/prensa/fetch_press.py`
- `scripts/prensa/helpers.py`
- `docs/data/prensa/sources.json`
- `docs/data/prensa/curated_news.json`
- `docs/prensa/index.html`
- `docs/assets/js/press-utils.js`
- `docs/assets/js/prensa-archive.js`

## Ejecución

Desde la raíz del repositorio:

```bash
python3 scripts/prensa/fetch_press.py
```

Opciones útiles:

```bash
python3 scripts/prensa/fetch_press.py --config docs/data/prensa/sources.json --output docs/data/prensa/curated_news.json --timeout 12
```

## Criterio de relevancia aplicado (v1)

- suma de puntos por palabras clave incluidas
- bonus por frases prioritarias (por ejemplo, "Los Ángeles de San Rafael")
- penalización por ruido (deportes, agenda cultural, etc.)
- `isRelevant = true` si supera el umbral `min_score`

## Categorías de salida

- `juntas_y_vecinos`
- `urbanismo`
- `recepcion`
- `infraestructuras`
- `servicios`
- `contexto_municipal`
- `judicial`

## Campo editorial `featured`

El JSON soporta `featured: true/false` para destacar noticias en la landing.

- Landing: muestra hasta 3 destacadas (`featured=true`) y, si faltan, completa con relevantes recientes.
- Archivo: muestra todas las noticias relevantes con filtros.

## Cómo añadir una fuente

Editar `docs/data/prensa/sources.json`:

1. añadir bloque en `sources` con `name`, `domain` y `feeds`
2. ajustar keywords/categorías si hace falta
3. regenerar JSON

## Limitaciones de esta v1

- depende de feeds RSS/Atom públicos
- no hace scraping profundo de páginas HTML complejas
- puede requerir ajuste de keywords para mejorar precisión
- la clasificación es heurística (no sustituye revisión editorial)

## Nota editorial

La sección Prensa se presenta como recopilación contextual de cobertura periodística, no como fuente oficial ni asesoramiento jurídico.
