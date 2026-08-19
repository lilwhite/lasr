/**
 * Post-proceso de los cuerpos Markdown ya renderizados.
 *
 * Astro persiste en el store el HTML de cada entrada (`entry.rendered.html`) y
 * la lista de sus encabezados. Trabajar sobre ese HTML —y no con un plugin de
 * Markdown— es lo que permite resolver identificadores contra el grafo: un
 * plugin remark/rehype no puede importar `astro:content`.
 *
 * Hace dos cosas:
 *   1. Convierte las referencias `ENTITY-ID` que la prosa escribe entre
 *      backticks en enlaces reales. Hoy son 327 en el corpus y se renderizan
 *      como código gris muerto.
 *   2. Parte el cuerpo por encabezados de nivel 2, para que la plantilla decida
 *      dónde coloca cada sección, y verifica que el cuerpo no contenga
 *      secciones que la plantilla genera desde el grafo.
 */

import { entityRoute, entityShortLabel, hasEntity, type Entity } from './graph';
import { url } from './url';

const ENTITY_CODE = /<code>((?:SRC|NOTE|EVENT|ACTOR|PROC|TOPIC|QUESTION)-[A-Z0-9-]+)<\/code>/g;

/** `<code>NOTE-…</code>` → enlace con etiqueta legible para un lector. */
export function linkify(html: string): string {
  return html.replace(ENTITY_CODE, (whole, id: string) => {
    if (!hasEntity(id)) return whole; // referencia desconocida: se deja tal cual
    const href = url(entityRoute(id));
    const label = entityShortLabel(id);
    return `<a class="ref" href="${href}" data-id="${id}" title="${id}">${label}</a>`;
  });
}

function rendered(entry: Entity): string {
  return (entry as unknown as { rendered?: { html?: string } }).rendered?.html ?? '';
}

function headings(entry: Entity): { depth: number; text: string; slug: string }[] {
  const meta = (entry as unknown as {
    rendered?: { metadata?: { headings?: { depth: number; text: string; slug: string }[] } };
  }).rendered?.metadata;
  return meta?.headings ?? [];
}

/** Cuerpo completo, con las referencias ya enlazadas. */
export function proseHtml(entry: Entity): string {
  return linkify(rendered(entry));
}

/**
 * Parte el cuerpo por sus `<h2>`. Devuelve un mapa `título de sección → HTML`
 * sin el propio encabezado, más la clave `''` con el texto anterior al primero.
 */
export function sections(entry: Entity): Map<string, string> {
  const html = proseHtml(entry);
  const out = new Map<string, string>();
  const h2 = headings(entry).filter((h) => h.depth === 2);
  if (h2.length === 0) {
    if (html.trim()) out.set('', html);
    return out;
  }
  // Los encabezados llevan id: partimos por la etiqueta de apertura de cada uno.
  const marks = h2.map((h) => ({ text: h.text, at: html.indexOf(`<h2 id="${h.slug}"`) }))
    .filter((m) => m.at >= 0);
  if (marks.length === 0) {
    if (html.trim()) out.set('', html);
    return out;
  }
  const intro = html.slice(0, marks[0].at).trim();
  if (intro) out.set('', intro);
  marks.forEach((m, i) => {
    const start = html.indexOf('</h2>', m.at) + '</h2>'.length;
    const end = i + 1 < marks.length ? marks[i + 1].at : html.length;
    out.set(m.text, html.slice(start, end).trim());
  });
  return out;
}

/**
 * Verifica que el cuerpo solo contenga secciones editoriales. Las que la
 * plantilla deriva del grafo —cronología, fuentes, actores, preguntas— no
 * pueden escribirse a mano: si conviven las dos versiones, dentro de unos meses
 * no coinciden. Romper el build es la única garantía de que no vuelva a pasar.
 */
export function assertSections(entry: Entity, allowed: readonly string[]): void {
  const found = headings(entry).filter((h) => h.depth === 2).map((h) => h.text);
  const stray = found.filter((t) => !allowed.includes(t));
  if (stray.length > 0) {
    throw new Error(
      `[prose] ${entry.id}: sección no permitida en el cuerpo: ${stray.map((s) => `"${s}"`).join(', ')}.\n` +
        `  Secciones editoriales permitidas: ${allowed.map((s) => `"${s}"`).join(', ')}.\n` +
        `  El resto las genera la plantilla desde el grafo (docs/WEB_DESIGN.md §5).`,
    );
  }
}

/** Secciones que un tema puede escribir a mano. Ver docs/WEB_DESIGN.md §5. */
export const TOPIC_SECTIONS = [
  'En 30 segundos',
  'Por qué importa',
  'Situación documentada',
  'Qué está en discusión',
] as const;
