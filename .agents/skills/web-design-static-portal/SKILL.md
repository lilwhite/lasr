# web-design-static-portal

## Purpose

Aplicar buenas prácticas de diseño web sobre el portal estático en `docs/`. Mantener coherencia visual, accesibilidad básica y legibilidad.

## When to Use

- Cambios en HTML, CSS o JavaScript del portal
- Modificaciones en la UI o experiencia de usuario
- Mejoras de accesibilidad o responsive
- Revisiones de diseño

## Scope

- `docs/index.html`
- `docs/assets/css/styles.css`
- `docs/assets/js/main.js`

## Input / Target Files

- HTML principal: `docs/index.html`
- Estilos: `docs/assets/css/styles.css`
- Scripts: `docs/assets/js/main.js`
- Configuración: `docs/assets/config.json`
- Contenido: `docs/assets/content.json`

## Rules

1. Mantener un solo `h1` en la página principal
2. Usar headings ordenados jerárquicamente (`h1` → `h2` → `h3`)
3. Centralizar estilos en `docs/assets/css/styles.css`
4. Centralizar scripts en `docs/assets/js/main.js`
5. Evitar inline styles y scripts inline salvo necesidad justificada
6. Usar clases CSS en lugar de selectores complejos
7. Priorizar diseño responsive con media queries
8. Mantener contraste suficiente (mínimo 4.5:1 para texto)
9. Usar HTML semántico (nav, main, section, article, footer)
10. Incluir atributos alt en imágenes

## Checklist

- [ ] Solo un `h1` en `docs/index.html`
- [ ] Headings bien ordenados
- [ ] Navegación visible y accesible
- [ ] Estilos centralizados en un archivo
- [ ] Scripts centralizados en un archivo
- [ ] Sin inline styles salvo necesidad
- [ ] Diseño responsive funcional
- [ ] Contraste adecuado
- [ ] HTML semántico correcto
- [ ] Rutas relativas preservadas

## Expected Output

- Portal visualmente coherente
- Navegación clara
- Responsive en móvil y desktop
- Accesibilidad básica cumplida

## What NOT to Do

- No mover carpetas innecesariamente
- No introducir frameworks (React, Vue, Next, etc.)
- No usar bundlers (Vite, Webpack, etc.) sin justificación
- No cambiar rutas relativas de assets
- No duplicar estilos en múltiples archivos CSS
- No usar JavaScript inline en HTML
- No romper la navegación existente
