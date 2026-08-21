# CONTENT_MODEL — Modelo de contenido de LASR-Web

Especificación canónica del modelo de conocimiento de LASR-Web. Cualquier contenido de `src/content/` debe ajustarse a este documento. Si el modelo cambia, se cambia primero aquí.

**Estado**: v1, instanciada con el corpus documental completo de la carpeta maestra (ver §12).

---

## 1. Objetivos

LASR-Web construye una **capa de conocimiento estructurado** sobre la documentación primaria de Los Ángeles de San Rafael (sentencias, autos, estatutos, actas, acuerdos, comunicaciones). No es un archivo de PDFs: es un grafo de afirmaciones verificables que permite a un vecino responder preguntas como *"¿qué han establecido los tribunales sobre la recepción?"* siguiendo cada afirmación hasta la página exacta del documento que la sustenta.

Pipeline conceptual:

```
PDFs → Sources → AtomicNotes → Relations → Events / Actors / Procedures → Topics / Questions → Web (Astro)
```

## 2. Principios

1. **Trazabilidad ante todo.** Toda afirmación relevante responde a "¿de dónde sale esto?" con documento + página + apartado.
2. **Atomicidad.** Una nota = una afirmación. Nada de resúmenes de diez páginas.
3. **Separación de ejes.** Qué clase de afirmación es (`type`), cómo de sólida es epistemológicamente (`basis`) y en qué punto del flujo editorial está (`status`) son tres cosas distintas y se guardan en tres campos distintos.
4. **El documento habla, la web no interpreta de más.** "La resolución establece X" es demostrable; "actualmente ocurre X" requiere documentación posterior. Cuando hay incertidumbre, se representa.
5. **Privacidad por defecto.** Ningún original se asume publicable; ningún dato personal se copia al modelo.
6. **Sin base de datos.** Markdown + YAML frontmatter versionado en Git, validable después por Astro Content Collections con Zod.
7. **Mantenibilidad sobre sofisticación.** Cada campo del modelo debe ganarse su existencia.

## 3. Entidades

Siete colecciones bajo `src/content/`. Cada entidad es un fichero Markdown con frontmatter YAML (datos estructurados) y cuerpo Markdown (explicación humana, matices, contexto).

| Colección | Entidad | Qué representa |
|---|---|---|
| `sources/` | Source | Un documento primario (sentencia, auto, estatutos, acta…) |
| `notes/` | AtomicNote | Una única afirmación sustentada por una o más fuentes |
| `events/` | Event | Un acontecimiento histórico o procesal datado |
| `actors/` | Actor | Un actor relevante (administración, tribunal, entidad, empresa…) |
| `procedures/` | Procedure | Un procedimiento judicial o administrativo y sus piezas |
| `topics/` | Topic | Un Map of Content: gran asunto que un vecino necesita comprender |
| `questions/` | Question | Una pregunta de vecino, respondida mediante notas |

### 3.1 Source

```yaml
---
id: SRC-2012-TSJCYL-581           # obligatorio, único, ver §8
title: >-                          # título editorial legible
  Sentencia 581/2012 del TSJ de Castilla y León …
docType: sentencia                 # sentencia | auto | estatutos | acta | convenio | comunicacion |
                                   # resolucion-administrativa | presupuesto | circular | informe |
                                   # escrito-de-parte | instrumento-urbanistico
date: 2012-12-21                   # fecha del documento (no de notificación)
issuer: ACTOR-TSJCYL-SALA-CA-BURGOS  # actor que emite el documento
resolutionNumber: "581/2012"       # opcional (resoluciones)
rollo: "Apelación 216/2012"        # opcional (segunda instancia)
procedure: PROC-2011-JCA-SEGOVIA-ETJ-20  # opcional → Procedure
parties:                           # opcional; solo partes institucionales
  - actor: ACTOR-AYUNTAMIENTO-EL-ESPINAR
    role: apelante                 # texto libre corto: apelante, apelada, demandante…
file: private-sources/pdf/src-2012-tsjcyl-581.pdf   # ruta local NO versionada; null si aún no hay fichero
sha256: e05219b1…                  # hash del PDF original: permite verificar el fichero sin publicarlo
originalFilename: "SENTENCIA TSJ RECEPCION …pdf"
pages: 22                          # páginas físicas del PDF
language: es
topics: [TOPIC-RECEPCION]
relations: []                      # ver §5
publicationStatus: private         # ver §10
privacyReview:
  status: pending                  # pending | approved | needs-redaction
  date: null
  notes: ""
---
Cuerpo: descripción del documento, calidad del escaneo, observaciones de captura.
```

Un Source **no** tiene `status` editorial ni `basis`: el documento es el que es. Lo que se revisa es su publicabilidad (`privacyReview`).

