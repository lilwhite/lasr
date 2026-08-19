/**
 * Grafo de conocimiento de LASR-Web.
 *
 * Carga las siete colecciones, las indexa por su ID canónico (frontmatter `id`,
 * en MAYÚSCULAS) y verifica la integridad referencial COMPLETA en el momento de
 * importar el módulo: cualquier referencia rota hace fallar el build con un
 * mensaje claro. No usamos `reference()` de Astro porque nuestras referencias
 * usan IDs canónicos (no ids de entrada) y `relations.target` es polimórfico.
 */
import { getCollection, type CollectionEntry } from 'astro:content';

export type Kind = 'sources' | 'notes' | 'events' | 'actors' | 'procedures' | 'topics' | 'questions';

export type Source = CollectionEntry<'sources'>;
export type Note = CollectionEntry<'notes'>;
export type Event = CollectionEntry<'events'>;
export type Actor = CollectionEntry<'actors'>;
export type Procedure = CollectionEntry<'procedures'>;
export type Topic = CollectionEntry<'topics'>;
export type Question = CollectionEntry<'questions'>;
export type Entity = Source | Note | Event | Actor | Procedure | Topic | Question;

export const graph = {
  sources: await getCollection('sources'),
  notes: await getCollection('notes'),
  events: await getCollection('events'),
  actors: await getCollection('actors'),
  procedures: await getCollection('procedures'),
  topics: await getCollection('topics'),
  questions: await getCollection('questions'),
} as const;

const kindOf = new Map<string, Kind>();
const byId = new Map<string, Entity>();

for (const kind of Object.keys(graph) as Kind[]) {
  for (const entry of graph[kind]) {
    const id = entry.data.id;
    if (byId.has(id)) throw new Error(`[graph] ID duplicado: ${id}`);
    if (entry.id !== id.toLowerCase()) {
      throw new Error(`[graph] ${id}: el nombre de fichero (${entry.id}) debe ser el ID en minúsculas`);
    }
    byId.set(id, entry);
    kindOf.set(id, kind);
  }
}

/** Resuelve un ID canónico; lanza error (build roto) si no existe. */
export function resolve(id: string): Entity {
  const entry = byId.get(id);
  if (!entry) throw new Error(`[graph] Referencia rota: ${id} no existe en ninguna colección`);
  return entry;
}

export function kind(id: string): Kind {
  resolve(id);
  return kindOf.get(id)!;
}

/* ------------------------------------------------------------------ */
/* Verificación global de integridad: se ejecuta al importar el módulo */
/* ------------------------------------------------------------------ */

function checkAll(owner: string, ids: readonly string[] | undefined, field: string, errors: string[]) {
  for (const id of ids ?? []) {
    if (!byId.has(id)) errors.push(`${owner} → ${field}: referencia rota "${id}"`);
  }
}

type CitationLike = { source: string; pdfPages: number[] };

/**
 * Una cita no puede apuntar a una página que el documento no tiene. Es el
 * fallo típico al transcribir citas desde una caché de OCR: una página en
 * blanco que el volcado omite desplaza toda la numeración posterior, y el
 * error solo se nota al cotejar contra el PDF. Solo se comprueba cuando el
 * Source declara `pages` (es opcional).
 */
function checkPdfPages(
  owner: string,
  citations: readonly CitationLike[] | undefined,
  field: string,
  errors: string[],
) {
  for (const c of citations ?? []) {
    const pages = (byId.get(c.source)?.data as { pages?: number } | undefined)?.pages;
    if (typeof pages !== 'number') continue;
    for (const p of c.pdfPages) {
      if (p > pages) {
        errors.push(`${owner} → ${field}: cita la página ${p} de ${c.source}, que tiene ${pages}`);
      }
    }
  }
}

