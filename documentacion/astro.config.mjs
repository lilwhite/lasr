// @ts-check
import { defineConfig } from 'astro/config';

/**
 * Generación estática para GitHub Pages, bajo el dominio propio del portal.
 *
 * La capa documental se sirve bajo `/documentacion/` del portal vecinal, así que
 * `base` no es opcional: sin él todos los enlaces internos apuntarían a la raíz
 * del dominio. Ambos valores se pueden fijar por entorno para previsualizar en
 * otra ubicación sin tocar código:
 *
 *     SITE=https://ejemplo.test BASE=/otra-ruta npm run build
 *
 * Si se cambian por entorno, `scripts/check_links.py` lee la misma variable, de
 * modo que build y validación no pueden divergir.
 *
 * `trailingSlash: 'always'` casa con las rutas que emite `entityRoute()` y hace
 * que una ruta sin barra final falle en desarrollo, no en producción.
 */
export default defineConfig({
  output: 'static',
  site: process.env.SITE ?? 'https://lasr-info.es',
  base: process.env.BASE ?? '/documentacion',
  trailingSlash: 'always',
  build: { format: 'directory' },
});
