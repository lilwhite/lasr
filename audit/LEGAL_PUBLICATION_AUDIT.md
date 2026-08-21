# Auditoría jurídica de publicación

**Fecha:** 21 de agosto de 2026
**Alcance:** `docs/` (portal), `documentacion/src` y `documentacion/docs` (guía documental), el historial de Git y la cadena de despliegue.
**Herramienta:** `scripts/legal/legal_scan.py` v1 — 374 ficheros, 372 inspeccionados, 2 no inspeccionables.

> Esto lo redacta un asistente, no un abogado, y no es asesoramiento jurídico. Reduce la superficie de discusión y deja rastro de las decisiones; no sustituye una revisión profesional, que aquí es especialmente aconsejable.

> Ningún hallazgo de este informe reproduce el dato que describe. Se cita la categoría, la ruta y la regla; nunca el valor ni el nombre de la persona afectada.

## Veredicto

**REVISIÓN HUMANA NECESARIA — RIESGO ALTO**

Dos exposiciones están vivas ahora mismo y ninguna se resuelve con la herramienta: exigen una decisión y una operación manual. El resto es postura, y va encaminado.

| Gravedad | Hallazgos |
|---|---|
| Crítica | 2 |
| Alta | 5 |
| Media | 6 |
| Baja | 3 |
| Informativa | 1 |

---

## Crítica

### LEGAL-CONFIDENTIAL-001 · Exportación de un grupo de WhatsApp en el historial público
**Dónde:** commit `bdbaeab` (10 de marzo de 2026), **ancestro de `origin/main`**
**Qué:** un ZIP de 4.919.896 bytes con la exportación completa de un grupo de copropietarios, el `.txt` del chat (28.871 bytes) y un vídeo de 4.911.328 bytes. Se borraron al día siguiente, pero siguen alcanzables desde el historial y descargables del repositorio público.

**Por qué importa.** Un export de WhatsApp lleva dentro nombres, números de teléfono y el contenido íntegro de conversaciones privadas de vecinos que nunca consintieron su publicación. Es el único hallazgo de todo el sitio con encaje penal posible —art. 197 CP, descubrimiento y revelación de secretos— además del incumplimiento del RGPD. Las reglas `*.zip` y `*.mp4` del `.gitignore` se añadieron **después** del daño y no lo revierten.

**Acción.** Reescritura del historial con `git-filter-repo`, **que no está instalado**. En este orden: rotar cualquier credencial, reescribir, forzar el push, avisar a todo el que tenga un clon —cambian todos los identificadores de commit— y pedir a GitHub la purga de vistas cacheadas y de forks. Sesión dedicada.

**Estado:** abierto. Es la acción más urgente del informe.

### LEGAL-PRIVACY-001 · PDF con dos números de documento de identidad servido en producción
**Dónde:** `docs/documentacion-relevante/estatutos-euc.pdf` en `origin/main`
**Qué:** la página 4 publica en claro dos nombres completos con su documento de identidad y un domicilio postal, más nombres de secretario, alcalde y notario, un número de protocolo notarial y una firma manuscrita escaneada. Comprobado el 21 de agosto: la URL responde 200 con 6.793.292 bytes.

**Por qué importa.** Es un documento descargable, indexable y ofrecido activamente desde la sección de documentos. Que sea un escaneo sin capa de texto no protege nada: se extrae con OCR en segundos.

**Acción.** La PR #63 lo retira y reapunta su ficha al tema de la guía documental. **Falta fusionarla y promocionar `dev` a `main`.** Hasta que el despliegue corra, el fichero se sigue sirviendo.

**Estado:** corregido en rama, pendiente de promoción a producción.

> El escáner clasifica este fichero como `LEGAL-OPAQUE-002`, no como limpio: es un escaneo sin capa de texto y la herramienta se niega a darlo por bueno. Esa es la respuesta correcta, y la razón por la que «no pude inspeccionarlo» nunca equivale a «está limpio».

---

## Alta