**Un Source es un fichero, 1:1.** Un PDF da lugar como mucho a un Source, y un Source apunta como mucho a un PDF. La razón es operativa: `sha256` identifica un fichero, y `scripts/inventory.py` cruza documentos y fichas por ese hash; dos Sources compartiendo `sha256` harían desaparecer uno del inventario en silencio. Cuando un solo fichero contiene varios documentos (p. ej. dos escritos de apelación encuadernados juntos), se ficha **un** Source: las partes van en `parties[]`, la estructura interna se explica en el cuerpo y cada `locator` indica de qué pieza procede la cita, igual que con los documentos transcritos (§6). Cuando un documento llega partido en varios ficheros (un escrito y su acuse de registro), se ficha el principal y el resto se anota en el registro documental.

**Notas sobre `docType`.** `escrito-de-parte` cubre todo escrito procesal dirigido a un órgano (demanda, apelación, recurso de amparo): la distinción entre ellos vive en `procedure`, `issuer` y el cuerpo, no en una taxonomía paralela. Sus notas son casi siempre `type: claim` (§9.4). Una comunicación entre partes privadas, aunque sea fehaciente (burofax), es `comunicacion`, no `escrito-de-parte`. `instrumento-urbanistico` cubre el planeamiento (planes parciales y generales, proyectos de urbanización).

**La legislación no es un Source.** Un Source es un documento primario *del caso*: tiene emisor dentro del relato, procedimiento y privacidad que revisar. Una norma no tiene nada de eso, y citar `pdfPages` de un ejemplar cualquiera de una ley es peor trazabilidad que citar artículo y boletín — más aún cuando existen versiones consolidadas sucesivas del mismo texto. El corpus cita norma a través de la resolución que la aplica. Los ejemplares de normativa que aparezcan entre los documentos originales se anotan como material de referencia en el registro documental.

**Registro documental.** `docs/document_registry.json` (fuente de verdad) y su volcado legible `docs/DOCUMENT_REGISTRY.md` recogen los ficheros originales que **no** dan lugar a un Source, con su `sha256` como clave: duplicados exactos de un documento ya fichado (`duplicate-of`), copias parciales (`fragment-of`), anexos y acuses (`annex-of`), normativa y doctrina (`reference-material`) y fragmentos no atribuibles a ningún documento conocido (`unidentified`). Cada entrada lleva la evidencia de la identificación. Sin este registro, `inventory.py` mostraría esos ficheros como pendientes indefinidamente, porque su `sha256` no coincide con ninguna ficha. En el Source afectado se añade además una línea en su bloque `**Captura**`/`**Versiones**` remitiendo al registro.

**Origen público (`official`).** Algunos documentos existen además en un repositorio oficial de acceso libre: sentencias en el CENDOJ, planeamiento en el Archivo de Planeamiento de la Junta de Castilla y León, disposiciones en el BOCyL. Cuando conste, se declara:

```yaml
official:
  repository: CENDOJ            # nombre del repositorio público
  ref: "SAP SG 290/2017"        # opcional: la referencia con la que localizarlo (ROJ, ECLI, nº de boletín)
  url: https://www.poderjudicial.es/search/indexAN.jsp   # opcional: dirección pública
```

Es la vía para que un vecino pueda consultar el original aunque nuestra copia no sea publicable, y **no exige revisión de privacidad**: quien publica es el organismo, no nosotros.

Dos cautelas. La `url` solo se rellena si se ha comprobado que funciona; si el repositorio no admite enlace directo a un documento concreto, se enlaza su buscador y la `ref` es lo que permite encontrarlo. Y `official` describe **dónde está el documento oficial**, no que nuestra copia sea publicable: eso lo sigue decidiendo `publicationStatus` con su `privacyReview`.

**Sources sin fichero (stubs).** Muchos documentos se conocen solo porque otro documento los cita (p. ej. la sentencia 217/2015 del TSJ, que el corpus conoce solo por la carta con la que la EUC comunicó sus efectos). En la v1 estos documentos se representan como **Events** con citas al documento que los menciona. Si más adelante conviene citarlos como fuente (p. ej. al conseguir el PDF), se crea su Source con `file: null` hasta tener el fichero. No crear stubs preventivamente.

### 3.2 AtomicNote

Una única afirmación significativa. Test de atomicidad: el `title` debe poder leerse como una frase completa y verificarse contra las páginas citadas sin necesitar el resto de la nota.

