/**
 * Política editorial y de privacidad de LASR-Web. ÚNICA fuente de verdad sobre
 * qué contenido puede mostrarse y cómo debe etiquetarse. Ningún componente ni
 * página debe reimplementar estas reglas.
 */
import type { Entity, Source } from './graph';

/**
 * Modo previsualización: en `astro dev` siempre; en build solo con
 * LASR_PREVIEW=1. La build de producción sin esa variable excluye el contenido
 * no publicable (draft, sources privados).
 */
export const PREVIEW: boolean = import.meta.env.DEV || process.env.LASR_PREVIEW === '1';

type Editorial = 'draft' | 'reviewed' | 'verified';
type Evidence = 'unassessed' | 'consistent' | 'disputed' | 'incomplete';

/**
 * ¿Puede esta entidad aparecer en la web en el modo actual?
 *
 * Publicable como contenido asentado ⇔ editorialStatus ∈ {reviewed, verified}
 * (más las reglas de privacidad de Source). `evidenceStatus: disputed` o
 * `incomplete` NUNCA ocultan contenido: se publica con la discrepancia
 * explícita — el sistema no esconde contradicciones documentales para
 * simplificar la explicación.
 */
export function isVisible(entry: Entity): boolean {
  const d = entry.data as { editorialStatus?: Editorial; publicationStatus?: string };
  if (entry.data.id.startsWith('SRC-')) {
    // La ficha de un Source privado no se publica; en preview sí se ve.
    return PREVIEW || d.publicationStatus !== 'private';
  }
  if (d.editorialStatus !== undefined) {
    return PREVIEW || d.editorialStatus !== 'draft';
  }
  return true; // actors y topics no tienen estado editorial
}

export function visibleOnly<T extends Entity>(entries: T[]): T[] {
  return entries.filter(isVisible);
}

/** ¿Puede enlazarse/publicarse el PDF original de un Source? */
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
