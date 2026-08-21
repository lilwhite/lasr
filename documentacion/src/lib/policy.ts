/**
 * Política editorial y de privacidad de LASR-Web. ÚNICA fuente de verdad sobre
 * qué contenido puede mostrarse y cómo debe etiquetarse. Ningún componente ni
 * página debe reimplementar estas reglas.
 */
import { graph, type Entity, type Source } from './graph';

/**
 * Modo editorial: en `astro dev` siempre; en build solo con LASR_PREVIEW=1.
 * Ya no gobierna qué se publica —eso lo decide `isVisible`—, sino qué
 * metadatería interna se enseña: identificadores canónicos, hashes, estados
 * técnicos y el área de revisión.
 */
export const PREVIEW: boolean = import.meta.env.DEV || process.env.LASR_PREVIEW === '1';

type Editorial = 'draft' | 'reviewed' | 'verified';
type Evidence = 'unassessed' | 'consistent' | 'disputed' | 'incomplete';

/**
 * Visibilidad pública.
 *
 * Hasta ahora ocultaba todo lo que estuviera en borrador, y como el corpus
 * entero lo está, el sitio público generaba 26 páginas de 433: un esqueleto.
 * La decisión editorial es publicar el borrador **con el estado a la vista**,
 * porque la trazabilidad ya existe y ocultarlo todo no hace la web más
 * rigurosa, solo inútil.
 *
 * Se conserva como punto único de estrangulamiento: si algún día hay que
 * excluir una entrada concreta, se hace aquí y en ningún otro sitio.
 */
export function isVisible(_entry: Entity): boolean {
  return true;
}

/** Filtra por visibilidad. Hoy identidad; ver `isVisible`. */
export function visibleOnly<T extends Entity>(entries: T[]): T[] {
  return entries.filter(isVisible);
}

export function canLinkPdf(source: Source): boolean {
  return (
    source.data.publicationStatus === 'public' &&
    source.data.privacyReview.status === 'approved'
  );
}

/* ------------------------------------------------------------------ */
/* Etiquetas de estado: el texto vive aquí, nunca escrito a mano en    */
/* páginas o componentes.                                              */
/* ------------------------------------------------------------------ */

export const EDITORIAL_LABEL: Record<Editorial, string> = {
  draft: 'Borrador — pendiente de revisión documental',
  reviewed: 'Revisado contra el documento',
  verified: 'Verificado',
};

export const EVIDENCE_LABEL: Record<Evidence, string> = {
  unassessed: 'Evidencia sin evaluar',
  consistent: 'Evidencia consistente',
  disputed: 'Evidencia controvertida — las fuentes discrepan',
  incomplete: 'Evidencia incompleta',
};

export const BASIS_LABEL: Record<string, string> = {
  documented: 'Documentado',
  inferred: 'Inferido — no consta literalmente en la documentación',
  interpretation: 'Interpretación editorial',
  unknown: 'Sin documentar',
};

export const NOTE_TYPE_LABEL: Record<string, string> = {
  fact: 'Hecho',
  ruling: 'Pronunciamiento',
  obligation: 'Obligación',
  agreement: 'Acuerdo',
  'legal-principle': 'Criterio jurídico',
  claim: 'Alegación de parte',
};

export const DOC_TYPE_LABEL: Record<string, string> = {
  sentencia: 'Sentencia',
  auto: 'Auto',
  estatutos: 'Estatutos',
  acta: 'Acta',
  convenio: 'Convenio',
  comunicacion: 'Comunicación',
  'resolucion-administrativa': 'Resolución administrativa',
  presupuesto: 'Presupuesto',
  circular: 'Circular',
  informe: 'Informe',
  'escrito-de-parte': 'Escrito de parte',
  'instrumento-urbanistico': 'Instrumento urbanístico',
};

export const EVENT_TYPE_LABEL: Record<string, string> = {
  'ruling-issued': 'Sentencia',
  'order-issued': 'Auto',
  'appeal-filed': 'Recurso',
  'agreement-approved': 'Acuerdo',
  'assembly-held': 'Junta',
  reception: 'Recepción',
  'request-filed': 'Solicitud',
  notification: 'Notificación',
  other: 'Acto',
};

export const ACTOR_TYPE_LABEL: Record<string, string> = {
  administracion: 'Administración',
  tribunal: 'Tribunal',
  'entidad-urbanistica': 'Entidad urbanística',
  'comunidad-propietarios': 'Comunidad de propietarios',
  asociacion: 'Asociación',
  empresa: 'Empresa',
  persona: 'Persona',
};

export const RELATION_LABEL: Record<string, { direct: string; inverse: string }> = {
  cites: { direct: 'Cita a', inverse: 'Citado por' },
  confirms: { direct: 'Confirma', inverse: 'Confirmado por' },
  annuls: { direct: 'Anula', inverse: 'Anulado por' },
  modifies: { direct: 'Modifica', inverse: 'Modificado por' },
  appeals: { direct: 'Resuelve recurso contra', inverse: 'Recurrido en' },
  executes: { direct: 'Se dicta en ejecución de', inverse: 'Ejecutado por' },
  supersedes: { direct: 'Sustituye a', inverse: 'Sustituido por' },
  supports: { direct: 'Apoya a', inverse: 'Apoyada por' },
  contradicts: { direct: 'Contradice a', inverse: 'Contradicha por' },
  'related-to': { direct: 'Relacionado con', inverse: 'Relacionado con' },
};

