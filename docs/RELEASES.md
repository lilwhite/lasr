# Releases automáticas y versionado

## Flujo

El flujo operativo sigue siendo:

1. Ramas de trabajo → `dev`
2. Validación en `dev`
3. Promoción `dev` → `main`

Al llegar cambios a `main`, se ejecuta automáticamente:

- Workflow `.github/workflows/release.yml`
- Actualización de `CHANGELOG.md`
- Generación/actualización de `docs/assets/build-meta.json`
- Creación de tag y GitHub Release

## Versionado

Se usa semver simple (`vMAJOR.MINOR.PATCH`) con incremento **patch** automático en cada publicación a `main`.

## Fuente de verdad

El historial oficial es `CHANGELOG.md`.

- Las notas de release se generan a partir del mismo contenido resumido.
- La web muestra versión/fecha/cambios principales desde `docs/assets/content.json` y `build-meta.json`.
