# Flujo de trabajo con ramas (`main` / `dev`)

## Objetivo

Usar un flujo simple y seguro para este portal estático:

- `main`: producción (GitHub Pages público)
- `dev`: integración/preproducción
- ramas cortas: trabajo puntual para cada cambio

## Modelo de ramas

### Ramas principales

- `main`: solo cambios promocionados desde `dev`
- `dev`: integración estable previa a producción

### Ramas de trabajo permitidas

- `feature/<slug>`
- `fix/<slug>`
- `docs/<slug>`
- `visual/<slug>`
- `chore/<slug>`

Todas deben crearse desde `dev`.

## Flujo operativo

1. Actualizar `dev` local
2. Crear rama corta desde `dev`
3. Hacer cambios, validar en local y abrir PR hacia `dev`
4. Revisar y mergear en `dev`
5. Promocionar a producción con PR `dev` -> `main`
6. Mergear PR de promoción y dejar que GitHub Actions publique

## Comandos de referencia

```bash
# Crear rama de trabajo desde dev
git checkout dev
git pull --ff-only origin dev
git checkout -b docs/actualizar-fuentes

# Subir rama y abrir PR hacia dev
git push -u origin docs/actualizar-fuentes
```

## CI/CD esperado

- Ramas de trabajo y PRs hacia `dev`: validaciones (estructura, JSON y checks de calidad)
- `dev`: integración, sin despliegue público
- `main`: único despliegue público en GitHub Pages

## Validación local con Docker

### Opción rápida (recomendada)

```bash
docker compose up -d
```

Abrir: `http://localhost:8080`

Detener:

```bash
docker compose down
```

### Opción build de imagen

```bash
docker build -t lasr-site .
docker run --rm -p 8080:80 lasr-site
```

## Reglas de branch protection recomendadas (configuración manual en GitHub)

Aplicar en **Settings -> Branches -> Branch protection rules**.

### Para `main`

- Bloquear push directo
- Requerir Pull Request antes de merge
- Requerir checks de CI en verde
- Requerir al menos 1 review
- Bloquear force-push y delete branch

### Para `dev`

- Bloquear push directo
- Requerir Pull Request antes de merge
- Requerir checks de CI en verde
- Recomendado: al menos 1 review
- Bloquear force-push y delete branch

## Buenas prácticas para evitar divergencia larga

- Mantener PRs pequeñas y frecuentes
- Promocionar `dev` a `main` con regularidad
- Evitar acumular cambios sin validar en `dev`
- No mezclar cambios de contenido, visuales y operativos en una sola PR si se puede separar
