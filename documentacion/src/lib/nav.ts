/**
 * Mapa único de las secciones del sitio. El menú, el pie, las migas de pan y
 * el sitemap salen todos de aquí: ningún `href` interno se escribe a mano.
 */

export interface NavItem {
  /** Ruta canónica relativa al sitio, sin base. */
  path: string;
  label: string;
  /** Descripción corta para índices y `<meta name="description">` por defecto. */
  blurb?: string;
}

/** Menú principal. Seis entradas: caben en dos líneas a 320 px sin hamburguesa. */
export const NAV: NavItem[] = [
  { path: '/', label: 'Inicio' },
  { path: '/temas/', label: 'Temas', blurb: 'Los grandes asuntos, explicados y documentados.' },
  { path: '/cronologia/', label: 'Cronología', blurb: 'Qué ha pasado, en orden, desde 1966.' },
  { path: '/preguntas/', label: 'Preguntas', blurb: 'Respuestas breves con su fundamento documental.' },
  { path: '/documentos/', label: 'Documentos', blurb: 'Las fuentes originales, ficha a ficha.' },
  { path: '/metodologia/', label: 'Metodología', blurb: 'Cómo se selecciona, extrae y verifica la información.' },
];

/** Enlaces secundarios: viven en el pie y en el cuerpo, no en el menú. */
export const FOOTER_NAV: NavItem[] = [
  { path: '/historia/', label: 'Historia del núcleo' },
  { path: '/documentos/mapa/', label: 'Mapa documental' },
  { path: '/actores/', label: 'Quién es quién' },
  { path: '/procedimientos/', label: 'Procedimientos judiciales' },
  { path: '/notas/', label: 'Todas las afirmaciones' },
  { path: '/aviso-legal/', label: 'Aviso legal y protección de datos' },
];

/** Rutas fijas que el sitemap debe incluir además de las de entidad. */
export const STATIC_ROUTES: string[] = [
  ...NAV.map((n) => n.path),
  ...FOOTER_NAV.map((n) => n.path),
];
