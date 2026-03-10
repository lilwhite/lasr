# github-validation-guard

## Purpose

Validar estructura y contenido mínimo antes de desplegar. Proteger el repositorio con comprobaciones tempranas que fallen rápido si falta algo esencial.

## When to Use

- Revisiones de calidad
- Validación en pull requests
- Pre-despliegue
- Cambios en archivos críticos

## Scope

- Validación de estructura de archivos
- Validación de sintaxis JSON
- Validación de workflows

## Input / Target Files

- `docs/index.html`
- `docs/assets/config.json`
- `docs/assets/content.json`
- `docs/assets/css/styles.css`
- `docs/assets/js/main.js`
- Documentos markdown: `docs/*.md`
- Workflows: `.github/workflows/*.yml`

## Rules

1. Validar existencia de archivos críticos:
   - `docs/index.html`
   - `docs/assets/config.json`
   - `docs/assets/content.json`
2. Validar sintaxis JSON con Python estándar
3. Fallar temprano con mensajes claros
4. Proteger siempre antes de desplegar
5. Ejecutar en:
   - Pull requests
   - Push a main
6. Mantener mensajes de error descriptivos
7. No usar Node.js ni npm para validación

## Checklist

- [ ] `docs/index.html` existe
- [ ] `docs/assets/config.json` existe y es válido
- [ ] `docs/assets/content.json` existe y es válido
- [ ] `docs/assets/css/styles.css` existe
- [ ] `docs/assets/js/main.js` existe
- [ ] Workflow falla si falta algo esencial
- [ ] Mensajes de error claros
- [ ] Se ejecuta en PR y push a main

## Expected Output

- Validación que falla temprano si falta algo
- Mensajes claros indicando qué falta
- Protección previa al despliegue

## What NOT to Do

- No usar Node.js para validar JSON
- No crear validaciones complejas innecesarias
- No omitir archivos críticos de la validación
- No usar librerías externas pesadas
- No cambiar estructura del proyecto para validar
- No hacer validaciones que requieran setup complejo