{
  const errors: string[] = [];
  for (const entry of byId.values()) {
    const d = entry.data as Record<string, unknown> & Entity['data'];
    const owner = d.id;
    checkAll(owner, (d as { topics?: string[] }).topics, 'topics', errors);
    checkAll(owner, (d as { actors?: string[] }).actors, 'actors', errors);
    checkAll(owner, (d as { events?: string[] }).events, 'events', errors);
    checkAll(owner, (d as { answeredBy?: string[] }).answeredBy, 'answeredBy', errors);
    checkAll(owner, (d as { relatedTopics?: string[] }).relatedTopics, 'relatedTopics', errors);
    for (const field of ['procedure', 'parent', 'issuer', 'organ'] as const) {
      const v = (d as Record<string, unknown>)[field];
      if (typeof v === 'string') checkAll(owner, [v], field, errors);
    }
    for (const p of (d as { parties?: { actor: string }[] }).parties ?? []) {
      checkAll(owner, [p.actor], 'parties.actor', errors);
    }
    for (const r of (d as { relations?: { target: string }[] }).relations ?? []) {
      checkAll(owner, [r.target], 'relations.target', errors);
    }
    const citations = (d as { citations?: CitationLike[] }).citations;
    for (const c of citations ?? []) {
      checkAll(owner, [c.source], 'citations.source', errors);
    }
    checkPdfPages(owner, citations, 'citations.pdfPages', errors);
    for (const ev of (d as { dateEvidence?: { citations: CitationLike[] }[] }).dateEvidence ?? []) {
      for (const c of ev.citations) checkAll(owner, [c.source], 'dateEvidence.citations.source', errors);
      checkPdfPages(owner, ev.citations, 'dateEvidence.citations.pdfPages', errors);
    }
  }
  if (errors.length > 0) {
    throw new Error(`[graph] Integridad referencial rota:\n  - ${errors.join('\n  - ')}`);
  }
}

/* -------------------- */
/* Rutas y etiquetas    */
/* -------------------- */

