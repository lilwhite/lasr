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
├── 📂 docs/                    # Portal web (GitHub Pages)
│   ├── index.html              # Página principal
│   ├── DEPLOY.md               # Guía de despliegue
│   └── 📂 assets/
│       ├── config.json         # Configuración
│       ├── content.json        # Contenido
│       ├── css/styles.css      # Estilos
│       └── js/main.js         # Funcionalidad
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
| 🌐 Hosting | GitHub Pages |
| ⚡ CI/CD | GitHub Actions |
| 🎨 Estilos | CSS vanilla |
| ✨ Scripts | JavaScript vanilla |
| 📝 Contenido | JSON + Markdown |
| 🔒 Validación | Python |

---

## 📰 Contexto del Conflicto

La urbanización **Los Ángeles de San Rafael**, desarrollada en los años 60, fue declarada recepcionable por sentencia del **TSJCyL** (2013). Más de 10 años después, la sentencia no se ha ejecutado completamente.

### Problema Central

| Tema | Situación |
|------|-----------|
| 💰 Fiscal | Vecinos pagan IBI + cuotas EUCC |
| 🏛️ Servicios | No reciben servicios municipales equivalentes |
| 📅 Temporal | 11 años sin asamblea de propietarios |
| ⚖️ Legal | Sentencia sin ejecución efectiva |

---

## 🚀 Despliegue

El portal se despliega automáticamente mediante **GitHub Actions**:

1. Los cambios en `docs/` se validan automáticamente
2. Al hacer push a `main`, se ejecuta el workflow
3. El contenido se publica en GitHub Pages

### Activar GitHub Pages

```
Settings → Pages → Source: GitHub Actions
```

Ver [`docs/DEPLOY.md`](docs/DEPLOY.md) para instrucciones detalladas.

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
