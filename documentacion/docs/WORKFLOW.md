# WORKFLOW — Cómo se incorpora un documento al corpus

Procedimiento operativo. La especificación de **qué** se escribe está en `docs/CONTENT_MODEL.md`; este documento describe **cómo** se llega hasta ahí, y por qué cada paso está donde está.

---

## 0. Antes de empezar

La carpeta maestra (`/mnt/c/Users/mario/OneDrive/LASR-DOC`) es **solo lectura**. Nunca se escribe, se mueve ni se renombra nada en ella. Todo el trabajo ocurre sobre copias en `private-sources/pdf/`, carpeta excluida de Git.

Comprobación de rutina antes de cualquier commit:

```sh
git status --short | grep private-sources    # debe salir vacío
```

## 1. Localizar lo pendiente

```sh
python3 scripts/inventory.py
```

Cruza por SHA-256 la carpeta maestra, la de trabajo y las fichas existentes, y regenera `docs/SOURCES_INVENTORY.md` y `docs/DOCUMENT_REGISTRY.md`. La línea que importa es la última:

```
Pendientes de analizar (0): []
```

Un fichero solo desaparece de esa lista de dos maneras: teniendo un `Source` con su `sha256`, o estando anotado en `docs/document_registry.json`.

**Los nombres de fichero engañan.** En este corpus, `Sentencia TSCyL Junio 2010.pdf` era la STSJ 271/2011 de junio de **2011**, `Auto Recepción.pdf` era el auto de ejecución de 24.2.2012 y `Estatutos EUC.pdf` no son los estatutos sino la comunicación municipal que los llevaba de anexo. Identificar un documento por su nombre es la primera fuente de error.

## 2. Copiar y volcar a texto

```sh
cp "$MAESTRA/Nombre Original.pdf" private-sources/pdf/nombre-provisional.pdf
python3 scripts/ocr.py private-sources/pdf/nombre-provisional.pdf
```

El nombre provisional es descriptivo y en kebab-case. El canónico se pone después, cuando el ID esté fijado (paso 5).

`scripts/ocr.py` produce un `.txt` en `private-sources/text/` con **un marcador por página, sin excepción**, incluidas las vacías: el número del marcador es exactamente el `pdfPages` que llevará la citación. Cada marcador dice si esa página venía con capa de texto o se ha reconocido por OCR.

Opciones útiles:

- `--jobs 4` para documentos largos; los de más de cien páginas conviene lanzarlos en segundo plano.
- `--force-ocr` cuando la capa de texto existe pero es basura. Ocurre: `SRC-2017-JCA-SEGOVIA-22` tiene una fuente de codificación no estándar cuyo texto se descifra con un desplazamiento de caracteres, pero **pierde todos los dígitos**.
- `--reindex` reconstruye el manifiesto desde las cabeceras de la caché si algo se descuadra.

## 3. Leer el documento entero

De la caché, no en diagonal. Lo que hay que salir sabiendo:

- **La fecha del documento**, que no es la de notificación ni la del sello de registro ni la que sugiera el nombre del fichero. Las tres inducen a error en este corpus.
- Emisor, número de resolución, rollo, procedimiento y partes institucionales.
- En qué página física vive cada afirmación que se vaya a citar.
- Si el documento contiene otros documentos transcritos dentro.

## 4. Decidir si genera ficha

No todo documento es un `Source`. Van al registro documental (`docs/document_registry.json`), no a `src/content/sources/`:

| Caso | `reason` |
|---|---|
| Otro escaneo de un documento ya fichado | `duplicate-of` |
| Copia parcial de un documento ya fichado | `fragment-of` |
| Acuse, anexo o continuación de otro escrito | `annex-of` |
| Normativa, doctrina, material de consulta | `reference-material` |
| Fragmento no atribuible a ningún documento conocido | `unidentified` |

Para confirmar un duplicado no basta el número de páginas: hay que **cotejar el texto de una página interior** de ambos. Cuando el duplicado se confirma, se añade además una línea al bloque `**Captura**` o `**Versiones**` del Source afectado remitiendo al registro.

## 5. Fijar el ID y renombrar

El ID sigue `docs/CONTENT_MODEL.md` §8 y **no cambia nunca** una vez creado. Solo incorpora datos de identificación externa objetiva y no controvertida: si el auto no lleva número, el ID usa un slug descriptivo; si la fecha está en discusión, no entra en el ID.

```sh
mv private-sources/pdf/nombre-provisional.pdf private-sources/pdf/<id-en-minusculas>.pdf
python3 scripts/ocr.py private-sources/pdf/<id-en-minusculas>.pdf
```