```yaml
---
id: NOTE-2012-TSJCYL-581-004
title: >-
  La STSJ 581/2012 establece que la prestación de los servicios públicos
  se realizará a costa del Ayuntamiento de El Espinar desde la recepción.
type: obligation                   # ver tabla
basis: documented                  # documented | inferred | interpretation | unknown, ver §7
editorialStatus: draft             # draft | reviewed | verified, ver §7
evidenceStatus: unassessed         # unassessed | consistent | disputed | incomplete, ver §7
citations:                         # obligatoria ≥1 si basis: documented, ver §6
  - source: SRC-2012-TSJCYL-581
    pdfPages: [21]
    locator: "Fallo, 2º.b"
    quote: "la prestación de tales servicios se realizará a costa del Ayuntamiento de El Espinar…"
actors: [ACTOR-AYUNTAMIENTO-EL-ESPINAR]
events: []                         # opcional → Events relacionados
topics: [TOPIC-RECEPCION]
relations: []
---
Cuerpo: la afirmación desarrollada, con sus matices y límites temporales.
```

Tipos de nota (`type`):

| type | Qué es | Ejemplo |
|---|---|---|
| `fact` | Hecho histórico o procesal que el documento acredita | "La solicitud de recepción se presentó el 10.7.2008" |
| `ruling` | Lo que una resolución **decide** (fallo / parte dispositiva) | "La sentencia confirma el auto de 24.2.2012" |
| `obligation` | Deber concreto que una resolución o norma impone a un actor | "El Ayuntamiento debe costear los servicios desde la recepción" |
| `agreement` | Pacto entre partes (convenio, acuerdo transaccional, acuerdo de junta) | "El acuerdo homologado fija un periodo transitorio de 5 años" |
| `legal-principle` | Criterio o doctrina jurídica que el tribunal enuncia con alcance general | "Conservar la urbanización y prestar servicios son obligaciones distintas" |
| `claim` | Alegación de una parte que el documento recoge **sin** asumirla | "El Ayuntamiento alegó que las instalaciones eran de titularidad privada" |

Diferencias clave: `ruling` es el pronunciamiento; `obligation` es el deber que de él (o de un pacto o norma) resulta para alguien; `agreement` nace de la voluntad de las partes, no de la decisión del tribunal; `claim` nunca debe presentarse como hecho probado. No existe un type `interpretation`: una lectura editorial es cualquier type con `basis: interpretation`.

### 3.3 Event

```yaml
---
id: EVENT-2012-02-24-AUTO-EJECUCION
title: El JCA nº 1 de Segovia dicta auto de ejecución de la sentencia de recepción
date: 2012-02-24                   # null cuando dateStatus es disputed o unknown
datePrecision: day                 # day | month | year; solo si date no es null
dateStatus: documented             # documented (default) | disputed | estimated | unknown
dateEvidence: []                   # obligatorio (≥2 entradas) si dateStatus: disputed; ver abajo
type: order-issued                 # ruling-issued | order-issued | appeal-filed |
                                   # agreement-approved | assembly-held | reception |
                                   # request-filed | notification | other
actors: [ACTOR-JCA-1-SEGOVIA]
procedure: PROC-2011-JCA-SEGOVIA-ETJ-20   # opcional
citations: [ … ]                   # mismo formato que en las notas
topics: [TOPIC-RECEPCION]
editorialStatus: draft
---
Cuerpo: qué ocurrió, y cualquier discrepancia documental sobre fecha o contenido.
```

Los Events alimentan la timeline futura. La fecha es la del acontecimiento, no la del documento que lo relata.

**Fechas contradictorias.** Cuando la documentación fecha un acontecimiento de forma contradictoria y no hay evidencia suficiente para decidir, **no se elige**: `date: null`, `dateStatus: disputed`, y cada candidata queda trazada en `dateEvidence`:

```yaml
date: null
dateStatus: disputed
dateEvidence:
  - value: 2013-06-03
    citations: [ …objeto citation estándar (§6)… ]
    note: "Fecha que usa la Sala al razonar sobre la homologación"
  - value: 2018-06-03
    citations: [ … ]
    note: "Fecha que consta en la parte dispositiva del auto transcrito"
```

Reglas: con `dateStatus: disputed`, `date` DEBE ser null y `dateEvidence` tener ≥2 entradas con citas; el cuerpo analiza la discrepancia sin resolverla. Para ordenar la timeline se usa la candidata más temprana como **clave de ordenación puramente presentacional** (documentado aquí, no es una afirmación sobre la fecha real), y la web marca el evento como "fecha disputada" mostrando todas las candidatas con sus citas. `estimated` (fecha aproximada única, con `datePrecision` amplio) y `unknown` (sin fecha; queda fuera de la timeline) completan el enum. Ver `EVENT-ACUERDO-TRANSACCIONAL-AGUA-001`.

### 3.4 Actor

```yaml
---
id: ACTOR-AYUNTAMIENTO-EL-ESPINAR
name: Ayuntamiento de El Espinar
type: administracion               # administracion | tribunal | entidad-urbanistica |
                                   # comunidad-propietarios | asociacion | empresa | persona
aliases: ["Excmo. Ayuntamiento de El Espinar"]
topics: [TOPIC-RECEPCION]
---
Cuerpo: quién es, papel en la historia de la urbanización, con las cautelas de §9.
```