### LEGAL-PRIVACY-002 · Menores y causas penales en el archivo de prensa
**Dónde:** `docs/data/prensa/curated_news.json`
**Qué:** el archivo publicaba 327 noticias, de las que 292 no tenían relación con el objeto del sitio. Incluían una menor identificada con nombre, apellidos y localidad, el fallecimiento de otra menor, detenciones, condenas y violencia de género: datos del art. 10 del RGPD.

**Por qué importa.** Publicarlas no tiene ninguna justificación en el objeto del sitio, y es lo que menos defensa admite.

**Cómo se coló, y qué se aprendió.** La primera corrección redujo el archivo a las 35 noticias con `isRelevant: true` dando por hecho que eran las del conflicto. No lo eran: el marcador puntúa la cercanía al topónimo, no el asunto, así que las dos noticias sobre menores seguían dentro porque decían «Los Ángeles de San Rafael». Lo detectó el escáner al pasarlo sobre lo ya publicado; a ojo hacía falta leer 35 titulares uno a uno. **Un umbral de relevancia no es un criterio editorial.**

**Acción.** Hecho: la puntuación decide qué es candidato y dos puertas deciden qué se publica —una lista de exclusión que nada supera y una de temas que hay que cumplir—. Quedan 8 noticias. De cada una, titular, medio, fecha y enlace; sin entradilla, lo que resuelve además la reproducción de texto ajeno.

**Estado:** corregido en la PR #63, pendiente de fusión.

### LEGAL-SECURITY-001 · El despliegue copia `docs/` sin lista blanca
**Dónde:** `.github/workflows/pages.yml:104` — `cp -r docs/* dist/`
**Qué:** todo lo que aterrice en `docs/` se publica, sin declaración ni revisión. Es el mecanismo exacto por el que se publicaron cuatro documentos internos de despliegue en marzo y el PDF con documentos de identidad en agosto. `*.pdf` y `*.docx` no están en ningún `.gitignore`.

**Acción.** Sustituir la copia por `gate.py --copy-portal dist`, que copia solo lo declarado en `audit/portal-manifest.json` y aborta si faltan los ficheros obligatorios. Probado: 31 ficheros publicados, 5 excluidos, sitio íntegro.

**Estado:** manifiesto listo (este commit); el cambio del workflow va en la fase 6.

### LEGAL-LEAK-001 · Rutas personales y nombres de fichero originales en el repositorio público
**Dónde:** `documentacion/docs/sources_inventory.json`, `SOURCES_INVENTORY.md`, `WORKFLOW.md`, `documentacion/scripts/inventory.py`
**Qué:** 4 apariciones de rutas absolutas del sistema de ficheros de una persona concreta, una de ellas apuntando a un segundo repositorio. Junto a ellas, el inventario de 46 documentos originales con su nombre de fichero real, su SHA-256, su número de páginas y si tiene capa de texto.

**Por qué importa.** La ruta vincula el sitio a una persona identificable, que es justo lo que un aviso legal sin datos personales trata de evitar. Y el inventario es, en la práctica, el mapa de dónde está lo sensible: quién tiene el original puede confirmar por su huella que la copia del proyecto es la suya. Un nombre de fichero ya filtró un nombre propio una vez y hubo que redactarlo a mano.

**Acción.** Parametrizar la ruta (`LASR_MASTER_DIR` ya existe; falta que el inventario no la escriba) y dejar de publicar los nombres de fichero originales.

**Estado:** abierto. Fase 2.3 del plan de exposición legal.

### LEGAL-LEAK-002 · El corpus publica dónde vive el material privado
**Dónde:** 63 apariciones en 42 ficheros de `documentacion/src/content/sources/` y `documentacion/docs/`
**Qué:** cada una de las 36 fichas de fuente declara `file: private-sources/pdf/…`, y las notas de privacidad describen con detalle qué datos personales contiene cada original.

**Por qué importa.** Los PDF no están en el repositorio y nunca lo estuvieron —comprobado: `git ls-files` y `git rev-list --objects --all` no devuelven nada bajo `private-sources/`—. Pero el repositorio sí publica el índice de qué contiene cada uno.