export type BadgeTone = 'neutral' | 'info' | 'ok' | 'warn' | 'alert';
export interface BadgeSpec { label: string; tone: BadgeTone }

/** Insignia de estado editorial (texto + tono, sistemático). */
export function editorialBadge(status: Editorial): BadgeSpec {
  const tone: BadgeTone = status === 'draft' ? 'warn' : status === 'verified' ? 'ok' : 'info';
  return { label: EDITORIAL_LABEL[status], tone };
}

/**
 * Insignia de estado de la evidencia. `disputed` e `incomplete` deben
 * mostrarse SIEMPRE (también en producción); `consistent` solo aporta en
 * preview/revisión — usar `showEvidenceBadge` para decidirlo.
 */
export function evidenceBadge(status: Evidence): BadgeSpec {
  const tone: BadgeTone =
    status === 'disputed' ? 'alert' : status === 'incomplete' ? 'warn' : status === 'unassessed' ? 'warn' : 'neutral';
  return { label: EVIDENCE_LABEL[status], tone };
}

/**
 * ¿Debe mostrarse la insignia de evidencia en una página pública?
 * disputed/incomplete SIEMPRE (también en producción); consistent y unassessed
 * solo aportan en preview (unassessed nunca llega a producción como asentado:
 * su nota sería draft o habría sido evaluada al revisarla).
 */
export function showEvidenceBadge(status: Evidence): boolean {
  return (status !== 'consistent' && status !== 'unassessed') || PREVIEW;
}

/** Insignia de base epistemológica. Solo `documented` es discreta. */
export function basisBadge(basis: string): BadgeSpec {
  const tone: BadgeTone = basis === 'documented' ? 'neutral' : basis === 'unknown' ? 'alert' : 'warn';
  return { label: BASIS_LABEL[basis] ?? basis, tone };
}

export const PUBLICATION_LABEL: Record<string, string> = {
  private: 'Documento privado — no publicado',
  'metadata-only': 'Solo metadatos públicos — PDF no publicado',
  public: 'Documento publicable',
};

export const PRIVACY_LABEL: Record<string, string> = {
  pending: 'Revisión de privacidad pendiente',
  approved: 'Revisión de privacidad aprobada',
  'needs-redaction': 'Requiere anonimización',
};


/* ------------------------------------------------------------------ */
/* Estados en lenguaje de vecino                                       */
/* ------------------------------------------------------------------ */

export interface ReaderFlag {
  icon: '✓' | '⚠' | '◌' | '✎';
  label: string;
  detail?: string;
  tone: BadgeTone;
}

/**
 * ¿Distingue algo el estado editorial hoy? Mientras las 150 afirmaciones estén
 * en borrador, marcarlas una a una no informa: es la misma etiqueta 150 veces.
 * El estado se comunica entonces como propiedad del SITIO. En cuanto exista
 * contenido revisado, esta constante pasa a `false` y las distinciones por
 * elemento aparecen solas, sin tocar ninguna plantilla.
 */
export const EDITORIAL_UNIFORM: boolean = (() => {
  const states = new Set<string>();
  for (const list of [graph.notes, graph.events, graph.procedures, graph.questions]) {
    for (const e of list) states.add((e.data as { editorialStatus: string }).editorialStatus);
  }
  return states.size <= 1;
})();

/**
 * Avisos que merecen aparecer JUNTO a un elemento concreto. Devuelve lista
 * vacía en el caso normal, que es el 94% de las afirmaciones: un distintivo
 * que sale siempre es ruido, no información.
 */
export function readerFlags(entry: Entity): ReaderFlag[] {
  const d = entry.data as Record<string, unknown>;
  const flags: ReaderFlag[] = [];

  if (d.evidenceStatus === 'disputed') {
    flags.push({
      icon: '⚠',
      label: 'Las fuentes discrepan',
      detail: 'Hay documentos que dicen cosas distintas sobre este punto.',
      tone: 'alert',
    });
  }
  if (d.evidenceStatus === 'incomplete') {
    flags.push({
      icon: '◌',
      label: 'Documentación incompleta',
      detail: 'Falta documentación para dar esto por cerrado.',
      tone: 'warn',
    });
  }
  if (typeof d.basis === 'string' && d.basis !== 'documented') {
    flags.push({
      icon: '✎',
      label: BASIS_LABEL[d.basis] ?? d.basis,
      tone: 'warn',
    });
  }
  if (d.dateStatus === 'disputed') {
    flags.push({
      icon: '⚠',
      label: 'Fecha discutida',
      detail: 'Los documentos no coinciden en la fecha.',
      tone: 'alert',
    });
  }
  if (!EDITORIAL_UNIFORM && d.editorialStatus === 'reviewed') {
    flags.push({ icon: '✓', label: 'Comprobado contra el documento', tone: 'ok' });
  }
  return flags;
}

/** La línea de fiabilidad de una página entera. */
export function pageTrust(entry: Entity): ReaderFlag {
  const flags = readerFlags(entry);
  if (flags.length > 0) return flags[0];
  return {
    icon: '✓',
    label: 'Respaldado por documentación',
    detail: 'Cada afirmación de esta página indica de qué documento sale y en qué página.',
    tone: 'ok',
  };
}

/** Por qué un documento no se puede descargar. Texto único. */
export function sourceUnavailableNote(): string {
  return (
    'El documento original no está publicado: contiene datos personales y su ' +
    'revisión de privacidad sigue pendiente. La ficha recoge qué dice y en qué ' +
    'página, para que cualquier afirmación pueda comprobarse.'
  );
}
