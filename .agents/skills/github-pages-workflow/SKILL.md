# github-pages-workflow

## Purpose

Aplicar buenas prácticas al workflow de despliegue de GitHub Pages. Mantener simplicidad, reproducibilidad y uso de acciones oficiales.

## When to Use

- Crear o modificar workflows de despliegue
- Cambios en GitHub Actions
- Configuración de Pages
- Automatización de build

## Scope

- `.github/workflows/*.yml`
- Configuración de GitHub Pages

## Input / Target Files

- Workflow principal: `.github/workflows/pages.yml`
- Workflow de validación: `.github/workflows/validate.yml`
- Configuración de Pages (en GitHub)

## Rules

1. Usar acciones oficiales de GitHub:
   - `actions/checkout@v4`
   - `actions/configure-pages@v4`
   - `actions/upload-pages-artifact@v3`
   - `actions/deploy-pages@v4`
2. Usar permisos mínimos correctos:
   - `contents: read`
   - `pages: write`
   - `id-token: write`
3. Definir concurrency para evitar despliegues simultáneos
4. Mantener pasos simples y transparentes
5. Publicar artefacto con `index.html` en raíz
6. Usar `.nojekyll` cuando ayude a evitar problemas
7. Incluir validación previa al despliegue
8. Permitir ejecución manual (`workflow_dispatch`)
9. Usar Python estándar para validaciones (sin Node/npm)

## Checklist

- [ ] Usa `actions/checkout@v4`
- [ ] Usa `actions/configure-pages@v4`
- [ ] Usa `actions/upload-pages-artifact@v3`
- [ ] Usa `actions/deploy-pages@v4`
- [ ] Permisos: `contents: read`, `pages: write`, `id-token: write`
- [ ] Concurrency definida
- [ ] Artefacto con `index.html` en raíz
- [ ] `.nojekyll` creado cuando aplica
- [ ] Validación previa incluida
- [ ] `workflow_dispatch` permitido

## Expected Output

- Workflow que se ejecuta en push a main
- Despliegue automático en GitHub Pages
- Validación previa al despliegue
- Artefacto publicado correctamente

## What NOT to Do

- No usar acciones no oficiales o de terceros sin justificación
- No introducir Node.js o npm sin necesidad
- No crear pasos de build complejos
- No omitir permisos de pages
- No eliminar validación previa
- No cambiar estructura de carpetas del proyecto
- No mover contenido fuera de `docs/`
