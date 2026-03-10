# Portal Los Ángeles de San Rafael - Guía de Despliegue

## 1. Información General

Este proyecto usa **GitHub Actions** para desplegar automáticamente el sitio en **GitHub Pages**.

### ¿Qué ha cambiado?

- Anterior: Despliegue manual desde rama/carpeta
- Actual: Despliegue automático mediante GitHub Actions

### Flujo de trabajo

1. Haces `git push` a `main`
2. Se valida la estructura del proyecto
3. Se copia `docs/` a `dist/`
4. Se despliega automáticamente en GitHub Pages

---

## 2. Estructura del Proyecto

```
mi-repo/
├── .github/
│   └── workflows/
│       ├── pages.yml      # Workflow de despliegue
│       └── validate.yml   # Workflow de validación
├── docs/                   # ← Contenido fuente
│   ├── index.html
│   ├── assets/
│   │   ├── config.json
│   │   ├── content.json
│   │   ├── css/styles.css
│   │   └── js/main.js
│   └── *.md               # Documentación
├── scripts/                # Scripts auxiliares
└── README.md
```

---

## 3. Activar GitHub Pages con Actions

### Paso 1: Subir los workflows

```bash
git add .github/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

### Paso 2: Configurar GitHub Pages

1. Ve a tu repositorio en GitHub
2. **Settings** → **Pages**
3. En "Source" selecciona: **GitHub Actions**
4. No necesitas seleccionar carpeta ni rama

### Paso 3: Esperar el despliegue

- Ve a la pestaña **Actions**
- Observa el workflow "Desplegar a GitHub Pages"
- Cuando termine, tu sitio estará disponible

---

## 4. Qué hace cada workflow

### validate.yml (automático)

Se ejecuta en:
- Cada `push` a `main`
- Cada `pull_request`

Valida:
- ✅ Existen todos los archivos obligatorios
- ✅ Los JSON tienen sintaxis válida
- ✅ Estructura correcta del proyecto

### pages.yml (despliegue)

Se ejecuta en:
- Cada `push` a `main`
- Manual: **Actions** → **Desplegar a GitHub Pages** → **Run workflow**

Hace:
1. Checkout del código
2. Validación de estructura
3. Validación de JSON
4. Copia `docs/` a `dist/`
5. Crea `.nojekyll`
6. Despliega en GitHub Pages

---

## 5. Checklist para Publicar

```bash
# 1. Edita el contenido que necesites
nano docs/assets/content.json

# 2. Commit y push
git add .
git commit -m "Actualización de contenido"
git push

# 3. Ve a Actions y observa el despliegue
# URL: https://github.com/TU_USUARIO/TU_REPO/actions
```

---

## 6. Solución de Problemas

### El workflow falla en "Validar estructura"

Revisa que existan:
- `docs/index.html`
- `docs/assets/config.json`
- `docs/assets/content.json`
- `docs/assets/css/styles.css`
- `docs/assets/js/main.js`

### El workflow falla en "Validar JSON"

Los archivos JSON tienen errores de sintaxis. Usa un validador:
- https://jsonformatter.org/
- VS Code: Cierra y abre el archivo

### El sitio no aparece

1. Ve a **Settings** → **Pages**
2. Confirma que "Source" está en **GitHub Actions**
3. Revisa la pestaña **Actions** para ver errores

### Error de permisos

Si ves error en `id-token`, asegurate de:
- Tener GitHub Pages habilitado en el repo
- Usar las acciones oficiales de GitHub

---

## 7. Actualizar Contenido

### Desde JSON (recomendado)

Edita `docs/assets/content.json`:
```bash
nano docs/assets/content.json
```

### Desde HTML

Edita `docs/index.html`:
```bash
nano docs/index.html
```

### Nuevo documento markdown

Simplemente crea el archivo en `docs/`:
```bash
nano docs/nuevo-documento.md
```

Después:
```bash
git add .
git commit -m "Añadir nuevo contenido"
git push
```

---

## 8. Archivos Modificados/Creados

| Archivo | Acción |
|---------|--------|
| `.github/workflows/pages.yml` | Nuevo - Despliegue |
| `.github/workflows/validate.yml` | Nuevo - Validación |
| `docs/DEPLOY.md` | Actualizado |
| `.nojekyll` | Se crea automáticamente |

---

## 9. Recursos

- [GitHub Pages con Actions](https://docs.github.com/es/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow)
- [Actions de GitHub Pages](https://github.com/actions/deploy-pages)
- [Configurar Pages](https://docs.github.com/es/pages)

---

**Nota:** Este portal mantiene su estructura original. Solo se añade automatización para el despliegue.