El type `persona` se reserva para cargos públicos o personas con relevancia pública actuando como tales; las personas físicas privadas **no** se modelan como Actor (§10).

### 3.5 Procedure

Entidad necesaria: los pilotos muestran una cadena `PO 28/2009 → ejecución 20/2011 → incidente 16/2018` con resoluciones y apelaciones en cada nivel, imposible de representar limpiamente solo con relaciones entre documentos.

```yaml
---
id: PROC-2011-JCA-SEGOVIA-ETJ-20
title: Ejecución de títulos judiciales 20/2011 (ejecución de la sentencia de recepción)
type: judicial                     # judicial | administrativo
organ: ACTOR-JCA-1-SEGOVIA         # órgano ante el que se tramita
number: "ETJ 20/2011"
parent: PROC-2009-JCA-SEGOVIA-PO-28   # null si es procedimiento raíz
parties:
  - actor: ACTOR-CP-LASR
    role: ejecutante
topics: [TOPIC-RECEPCION]
editorialStatus: draft
---
Cuerpo: objeto del procedimiento y estado conocido (con fecha del último dato).
```

Decisiones:
- **Las piezas separadas e incidentes son Procedures hijos** (`parent`), no campos del padre. Esto modela `procedimiento → sentencia → apelación → ejecución → incidente` sin inventar más entidades.
- **Los rollos de apelación no son Procedures**: la apelación queda registrada en el Source que la resuelve (`rollo:`) y, si interesa el acto de interponerla, como Event `appeal-filed`. Crear un Procedure por rollo duplicaría información sin beneficio.
- **Un Procedure no lista sus resoluciones**: se derivan en build de los Sources/Events que apuntan a él (evita listas duplicadas que se desincronizan).

### 3.6 Topic

Un Topic es un **Map of Content**: la página curada que un vecino leería para entender un gran asunto.

```yaml
---
id: TOPIC-RECEPCION
slug: recepcion-de-la-urbanizacion # slug de URL: explícito, kebab-case, único y ESTABLE
title: Recepción de la urbanización
summary: >-
  Una frase que resume el asunto.
relatedTopics: []                  # solo IDs existentes
---
Cuerpo: narrativa curada en Markdown que enlaza por ID las notas, eventos,
fuentes, actores y preguntas relevantes, y lista las incógnitas abiertas.
```

La pertenencia inversa (qué notas/eventos/fuentes tocan un Topic) **no se mantiene a mano** en el Topic: se computa en build a partir de los arrays `topics:` de las demás entidades. El cuerpo del Topic es curación editorial, no un índice exhaustivo.

**Campo `area`.** Cada Topic declara a cuál de las dos grandes áreas de la interfaz pertenece: `comunidad-y-recepcion` o `desanexion`. Es **agrupación editorial de navegación**: no crea jerarquía, no altera la pertenencia inversa y no hace que las afirmaciones de un tema cuenten en otro. Una afirmación aparece en todos los contextos que le correspondan sin duplicarse. Ver `docs/WEB_DESIGN.md` §2.2.

**Contrato de secciones del cuerpo.** El cuerpo de un Topic solo puede contener las secciones que no son derivables del grafo: `## En 30 segundos`, `## Por qué importa`, `## Situación documentada` y `## Qué está en discusión`. Las demás —cronología, preguntas, procedimientos, actores, documentos— las genera la plantilla desde las colecciones, y escribirlas a mano hace **fallar el build**. La razón es concreta: hasta ahora los temas llevaban esas listas escritas a mano *y* la plantilla las generaba, de modo que había dos versiones destinadas a divergir.

### 3.7 Question

```yaml
---
id: QUESTION-RECEPCION-001
slug: recepcion-001                # slug de URL: explícito, kebab-case, único y ESTABLE
question: ¿Qué han establecido los tribunales sobre la recepción de la urbanización?
topics: [TOPIC-RECEPCION]
answeredBy:                        # notas que sustentan la respuesta
  - NOTE-2012-TSJCYL-581-001
  - NOTE-2012-TSJCYL-581-007
editorialStatus: draft
---
Cuerpo (opcional): síntesis breve que hilvana las notas de answeredBy.
No duplica el contenido de las notas; la respuesta ES el conjunto de notas.
```

### 3.8 Page

Prosa divulgativa que no se deriva de ninguna colección: la portada, la historia, la metodología y el aviso legal.

```yaml
---
slug: metodologia            # kebab-case, estable: define la URL
title: Cómo verificamos la información
summary: >-                  # entradilla y `<meta name="description">` por defecto
  De dónde salen los documentos, cómo se extraen las afirmaciones y qué
  significa que algo esté documentado, discutido o incompleto.
updated: 2026-08-19
editorialStatus: draft
---
Cuerpo Markdown.
```

