/**
 * Sitemap generado desde el grafo, no escrito a mano.
 *
 * `docs/WEB_DESIGN.md` §12 lo daba por hecho y no existía. Se construye con las
 * mismas dos fuentes que la navegación —`STATIC_ROUTES` para las páginas fijas y
 * `entityRoute()` para las entidades—, así que una entidad nueva entra sola y
 * una ruta renombrada no puede quedarse aquí desactualizada.
 *
 * Solo cubre la guía documental. Las páginas del portal viven fuera de este
 * build y tienen su propio `docs/sitemap.xml`.
 */
import type { APIRoute } from 'astro';
import { graph, entityRoute, type Entity } from '../lib/graph';
import { STATIC_ROUTES } from '../lib/nav';
import { visibleOnly } from '../lib/policy';
import { canonicalURL } from '../lib/url';

export const GET: APIRoute = ({ site }) => {
  const entidades: Entity[] = [
    ...graph.topics,
    ...graph.questions,
    ...graph.sources,
    ...graph.notes,
    ...graph.events,
    ...graph.procedures,
    ...graph.actors,
  ];

  // Set: `/cronologia/` es a la vez ruta fija e índice de acontecimientos, y no
  // debe aparecer dos veces.
  const rutas = new Set<string>([
    ...STATIC_ROUTES,
    ...visibleOnly(entidades).map((e) => entityRoute(e)),
  ]);

  const urls = [...rutas]
    .sort()
    .map((ruta) => `  <url><loc>${canonicalURL(ruta, site)}</loc></url>`)
    .join('\n');

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } },
  );
};
