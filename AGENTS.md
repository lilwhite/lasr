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

### Skills Disponibles

#### skill.web-design-static-portal
- **Propósito:** Buenas prácticas de diseño web en portales estáticos
- **Aplicar cuando:** Cambios en UI, HTML, CSS, JS

#### skill.github-pages-workflow
- **Propósito:** Buenas prácticas en despliegue con GitHub Actions
- **Aplicar cuando:** Cambios en workflows

#### skill.github-validation-guard
- **Propósito:** Validaciones mínimas antes de desplegar
- **Aplicar cuando:** Cambios en validación o calidad

#### skill.safe-static-site-refactor
- **Propósito:** Cambios sin romper el portal
- **Aplicar cuando:** Cambios en estructura o rutas

#### skill.docs-and-maintenance
- **Propósito:** Documentación operativa consistente
- **Aplicar cuando:** Cambios en documentación

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

- `docs/urbanizacion_los_angeles_san_rafael.md` - Documento principal con el contexto completo
- `docs/documentacion_relevante.md` - Fuentes de información, jurisprudencia y normativa
- `docs/contexto_general.md` - Contexto general del conflicto
- `docs/timeline_conflicto.md` - Línea temporal detallada
- `docs/problemas_detectados.md` - Problemas identificados
- `docs/actores.md` - Actores y roles
- `docs/opciones_legales.md` - Vías legales disponibles
- `docs/preguntas_abiertas.md` - Preguntas sin resolver

### Raíz del proyecto

- `README.md` - Página principal del repositorio
- `AGENTS.md` - Instrucciones para agentes IA

## Comandos de desarrollo

No aplica - es un proyecto de documentación sin código fuente.

### Despliegue del portal web

El portal está diseñado para GitHub Pages mediante GitHub Actions:

1. Los cambios en `docs/` se validan automáticamente
2. Al hacer push a `main`, el workflow copia `docs/` a `dist/`
3. GitHub Pages sirve el contenido desde `dist/`

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

## Estructura del documento principal

El documento `urbanizacion_los_angeles_san_rafael.md` sigue la estructura:

1. Introducción - ubicación y contexto general
2. Origen de la urbanización - historia y desarrollo inicial
3. Evolución del modelo urbano - cambios demográficos y funcionales
4. Sistema de mantenimiento (EUCC) - figura jurídica y funcionamiento
5. Hito legal clave - sentencia judicial
6. Situación actual - estado de la ejecución
7. Actores implicados - vecinos, Ayuntamiento, EUCC, tribunales, Junta
8. Problema central - resumen del conflicto
9. Posibles vías de actuación - judicial, institucional, política
10. Línea temporal resumida - cronología
11. Uso del documento - aplicaciones previsto

## Notas para agentes

- Este documento sirve como base para generar visualizaciones (diagramas, infografías, mapas de actores, líneas temporales)
- Mantener consistencia terminológica: EUCC, TSJCyL, Tribunal Supremo, Ayuntamiento de El Espinar
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
