/**
 * Disposición del mapa documental (`/documentos/mapa/`).
 *
 * Todo lo que se dibuja sale del grafo: no hay una sola coordenada escrita a
 * mano. Tres decisiones de forma conviene entenderlas antes de tocar nada.
 *
 *  1. **El eje de tiempo tiene saltos declarados.** El corpus va de 1966 a
 *     2026, pero 34 de los 36 documentos caen entre 2002 y 2026. A escala
 *     lineal, dos tercios del ancho serían desierto. Los tramos de dos o más
 *     años consecutivos sin ningún documento se comprimen a un hueco fijo y se
 *     marcan con un corte visible: la escala se salta el vacío, pero lo dice.
 *
 *  2. **Cada procedimiento es un carril.** Es la única estructura densa que
 *     existe en el corpus: 21 de los 36 documentos pertenecen a un
 *     procedimiento y casi todas las relaciones declaradas —confirma, anula,
 *     resuelve el recurso, ejecuta— son internas a uno. Los 15 restantes van a
 *     una banda propia; que se vea que no encajan en ninguna cadena es
 *     información, no un defecto de la figura.
 *
 *  3. **Solo se dibujan relaciones declaradas.** Son 20. No se inventan
 *     aristas por coincidencia de tema, de emisor ni de año: dos documentos
 *     del mismo tema no están relacionados entre sí, y una línea diría que sí.
 */
import {
  graph, entityRoute, sourceShortLabel, notesCiting, formatDate,
  type Source, type Procedure,
} from './graph';

/* --------------------------------------------------------------- */
/* Geometría                                                        */
/* --------------------------------------------------------------- */

const YEAR_W = 62;       // ancho de un año con documentos
const GAP_W = 26;        // ancho de un tramo comprimido, sea de 3 años o de 29
const PAD_X = 14;
const ROW_H = 26;        // alto de una subfila dentro de un carril
const LANE_HEAD = 24;    // línea del título del carril
const LANE_FOOT = 10;
const AXIS_H = 30;
const CHAR_W = 6.3;      // ancho medio de la monoespaciada a 10.5px
const MARKER_GAP = 13;   // del centro del marcador al inicio de la etiqueta

/** Desplazamiento de la etiqueta respecto al marcador, para quien dibuja. */
export const LABEL_DX = MARKER_GAP;

export interface DocNode {
  id: string;
  label: string;
  title: string;
  docType: string;
  family: 'judicial' | 'parte' | 'otro';
  date: Date;
  dateText: string;
  noteCount: number;
  href: string;
  x: number;
  y: number;
  r: number;
  /** Ancho de la etiqueta, para que el consumidor no reimplemente la métrica. */
  labelWidth: number;
}

export interface DocEdge {
  type: string;
  label: string;
  from: DocNode;
  to: DocNode;
  /** Trazado ya resuelto: curva si salta de carril, arco bajo si es del mismo. */
  path: string;
}

export interface DocLane {
  key: string;
  kind: 'procedure' | 'loose';
  /** Identificador corto: número del procedimiento, o vacío en la banda suelta. */
  tag: string;
  title: string;
  href?: string;
  depth: number;
  y: number;
  height: number;
  rows: number;
  nodes: DocNode[];
}

export interface DocMap {
  lanes: DocLane[];
  edges: DocEdge[];
  ticks: { year: number; x: number; labelX: number }[];
  breaks: { x: number; years: number }[];
  width: number;
  height: number;
  axisY: number;
  /** Recuentos para el texto de la página: ni uno se escribe a mano. */
  totals: { sources: number; inProcedure: number; loose: number; edges: number; isolated: number };
}

/* --------------------------------------------------------------- */
/* Etiquetas                                                        */
/* --------------------------------------------------------------- */

const MESES = ['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.',
  'jul.', 'ago.', 'sep.', 'oct.', 'nov.', 'dic.'];

/**
 * Etiqueta de nodo. Parte de `sourceShortLabel`, pero ahí hay colisiones: dos
 * comunicaciones de 2013 se llamarían las dos "Comunicación, 2013". Cuando la
 * etiqueta corta no distingue, se le añade el mes. No se recorta ni se inventa
 * nada: el título completo va en el `<title>` del nodo y en la lista de abajo.
 */
function buildLabels(sources: Source[]): Map<string, string> {
  const short = new Map<string, string>();
  const count = new Map<string, number>();
  for (const s of sources) {
    const l = sourceShortLabel(s);
    short.set(s.data.id, l);
    count.set(l, (count.get(l) ?? 0) + 1);
  }
  const out = new Map<string, string>();
  for (const s of sources) {
    const l = short.get(s.data.id)!;
    out.set(s.data.id, (count.get(l) ?? 0) > 1
      ? l.replace(/, (\d{4})$/, `, ${MESES[s.data.date.getUTCMonth()]} $1`)
      : l);
  }
  return out;
}

