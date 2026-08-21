/**
 * Construcción de URL. Punto ÚNICO donde se aplica la base del sitio.
 *
 * El sitio vive bajo un subdirectorio de GitHub Pages, de modo que ningún
 * `href` interno puede escribirse a mano: `npm run check` falla si aparece uno.
 * `entityRoute()` sigue devolviendo la ruta canónica relativa al sitio —que es
 * la que necesitan el canonical y el sitemap— y la base se aplica aquí, en el
 * borde de renderizado.
 */

const BASE = import.meta.env.BASE_URL ?? '/';

/** Ruta absoluta lista para un `href`, con base aplicada y barra final. */
export function url(path: string): string {
  if (/^(https?:)?\/\//.test(path) || path.startsWith('#') || path.startsWith('mailto:')) {
    return path;
  }
  const joined = `${BASE}/${path}`.replace(/\/{2,}/g, '/');
  // Los ficheros (con extensión) no llevan barra final; las páginas, sí.
  const isFile = /\.[a-z0-9]{2,5}$/i.test(joined);
  return isFile ? joined : joined.replace(/\/?$/, '/');
}

/** URL absoluta, para canonical, OpenGraph y sitemap. */
export function canonicalURL(path: string, site: URL | undefined): string {
  return new URL(url(path), site ?? 'https://example.invalid').href;
}

/** ¿Es `path` la página actual? Tolera la barra final y la base. */
export function isCurrent(path: string, pathname: string): boolean {
  const norm = (s: string) => s.replace(/\/+$/, '') || '/';
  return norm(url(path)) === norm(pathname);
}
