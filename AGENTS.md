# AGENTS.md

## Proyecto: Documentación Urbanística Los Ángeles de San Rafael

Este repositorio contiene documentación sobre la situación urbanística de la urbanización Los Ángeles de San Rafael en El Espinar (Segovia, España).

**Nota:** Este es un proyecto de documentación con portal estático. El despliegue se hace mediante GitHub Actions.

---

## Modelo de Trabajo del Agente

El agente debe trabajar de forma estructurada usando skills especializadas:

### Principios Operativos

1. Priorizar cambios mínimos y reversibles
2. No rehacer arquitectura sin petición explícita
3. No introducir frameworks, bundlers ni dependencias pesadas **en el portal** (`docs/`), que sigue siendo HTML/CSS/JS sin build. La guía documental (`documentacion/`) sí usa Astro; ninguna otra parte del repositorio introduce herramientas de compilación
4. El sitio se compone de **dos fuentes**: `docs/` (portal, se copia tal cual a la raíz) y `documentacion/` (guía documental, se compila con Astro y se coloca en `/documentacion/`). Ninguna otra carpeta se publica
5. Separar cambios visuales, de contenido y operativos
6. Validar siempre antes de proponer despliegue
7. Documentar decisiones relevantes
8. Preservar rutas relativas y comportamiento actual
9. Favorecer mantenibilidad sobre complejidad
10. Aplicar skills especializadas antes de modificar archivos
11. **NUNCA subir información sensible** (datos personales, contraseñas, claves, tokens, información privada de vecinos). En particular, `documentacion/private-sources/` contiene los PDF originales del caso, con datos personales: está excluido en dos `.gitignore` y antes de cualquier commit `git status --short | grep private-sources` debe salir vacío

### Flujo de Trabajo con Ramas y PRs

El agente debe trabajar siguiendo este flujo obligatorio:

#### Reglas Obligatorias

1. **NUNCA hacer commit directo en `main`**
2. **NUNCA hacer commit directo en `dev`**
3. **Siempre crear rama para cada tarea**
4. **Las ramas de trabajo deben nacer desde `dev`**

#### Pasos por Tarea

1. **Actualizar rama base local `dev`** y crear rama de trabajo desde `dev`.

2. **Crear rama** con formato:
   ```
   <tipo>/<descripcion-corta>
   ```
   Ejemplos:
   - `feature/mejorar-linea-tiempo`
   - `fix/corregir-enlace-sentencia`
   - `docs/actualizar-fuentes`
   - `visual/ajustar-cards-documentacion`
   - `chore/actualizar-workflows`

3. **Hacer cambios** en los archivos necesarios

4. **Hacer commit** siguiendo Conventional Commits:
   - `feat:` nueva funcionalidad
   - `docs:` cambios en documentación
   - `fix:` corrección
   - `refactor:` mejora interna
   - `chore:` cambios operativos/infraestructura

5. **Hacer push** de la rama

6. **Crear Pull Request normal** hacia `dev`

7. **Promoción a producción**: crear PR de `dev` hacia `main`.

#### Formato de la Pull Request

La PR debe incluir:

```markdown
## Summary
Breve descripción del cambio.

## Changes
Lista de archivos añadidos/modificados.

## Purpose
Por qué se realiza este cambio.
```

#### Reglas Importantes

- ✅ El agente **debe** crear ramas para cada cambio
- ✅ El agente **debe** crear ramas desde `dev`
- ✅ El agente **debe** hacer commit con Conventional Commits
- ✅ El agente **debe** crear PRs normales hacia `dev`
- ✅ El agente **debe** usar PR `dev` → `main` para producción
- ❌ El agente **nunca** debe hacer commit directo en main
- ❌ El agente **nunca** debe hacer commit directo en dev
- ❌ El agente **nunca** debe hacer merge automático
- ❌ La revisión humana es **obligatoria** antes del merge

### Skills Disponibles

Las skills están definidas en `.agents/skills/<skill-name>/SKILL.md`:

#### skill.web-design-static-portal
- **Propósito:** Buenas prácticas de diseño web en portales estáticos
- **Aplicar cuando:** Cambios en UI, HTML, CSS, JS
- **Archivo:** `.agents/skills/web-design-static-portal/SKILL.md`

#### skill.github-pages-workflow
- **Propósito:** Buenas prácticas en despliegue con GitHub Actions
- **Aplicar cuando:** Cambios en workflows
- **Archivo:** `.agents/skills/github-pages-workflow/SKILL.md`

#### skill.github-validation-guard
- **Propósito:** Validaciones mínimas antes de desplegar
- **Aplicar cuando:** Cambios en validación o calidad
- **Archivo:** `.agents/skills/github-validation-guard/SKILL.md`

#### skill.safe-static-site-refactor
- **Propósito:** Cambios sin romper el portal
- **Aplicar cuando:** Cambios en estructura o rutas
- **Archivo:** `.agents/skills/safe-static-site-refactor/SKILL.md`

#### skill.docs-and-maintenance
- **Propósito:** Documentación operativa consistente
- **Aplicar cuando:** Cambios en documentación
- **Archivo:** `.agents/skills/docs-and-maintenance/SKILL.md`

### Reglas de Decisión

- UI → `skill.web-design-static-portal`
- Workflows/despliegue → `skill.github-pages-workflow`
- Validación/calidad → `skill.github-validation-guard`
- Estructura/rutas → `skill.safe-static-site-refactor`
- Documentación → `skill.docs-and-maintenance`

### Formato de Respuesta

Para cada tarea técnica:
1. Tipo de tarea detectada
2. Skills aplicadas
3. Riesgos detectados
4. Archivos a modificar
5. Cambios propuestos
6. Validaciones a ejecutar
7. Resultado esperado