Vive en `src/content/pages/`. Es contenido, no plantilla: se revisa igual que el resto, admite las referencias entre backticks que se convierten en enlaces, y mantiene el texto editorial fuera de los ficheros `.astro`.

**Ninguna cifra se escribe aquí.** Los recuentos del corpus se inyectan desde el grafo; escribirlos a mano garantizaría que quedaran desfasados.

## 4. Schemas

Los schemas formales (Zod) se escribirán en `src/content.config.ts` en la fase Astro, espejo campo a campo de §3. Reglas transversales que Zod deberá imponer:

- `id` obligatorio, único en su colección, con el prefijo de su tipo (§8).
- Toda referencia (`actors`, `topics`, `procedure`, `answeredBy`, `citations[].source`, `relations[].target`, `parent`, `issuer`, `organ`) debe resolver a un ID existente.
- `citations` no vacío cuando `basis: documented`.
- Enums cerrados para `docType`, `type`, `basis`, `editorialStatus`, `evidenceStatus`, `dateStatus`, `datePrecision`, `publicationStatus`, `privacyReview.status`, `relations[].type`.
- `slug` obligatorio y único en Topic y Question.

## 5. Relaciones semánticas

Representación: array `relations` en el frontmatter de la entidad **origen**:

```yaml
relations:
  - type: related-to
    target: SRC-2012-TSJCYL-581
    note: "Misma ejecutoria (PO 28/2009)"   # opcional, recomendado
```

**Las relaciones inversas no se almacenan.** Se computan en build (si A `confirms` B, la página de B muestra "confirmada por A"). Mantenerlas a mano duplicaría información y acabaría inconsistente.

Taxonomía (cerrada; ampliar solo vía este documento):

| type | Origen → destino | Significado | Inversa mostrada |
|---|---|---|---|
| `cites` | source → source | La resolución cita otro documento | "citado por" |
| `confirms` | source → source | Confirma la resolución recurrida | "confirmado por" |
| `annuls` | source → source | Anula o revoca (total o en el extremo que indique `note`) | "anulado por" |
| `modifies` | source → source | Modifica, complementa o aclara | "modificado por" |
| `appeals` | source → source | Resuelve un recurso contra el destino | "recurrido en" |
| `executes` | source → source | Se dicta en ejecución del destino | "ejecutado por" |
| `supersedes` | source → source | Versión posterior del mismo documento (estatutos, presupuestos) | "sustituido por" |
| `supports` | note → note | Refuerza la otra afirmación | "apoyada por" |
| `contradicts` | note → note | Tensión documental; ambas notas deben pasar a `evidenceStatus: disputed` | "contradicha por" |
| `related-to` | cualquiera → cualquiera | Conexión relevante sin tipo específico; último recurso, con `note` | "relacionado con" |

Descartadas deliberadamente: `involves` (lo cubren los arrays `actors`/`parties`), `derived-from` (lo cubren las `citations` de la nota). No añadir relaciones que dupliquen un campo existente.

## 6. Trazabilidad

Objeto `citation`, usado en `notes` y `events`:

```yaml
citations:
  - source: SRC-2012-TSJCYL-581    # obligatorio → Source
    pdfPages: [20, 21]             # obligatorio: páginas físicas del PDF
    printedPages: [19, 20]         # solo si el documento tiene paginación propia visible y distinta
    locator: "Fallo, 2º.b"         # apartado: "FJ 5º", "Antecedente 1º", "Art. 12", "Estipulación 1ª"
    quote: >-                      # opcional: extracto literal breve (< ~50 palabras)
      la prestación de tales servicios se realizará a costa del Ayuntamiento…
```

Reglas:
- `pdfPages` siempre; es lo único que permite verificar contra el fichero real.
- `printedPages` solo cuando exista y difiera (los dos pilotos son escaneos sin paginación impresa visible: se omite).
- `locator` es texto libre pero normalizado: "FJ n", "Fallo", "Antecedente n", "Parte dispositiva", "Art. n", "Estipulación n". Cuando la afirmación procede de un texto **transcrito dentro de** otro documento (muy común: autos transcritos en sentencias), el locator lo dice: `"FD Tercero (transcripción del auto 177/2018)"`. La afirmación acreditada es entonces "el auto transcrito dice X", no "X".
- `quote` nunca incluye datos personales (§10).
- Una nota `documented` sin citación verificable **no se escribe**.

## 7. Estados

Cuatro ejes independientes; no mezclarlos. Una nota puede estar humanamente revisada y, a la vez, sustentada por documentación contradictoria: eso es `editorialStatus: reviewed` + `evidenceStatus: disputed`. Y puede estar impecablemente revisada y aun así no ser publicable, porque nombra a un particular: eso es el cuarto eje.

**`basis` — naturaleza del conocimiento** (qué clase de apoyo tiene la afirmación):