**Acción.** Reducir las notas de privacidad a un código de estado sin descripción, o sacarlas del árbol versionado.

**Estado:** abierto.

### LEGAL-COOKIES-001 · Analítica sin consentimiento y sin aviso legal
**Dónde:** `docs/assets/js/ga4.js` y seis páginas HTML
**Qué:** el portal carga Google Analytics 4 sin banner de consentimiento, sin política de cookies, sin aviso legal, sin identificación del responsable y sin canal de contacto. La guía documental sí tiene `/documentacion/aviso-legal/`; el portal no tiene nada.

**Por qué importa.** El art. 22.2 de la LSSI exige consentimiento previo e informado para almacenar información en el equipo del usuario. Y la analítica es lo que convierte al proyecto en responsable de un tratamiento, con las obligaciones de información que eso arrastra.

**Acción.** Retirar GA4 y publicar un aviso legal con canal de retirada. **Un canal de retirada que funcione es la medida más protectora de todo el plan, y no expone a nadie: un correo no dice quién eres.**

**Estado:** abierto. Fase 9.

---

## Media

### LEGAL-THIRDPARTY-001 · Cuatro terceros reciben la IP de quien visita el sitio
**Dónde:** `docs/index.html` y otras cinco páginas, `docs/parcelas/index.html`, `docs/assets/js/parcelas.js`

| Tercero | Dónde | Qué recibe |
|---|---|---|
| `www.googletagmanager.com` | 6 páginas | IP, user-agent, página visitada |
| `cdn.jsdelivr.net` | 3 páginas | ídem, por cada carga de biblioteca |
| `unpkg.com` | mapa de parcelas | ídem |
| `tile.openstreetmap.org` | mapa de parcelas | **una petición por cuadrícula**: qué parte del núcleo está mirando |

El portal declara una CSP que autoriza estos dominios, lo cual indica que alguien lo pensó. Pero **una CSP autoriza la petición, no la evita**: el navegador la hace igual y el tercero recibe los datos.

Las teselas de OpenStreetMap son las más discretas y las más reveladoras: mientras alguien arrastra el mapa de parcelas, OSM va recibiendo qué zona de la urbanización está examinando.

**Acción.** Retirar la analítica; alojar Leaflet y los estilos en el propio sitio; y para el mapa, o alojar las teselas o advertirlo en el aviso legal.

**Estado:** abierto. Aceptado temporalmente en el manifiesto, con motivo declarado.

### LEGAL-PROCEDURAL-001 · El sitio publica su propio andamiaje interno
**Dónde:** `documentacion/src/pages/documentos/[slug].astro:35, 38-39, 62, 63`
**Qué:** las 37 fichas de documento publican el identificador canónico interno, el número de páginas, el **SHA-256 del PDF privado**, y las etiquetas de estado de publicación y privacidad — que anuncian en claro qué once documentos su propio autor ha marcado como «requiere anonimización».

**Por qué importa.** El hash funciona en las dos direcciones: garantiza la integridad, y también permite a quien tenga el original confirmar que la copia del proyecto es la suya, y acotar por dónde salió.

**Acción.** Envolver las cuatro cosas en `PREVIEW`, como ya se hace en `temas/[slug].astro:79`.

**Estado:** abierto. Fase 8.

### LEGAL-SECURITY-002 · Documentación de operación servida en crudo
**Dónde:** `docs/DEPLOY.md`, `docs/WORKFLOW.md`, `docs/RELEASES.md`, `docs/automatizacion-prensa.md`, `docs/data/prensa/sources.json`
**Qué:** cinco ficheros accesibles hoy en lasr-info.es sin estar enlazados desde ninguna parte. No contienen datos personales, pero nadie decidió publicarlos: lo decidió el `cp -r` sin filtro. El último expone además la configuración de raspado —dominios, endpoints y umbrales—.

**Acción.** Hecho en este commit: los cinco quedan declarados `publish: false` en el manifiesto y dejan de copiarse en cuanto la fase 6 cambie el workflow.

