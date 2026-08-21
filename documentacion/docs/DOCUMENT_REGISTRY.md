# Registro de documentos no fichables

Generado por `scripts/inventory.py` a partir de `docs/document_registry.json`,
que es la fuente de verdad y se edita a mano. Recoge los ficheros originales que
**no** dan lugar a un `Source`, con la evidencia de por qué. Ver `docs/CONTENT_MODEL.md` §3.1.

| Fichero | SHA-256 (8) | Motivo | Documento | Evidencia |
|---|---|---|---|---|
| `SOLICITUD de AMPARO2.pdf` | `e3e3ea37` | annex-of | SRC-2009-CP-LASR-AMPARO | Página única con sello del Registro General del Tribunal Constitucional (24-25 de julio de 2009) y referencia al art. 1512 LEC. |
| `Estatutos EUC.pdf` | `a5775585` | duplicate-of | SRC-2013-AYTO-EL-ESPINAR-RECEPCION | Mismo número de páginas (17) y texto idéntico en la pág. PDF 5 (autorización de uso gratuito de las instalaciones de agua). |
| `Sentencia Acuerdo Aquagest.pdf` | `fa4cddd8` | duplicate-of | SRC-2005-JPI3-SEGOVIA-139 | Mismo número de páginas (5) y texto idéntico en la pág. PDF 3. |
| `Sentencia Audiencia Sego 220104.pdf` | `99981b78` | duplicate-of | SRC-2003-AP-SEGOVIA-323 | Mismo número de páginas (10) y texto idéntico en la pág. PDF 4. |
| `Sentencia Burgos Recepcion YA 21-12-2012.pdf` | `271c0893` | duplicate-of | SRC-2012-TSJCYL-581 | Mismo número de páginas (22) y texto idéntico en la pág. PDF 3 (antecedente Segundo, recurso de apelación de 16.3.2012). |
| `2º Sentencia 13072010 Aud Segovia Junta 2006.doc.pdf` | `83ea0e10` | fragment-of | SRC-2010-AP-SEGOVIA-156 | Sus 3 páginas reproducen las págs. 4-6 del texto de la sentencia; la frase "permitan la individualización de los gastos como pretende la Comunidad" aparece en ambos. |
| `documento_imagen.pdf` | `09407afd` | fragment-of | SRC-2011-TSJCYL-271 | Página suelta con pie "Página 10 de 38" y fecha de junio de 2011. Cuatro frases suyas aparecen en el texto de la STSJ 271/2011: "dando lugar al P.O 753/2008", "Etapas de Realización", "Modo de ejecución de las obras de urbanización" y "27 de julio de 2009". |
| `37633481_112_DOCSLEG_LCyL_1998_191.pdf` | `a922439b` | reference-material | — | Ley 1/1998, de 4 de junio, de Régimen Local de Castilla y León, en versión de base de datos jurídica (27 páginas, con capa de texto). |
| `EMPADRONADO Sí o No.pdf` | `a26d48f4` | reference-material | — | Nota de una página, sin membrete, fecha ni firma, que resume la normativa general del Padrón Municipal (RD 1690/1986 y art. 15 LRBRL) y el efecto del empadronamiento sobre la financiación municipal. Los metadatos del PDF la atribuyen a un particular y la fechan el 18 de agosto de 2026. |
| `EXTRACTO LEY 1 1998 de 04 06 98 TEXTO CONSOLIDADO 14052024.pdf` | `87a03ad8` | reference-material | — | El mismo texto legal que la entrada anterior, en el texto consolidado del BOE a 14.5.2024 (3 páginas). |
| `POBLACIÓN LASR + LAV.pdf` | `ef881c49` | reference-material | — | Tabla de una página que compara los núcleos de El Espinar por población a 31.12.2025 y por dotaciones municipales (edificio municipal, colegio, consultorio, instalaciones deportivas, centro cívico, de jóvenes y de mayores, biblioteca y reparto de correo). Declara como origen de la población los datos publicados por el Ayuntamiento el 5.1.2026 y, para Los Ángeles de Vegas de Matute, el INE a 31.12.2024. Metadatos del PDF: mismo particular, 18 de agosto de 2026. |

## Notas

- **`2º Sentencia 13072010 Aud Segovia Junta 2006.doc.pdf`** — Ya documentado en el cuerpo del Source.
- **`37633481_112_DOCSLEG_LCyL_1998_191.pdf`** — Normativa aplicable, no documentación del caso: no es Source (CONTENT_MODEL §3.1). El corpus cita la norma a través de la resolución que la aplica.
- **`EMPADRONADO Sí o No.pdf`** — Material divulgativo elaborado por un vecino, no documento del caso: no tiene emisor dentro del relato, ni procedimiento, ni contenido específico sobre Los Ángeles de San Rafael. La normativa que resume se cita, cuando haga falta, a través de la resolución que la aplique.
- **`EXTRACTO LEY 1 1998 de 04 06 98 TEXTO CONSOLIDADO 14052024.pdf`** — Que existan dos ejemplares del mismo texto en distinto estado de consolidación ilustra por qué citar la página de un ejemplar sería peor trazabilidad que citar artículo y boletín.
- **`Estatutos EUC.pdf`** — El nombre del fichero es engañoso en las dos copias: no son los estatutos de la EUC, sino la comunicación del Ayuntamiento que los lleva como Anexo 2.
- **`POBLACIÓN LASR + LAV.pdf`** — Compilación de un vecino, no documento primario: la columna de dotaciones no declara fuente y contiene celdas marcadas con interrogante. Su contenido es relevante —Los Ángeles de San Rafael figura como tercer núcleo del término por población (1.853 habitantes) y sin la mayoría de las dotaciones que sí tienen núcleos menores—, pero para incorporarlo al corpus haría falta la publicación municipal de 5.1.2026, que sí sería Source. Queda anotado como pista.
- **`SOLICITUD de AMPARO2.pdf`** — Acuse de registro del recurso de amparo. Se ficha el escrito principal; esta página se documenta en el cuerpo de su Source.
- **`Sentencia Acuerdo Aquagest.pdf`** — Copiado como private-sources/pdf/sentencia-aud-139-2005-anul-asamblea-14032004.pdf. Ni el nombre original ni el de trabajo describen bien el documento: no es una sentencia sobre Aquagest ni de la Audiencia, sino la del JPI nº 3.
- **`Sentencia Audiencia Sego 220104.pdf`** — Copia recibida por fax el 22.1.2004; la fichada es la versión unificada notificada ese mismo día. Ya documentado en el cuerpo del Source.
- **`Sentencia Burgos Recepcion YA 21-12-2012.pdf`** — Escaneo independiente, también sin capa de texto. No se copia a private-sources/pdf/.
- **`documento_imagen.pdf`** — Procede del original notificado, de 38 páginas; la copia fichada es la versión CENDOJ, con maquetación distinta (26 páginas). El dato de las 38 páginas del original solo consta aquí.