const JUDICIAL = new Set(['sentencia', 'auto', 'resolucion-administrativa']);
const PARTE = new Set(['escrito-de-parte', 'comunicacion', 'circular']);

function familyOf(docType: string): DocNode['family'] {
  if (JUDICIAL.has(docType)) return 'judicial';
  if (PARTE.has(docType)) return 'parte';
  return 'otro';
}

/* --------------------------------------------------------------- */
/* Escala de tiempo                                                 */
/* --------------------------------------------------------------- */

interface Scale {
  x(date: Date): number;
  ticks: { year: number; x: number; labelX: number }[];
  breaks: { x: number; years: number }[];
  end: number;
}

function buildScale(years: Set<number>): Scale {
  const min = Math.min(...years);
  const max = Math.max(...years);
  const start = new Map<number, number>();
  const ticks: { year: number; x: number; labelX: number }[] = [];
  const breaks: { x: number; years: number }[] = [];
  let cursor = PAD_X;

  for (let year = min; year <= max;) {
    if (years.has(year)) {
      start.set(year, cursor);
      ticks.push({ year, x: cursor, labelX: cursor + YEAR_W / 2 });
      cursor += YEAR_W;
      year += 1;
      continue;
    }
    let end = year;
    while (end <= max && !years.has(end)) end += 1;
    const empty = end - year;
    if (empty === 1) {
      // Un solo año en blanco se dibuja: cortar ahí sería ruido, no información.
      start.set(year, cursor);
      ticks.push({ year, x: cursor, labelX: cursor + YEAR_W / 2 });
      cursor += YEAR_W;
    } else {
      breaks.push({ x: cursor + GAP_W / 2, years: empty });
      cursor += GAP_W;
    }
    year = end;
  }

  return {
    x(date: Date): number {
      const y = date.getUTCFullYear();
      const s = start.get(y);
      if (s === undefined) throw new Error(`[docmap] año fuera de escala: ${y}`);
      const jan = Date.UTC(y, 0, 1);
      const next = Date.UTC(y + 1, 0, 1);
      return s + ((date.getTime() - jan) / (next - jan)) * YEAR_W;
    },
    ticks,
    breaks,
    end: cursor,
  };
}

/* --------------------------------------------------------------- */
/* Construcción                                                     */
/* --------------------------------------------------------------- */

function firstDate(sources: Source[]): number {
  return Math.min(...sources.map((s) => s.data.date.getTime()));
}

/** Procedimientos con documentos, cada hijo inmediatamente bajo su padre. */
function orderProcedures(sources: Source[]): { proc: Procedure; depth: number; sources: Source[] }[] {
  const withDocs = new Map<string, Source[]>();
  for (const s of sources) {
    const p = s.data.procedure;
    if (!p) continue;
    const list = withDocs.get(p);
    if (list) list.push(s); else withDocs.set(p, [s]);
  }
  const out: { proc: Procedure; depth: number; sources: Source[] }[] = [];

  const emit = (proc: Procedure, depth: number): void => {
    const own = withDocs.get(proc.data.id);
    if (own) out.push({ proc, depth, sources: [...own].sort((a, b) => a.data.date.getTime() - b.data.date.getTime()) });
    const kids = graph.procedures
      .filter((p) => p.data.parent === proc.data.id && withDocs.has(p.data.id))
      .sort((a, b) => firstDate(withDocs.get(a.data.id)!) - firstDate(withDocs.get(b.data.id)!));
    for (const k of kids) emit(k, own ? depth + 1 : depth);
  };

  graph.procedures
    .filter((p) => p.data.parent === null && withDocs.has(p.data.id))
    .sort((a, b) => firstDate(withDocs.get(a.data.id)!) - firstDate(withDocs.get(b.data.id)!))
    .forEach((p) => emit(p, 0));

  return out;
}

/** Reparte los nodos de un carril en subfilas para que las etiquetas no choquen. */
function assignRows(nodes: DocNode[]): number {
  const occupied: number[] = [];
  for (const n of [...nodes].sort((a, b) => a.x - b.x)) {
    let row = occupied.findIndex((right) => right <= n.x - MARKER_GAP);
    if (row === -1) { row = occupied.length; occupied.push(0); }
    occupied[row] = n.x + MARKER_GAP + n.labelWidth + 8;
    n.y = row;   // provisional: índice de fila; se convierte en píxeles después
  }
  return occupied.length;
}

/** Título corto del carril: número del procedimiento + su descripción. */
function laneTitle(proc: Procedure): string {
  const dash = proc.data.title.indexOf('—');
  return dash === -1 ? proc.data.title : proc.data.title.slice(dash + 1).trim();
}

/**
 * @param sources documentos a dibujar. Por defecto todos, pero las páginas
 * pasan los publicables: dibujar un nodo cuya ficha no existe deja un enlace
 * al vacío, y el mapa dejaría de coincidir con el sitio.
 */
