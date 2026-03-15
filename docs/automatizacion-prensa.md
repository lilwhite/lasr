# Automatización de prensa (v2)

## Objetivo

Esta v2 implementa un flujo semiautomático y mantenible:

1. recopilar noticias candidatas desde feeds de medios
2. ampliar histórico de WordPress cuando la fuente lo permita
3. puntuar relevancia para Los Ángeles de San Rafael
4. categorizar y deduplicar
5. generar JSON reutilizable por la web

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

## Criterio de relevancia aplicado (v2)

- suma de puntos por palabras clave incluidas
- bonus por frases prioritarias (por ejemplo, "Los Ángeles de San Rafael")
- penalización por ruido (deportes, agenda cultural, etc.)
- `isRelevant = true` si supera el umbral `min_score`

## Histórico completo para La Voz de El Espinar

Además del feed RSS, para `lavozdeelespinar.es` se consulta la API pública de WordPress:

- `wp_endpoint`: endpoint REST de posts
- `historical_searches`: términos para recorrer histórico temático
- `wp_per_page`: tamaño de página (máximo 100)

El script itera paginación completa (`page=1..N`) por cada término de búsqueda y deduplica por:

- URL canónica (`canonicalUrl`)
- slug por fuente
- clave normalizada de titular

Esto evita que el archivo quede limitado al año en curso cuando el feed público solo expone ítems recientes.

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

## Modelo de salida (campos)

Cada noticia puede incluir:

- `source`
- `date`
- `publishedAt`
- `year`
- `category`
- `tags`
- `url`
- `canonicalUrl`
- `relevanceScore`
- `isRelevant`
- `featured`

## Cómo añadir una fuente

Editar `docs/data/prensa/sources.json`:

1. añadir bloque en `sources` con `name`, `domain` y `feeds`
2. ajustar keywords/categorías si hace falta
3. regenerar JSON

## Limitaciones de esta v2

- depende de feeds RSS/Atom públicos
- para histórico avanzado depende de APIs públicas (WordPress REST)
- no hace scraping profundo de páginas HTML complejas
- puede requerir ajuste de keywords para mejorar precisión
- la clasificación es heurística (no sustituye revisión editorial)

## Nota editorial

La sección Prensa se presenta como recopilación contextual de cobertura periodística, no como fuente oficial ni asesoramiento jurídico.