| basis | Significado | Regla |
|---|---|---|
| `documented` | Se lee directamente en las páginas citadas | Exige `citations` |
| `inferred` | Se deduce razonablemente de documentos, pero ninguno lo dice literalmente | El cuerpo explica la inferencia y cita las premisas |
| `interpretation` | Lectura editorial u opinión razonada | Debe presentarse siempre como tal en la web |
| `unknown` | Se sabe que la cuestión existe pero no cómo se resolvió | Útil para incógnitas explícitas |

**`editorialStatus` — flujo de revisión humana** (`draft → reviewed → verified`). Aplica a notes, events, procedures y questions:

| editorialStatus | Significado |
|---|---|
| `draft` | Contenido generado o incorporado (posiblemente con ayuda de IA) pero todavía **no comprobado manualmente contra la fuente**. No publicable como información asentada. |
| `reviewed` | Una persona ha comprobado: que la fuente existe; que la cita corresponde a la página indicada; que el contenido representa fielmente lo que dice la fuente; que no se ha añadido ninguna conclusión no sustentada; y que `type` y `basis` son correctos. **Es el estado normal del contenido apto para publicación.** |
| `verified` | Nivel superior de validación, reservado para revisiones reforzadas (p. ej. segunda persona o cotejo externo). No se usa de forma generalizada todavía. |

La promoción `draft → reviewed` es siempre un acto humano; nada se promociona automáticamente.

**`evidenceStatus` — coherencia de las fuentes** (solo en AtomicNotes):

| evidenceStatus | Significado |
|---|---|
| `unassessed` | (default) Aún no se ha evaluado la coherencia documental de la afirmación. Estado de nacimiento de todo contenido nuevo. |
| `consistent` | Evaluada: no se conoce contradicción documental sobre la afirmación |
| `disputed` | Las fuentes disponibles discrepan entre sí sobre la afirmación |
| `incomplete` | Falta documentación conocida para sustentarla del todo |

`unassessed → consistent` requiere una evaluación (normalmente durante la revisión humana). `disputed` puede asignarse en la ingesta cuando la contradicción documental es objetiva: describe la evidencia, no una validación editorial.

`disputed` e `incomplete` **no ocultan contenido**: una nota `reviewed` con evidencia controvertida puede publicarse, pero la interfaz debe dejar explícita la discrepancia. El sistema nunca esconde una contradicción documental para simplificar la explicación. Las fechas contradictorias de los Events no usan este eje: tienen su mecanismo específico `dateStatus`/`dateEvidence` (§3.3), sin duplicar información.

**Todo lo generado con ayuda de IA nace `draft`**, sin excepciones. `basis` y `evidenceStatus` se muestran siempre al lector cuando aportan cautela.

### 7.4 `legalStatus` — ¿puede el sitio publicar esto?

> Esta sección corrige lo que decía la anterior. Durante un tiempo aquí se leía que era publicable lo que tuviera `editorialStatus ∈ {reviewed, verified}`. `policy.ts:31` dejó de aplicar esa regla hace tiempo —devuelve `true` para todo, con el razonamiento escrito en su comentario— y la especificación no se actualizó. La regla real es la de abajo.

El cuarto eje no dice si una afirmación es cierta ni si está revisada: dice si el sitio puede publicarla sin exponer a nadie. Es ortogonal a los otros tres.

| legalStatus | Significado | ¿Genera página? |
|---|---|---|
| `unchecked` | (default) Sin revisión jurídica. Se publica y queda inventariado como deuda | Sí |
| `cleared` | Revisado: no expone datos de ninguna persona física | Sí |
| `cleared-redacted` | Revisado **tras suprimir algo**. Exige `redactions` | Sí |
| `needs-human-review` | Hay una cuestión que una persona tiene que valorar | Sí, pero bloquea la rama que lo toque |
| `blocked` | No se publica | **No** |

**No se confunde con `privacyReview` (§10), y los dos conviven.** `privacyReview` solo existe en Source y decide sobre el PDF original: *¿enlazo el fichero?* `legalStatus` decide sobre lo que el sitio publica: la nota, la cita, la ficha, la página. Un documento puede estar en `privacyReview: needs-redaction` y su ficha en `legalStatus: cleared`, porque la ficha cuenta qué dice el documento sin reproducir el dato.

**`blocked` nunca saca la entidad del grafo.** `graph.ts:resolve()` lanza si un identificador no existe, y las relaciones, las citas y el emisor siguen apuntándole. Se filtra solo en publicación, en `policy.ts`.

**Trazabilidad.** Todo estado distinto de `unchecked` exige `legalReview` con `reviewedAt` y `reason`; `cleared-redacted` exige además `redactions`. Y hay una regla dura sobre qué se escribe ahí:

> `reason` y cada `redactions` describen la **categoría** del dato tratado y la regla aplicada, **nunca su valor**. El build lo comprueba y se niega a terminar si el texto contiene un documento de identidad, un IBAN o una dirección de correo.