**Estado:** declarado; efectivo al aplicar la fase 6.

### LEGAL-SECURITY-003 · La caché del despliegue puede republicar un build de vista previa
**Dónde:** `.github/workflows/pages.yml:85-90` y `:93`
**Qué:** la clave de caché de `documentacion/dist` no incluye `LASR_PREVIEW`. Un build hecho una vez con la vista previa activada quedaría cacheado con el área `/revision/` dentro —contadores de privacidad, identificadores canónicos, qué documentos requieren anonimización— y se restauraría en ejecuciones posteriores. Y como `check_links.py` está dentro del `if: cache-hit != 'true'`, se publicaría **saltándose también la validación**.

**Acción.** Añadir `LASR_PREVIEW` a la clave y sacar todas las validaciones del condicional: solo el `npm run build` debe ser cacheable.

**Estado:** abierto. Fase 6.

### LEGAL-SECURITY-004 · Un cron empuja a la rama publicada sin revisión
**Dónde:** `.github/workflows/prensa.yml`
**Qué:** el agregador de prensa se ejecuta a diario, hace commit directo sobre `main` como `github-actions[bot]` y dispara el despliegue, sin PR ni revisión humana. El alcance es un solo JSON, pero es un canal de escritura automatizado hacia la rama que se publica.

**Acción.** Correr el escáner y el check de regresión antes del push; si fallan, no empujar.

**Estado:** abierto. Fase 6.

### LEGAL-PROCEDURAL-002 · El aviso legal de la guía afirma más de lo que podía sostener
**Dónde:** `documentacion/src/content/pages/aviso-legal.md`
**Qué:** dice que ningún dato personal de la documentación original se ha copiado a la web. Hasta hoy, el corpus lo desmentía: había un apellido familiar en nueve páginas y un nombre de pila en una ficha.

**Acción.** La PR #63 retira ambos, con lo que la afirmación pasa a ser cierta. Aun así, el aviso legal debe revisarse: no menciona el RGPD, ni el responsable del tratamiento, ni la base jurídica, ni los derechos, ni las cookies.

**Estado:** el hecho, corregido; el texto, pendiente.

### LEGAL-COPYRIGHT-001 · Licencia MIT sobre contenido de terceros
**Dónde:** `LICENSE`, `docs/assets/config.json` y el pie del portal
**Qué:** el sitio anuncia licencia MIT para todo, lo que ofrece a cualquiera derecho irrestricto sobre material del que el proyecto no es titular: prensa, cartografía catastral y documentos ajenos.

**Acción.** MIT para el código, licencia de contenido aparte para lo propio, y nota explícita de que los materiales de terceros conservan sus derechos.

**Estado:** abierto.

---

## Baja

### LEGAL-NAME-001 · 150 candidatos a nombre de particular pendientes de revisión
**Dónde:** 80 ficheros de `docs/` y `documentacion/`
**Qué:** cadenas capitalizadas que no figuran entre los 21 actores declarados. **Es una heurística**, y por eso su severidad es leve y su estado `needs-human-review`: propone a quién mirar, no afirma quién es. Buena parte son términos institucionales o fragmentos de nombres de fichero.

**Acción.** Triar por lotes y aceptar en `legal-baseline.json` lo que resulte no ser una persona física, para que el escáner no lo vuelva a levantar.

### LEGAL-PDF-001 · Metadatos conservados en el PDF que sigue publicado
**Dónde:** `docs/documentacion-relevante/estatutos-comunidad.pdf`
**Qué:** cuatro metadatos de documento (creador, productor y afines). Es el vector de fuga que nadie mira: un PDF exportado desde un procesador de textos puede nombrar a quien lo escribió aunque el texto visible esté anonimizado. El fichero es además un escaneo sin capa de texto, así que su contenido **no ha sido inspeccionado**.

**Acción.** Revisión humana página a página antes de mantenerlo publicado, y saneado de metadatos.

**Estado:** declarado `needs-human-review` en el manifiesto.

