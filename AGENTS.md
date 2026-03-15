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
3. No introducir frameworks, bundlers o dependencias pesadas
4. Mantener `/docs` como fuente del sitio
5. Separar cambios visuales, de contenido y operativos
6. Validar siempre antes de proponer despliegue
7. Documentar decisiones relevantes
8. Preservar rutas relativas y comportamiento actual
9. Favorecer mantenibilidad sobre complejidad
10. Aplicar skills especializadas antes de modificar archivos
11. **NUNCA subir información sensible** (datos personales, contraseñas, claves, tokens, información privada de vecinos)

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

No aplica - es un proyecto de documentación sin código fuente.

### Despliegue del portal web

El portal está diseñado para GitHub Pages mediante GitHub Actions:

1. Los cambios en `docs/` se validan automáticamente
2. Las ramas de trabajo y PRs hacia `dev` ejecutan validaciones
3. `dev` actúa como integración previa sin publicación final
4. Solo `main` publica en GitHub Pages copiando `docs/` a `dist/`

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
- Usar腥Links cuando sea necesario `[texto](url)`
- Tables para información estructurada

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