```yaml
legalStatus: cleared-redacted
legalReview:
  reviewedAt: 2026-08-21
  reason: 'LEGAL-PRIVACY-001: la ficha citaba a un particular por su nombre'
  redactions:
    - 'nombre de particular → «la parte apelante»'
    - 'número de documento de identidad → suprimido'
```

**El eje es interno.** El lector nunca lo ve: solo aparece bajo `PREVIEW` y en `/revision/`. Publicar «pendiente de revisión jurídica» en una página es señalar dónde mirar.

**Regla de publicación real**, implementada en `src/lib/policy.ts` y comprobada por `documentacion/scripts/check_gate.py`:

```
se publica ⇔ legalStatus ≠ 'blocked'
se enlaza el PDF original ⇔ legalStatus ≠ 'blocked'
                            ∧ publicationStatus = 'public'
                            ∧ privacyReview.status = 'approved'
```

El eje se declara en las **ocho** colecciones. Olvidarlo en una no rompe nada: esa colección se queda sin eje jurídico para siempre, en silencio. Por eso `scripts/legal/gate.py --check-schema` cuenta que `...legalFields` aparezca ocho veces.

## 8. IDs estables

Formato general: `PREFIJO-…-EN-MAYÚSCULAS`, legible, sin dependencia del título.

| Entidad | Patrón | Ejemplo |
|---|---|---|
| Source | `SRC-<año>-<órgano>-<número o slug>` | `SRC-2012-TSJCYL-581` |
| AtomicNote | `NOTE-<sufijo del Source principal>-<NNN>` | `NOTE-2012-TSJCYL-581-004` |
| Event | `EVENT-<fecha ISO>-<slug>` | `EVENT-2012-02-24-AUTO-EJECUCION` |
| Actor | `ACTOR-<slug>` | `ACTOR-AYUNTAMIENTO-EL-ESPINAR` |
| Procedure | `PROC-<año>-<órgano>-<tipo y número>` | `PROC-2009-JCA-SEGOVIA-PO-28` |
| Topic | `TOPIC-<slug>` | `TOPIC-RECEPCION` |
| Question | `QUESTION-<topic>-<NNN>` | `QUESTION-RECEPCION-001` |

Reglas:
- Un ID nunca cambia ni se reutiliza. Si una nota se elimina, su número queda retirado.
- **Un ID solo incorpora datos (fechas, números) que procedan de una identificación externa objetiva y no controvertida** (el número y año de una sentencia, sí). Si el dato es discutido, inferido o susceptible de corrección futura, el ID usa `PREFIJO-<slug>-<NNN>` sin ese dato: p. ej. `EVENT-ACUERDO-TRANSACCIONAL-AGUA-001` (su fecha está disputada entre 2013 y 2018). Los Events con fecha documentada y pacífica siguen usando `EVENT-<fecha ISO>-<slug>`.
- El número de nota (`NNN`) es secuencial dentro de su Source principal y no significa orden ni importancia.
- Una nota sustentada por varios Sources se numera bajo el Source que mejor la acredita; las demás fuentes van en `citations`.
- **Nombre de fichero = ID en minúsculas** (`note-2012-tsjcyl-581-004.md`). El slug de Astro saldrá del nombre de fichero; el `title` puede editarse libremente sin romper enlaces.
- **URLs públicas**: nunca dependen del título. Topic y Question llevan un campo `slug` explícito (kebab-case, único en su colección, tan estable como el ID); el resto de entidades derivan su URL del propio ID. Cambiar un `slug` publicado rompe enlaces externos: no se hace sin redirección.
- Órganos abreviados de forma consistente: `TSJCYL`, `JCA-SEGOVIA`, `AP-SEGOVIA`, `TS`, `AYTO-EL-ESPINAR`…

## 9. Reglas editoriales (interpretación jurídica)

1. Distinguir siempre **"la resolución establece…"** (demostrable con el documento, `basis: documented`) de **"actualmente ocurre…"** (exige documentación posterior; sin ella, como máximo `inferred`, explicando el salto).
2. Una resolución antigua no se convierte en afirmación sobre la situación actual. Los cuerpos de las notas acotan el alcance temporal ("en la fecha de la sentencia…").
3. Prohibidas las fórmulas concluyentes ("esto demuestra definitivamente que…") salvo respaldo documental inequívoco.
4. Lo que una parte alega es `claim`; nunca se redacta como hecho.
5. Lo que un documento transcrito dentro de otro afirma se atribuye al documento transcrito (ver `locator`, §6).
6. Las discrepancias internas de un documento (fechas, números) se documentan, no se resuelven en silencio.
7. LASR-Web no es asesoría jurídica de nadie; los Topics lo recuerdan cuando proceda.

## 10. Protección de datos