export function buildDocMap(sources: Source[] = graph.sources): DocMap {
  const labels = buildLabels(sources);

  const toNode = (s: Source): DocNode => {
    const label = labels.get(s.data.id)!;
    const n = notesCiting(s.data.id).length;
    return {
      id: s.data.id,
      label,
      title: s.data.title,
      docType: s.data.docType,
      family: familyOf(s.data.docType),
      date: s.data.date,
      dateText: formatDate(s.data.date, 'day'),
      noteCount: n,
      href: entityRoute(s),
      x: 0,
      y: 0,
      r: 4 + (Math.min(n, 13) / 13) * 4,
      labelWidth: label.length * CHAR_W,
    };
  };

  const scale = buildScale(new Set(sources.map((s) => s.data.date.getUTCFullYear())));

  const lanes: DocLane[] = [];
  for (const { proc, depth, sources: docsDelProc } of orderProcedures(sources)) {
    lanes.push({
      key: proc.data.id,
      kind: 'procedure',
      tag: proc.data.number,
      title: laneTitle(proc),
      href: entityRoute(proc),
      depth,
      y: 0,
      height: 0,
      rows: 0,
      nodes: docsDelProc.map(toNode),
    });
  }

  const loose = sources
    .filter((s) => !s.data.procedure)
    .sort((a, b) => a.data.date.getTime() - b.data.date.getTime());
  lanes.push({
    key: 'sin-procedimiento',
    kind: 'loose',
    tag: '',
    title: 'Fuera de todo procedimiento judicial',
    depth: 0,
    y: 0,
    height: 0,
    rows: 0,
    nodes: loose.map(toNode),
  });

  // Posiciones: primero x (tiempo), luego subfila, luego y absoluta.
  let cursorY = AXIS_H;
  for (const lane of lanes) {
    for (const n of lane.nodes) n.x = scale.x(n.date);
    lane.rows = assignRows(lane.nodes);
    lane.y = cursorY;
    lane.height = LANE_HEAD + lane.rows * ROW_H + LANE_FOOT;
    for (const n of lane.nodes) n.y = lane.y + LANE_HEAD + n.y * ROW_H + ROW_H / 2;
    cursorY += lane.height;
  }

  const byId = new Map<string, DocNode>();
  for (const lane of lanes) for (const n of lane.nodes) byId.set(n.id, n);

  const edges: DocEdge[] = [];
  for (const s of sources) {
    for (const r of s.data.relations) {
      const from = byId.get(s.data.id);
      const to = byId.get(r.target);
      if (!from || !to) continue;   // relaciones a notas o acontecimientos: no son de este mapa
      edges.push({
        type: r.type,
        label: RELATION_SHORT[r.type] ?? r.type,
        from,
        to,
        path: edgePath(from, to),
      });
    }
  }

  const width = Math.max(
    scale.end + PAD_X,
    ...[...byId.values()].map((n) => n.x + MARKER_GAP + n.labelWidth + PAD_X),
  );

  const related = new Set<string>();
  for (const e of edges) { related.add(e.from.id); related.add(e.to.id); }

  return {
    lanes,
    edges,
    ticks: scale.ticks,
    breaks: scale.breaks,
    width: Math.round(width),
    height: Math.round(cursorY + 8),
    axisY: AXIS_H - 10,
    totals: {
      sources: sources.length,
      inProcedure: sources.length - loose.length,
      loose: loose.length,
      edges: edges.length,
      isolated: sources.length - related.size,
    },
  };
}

/** Verbo corto para la arista; el largo (RELATION_LABEL) se usa en la lista. */
export const RELATION_SHORT: Record<string, string> = {
  cites: 'cita',
  confirms: 'confirma',
  annuls: 'anula',
  modifies: 'modifica',
  appeals: 'resuelve el recurso',
  executes: 'ejecuta',
  supersedes: 'sustituye',
  supports: 'apoya',
  contradicts: 'contradice',
  'related-to': 'relacionado',
};

/**
 * Trazado de una arista. Dentro del mismo carril la curva se arquea por debajo
 * para no taparlo; entre carriles distintos es una curva suave en S.
 */
function edgePath(a: DocNode, b: DocNode): string {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  if (Math.abs(dy) < 1) {
    const lift = Math.min(14, Math.max(7, Math.abs(dx) / 6));
    return `M ${a.x} ${a.y} Q ${(a.x + b.x) / 2} ${a.y + lift} ${b.x} ${b.y}`;
  }
  const c = Math.abs(dy) / 2;
  // Si los dos documentos caen casi en la misma vertical, la curva sin panza se
  // confundiría con una regla que parte la figura en dos. Se le da bombo.
  const lateral = Math.abs(dx) > 160
    ? dx * 0.12
    : (dx === 0 ? 1 : Math.sign(dx)) * Math.max(26, Math.abs(dy) * 0.16);
  return `M ${a.x} ${a.y} C ${a.x + lateral} ${a.y + Math.sign(dy) * c} ${b.x - lateral} ${b.y - Math.sign(dy) * c} ${b.x} ${b.y}`;
}
