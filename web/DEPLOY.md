# Portal Los Ángeles de San Rafael - Guía de Despliegue

## 1. Estructura del Proyecto

```
lasr-portal/
├── index.html              # Página principal
├── assets/
│   ├── config.json         # Configuración del sitio
│   ├── content.json        # Contenido del portal
│   ├── css/
│   │   └── styles.css     # Estilos
│   ├── js/
│   │   └── main.js        # Funcionalidad JavaScript
│   └── images/            # Imágenes (opcional)
├── docs/                  # Documentación adicional
└── README.md              # Este archivo
```

## 2. Despliegue en GitHub Pages

### Opción A: Usando Git (Recomendado)

1. **Crear repositorio en GitHub**
   - Ve a https://github.com/new
   - Nombre: `lasr-info` (o el nombre que prefieras)
   - Selecciona "Public"

2. **Subir archivos al repositorio**

```bash
# En tu máquina local
cd ruta/al/proyecto/web

# Inicializar git (si no lo has hecho)
git init

# Añadir todos los archivos
git add .

# Crear commit
git commit -m "Initial commit - Portal LASR"

# Añadir remoto (reemplaza con tu usuario)
git remote add origin https://github.com/TU_USUARIO/lasr-info.git

# Subir a GitHub
git push -u origin main
```

3. **Activar GitHub Pages**

   - Ve a tu repositorio en GitHub
   - Settings → Pages
   - En "Source" selecciona: **Deploy from a branch**
   - En "Branch" selecciona: **main**
   - En "Folder" selecciona: **/(root)**
   - Click en "Save"

4. **Acceder al sitio**

   - GitHub te proporcionará una URL como: `https://TU_USUARIO.github.io/lasr-info/`

### Opción B: Usando GitHub CLI

```bash
# Crear repositorio
gh repo create lasr-info --public --source=. --clone=false

# Subir archivos
git add .
git commit -m "Initial commit"
git push -u origin main

# Configurar GitHub Pages
gh pages-enabled --branch main
```

## 3. Configuración Post-Despliegue

### Actualizar URL en el código

Edita `assets/config.json` y cambia:

```json
"meta": {
    "ogUrl": "https://TU_USUARIO.github.io/lasr-info"
}
```

### Editar meta tags en index.html

Busca y actualiza:

```html
<meta name="description" content="Tu descripción aquí">
<meta property="og:url" content="https://TU_USUARIO.github.io/lasr-info">
```

## 4. Mantenimiento del Contenido

### Añadir nuevo contenido

El contenido se gestiona desde `assets/content.json`. Para actualizar:

1. Abre el archivo en un editor de texto
2. Busca la sección que quieres modificar
3. Edita el texto (mantén el formato JSON)
4. Guarda y haz commit

**Ejemplo - Añadir un nuevo documento:**

```json
{
    "titulo": "Nuevo documento",
    "descripcion": "Descripción del documento",
    "tipo": "prensa",
    "url": "https://enlace.com/documento.pdf",
    "fecha": "2026"
}
```

### Añadir FAQ

En `assets/content.json`, busca la sección `faq.preguntas`:

```json
{
    "pregunta": "¿Tu pregunta aquí?",
    "respuesta": "Tu respuesta aquí."
}
```

## 5. Personalización

### Colores

Edita `assets/config.json`:

```json
"colors": {
    "primary": "#2D5A5A",    // Color principal (verde oscuro)
    "secondary": "#4A7C7C",  // Color secundario
    "accent": "#D4A574"     // Color de acento (dorado)
}
```

### Título y descripción

Edita `assets/config.json`:

```json
"site": {
    "title": "Tu Título",
    "subtitle": "Tu subtítulo",
    "description": "Tu descripción"
}
```

## 6. Solución de Problemas

### El sitio no carga

1. Verifica que GitHub Pages esté habilitado
2. Confirma que el archivo `index.html` está en la raíz
3. Revisa la consola del navegador (F12) para errores

### Los estilos no se cargan

1. Verifica que `assets/css/styles.css` existe
2. Confirma las rutas en el HTML

### El contenido no aparece

1. Abre la consola (F12)
2. Busca errores de red al cargar `content.json`
3. Verifica que el JSON es válido

## 7. Actualizaciones Futuras

### Actualizar contenido existente

```bash
# Descargar cambios
git pull origin main

# Editar archivos
# ...

# Subir cambios
git add .
git commit -m "Actualización de contenido"
git push
```

### Añadir nuevas secciones

1. Añade la estructura HTML en `index.html`
2. Añade el contenido en `content.json`
3. Añade estilos si es necesario en `styles.css`

## 8. Recursos Adicionales

- [GitHub Pages Documentation](https://docs.github.com/es/pages)
- [GitHub CLI](https://cli.github.com/)
- [JSON Validator](https://jsonformatter.org/)

---

**Nota:** Este portal está diseñado para ser fácil de mantener. No requiere conocimientos de programación para actualizar el contenido.
