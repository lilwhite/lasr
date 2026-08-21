# 🏘️ Los Ángeles de San Rafael

> Documentación sobre la situación urbanística y jurídica de la urbanización en El Espinar (Segovia, España)

---

## 📋 Descripción

Este repositorio contiene documentación sobre el conflicto urbanístico entre los vecinos de **Los Ángeles de San Rafael** y el **Ayuntamiento de El Espinar** respecto a la recepción municipal de las infraestructuras.

El proyecto incluye:
- 📄 Documentación de referencia en Markdown
- 🌐 Portal web estático publicado en GitHub Pages
- ⚙️ Workflows de GitHub Actions para validación y despliegue
- 🤖 Instrucciones para agentes IA

---

## 📁 Estructura del Proyecto

```
📂 LASR/
├── 📂 docs/                    # Portal web -> raíz del dominio
│   ├── index.html              # Página principal
│   ├── DEPLOY.md               # Guía de despliegue
│   └── 📂 assets/
│       ├── config.json         # Configuración
│       ├── content.json        # Contenido
│       ├── css/tokens.css      # Paleta y tema: fuente única de TODO el sitio
│       ├── css/styles.css      # Estilos del portal
│       └── js/main.js          # Funcionalidad
│
├── 📂 documentacion/           # Guía documental (Astro) -> /documentacion/
│   ├── README.md               # Cómo desarrollarla
│   ├── 📂 docs/                # Sus especificaciones (NO es el portal)
│   ├── 📂 src/content/         # El corpus: 36 documentos, 150 afirmaciones
│   └── 📂 scripts/             # Herramientas del corpus (OCR, inventario)
│
├── 📂 .agents/skills/          # Skills para agentes IA
│   ├── web-design-static-portal/
│   ├── github-pages-workflow/
│   ├── github-validation-guard/
│   ├── safe-static-site-refactor/
│   └── docs-and-maintenance/
│
├── 📄 docs/documentacion_relevante.md
├── 📄 AGENTS.md
└── 📄 README.md
```

---

## 🏗️ Arquitectura Técnica

| Componente | Tecnología |
|------------|------------|
| 🌐 Hosting | GitHub Pages, dominio propio `lasr-info.es` |
| ⚡ CI/CD | GitHub Actions |
| 🎨 Estilos | CSS vanilla, con los tokens compartidos por las dos mitades |
| ✨ Scripts | JavaScript vanilla (portal) · Astro estático sin JS de aplicación (guía) |
| 📝 Contenido | JSON + Markdown (portal) · colecciones validadas con Zod (guía) |
| 🔒 Validación | Python + `astro check` |

El sitio son **dos fuentes que se combinan en el despliegue**: `docs/` se copia
tal cual a la raíz y `documentacion/` se compila con Astro y se coloca en
`/documentacion/`. La paleta y el tema claro/oscuro salen de un único fichero,
`docs/assets/css/tokens.css`, que la guía copia en su build.

---

## 📰 Contexto del Conflicto

La urbanización **Los Ángeles de San Rafael**, desarrollada en los años 60, fue declarada recepcionable por sentencia del **TSJCyL** (2013). Más de 10 años después, la sentencia no se ha ejecutado completamente.

### Problema Central

| Tema | Situación |
|------|-----------|
| 💰 Fiscal | Vecinos pagan IBI + cuotas EUC |
| 🏛️ Servicios | No reciben servicios municipales equivalentes |
| 📅 Temporal | 11 años sin asamblea de propietarios |
| ⚖️ Legal | Sentencia sin ejecución efectiva |

---

## 🚀 Despliegue

El portal se despliega automáticamente mediante **GitHub Actions**:

1. Los cambios en `docs/` se validan automáticamente
2. Las ramas de trabajo y PRs hacia `dev` ejecutan validaciones sin publicar
3. Solo `main` publica la web pública final en GitHub Pages

### Releases y changelog automático

Cada push a `main` ejecuta el workflow de release automático:

1. Calcula la siguiente versión semántica (incremento patch sobre la última `v*`)
2. Actualiza `CHANGELOG.md`
3. Actualiza `docs/assets/build-meta.json` (versión y fecha)
4. Publica tag y GitHub Release con notas en castellano

Fuente de verdad de cambios: **`CHANGELOG.md`**.

### Activar GitHub Pages

```
Settings → Pages → Source: GitHub Actions
```

Ver [`docs/DEPLOY.md`](docs/DEPLOY.md) para instrucciones detalladas.

Para la sección de prensa semiautomatizada, ver [`docs/automatizacion-prensa.md`](docs/automatizacion-prensa.md).
El archivo de prensa está disponible en `docs/prensa/index.html` (ruta pública `/prensa/`).

---

## 🌿 Flujo de ramas

- `main`: producción (publica GitHub Pages)
- `dev`: integración/preproducción (no publica)
- Ramas cortas desde `dev`: `feature/*`, `fix/*`, `docs/*`, `visual/*`, `chore/*`

Flujo recomendado:
1. Crear rama desde `dev`
2. Abrir PR de rama de trabajo hacia `dev`
3. Validar y consolidar en `dev`
4. Promocionar con PR `dev` → `main`

Guía completa en [`docs/WORKFLOW.md`](docs/WORKFLOW.md).

---

## 🐳 Validación local con Docker

```bash
cd documentacion && npm run build && cd ..   # la guía hay que compilarla antes
docker compose up -d
```

Luego abre `http://localhost:8080`. Sirve el sitio **combinado**, con la misma
estructura de rutas que el despliegue: el portal en la raíz y la guía en
`/documentacion/`. Es la única forma de probar los enlaces cruzados entre ambos.

Para detener:

```bash
docker compose down
```

---

## 🤖 Skills del Agente

El proyecto usa un sistema de skills para mantener buenas prácticas:

| Skill | Propósito |
|-------|-----------|
| 🌐 `web-design-static-portal` | Diseño web en portales estáticos |
| ⚙️ `github-pages-workflow` | Despliegue con GitHub Actions |
| 🛡️ `github-validation-guard` | Validaciones previas al despliegue |
| 🔒 `safe-static-site-refactor` | Cambios seguros en estructura |
| 📚 `docs-and-maintenance` | Documentación operativa |

Ver [`AGENTS.md`](AGENTS.md) para más detalles.

---

## 📚 Fuentes

- 📰 Artículos de prensa local (El Adelantado, El Norte de Castilla, El Espinar Hoy)
- ⚖️ Jurisprudencia del TSJCyL
- 📜 Normativa urbanística de Castilla y León

---

## 📝 Licencia

Este proyecto se distribuye bajo licencia **MIT**.

- Texto completo: [`LICENSE`](LICENSE)
- Nota: el contenido mantiene carácter informativo y no constituye asesoramiento jurídico.