- Los PDFs originales viven en `private-sources/`, carpeta **excluida de Git** (`.gitignore`): no se versionan en el repositorio público ni pueden llegar al build. El Source conserva `originalFilename` y `sha256` como metadatos verificables sin necesidad de publicar el fichero.
- `publicationStatus` en Source: `private` (default: ni el PDF ni sus metadatos sensibles se publican) | `metadata-only` (se publica la ficha, no el PDF) | `public` (PDF publicable, tras revisión y en su caso anonimizado).
- `privacyReview.status`: `pending` (default) | `approved` | `needs-redaction`. Nada pasa de `private` con revisión `pending`.
- Publicar un original será siempre un acto explícito (copiarlo deliberadamente tras aprobar su revisión), nunca un efecto del build.
- Al modelo no se copian DNI, direcciones, teléfonos, emails, cuentas ni firmas. Los nombres de particulares (incluidos procuradores y letrados) no se copian a notas ni quotes salvo necesidad real; magistrados y cargos públicos actuando como tales son admisibles.
- Personas físicas privadas: nunca Actor, nunca en quotes.

## 11. Estructura en disco

```
docs/CONTENT_MODEL.md              # este documento
docs/SOURCES_INVENTORY.md          # inventario y correspondencia de nombres (versionado)
docs/DOCUMENT_REGISTRY.md          # ficheros que no dan lugar a Source (versionado)
docs/document_registry.json        # el mismo registro, fuente de verdad editada a mano
private-sources/pdf/               # originales; EXCLUIDO de Git vía .gitignore
private-sources/text/              # caché de texto/OCR, generada por scripts/ocr.py; EXCLUIDA
src/content/
  sources/    src-2012-tsjcyl-581.md …
  notes/      note-2012-tsjcyl-581-001.md …
  events/     event-2012-02-24-auto-ejecucion.md …
  actors/     actor-ayuntamiento-el-espinar.md …
  procedures/ proc-2009-jca-segovia-po-28.md …
  topics/     topic-recepcion.md …
  questions/  question-recepcion-001.md …
```

## 12. Ejemplos reales (piloto)

El modelo está instanciado con el corpus documental completo de la carpeta maestra: **36 Sources, 150 notas atómicas, 48 Events, 21 Actors, 11 Procedures, 4 Topics y 10 Questions**. Todo el contenido está en `editorialStatus: draft`: nada se ha promocionado todavía a `reviewed`.

Cobertura documental: los 42 PDF de la carpeta maestra están procesados (33), o registrados en `docs/DOCUMENT_REGISTRY.md` como duplicado (4), fragmento (2), anexo (1) o material de referencia (2). `scripts/inventory.py` no muestra ningún pendiente.

Arco temporal cubierto: de la memoria del Plan Parcial (agosto de 1966) a la circular de la Comunidad de Propietarios de 2026.

Casos límite que el corpus ejercita:

- **Fechas contradictorias entre documentos** → `EVENT-ACUERDO-TRANSACCIONAL-AGUA-001` (acuerdo fechado 3.6.2013 y 3.6.2018 dentro de la misma sentencia) y `EVENT-2012-05-14-AUTO-COMPLEMENTO` (auto fechado el 14 de mayo por la sentencia de apelación y el 4 de mayo por los escritos de las partes). Ambos con `dateStatus: disputed`, ambas candidatas en `dateEvidence` y el identificador congelado en lo que se supo al crearlo.
- **Afirmaciones contenidas en un documento transcrito dentro de otro** → locator "(transcripción del auto 177/2018)", "(transcripción de la SAP Madrid de 4.11.2002)", "(transcripción del convenio entre el Ayuntamiento y las promotoras)".
- **Alegación de parte no asumida por el tribunal** → `NOTE-2012-TSJCYL-581-010` y todas las notas de los Sources con `docType: escrito-de-parte`.
- **Documentos cuyo PDF no tenemos** → representados como Events con citas al documento que los menciona: el auto de complemento de 2012, la STSJ 217/2015, las resoluciones madrileñas de 2000 y 2002.
- **Un fichero con varios documentos dentro** → `SRC-2012-CP-AYTO-APELACIONES` (dos recursos de apelación), resuelto con un Source y `locator` diferenciado.
- **Copias distintas del mismo documento** → cuatro duplicados y dos fragmentos con sha256 propio, anotados en el Source afectado y en el registro documental.
- **Paginación impresa distinta de la física** → `printedPages` en las citas del informe jurídico de 2014 y de los recursos de 2012.
- **Extracción de texto poco fiable** → Sources escaneados con bloque `**Captura**` que indica qué páginas son OCR; `SRC-2017-JCA-SEGOVIA-22`, con capa de texto codificada que pierde todos los dígitos; y dos documentos de más de cien páginas con cobertura selectiva declarada en el propio Source.
