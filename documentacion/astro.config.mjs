// @ts-check
import { defineConfig } from 'astro/config';

/**
 * Generación estática para GitHub Pages (página de proyecto).
 *
 * El sitio se sirve bajo un subdirectorio, así que `base` no es opcional: sin
 * él todos los enlaces internos apuntarían a la raíz del dominio de usuario.
 * Ambos valores se pueden fijar por entorno para no tocar código al desplegar:
 *
 *     SITE=https://miusuario.github.io BASE=/lasr npm run build
 *
 * `trailingSlash: 'always'` casa con las rutas que emite `entityRoute()` y hace
 * que una ruta sin barra final falle en desarrollo, no en producción.
 */
export default defineConfig({
  output: 'static',
  site: process.env.SITE ?? 'https://mblancop.github.io',
  base: process.env.BASE ?? '/lasr',
  trailingSlash: 'always',
  build: { format: 'directory' },
});