## Archivos

### Portal Web (docs/) - GitHub Pages

El portal web está en la carpeta `docs/` para despliegue en GitHub Pages:

- `docs/index.html` - Página principal del portal
- `docs/assets/config.json` - Configuración del sitio
- `docs/assets/content.json` - Contenido del portal (editable)
- `docs/assets/css/styles.css` - Estilos
- `docs/assets/js/main.js` - Funcionalidad
- `docs/DEPLOY.md` - Instrucciones de despliegue

### Guía documental (documentacion/) - se compila y se publica en /documentacion/

Capa de evidencia del sitio: un grafo de afirmaciones trazables sobre la
documentación primaria del caso. 36 documentos, 150 afirmaciones, 48
acontecimientos; unas 290 páginas generadas.

- `documentacion/README.md` - Cómo desarrollar, qué valida el build, protección de datos
- `documentacion/src/content/` - El corpus: Markdown con frontmatter YAML, validado con Zod
- `documentacion/src/lib/policy.ts` - Punto único de qué se muestra y cómo se etiqueta
- `documentacion/src/lib/url.ts` - Punto único donde se aplica la base del sitio
- `documentacion/scripts/` - Herramientas del corpus (OCR, inventario, verificación de citas)
- `documentacion/private-sources/` - **Originales con datos personales. NUNCA se versiona**

**Sus tres especificaciones**, que hay que leer antes de tocar contenido:

- `documentacion/docs/CONTENT_MODEL.md` - Qué se guarda y con qué reglas
- `documentacion/docs/WEB_DESIGN.md` - Cómo se muestra
- `documentacion/docs/WORKFLOW.md` - Cómo se incorpora un documento nuevo

> **Cuidado con el nombre `docs/`.** En la raíz es el **portal publicado**. Dentro
> de `documentacion/` son las **especificaciones** de la guía. No son lo mismo y
> conviene nombrarlos siempre completos.

### Documentación Markdown (docs/)

- `docs/documentacion_relevante.md` - Fuentes de información, jurisprudencia y normativa

### Raíz del proyecto

- `README.md` - Página principal del repositorio
- `AGENTS.md` - Instrucciones para agentes IA

### .agents/ - Skills del Agente

```
.agents/skills/
├── web-design-static-portal/SKILL.md
├── github-pages-workflow/SKILL.md
├── github-validation-guard/SKILL.md
├── safe-static-site-refactor/SKILL.md
└── docs-and-maintenance/SKILL.md
```

## Comandos de desarrollo

El portal (`docs/`) no necesita build: se edita y se abre. La guía documental sí.

```sh
# Guía documental
cd documentacion
npm ci
npm run dev      # http://localhost:4321/documentacion/
npm run check    # astro check + build + validación de enlaces. Ejecutar SIEMPRE antes de una PR

# Sitio combinado, con la estructura de rutas real del despliegue
cd documentacion && npm run build && cd ..
docker compose up    # http://localhost:8080/
```

El sitio combinado es la única forma de probar los enlaces entre el portal y la
guía, y las tres redirecciones de `/cronologia/`, `/recepcion-urbanizacion/` y
`/sentencia-tsjcyl/`.

`npm run build` sincroniza antes la paleta y los scripts de tema desde
`docs/assets/`: **la guía no se compila sin el portal**.

### Despliegue del portal web

El portal está diseñado para GitHub Pages mediante GitHub Actions:

1. Los cambios en `docs/` se validan automáticamente
2. Las ramas de trabajo y PRs hacia `dev` ejecutan validaciones, incluida la compilación completa de la guía documental
3. `dev` actúa como integración previa sin publicación final
4. Solo `main` publica en GitHub Pages: copia `docs/` a `dist/` y compila la guía en `dist/documentacion/`. El build de la guía se cachea, porque el cron diario de prensa dispara este workflow sin tocarla

**Activar GitHub Actions:**
- Settings → Pages → Source: **GitHub Actions**

Ver `docs/DEPLOY.md` para instrucciones detalladas.

## Directrices de estilo

### Documentación en Markdown

- Encabezados en español usando `#`, `##`, `###`
- Párrafos con lenguaje claro y accesible
- Listas con `-` para viñetas
- Negrita con `**texto**`
- Cursiva con `*texto*`
- Usar enlaces cuando sea necesario `[texto](url)`
- Tablas para información estructurada

### Contenido

- Lenguaje neutral y objetivo
- Accesible para vecinos sin conocimientos jurídicos
- Hechos verificables claramente separados de interpretaciones
- Fuentes de información identificadas cuando sea posible
- Evitar jerga jurídica innecesaria
- Explicar términos técnicos cuando sea imprescindible usarlos

## Notas para agentes

- Este documento sirve como base para generar visualizaciones (diagramas, infografías, mapas de actores, líneas temporales)
- Mantener consistencia terminológica: EUC, TSJCyL, Tribunal Supremo, Ayuntamiento de El Espinar
- Actualizar la línea temporal conforme evolucione la situación
- No inventar hechos no presentes en fuentes verificables
- Separar claramente opiniones/hechos de interpretaciones

## Lineamientos de contenido

### Para secciones fácticas (origen,timeline, actores)

- Basarse únicamente en información verificada
- Citar fechas concretas cuando estén disponibles
- Describir roles institucionales con precisión

### Para secciones analíticas (problema, vías de actuación)

- Mantener neutralidad
- Presentar múltiples perspectivas
- Evitar lenguaje emocional o polemico

### Para visualizaciones

El documento está estructurado para facilitar la generación de:
- Diagramas de flujo (proceso de reclamación)
- Mapas de actores (relaciones entre partes)
- Infografías (resúmenes accesibles)
- Líneas temporales interactivas
- Comparativas (situación vs. casco urbano)