### LEGAL-PRIVACY-007 · Precisión del censo catastral
**Dónde:** `docs/assets/js/parcelas.js`
**Qué:** 2.112 inmuebles con coordenadas de precisión métrica; 541 con referencia catastral de 20 dígitos y dirección con escalera, planta y puerta, cada uno enlazado al servicio que devuelve su ficha. No hay nombres de propietarios —comprobado—, lo que rebaja mucho el riesgo.

**Acción.** Atribución y condiciones de reutilización del Catastro, que hoy no aparecen; y truncar las referencias a los 14 dígitos de parcela y las direcciones a portal. El uso declarado —contar propietarios para el umbral del art. 16.2 LPH— funciona igual a nivel de parcela.

**Estado:** aceptado en el manifiesto con motivo declarado.

---

## Informativa

### Lo que está bien, y conviene no perder
- **`private-sources/` nunca entró en el repositorio.** Ni en el árbol ni en el historial: comprobado con `git ls-files` y `git rev-list --objects --all`. La doble regla en dos `.gitignore` funcionó.
- **Ningún nombre de propietario en los datos catastrales**, ninguna fotografía de personas o viviendas, ninguna matrícula.
- **El área de revisión editorial está bien cerrada:** las tres páginas de `/revision/` devuelven `[]` fuera de vista previa, y el build lo confirma.
- **`canLinkPdf()` exige dos condiciones a la vez** y hoy devuelve falso para los 36 documentos: ningún original es descargable desde la guía.
- **El aparato documental es riguroso:** cada afirmación indica documento y página, y el build se niega a terminar si una cita apunta a una página que no existe.

---

## Redacciones necesarias

1. Purgar del historial el ZIP, el `.txt` y el vídeo del commit `bdbaeab`.
2. Retirar de producción `estatutos-euc.pdf` promocionando la PR #63.
3. Dejar de escribir la ruta de la carpeta maestra y los nombres de fichero originales en el inventario.
4. Reducir las notas de privacidad a un código de estado.
5. Sacar de producción el SHA-256, el identificador canónico y las etiquetas de privacidad de las fichas de documento.

## Cambios editoriales

1. Aviso legal del portal, con responsable, base jurídica, derechos y canal de retirada.
2. Revisar el aviso legal de la guía: hoy no menciona el RGPD ni las cookies.
3. Separar la licencia del código de la del contenido.
4. Atribución del Catastro en el mapa de parcelas.

## Decisión de publicación

**No se puede considerar el sitio jurídicamente saneado hasta resolver `LEGAL-CONFIDENTIAL-001` y `LEGAL-PRIVACY-001`.** El resto de hallazgos son postura y pueden abordarse por fases sin detener el sitio.

Ningún hallazgo de este informe exige retirar el proyecto ni dejar de publicar. El planteamiento de fondo —afirmaciones con su fuente y su página, ningún original publicado— es sólido; lo que falla es el perímetro.

## Incertidumbre jurídica

Tres cuestiones dependen de una ponderación que un profesional debe hacer, no una herramienta:

1. **El chat de WhatsApp.** Qué obligaciones de notificación genera la exposición, si procede comunicarlo a las personas afectadas y en qué plazo. Es la pregunta más urgente. Al abogado hay que darle: qué se publicó, desde cuándo, cuántas personas aparecen y qué se ha hecho para retirarlo.
2. **El ámbito de la LSSI.** Si un sitio vecinal sin ánimo de lucro, sin publicidad ni donaciones y sin analítica queda fuera del art. 10, que es la pieza sobre la que se sostiene no publicar los datos de quien lo mantiene.
3. **La ponderación del art. 85 del RGPD.** Hasta dónde ampara la libertad de información la publicación de resoluciones judiciales identificando a particulares, en un sitio plenamente indexable, cuando el CENDOJ las publica anonimizadas.

## Cómo reproducir este informe

```sh
python3 scripts/legal/legal_scan.py --paths docs documentacion/src documentacion/docs --json
python3 scripts/legal/gate.py --check-manifest
```
