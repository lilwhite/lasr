# DESIGN.md — Portal LASR

Dirección visual: **«Sierra vecinal»** (elegida en agosto 2026 entre tres propuestas). El mundo material es la sierra de Guadarrama en la que está la urbanización: granito, pinar y luz de montaña, con tono directo de asamblea vecinal. La accesibilidad de lectura es parte de la identidad, no un requisito externo: la audiencia incluye muchos lectores mayores.

Fuente de verdad de los tokens: `docs/assets/css/styles.css` (bloques `:root` y `[data-theme="dark"]`). Este documento explica las decisiones; el CSS manda si divergen.

## Paleta

Familia «Forest»: verde profundo + hueso + ámbar. Nunca volver a crema+terracota (era el cliché que motivó el rediseño).

| Rol | Claro | Oscuro | Uso |
|---|---|---|---|
| Fondo | `#F2F2EB` (hueso-piedra) | `#1B211D` (noche de pinar) | `--color-bg` |
| Superficie | `#FBFBF7` | `#242B26` | tarjetas, header |
| Primario (pino) | `#2F5C43` | `#8FBF9F` | acciones, enlaces, marca |
| Acento (sol) | `#B27C2F` | `#D9A860` | solo superficies/detalles grandes |
| Acento como texto | `#8A5B25` | `#D9A860` | `--color-accent-text`: fechas, chips — nunca `--color-accent` en texto pequeño claro |
| Texto | `#232B26` | `#EBEEE8` | cuerpo |

- Texto sobre primario: `--color-on-primary` (`#fff` claro / `#16241B` oscuro). Nunca `color: white` literal.
- Sombras teñidas del verde del fondo (`rgba(24,34,27,…)`), nunca negro puro en claro.
- El azul `--color-info` queda reservado a semántica informativa y enlaces documentales; los avisos «Nota:» usan los tokens verdes `--theme-keyidea-*`.
- Un solo acento por página (el sol); verde es estructura, no acento.

## Tipografía

Autoalojada en `docs/assets/fonts/` (WOFF2, subset latino, `font-display: swap`) — la CSP `font-src 'self'` prohíbe CDNs de fuentes.

- **Display**: Bricolage Grotesque 600/700/800 (`--font-family-heading`). Titulares en 700–800, `line-height` 1.05–1.2, `letter-spacing -0.01/-0.02em`. Nunca serif como display: el serif-por-defecto era parte del cliché anterior.
- **Cuerpo**: Atkinson Hyperlegible 400/400i/700 (`--font-family`), diseñada para baja visión. Medida ≤65–75ch, `line-height` ≥1.6.
- **Datos**: `--font-family-mono` (pila de sistema) para referencias catastrales, cifras y fechas técnicas, con `font-variant-numeric: tabular-nums`. Mono solo para datos, nunca como disfraz «técnico».

## Firma visual

1. **Los hechos** (`.hechos`): 10+ / 1 / 0 como `<dl>` con un único filete superior continuo sobre el bloque, número en Bricolage 800 verde pino. Sin tarjetas, sin sombras. Vive en «Situación actual», nunca en el hero.
2. La silueta de sierra en SVG se probó como firma del hero y **el usuario la descartó** (ago 2026) — no reintroducirla. El hero cierra plano; la personalidad la llevan la tipografía y la paleta.

El titular del hero es el nombre de la urbanización, «Los Ángeles de San Rafael» (decisión del usuario); el mensaje de la sentencia vive en el subtexto y en los hechos.

## Reglas de componentes

- **Hero**: máx. 4 elementos (titular ≤2 líneas desktop, subtexto ≤20 palabras, 1 CTA primaria + 1 secundaria). Alineado a la izquierda. Sin eyebrow, sin tarjetas de métricas, sin degradados.
- **Botones**: primario = pino relleno; secundario = borde 2px pino. `--color-on-primary` para el texto. Etiquetas de una línea que nombran la acción («Buscar mi parcela», no «Enviar»).
- **Tarjetas**: radio 12px (`--radius-lg`), elevación por sombra teñida O borde, nunca ambos con protagonismo. Prohibido el filete lateral grueso (`border-left` de color >1px) — era el tell nº 1 del detector.
- **Chips de tipo de documento** (`.doc-type`): omitir cuando repiten el título del grupo (lógica `isRedundantChip` en `main.js`).
- **Anclas**: todo `[id]` lleva `scroll-margin-top` compensando el header fijo. No quitarlo.
- **Foco y selección**: `:focus-visible` global con outline pino; `::selection` pino sobre superficie. Tematizados en ambos temas.

## Los dos temas

Ambos obligatorios y de primera clase. `theme-init.js` respeta `prefers-color-scheme` en primera visita. Todo color nuevo se define en `:root` **y** en `[data-theme="dark"]`; nunca un literal que solo funciona en un tema. El oscuro no es una inversión: es la sierra de noche (fondos verdinegro, primario verde claro, siluetas más oscuras que el cielo).

## Voz

Español directo, segunda persona o primera del plural («qué podemos hacer los propietarios»). Divulgativo, no jurídico; las notas legales («no constituye asesoramiento jurídico») se preservan siempre. Todo dato afirmado sale de la sentencia, del Catastro o de la hemeroteca — no inventar métricas.

## Prohibiciones activas (de la auditoría)

Eyebrows sobre titulares (máx. 1 por cada 3 secciones, mejor ninguno) · hero de estadísticas · degradado en texto · serif display · `Inter`/`Fraunces` · paleta crema+terracota · `border-left` grueso de color · monospace decorativo · texto blanco literal sobre primario · emojis como iconos.

## Deuda registrada (siguiente capa)

- Acordeón FAQ: migrar `transition: max-height` a `grid-template-rows`, y revisar el `body * { transition }` universal.
- Monotonía de tarjetas en secciones interiores (Sentencia/Incumplimientos merecen composición propia).
- `fade-in` bajo el fold → IntersectionObserver o eliminarlo.
- Pasada propia para `doc.html`, prensa, actualizaciones y el buscador de parcelas (heredan tokens, falta acabado: scrollbars, panel, popup del mapa).
- Retirar el relleno de prensa «Nueva noticia en revisión editorial» (main.js).
- `og:url` apunta a lilwhite.github.io en vez de lasr-info.es; falta `<link rel="canonical">`.
