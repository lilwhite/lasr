# Guía documental de Los Ángeles de San Rafael

Capa de evidencia del portal vecinal. Se publica en
**https://lasr-info.es/documentacion/** y se despliega junto al portal desde
`.github/workflows/pages.yml`, en la raíz del repositorio.

No es un archivo de PDFs: es un grafo de afirmaciones verificables sobre la
documentación primaria del caso —sentencias, autos, estatutos, actas, acuerdos y
comunicaciones—, donde cada afirmación indica de qué documento sale y en qué
página. Hoy son 36 documentos, 150 afirmaciones, 48 acontecimientos, 21 actores,
11 procedimientos y 5 temas, y de ahí salen unas 290 páginas.

## Los tres documentos que gobiernan esto

Antes de tocar contenido, léelos: son la especificación, no notas.

| Documento | Qué fija |
|---|---|
| [`docs/CONTENT_MODEL.md`](docs/CONTENT_MODEL.md) | **Qué** se guarda: las colecciones, los tres ejes de estado, los identificadores, las reglas de protección de datos |
| [`docs/WEB_DESIGN.md`](docs/WEB_DESIGN.md) | **Cómo** se muestra: las dos capas, el aparato documental, la accesibilidad |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | **Cómo** se incorpora un documento nuevo, paso a paso |

> Ojo con el nombre: `docs/` aquí son **especificaciones**. El `docs/` de la raíz
> del repositorio es el **portal publicado**. No son lo mismo.

## Desarrollo

```sh
npm ci
npm run dev      # http://localhost:4321/documentacion/
npm run check    # astro check + build + validación de enlaces
```

`predev` y `prebuild` ejecutan `scripts/sync-portal-assets.mjs`, que copia del
portal la paleta (`docs/assets/css/tokens.css`), los scripts de tema y la imagen
OpenGraph. **Este subproyecto no se compila solo**: necesita el `docs/` de la
raíz. Los destinos de esa copia están en `.gitignore`; editarlos no sirve de
nada, la fuente está en el portal.

Para ver el sitio combinado, con la misma estructura de rutas que produce el
despliegue:

```sh
npm run build && cd .. && docker compose up   # http://localhost:8080/
```

Es la única forma de probar los enlaces cruzados con el portal y las tres
redirecciones.

### Qué valida el build

No hay tests: la garantía es que el build se niega a terminar si algo no cuadra.

- **Zod** (`src/content.config.ts`): esquemas estrictos con enumeraciones cerradas.
- **`src/lib/graph.ts`**: integridad referencial de todo el grafo, invariante
  fichero = identificador, y que ninguna cita apunte a una página que el
  documento no tiene.
- **`src/lib/prose.ts`**: `assertSections` rompe el build si un tema escribe a
  mano una sección que la plantilla genera. Es la garantía contra dos
  cronologías que dentro de seis meses no coinciden.
- **`scripts/check_links.py`**: sobre `dist/`, que ningún enlace interno omita la
  base del sitio y que ninguno apunte a una página inexistente. Nació de un fallo
  real de 1.757 enlaces.

Añadir `LASR_PREVIEW=1` genera además el área de revisión editorial (`/revision/`)
y muestra los identificadores internos. La build pública no la incluye.

## Herramientas del corpus

`scripts/ocr.py`, `scripts/inventory.py` y `scripts/verify_quotes.py` solo hacen
falta para incorporar documentos nuevos; nada de CI los usa.

No tienen dependencias de Python —solo biblioteca estándar—, pero sí necesitan
estos binarios en el `PATH`, todos de **poppler-utils** y **tesseract-ocr**:

```sh
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-spa
```

`inventory.py` cruza la carpeta maestra de originales con el corpus. Esa carpeta
vive fuera del repositorio y cambia según la máquina:

```sh
LASR_MASTER_DIR=/ruta/a/LASR-DOC python3 scripts/inventory.py
```

## Protección de datos

`private-sources/` contiene los PDF originales, que llevan datos personales.
**Nunca se versiona ni se publica**, y está excluido en dos `.gitignore` a
propósito. Antes de cualquier commit:

```sh
git status --short | grep private-sources    # debe salir vacío
```

Ningún documento original se publica en la web. Las fichas explican qué dice cada
uno y en qué página, que es lo que permite comprobar una afirmación sin exponer
el documento.

## Estado editorial

Todo el corpus está en `editorialStatus: draft`. Se publica igualmente, con el
estado a la vista: la trazabilidad ya existe y ocultarlo todo no haría la web más
rigurosa, solo inútil. La promoción a `reviewed` es un acto humano, con el PDF
delante y el checklist de `docs/CONTENT_MODEL.md` §7. Ver `src/lib/policy.ts`,
que es el punto único donde se decide qué se muestra y cómo se etiqueta.
