# Automatización de prensa (v3 multifuente)

## Objetivo

La v3 incorpora una arquitectura por adaptadores para agregar noticias de varias fuentes locales, provinciales e institucionales con filtrado temático orientado a Los Ángeles de San Rafael.

Flujo:

1. obtención por fuente (`adapters/`)
2. parsing de feed/API (`core/parser.py`)
3. normalización a modelo común (`core/normalize.py`)
4. scoring temático (`core/scorer.py`)
5. deduplicación (`core/dedupe.py`)
6. generación de JSON reutilizable para UI

## Estructura

```text
scripts/prensa/
├── adapters/
│   ├── lavozespinar.py
│   ├── elnortedecastilla.py
│   ├── eladelantado.py
│   ├── segoviaaudaz.py
│   ├── ayuntamiento_elespinar.py
│   ├── diputacion_segovia.py
│   └── junta_cyl.py
├── core/
│   ├── fetch.py
│   ├── parser.py
│   ├── normalize.py
│   ├── scorer.py
│   ├── dedupe.py
│   └── types.py
└── fetch_press.py
```

## Modelo normalizado

Cada noticia se publica con el esquema:

- `id`
- `title`
- `date`
- `source`
- `sourceType` (`local`, `provincial`, `institucional`)
- `url`
- `summary`
- `tags`
- `relatedTo`
- `score`

Y por compatibilidad UI actual:

- `excerpt`
- `relevanceScore`
- `isRelevant`
- `category`
- `publishedAt`
- `year`
- `canonicalUrl`
- `featured`

## Fuentes actualmente configuradas

- **Local**: La Voz de El Espinar
- **Provincial**: El Norte de Castilla, El Adelantado de Segovia, Segovia Audaz (placeholder técnico)
- **Institucional**: Ayuntamiento de El Espinar, Diputación de Segovia (placeholder técnico), Junta de Castilla y León (placeholder técnico)

> Nota: cuando una fuente no dispone de feed estable o endpoint robusto, el adapter devuelve warning y no bloquea la ejecución.

## Scoring temático

El scoring se define en `docs/data/prensa/sources.json`.

- positivos por términos clave (LASR, EUC, urbanismo, servicios, seguridad, N-603, presa del Tejo, MILASR, etc.)
- negativos por ruido editorial (fiestas/agenda/deportes)
- penalización adicional por falta de relación clara con LASR

Se publica como relevante (`isRelevant=true`) si supera `relevance_threshold`.

## Ejecución

```bash
python3 scripts/prensa/fetch_press.py
```

Opciones:

```bash
python3 scripts/prensa/fetch_press.py --config docs/data/prensa/sources.json --output docs/data/prensa/curated_news.json --timeout 15
```

## Cómo añadir una nueva fuente

1. Crear adapter en `scripts/prensa/adapters/<fuente>.py` con función `collect(source, timeout, max_per_source)`.
2. Añadir bloque en `docs/data/prensa/sources.json` con:
   - `name`
   - `adapter`
   - `source_type`
   - `feeds` y/o opciones específicas
   - `related_to`
3. Ejecutar scraper y revisar warnings.
4. Validar resultados en `/prensa/`.

## Limitaciones actuales

- Depende de disponibilidad pública de feeds/APIs.
- Evita scraping HTML frágil salvo necesidad justificada.
- Algunas fuentes institucionales se mantienen en modo placeholder hasta identificar endpoint estable.

## Nota editorial

La sección Prensa es una recopilación contextual orientada a seguimiento vecinal. No sustituye fuentes oficiales ni asesoramiento jurídico.