La segunda llamada no reprocesa nada: el manifiesto está indexado por hash y se limita a mover el `.txt`.

## 6. Escribir el Source

Datos que se toman de la máquina, nunca de memoria:

```sh
sha256sum private-sources/pdf/<id>.pdf
pdfinfo   private-sources/pdf/<id>.pdf | grep Pages
```

`originalFilename` se copia exacto, con sus erratas si las tiene. El cuerpo lleva siempre un bloque **`**Captura**`** que diga: si hay capa de texto o es OCR y en qué páginas; si la paginación impresa difiere de la física; y qué se ha cotejado visualmente.

Cuando el documento supera las cien páginas o es mayoritariamente gráfico, la cobertura es **selectiva y declarada**: un índice de secciones en el cuerpo, notas solo de lo que el corpus necesita citar, y una frase explícita diciendo qué queda sin analizar. Un hueco declarado es información; un hueco silencioso se lee como cobertura completa.

`privacyReview` se rellena con honestidad. `needs-redaction` en cuanto aparezcan nombres de particulares, DNI, domicilios, teléfonos, correos, cuentas o firmas.

## 7. Escribir las notas

Una nota, una afirmación. El `title` debe poder verificarse contra las páginas citadas sin leer el resto de la nota.

**La regla que más trabajo ahorra a largo plazo**: toda página de la que salga una `quote` literal se lee como imagen antes de escribirla, no desde la caché. El OCR de estos escaneos confunde letras dentro de palabras, pierde el último carácter de cada línea junto al margen y no es fiable para dígitos. La caché sirve para navegar y localizar; el PDF es la fuente.

Durante esta tanda, esa comprobación evitó dar por buenas dos afirmaciones erróneas y descubrió una discrepancia de fecha entre documentos que ninguna lectura del volcado habría detectado.

Orientación de volumen: 3-8 notas para una resolución típica, 1-3 para una carta corta, hasta 10 para un documento extenso con cobertura selectiva.

Sobre el tipo: lo que afirma un escrito de parte es `claim`, con el cuerpo abriendo en `**Alegación de parte, no hecho probado**:`. Lo que afirma un documento transcrito dentro de otro se atribuye al documento transcrito, y el `locator` lo dice.

## 8. Cablear el grafo

Crear los `Actor` y `Procedure` que falten —solo los que se vayan a referenciar de verdad—, extender o crear los `Event` correspondientes, y rellenar `topics`, `actors`, `events` y `relations`. Comprobar si alguna `Question` gana un `answeredBy`.

Cuando el documento nuevo desmiente algo que el corpus daba por cierto —"no disponemos de su PDF", "solo aparece en este acta", "no constan en el corpus"—, **hay que ir a corregir esas frases**. Dejarlas es peor que no haber incorporado el documento.

Si dos fuentes dan fechas distintas para el mismo hecho, no se elige: `date: null`, `dateStatus: disputed` y ambas candidatas en `dateEvidence`.

## 9. Verificar

```sh
npm run build                    # Zod + graph.ts: IDs, fichero=ID, integridad referencial, rango de páginas
LASR_PREVIEW=1 npm run build     # imprescindible: la build pública no genera las páginas draft
npm run check
python3 scripts/inventory.py
```

El segundo no es opcional. La build pública no renderiza contenido `draft` ni el área de revisión, así que un fallo de plantilla o una etiqueta que falte en `policy.ts` **solo aparece con `LASR_PREVIEW=1`**.

Para revisión editorial: `npx astro dev` y `/revision/`, que da los recuentos por estado y permite recorrer las notas una a una con el checklist de §7 delante.

## 10. Commit

Un commit por documento, con el cuerpo explicando qué aporta y qué decisiones se tomaron. Preparar los cambios de forma explícita (`git add src/content docs`) en lugar de `git add -A`, para no arrastrar cambios de herramientas dentro de un commit de contenido.

---

## Lo que este flujo no hace

**No promociona nada a `reviewed`.** Todo el contenido nace `editorialStatus: draft` y ahí se queda. La promoción es un acto humano, con el PDF delante y el checklist de `CONTENT_MODEL.md` §7: comprobar que la fuente existe, que la cita corresponde a la página indicada, que la nota representa fielmente la fuente, que no se ha añadido ninguna conclusión no sustentada y que `type` y `basis` son correctos.

El borrador **sí se publica**, con el estado a la vista: ocultar todo el corpus dejaba la web en 26 páginas de 433, es decir, inútil. Lo que `src/lib/policy.ts` sigue siendo es el punto único donde se decide qué se muestra y con qué etiqueta, de modo que excluir una entrada concreta sea un cambio de una línea y en un solo sitio.
