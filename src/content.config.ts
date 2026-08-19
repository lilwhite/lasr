import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Schemas espejo de docs/CONTENT_MODEL.md. Si el modelo cambia, se cambia
// primero CONTENT_MODEL.md y después este fichero.

const ENTITY_ID = /^(SRC|NOTE|EVENT|ACTOR|PROC|TOPIC|QUESTION)-[A-Z0-9-]+$/;

/**
 * ID de entrada = nombre de fichero, SIEMPRE. Sin esto, el loader glob trata
 * el campo frontmatter `slug` (Topics/Questions) como override del id de
 * entrada y rompe el invariante "fichero = ID en minúsculas".
 */
const byFilename = (options: { pattern: string; base: string }) =>
  glob({ ...options, generateId: ({ entry }) => entry.replace(/\.(md|mdx)$/, '') });

const entityRef = z.string().regex(ENTITY_ID, 'Referencia con formato de ID inválido');
const actorRef = z.string().regex(/^ACTOR-[A-Z0-9-]+$/);
const topicRef = z.string().regex(/^TOPIC-[A-Z0-9-]+$/);
const procRef = z.string().regex(/^PROC-[A-Z0-9-]+$/);
const noteRef = z.string().regex(/^NOTE-[A-Z0-9-]+$/);
const eventRef = z.string().regex(/^EVENT-[A-Z0-9-]+$/);
const sourceRef = z.string().regex(/^SRC-[A-Z0-9-]+$/);

const editorialStatus = z.enum(['draft', 'reviewed', 'verified']);
const evidenceStatus = z.enum(['unassessed', 'consistent', 'disputed', 'incomplete']);
const urlSlug = z.string().regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, 'Slug en kebab-case');

const citation = z.object({
  source: sourceRef,
  pdfPages: z.array(z.number().int().positive()).nonempty(),
  printedPages: z.array(z.number().int().positive()).optional(),
  locator: z.string().optional(),
  quote: z.string().optional(),
}).strict();

const relation = z.object({
  type: z.enum([
    'cites', 'confirms', 'annuls', 'modifies', 'appeals',
    'executes', 'supersedes', 'supports', 'contradicts', 'related-to',
  ]),
  target: entityRef,
  note: z.string().optional(),
}).strict();

const party = z.object({ actor: actorRef, role: z.string() }).strict();

const sources = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/sources' }),
  schema: z.object({
    id: sourceRef,
    title: z.string(),
    docType: z.enum([
      'sentencia', 'auto', 'estatutos', 'acta', 'convenio', 'comunicacion',
      'resolucion-administrativa', 'presupuesto', 'circular', 'informe',
    ]),
    date: z.date(),
    issuer: actorRef,
    resolutionNumber: z.string().optional(),
    rollo: z.string().optional(),
    procedure: procRef.optional(),
    parties: z.array(party).optional(),
    file: z.string().nullable(),
    sha256: z.string().regex(/^[0-9a-f]{64}$/).optional(),
    originalFilename: z.string().optional(),
    pages: z.number().int().positive().optional(),
    language: z.string().default('es'),
    topics: z.array(topicRef).default([]),
    relations: z.array(relation).default([]),
    publicationStatus: z.enum(['private', 'metadata-only', 'public']).default('private'),
    privacyReview: z.object({
      status: z.enum(['pending', 'approved', 'needs-redaction']).default('pending'),
      date: z.date().nullable().optional(),
      notes: z.string().optional(),
    }).strict(),
  }).strict(),
});

const notes = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/notes' }),
  schema: z.object({
    id: noteRef,
    title: z.string(),
    type: z.enum(['fact', 'ruling', 'obligation', 'agreement', 'legal-principle', 'claim']),
    basis: z.enum(['documented', 'inferred', 'interpretation', 'unknown']),
    editorialStatus,
    evidenceStatus: evidenceStatus.default('unassessed'),
    citations: z.array(citation).default([]),
    actors: z.array(actorRef).default([]),
    events: z.array(eventRef).default([]),
    topics: z.array(topicRef).default([]),
    relations: z.array(relation).default([]),
  }).strict()
    .refine((n) => n.basis !== 'documented' || n.citations.length > 0, {
      message: 'Una nota con basis "documented" exige al menos una citation (CONTENT_MODEL §6)',
    }),
});

const dateEvidence = z.object({
  value: z.date(),
  citations: z.array(citation).nonempty(),
  note: z.string().optional(),
}).strict();

const events = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/events' }),
  schema: z.object({
    id: eventRef,
    title: z.string(),
    date: z.date().nullable(),
    datePrecision: z.enum(['day', 'month', 'year']).nullable().optional(),
    dateStatus: z.enum(['documented', 'disputed', 'estimated', 'unknown']).default('documented'),
    dateEvidence: z.array(dateEvidence).default([]),
    type: z.enum([
      'ruling-issued', 'order-issued', 'appeal-filed', 'agreement-approved',
      'assembly-held', 'reception', 'request-filed', 'notification', 'other',
    ]),
    actors: z.array(actorRef).default([]),
    procedure: procRef.optional(),
    citations: z.array(citation).default([]),
    topics: z.array(topicRef).default([]),
    editorialStatus,
  }).strict()
    .refine((e) => e.dateStatus !== 'disputed' || (e.date === null && e.dateEvidence.length >= 2), {
      message: 'Un evento con fecha disputada exige date: null y ≥2 entradas en dateEvidence (CONTENT_MODEL §3.3)',
    })
    .refine((e) => e.date !== null || e.dateStatus === 'disputed' || e.dateStatus === 'unknown', {
      message: 'date solo puede ser null cuando dateStatus es disputed o unknown',
    }),
});

const actors = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/actors' }),
  schema: z.object({
    id: actorRef,
    name: z.string(),
    type: z.enum([
      'administracion', 'tribunal', 'entidad-urbanistica',
      'comunidad-propietarios', 'asociacion', 'empresa', 'persona',
    ]),
    aliases: z.array(z.string()).default([]),
    topics: z.array(topicRef).default([]),
  }).strict(),
});

const procedures = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/procedures' }),
  schema: z.object({
    id: procRef,
    title: z.string(),
    type: z.enum(['judicial', 'administrativo']),
    organ: actorRef,
    number: z.string(),
    parent: procRef.nullable(),
    parties: z.array(party).default([]),
    topics: z.array(topicRef).default([]),
    editorialStatus,
  }).strict(),
});

const topics = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/topics' }),
  schema: z.object({
    id: topicRef,
    slug: urlSlug,
    title: z.string(),
    summary: z.string(),
    relatedTopics: z.array(topicRef).default([]),
  }).strict(),
});

const questions = defineCollection({
  loader: byFilename({ pattern: '**/*.md', base: './src/content/questions' }),
  schema: z.object({
    id: z.string().regex(/^QUESTION-[A-Z0-9-]+$/),
    slug: urlSlug,
    question: z.string(),
    topics: z.array(topicRef).default([]),
    answeredBy: z.array(noteRef).default([]),
    editorialStatus,
  }).strict(),
});

export const collections = { sources, notes, events, actors, procedures, topics, questions };