export function slugify(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export const ROUTE_PREFIX: Record<Kind, { base: string; strip: RegExp }> = {
  topics: { base: '/temas', strip: /^TOPIC-/ },
  sources: { base: '/documentos', strip: /^SRC-/ },
  notes: { base: '/notas', strip: /^NOTE-/ },
  events: { base: '/acontecimientos', strip: /^EVENT-/ },
  actors: { base: '/actores', strip: /^ACTOR-/ },
  procedures: { base: '/procedimientos', strip: /^PROC-/ },
  questions: { base: '/preguntas', strip: /^QUESTION-/ },
};

/**
 * Slug de URL de una entidad. Topics y Questions llevan `slug` explícito y
 * estable en su frontmatter (las URLs públicas no dependen del título); el
 * resto lo deriva de su ID estable.
 */
export function entitySlug(entry: Entity): string {
  const k = kindOf.get(entry.data.id)!;
  if (k === 'topics' || k === 'questions') return (entry as Topic | Question).data.slug;
  return entry.data.id.replace(ROUTE_PREFIX[k].strip, '').toLowerCase();
}

/** Ruta de la página de una entidad. */
export function entityRoute(idOrEntry: string | Entity): string {
  const entry = typeof idOrEntry === 'string' ? resolve(idOrEntry) : idOrEntry;
  const k = kindOf.get(entry.data.id)!;
  return `${ROUTE_PREFIX[k].base}/${entitySlug(entry)}/`;
}

/** Etiqueta legible de una entidad para enlaces y listas. */
export function entityLabel(idOrEntry: string | Entity): string {
  const entry = typeof idOrEntry === 'string' ? resolve(idOrEntry) : idOrEntry;
  const d = entry.data as Record<string, unknown>;
  return (d.title ?? d.name ?? d.question ?? d.id) as string;
}

/**
 * Etiqueta corta de un Source para citas: "STSJ CyL 581/2012", "Acta, 2015".
 *
 * El respaldo importa: 19 de los 36 documentos no tienen número de resolución
 * (actas, cartas, convenios, el plan parcial). Devolver el identificador crudo
 * pondría "SRC-1966-PLAN-PARCIAL-CARRASCAL" delante de un vecino.
 */
export function sourceShortLabel(source: Source): string {
  const n = source.data.resolutionNumber;
  if (n && source.data.id.includes('TSJCYL')) return `STSJ CyL ${n}`;
  if (n) return `${DOC_TYPE_SHORT[source.data.docType] ?? source.data.docType} ${n}`;
  const year = source.data.date instanceof Date ? source.data.date.getUTCFullYear() : null;
  const tipo = DOC_TYPE_SHORT[source.data.docType] ?? source.data.docType;
  return year ? `${tipo}, ${year}` : tipo;
}

/** Nombres de tipo documental en la forma en que se leen dentro de una cita. */
const DOC_TYPE_SHORT: Record<string, string> = {
  sentencia: 'Sentencia',
  auto: 'Auto',
  estatutos: 'Estatutos',
  acta: 'Acta',
  convenio: 'Convenio',
  comunicacion: 'Comunicación',
  'resolucion-administrativa': 'Resolución',
  presupuesto: 'Presupuesto',
  circular: 'Circular',
  informe: 'Informe',
  'escrito-de-parte': 'Escrito de parte',
  'instrumento-urbanistico': 'Plan parcial',
};

/** ¿Existe una entidad con ese ID? A diferencia de `resolve`, no lanza. */
export function hasEntity(id: string): boolean {
  return byId.has(id);
}

/**
 * Etiqueta breve para una referencia embebida en la prosa.
 *
 * No sirve `entityLabel`: los títulos de nota miden 205 caracteres de media y
 * los de acontecimiento 88. Dentro de una frase hay que dar la referencia, no
 * el enunciado entero.
 */
export function entityShortLabel(idOrEntry: string | Entity): string {
  const entry = typeof idOrEntry === 'string' ? resolve(idOrEntry) : idOrEntry;
  const k = kindOf.get(entry.data.id)!;
  const d = entry.data as Record<string, any>;
  switch (k) {
    case 'sources':
      return sourceShortLabel(entry as Source);
    case 'events': {
      const e = entry as Event;
      return e.data.date ? formatDate(e.data.date, e.data.datePrecision ?? 'day') : entityLabel(e);
    }
    case 'notes': {
      const first = (d.citations ?? [])[0];
      if (first && byId.has(first.source)) {
        const src = sourceShortLabel(byId.get(first.source) as Source);
        const pg = (first.pdfPages ?? [])[0];
        return pg ? `${src}, pág. ${pg}` : src;
      }
      return 'afirmación documentada';
    }
    case 'actors':
      return d.name as string;
    case 'procedures':
      return d.number as string;
    default:
      return entityLabel(entry);
  }
}

/* ----------------------------- */
/* Consultas del grafo (inversas) */
/* ----------------------------- */

function hasTopic(entry: { data: { topics?: string[] } }, topicId: string): boolean {
  return (entry.data.topics ?? []).includes(topicId);
}

/** Entidades que declaran pertenencia a un topic (pertenencia inversa computada). */
export function topicMembers(topicId: string) {
  resolve(topicId);
  return {
    notes: graph.notes.filter((n) => hasTopic(n, topicId)),
    events: graph.events.filter((e) => hasTopic(e, topicId)),
    sources: graph.sources.filter((s) => hasTopic(s, topicId)),
    actors: graph.actors.filter((a) => hasTopic(a, topicId)),
    procedures: graph.procedures.filter((p) => hasTopic(p, topicId)),
    questions: graph.questions.filter((q) => hasTopic(q, topicId)),
  };
}

/** Notas que citan un Source. */
export function notesCiting(sourceId: string): Note[] {
  resolve(sourceId);
  return graph.notes.filter((n) => n.data.citations.some((c) => c.source === sourceId));
}

/** Eventos que citan un Source (incluida dateEvidence). */
export function eventsCiting(sourceId: string): Event[] {
  resolve(sourceId);
  return graph.events.filter(
    (e) =>
      e.data.citations.some((c) => c.source === sourceId) ||
      e.data.dateEvidence.some((ev) => ev.citations.some((c) => c.source === sourceId)),
  );
}

/** Relaciones inversas: quién apunta a esta entidad vía `relations`. */
export function inverseRelations(id: string): { type: string; from: Entity; note?: string }[] {
  resolve(id);
  const out: { type: string; from: Entity; note?: string }[] = [];
  for (const entry of byId.values()) {
    for (const r of (entry.data as { relations?: { type: string; target: string; note?: string }[] }).relations ?? []) {
      if (r.target === id) out.push({ type: r.type, from: entry, note: r.note });
    }
  }
  return out;
}

export function procedureChildren(procId: string): Procedure[] {
  resolve(procId);
  return graph.procedures.filter((p) => p.data.parent === procId);
}

export function sourcesOfProcedure(procId: string): Source[] {
  resolve(procId);
  return graph.sources.filter((s) => s.data.procedure === procId);
}

export function eventsOfProcedure(procId: string): Event[] {
  resolve(procId);
  return graph.events.filter((e) => e.data.procedure === procId);
}

export function questionsAnsweredBy(noteId: string): Question[] {
  resolve(noteId);
  return graph.questions.filter((q) => q.data.answeredBy.includes(noteId));
}

/* -------------- */
/* Fechas         */
/* -------------- */

/**
 * Clave de ordenación de un evento en la timeline. Para fechas disputadas usa
 * la candidata más temprana: decisión PURAMENTE presentacional (CONTENT_MODEL
 * §3.3), no una afirmación sobre la fecha real.
 */
export function eventSortKey(e: Event): number {
  if (e.data.date) return e.data.date.getTime();
  const candidates = e.data.dateEvidence.map((ev) => ev.value.getTime());
  return candidates.length ? Math.min(...candidates) : Number.MAX_SAFE_INTEGER;
}

const dateFmt = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
const monthFmt = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric', timeZone: 'UTC' });

export function formatDate(date: Date, precision: 'day' | 'month' | 'year' = 'day'): string {
  if (precision === 'year') return String(date.getUTCFullYear());
  if (precision === 'month') return monthFmt.format(date);
  return dateFmt.format(date);
}

/** Texto de fecha de un evento, honrando dateStatus. */
export function eventDateText(e: Event): string {
  if (e.data.date) return formatDate(e.data.date, e.data.datePrecision ?? 'day');
  if (e.data.dateStatus === 'disputed') {
    const candidates = e.data.dateEvidence.map((ev) => formatDate(ev.value));
    return candidates.join(' o ');
  }
  return 'Fecha sin documentar';
}

/* ------------------------------------------------------------------ */
/* Unicidad de slugs de URL (se ejecuta al final del módulo, cuando   */
/* entitySlug ya está disponible): colisión → build roto.             */
/* ------------------------------------------------------------------ */
{
  const errors: string[] = [];
  for (const k of Object.keys(graph) as Kind[]) {
    const seen = new Map<string, string>();
    for (const entry of graph[k]) {
      const slug = entitySlug(entry);
      const prev = seen.get(slug);
      if (prev) errors.push(`Slug duplicado en ${k}: "${slug}" (${prev} y ${entry.data.id})`);
      seen.set(slug, entry.data.id);
    }
  }
  if (errors.length > 0) {
    throw new Error(`[graph] Slugs de URL en conflicto:\n  - ${errors.join('\n  - ')}`);
  }
}

/** Notas en orden estable por ID (para revisión secuencial). */
export function notesOrdered(): Note[] {
  return [...graph.notes].sort((a, b) => a.data.id.localeCompare(b.data.id));
}

/* --------------------------------------------- */
/* Consultas derivadas para la capa de presentación */
/* --------------------------------------------- */

/** Afirmaciones que sitúan un acontecimiento. Se hacía a mano en la plantilla. */
export function notesOfEvent(eventId: string): Note[] {
  return graph.notes.filter((n) => n.data.events.includes(eventId));
}

/** Todo lo que menciona a un actor, agrupado. Se hacía a mano en la plantilla. */
export function actorMentions(actorId: string) {
  const inParties = (d: { parties?: { actor: string }[] }) =>
    (d.parties ?? []).some((p) => p.actor === actorId);
  return {
    notes: graph.notes.filter((n) => n.data.actors.includes(actorId)),
    events: graph.events.filter((e) => e.data.actors.includes(actorId)),
    sources: graph.sources.filter((s) => s.data.issuer === actorId || inParties(s.data)),
    procedures: graph.procedures.filter((p) => p.data.organ === actorId || inParties(p.data)),
  };
}

/**
 * Actores de un tema, derivados de sus miembros cuando el etiquetado no los
 * declara. `TOPIC-EUC` tiene 25 afirmaciones y ningún actor etiquetado: sin
 * este respaldo su página mostraría un encabezado sobre el vacío.
 */
export function topicActorsDerived(topicId: string): Actor[] {
  const m = topicMembers(topicId);
  const ids = new Set<string>();
  for (const n of m.notes) n.data.actors.forEach((a) => ids.add(a));
  for (const e of m.events) e.data.actors.forEach((a) => ids.add(a));
  for (const s of m.sources) {
    ids.add(s.data.issuer);
    (s.data.parties ?? []).forEach((p) => ids.add(p.actor));
  }
  return graph.actors.filter((a) => ids.has(a.data.id));
}

/** Procedimientos de un tema, derivados de sus miembros. Mismo motivo. */
export function topicProceduresDerived(topicId: string): Procedure[] {
  const m = topicMembers(topicId);
  const ids = new Set<string>();
  for (const e of m.events) if (e.data.procedure) ids.add(e.data.procedure);
  for (const s of m.sources) if (s.data.procedure) ids.add(s.data.procedure);
  // Arrastra los ascendientes, para que el árbol tenga raíz.
  for (const id of [...ids]) {
    let cur = byId.get(id) as Procedure | undefined;
    while (cur?.data.parent) {
      ids.add(cur.data.parent);
      cur = byId.get(cur.data.parent) as Procedure | undefined;
    }
  }
  return graph.procedures.filter((p) => ids.has(p.data.id));
}

/** Documentos de un tema ordenados por cuántas afirmaciones los citan. */
export function topicSourcesRanked(topicId: string): { source: Source; noteCount: number }[] {
  return topicMembers(topicId)
    .sources.map((source) => ({ source, noteCount: notesCiting(source.data.id).length }))
    .sort((a, b) => b.noteCount - a.noteCount);
}
