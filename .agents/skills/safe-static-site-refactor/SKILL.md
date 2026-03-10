# safe-static-site-refactor

## Purpose

Hacer cambios en el portal sin romper estructura, rutas ni despliegue. Mantener cambios mínimos, reversibles y bien documentados.

## When to Use

- Reorganización de carpetas
- Cambios en rutas
- Refactors de estructura
- Migraciones de contenido

## Scope

- `docs/`
- `.github/workflows/`
- Cualquier cambio estructural

## Input / Target Files

- Cualquier archivo en `docs/`
- Cualquier archivo en `.github/`
- Estructura de carpetas del proyecto

## Rules

1. Priorizar cambios mínimos y reversibles
2. No mover carpetas sin necesidad justificada
3. Preservar rutas relativas de assets:
   - `assets/css/`
   - `assets/js/`
   - `assets/images/`
4. Mantener `docs/` como fuente del sitio
5. Documentar cualquier cambio estructural
6. Evitar introducir dependencias nuevas
7. No cambiar comportamiento funcional salvo necesidad
8. Verificar que enlaces internos funcionan
9. Verificar que assets se cargan correctamente

## Checklist

- [ ] No se mueven carpetas innecesariamente
- [ ] Rutas relativas preservadas
- [ ] `docs/` sigue como fuente del sitio
- [ ] No se introducen dependencias nuevas
- [ ] Enlaces internos funcionan
- [ ] Assets se cargan correctamente
- [ ] Cambio documentado si es estructural
- [ ] Cambio reversible documentado

## Expected Output

- Cambios mínimos que no rompen el portal
- Rutas funcionales
- Despliegue sin errores

## What NOT to Do

- No fuera de `docs mover contenido/`
- No cambiar arquitectura sin necesidad
- No introducir frameworks
- No cambiar rutas de assets
- No romper enlaces existentes
- No duplicar contenido
- No hacer cambios grandes de una vez
