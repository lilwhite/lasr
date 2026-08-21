# WEB_DESIGN — Diseño, experiencia y arquitectura de información

Especificación de la capa pública de LASR-Web. `docs/CONTENT_MODEL.md` define **qué** se guarda; este documento define **cómo se muestra**. Si los dos entran en conflicto, manda CONTENT_MODEL: la capa visual se apoya sobre el modelo, nunca al revés.

---

## 1. Principios

**1.1 Divulgación primero, evidencia debajo.** Un vecino que llega desde un enlace de WhatsApp debe entender de qué se habla antes de encontrarse una sola palabra técnica. La evidencia no se esconde: se ofrece un nivel más abajo, siempre a un clic.

**1.2 El vocabulario interno no sale a la superficie.** "Nota atómica", "MOC", "evidenceStatus", "Zettelkasten" y los identificadores canónicos (`NOTE-2012-TSJCYL-581-004`) son herramientas de trabajo. El lector ve afirmaciones, documentos, fechas y preguntas.

**1.3 Cada afirmación lleva su procedencia pegada.** No es un pie de página opcional: es la característica del producto y por tanto el eje del diseño.

**1.4 Lo que no se sabe se dice.** Una sección vacía con una explicación honesta vale más que una sección rellena. El estado "no consta" es de primera clase, no una excepción a maquetar deprisa.

**1.5 Neutralidad.** Se distingue siempre entre lo que un documento establece, lo que una parte alega y lo que nadie ha acreditado. Sin adjetivos de bando.

**1.6 Sin dato inventado.** Ninguna cifra, gráfico ni afirmación que no salga de las colecciones. Los recuentos se calculan desde el grafo, nunca se escriben a mano.

**1.7 Una sola fuente de verdad.** Si algo es derivable de las colecciones, se deriva. Nunca convivirán una cronología escrita a mano y otra generada.

**1.8 Rendimiento y privacidad como parte del diseño.** Sitio estático, sin peticiones a terceros, sin JavaScript salvo donde aporte algo real. Desde la integración en el portal, ese «algo real» son tres ficheros que no hacen nada funcional: los que respetan la preferencia de tema claro/oscuro del resto del sitio. Ninguna página depende de JavaScript para mostrar su contenido.

---

## 2. Arquitectura de información

### 2.1 Las dos capas

| | Capa 1 — Divulgación | Capa 2 — Evidencia |
|---|---|---|
| Para quién | Cualquier vecino | Quien quiere comprobar |
| Entra por | Menú, enlace compartido | Una cita, "¿de dónde sale esto?", "explorar toda la documentación" |
| Contenido | Inicio, Historia, Temas, Cronología, Preguntas, Quién es quién, Metodología | Documentos, Afirmaciones, Acontecimientos, Procedimientos |
| Registro | Narrativo | Documental |

La capa 2 **no está en el menú principal**. Se llega a ella desde el contexto que le da sentido.

### 2.2 Las dos grandes áreas

La interfaz agrupa los temas en dos bloques, a petición del vecindario:

```
COMUNIDAD Y RECEPCIÓN DE LASR
├── Recepción de la urbanización
├── La Entidad Urbanística de Conservación
├── El agua: abastecimiento y saneamiento
└── Las juntas de la Comunidad de Propietarios

DESANEXIÓN
└── (por documentar)
```

Se implementa con un campo `area` en `topics`: un enum cerrado, **no una jerarquía**. Una jerarquía real invitaría a calcular pertenencia transitiva —que las afirmaciones de un tema cuenten también en su contenedor— y eso duplicaría evidencia. `area` es clasificación de navegación y no toca el grafo.

**Una afirmación puede aparecer en varios contextos sin duplicarse.** La organización temática de la interfaz jamás altera la evidencia subyacente.

### 2.3 Mapa del sitio

**Capa 1**

| Ruta | Qué es |
|---|---|
| `/` | Portada |
| `/historia/` | Narrativa breve para situarse |
| `/temas/` | Índice, agrupado en las dos áreas |
| `/temas/<slug>/` | Página temática (§5) |
| `/cronologia/` | Los 48 acontecimientos, agrupados por década |
| `/preguntas/` · `/preguntas/<slug>/` | Preguntas frecuentes |
| `/actores/` · `/actores/<slug>/` | Quién es quién |
| `/metodologia/` | Cómo verificamos la información |
| `/aviso-legal/` | Protección de datos y descargo |
| `/404` | |

**Capa 2**

| Ruta | Qué es |
|---|---|
| `/documentos/` · `/documentos/<slug>/` | Fichas de documento |
| `/documentos/mapa/` | Mapa documental (§6.5) |
| `/notas/<slug>/` | Afirmaciones |
| `/acontecimientos/<slug>/` | Acontecimientos (`/cronologia/` es su índice) |
| `/procedimientos/` · `/procedimientos/<slug>/` | Procedimientos judiciales |

**Menú principal, seis entradas**: Inicio · Temas · Cronología · Preguntas · Documentos · Metodología.
En el pie: Historia, Quién es quién, Procedimientos, Aviso legal.

### 2.4 Navegación

Sin mega-menú. Barra plana, seis entradas, `aria-current` en la activa. En móvil no se pliega en hamburguesa: seis etiquetas cortas caben en dos líneas y una hamburguesa esconde la navegación justo a quien más la necesita.

Migas de pan en capa 2, donde se entra por enlaces profundos: `Inicio › Recepción › STSJ 271/2011`.

---

## 3. Sistema visual

### 3.1 La tesis

Lo característico de este proyecto no es el paisaje de la sierra: es que **cada afirmación lleva pegado un número de página**. La portada abre con una afirmación documentada y su procedencia inmediatamente debajo. Quien llega entiende en tres segundos qué clase de sitio es este.

### 3.2 El elemento distintivo: el aparato documental

Un registro tipográfico secundario, en monoespaciada, que recorre todo el sitio llevando la procedencia, maquetado como el aparato crítico de una edición: en pantalla ancha ocupa una columna estrecha junto a la prosa; en móvil se pliega bajo la afirmación.

Es la encarnación visual de las dos capas. **Toda la audacia del diseño se gasta aquí**; el resto del sistema es deliberadamente discreto.

### 3.3 Tipografía

Superfamilia **IBM Plex**, autoalojada vía `@fontsource` — cero peticiones a terceros, compatible con GitHub Pages.

| Rol | Familia | Pesos |
|---|---|---|
| Narrativa y titulares | Plex Serif | 400, 600 |
| Interfaz | Plex Sans | 400, 600 |
| Aparato documental | Plex Mono | 400 |

Una sola superfamilia, tres roles, diseñada por un mismo equipo para la documentación técnica de una institución. Subsetada a `latin-ext`, `font-display: swap`, precarga solo de los dos ficheros de la portada.

Escala de siete pasos, con `clamp()` en los dos mayores. Medida de lectura: 46 rem (~68 caracteres).

### 3.4 Paleta

Se conserva la metáfora de nombres del proyecto —papel, tinta, filete, sello— y se retunean los valores.

| Token | Valor | Uso |
|---|---|---|
| `--paper` | `#F7F7F5` | Fondo. Neutro frío |
| `--surface` | `#FFFFFF` | Fichas |
| `--ink` | `#16202A` | Texto. Granito |
| `--ink-soft` | `#5A6875` | Texto secundario |
| `--line` | `#DFE2E0` | Filetes |
| `--stamp` | `#24506E` | Acento principal: enlaces y estructura |
| `--sierra` | `#3D5A4A` | Verde discreto, **solo** motivo territorial |
| `--marca` | `#8C6A22` | Aparato documental y citas |

El ocre de `--marca` no es decorativo: los escaneos originales de este corpus están subrayados a rotulador amarillo. El acento del aparato hace eco del subrayado del expediente físico.

**Ningún estado depende solo del color**: siempre glifo + etiqueta de texto + estilo de filete. Contraste mínimo AA sobre `--paper`.

### 3.5 Motivo territorial

Una única línea de nivel topográfica, en SVG abstracto, a muy bajo contraste, **solo en la portada**. Abstracta a propósito: no debe confundirse con cartografía real. Es el único accesorio del sitio; nada de sierra, pinar ni mapas en ninguna otra página.

### 3.6 Espacio, filete y movimiento

Escala de espaciado de nueve pasos. Radio de 4 px en fichas, 0 en filetes. Sin sombras: la jerarquía la dan el espacio y el filete.

Movimiento solo funcional: `hover`, foco, apertura de `<details>`. Nada decorativo. `prefers-reduced-motion` respetado.

---

## 4. Sistema de componentes

Doce componentes. `Citation` y `EntityLink` son los más valiosos.

| Componente | Papel |
|---|---|
| `Citation` | **El aparato documental.** Documento · página · locator · cita literal plegable |
| `EntityLink` | Enlace a entidad con degradación segura |
| `EvidenceChain` | "¿De dónde sale esto?": documento → lo que dice → lo que se concluye |
| `Timeline` | Cronología con divulgación progresiva |
| `NoteCard` | Una afirmación con su procedencia plegada |
| `Prose` | Cuerpo Markdown con las referencias convertidas en enlaces |
| `DocMap` | El mapa documental del corpus (§6.5) |
| `OriginalAccess` | Cómo consultar el original, o por qué no se publica |
| `EmptySection` | Estado vacío honesto |
| `StateLine` | La fiabilidad de la página en lenguaje llano |
| `Badge` · `Card` | Primitivas |

**Lo que no es un componente.** Las cabeceras temáticas, los índices de sección,
las listas de entidades, el árbol de procedimientos, las migas y las tarjetas de
portada viven hoy en las plantillas de `src/pages/`. Cada índice tiene su propia
composición y ninguno se repite lo bastante para justificar un componente; si
alguno llega a repetirse, ese será el momento de extraerlo.

Por la misma razón no existen `Container`, `Heading`, `Button` ni `Grid`:
envolver un `<h2>` en un componente no aporta nada.

---

## 5. La página temática

Orden fijo. **Cada sección desaparece entera si no tiene datos**; nunca un encabezado sobre el vacío.

1. **En 30 segundos** — 3-5 puntos. Lo único que leerá mucha gente.
2. **Por qué importa** — qué cambia esto para un vecino.
3. **Situación documentada** — qué puede afirmarse y con qué respaldo.
4. **Qué está en discusión** — solo si hay elementos controvertidos.
5. **Cronología** — `Timeline` filtrada por el tema.
6. **Preguntas principales**
7. **Procedimientos relacionados** — `ProcedureTree`.
8. **Quién interviene** — actores.
9. **Documentos fundamentales** — los más citados, no todos.
10. **Explorar toda la documentación** — puerta a la capa 2.

### Contrato de secciones

Las secciones 1 a 4 se escriben a mano en el cuerpo del tema. Las 5 a 10 las genera la plantilla desde el grafo, y **está prohibido escribirlas a mano**: `assertSections` rompe el build si aparece un `## Fuentes`, `## Actores`, `## Preguntas` o `## Cronología` en el Markdown de un tema.

Es la garantía estructural contra el problema que este rediseño viene a resolver: hoy los cuatro temas llevan esas listas escritas a mano *y* la plantilla las genera. Dos cronologías que dentro de seis meses no coinciden.

---

## 6. Evidencia y fuentes

### 6.1 La referencia documental

```
Consta en:
STSJ CyL 271/2011 · pág. PDF 26 · Fallo
▸ Ver extracto literal
```

Monoespaciada para las coordenadas, serif para la cita. La cita literal va siempre plegada en `<details>`: es jerga jurídica y no debe interrumpir la lectura.

### 6.2 La cadena de procedencia

Tres pasos en vertical, sin diagramas ni grafos. La regla es de esta pieza, no del
sitio entero: junto a una afirmación, un grafo compite con lo único que importa ahí
—de dónde sale lo que se acaba de leer—. El mapa de conjunto tiene su sitio, y es
§6.5.

**Documento** → tipo, fecha, emisor, enlace a la ficha.
**Lo que dice** → cita literal con su página.
**Lo que se concluye** → la afirmación.

El grafo completo existe internamente. Al pie de una afirmación no se enseña; como
índice del corpus, sí (§6.5).

### 6.3 Estados en lenguaje llano

| Interno | Lo que ve el lector | Dónde |
|---|---|---|
| caso normal | ✓ Respaldado por documentación | Una línea en la cabecera |
| `evidenceStatus: disputed` | ⚠ Las fuentes discrepan | Junto al elemento |
| `evidenceStatus: incomplete` | ◌ Documentación incompleta | Junto al elemento |
| `basis` ≠ `documented` | ✎ Inferencia editorial | Junto al elemento |
| `dateStatus: disputed` | ⚠ Fecha discutida | En la cronología |

`unassessed` no muestra nada: son 141 de 150 afirmaciones y sería ruido en toda la web.

Mientras todo el corpus esté en borrador, el estado editorial es **del sitio**, no del elemento: un aviso en el pie y una línea en cada cabecera, con enlace a `/metodologia/`. En cuanto existan afirmaciones revisadas, las distinciones por elemento aparecen solas.

### 6.4 Documentos sin PDF

Ningún documento es publicable hoy: los 36 están en revisión de privacidad. La ficha muestra qué es, quién lo emitió, cuándo, cuántas páginas tiene, qué dice y qué afirmaciones sostiene, con sus citas literales — y explica en una frase por qué el original no está disponible. Una ficha así ya es útil; un enlace roto no.

### 6.5 El mapa documental

`/documentos/mapa/` es la vista de conjunto del corpus: los 36 documentos situados en
el tiempo, agrupados por el procedimiento judicial al que pertenecen, unidos por las
relaciones que ellos mismos declaran. Su página vive dentro de Documentos, y la figura
—sin las cadenas en texto— se repite en la portada, como banda propia después de la
narrativa histórica.

Es la única excepción a la regla de §6.2, y está medida: la portada abre con una
afirmación documentada y su procedencia, no con el mapa, y el mapa llega cuando el
lector ya sabe de qué se le habla. No aparece en ningún otro sitio —ni en las páginas
temáticas, ni junto a una afirmación—, porque ahí competiría con la lectura en lugar
de situarla.

**Cada marcador es un enlace.** La figura es un índice navegable, no una ilustración.
Si un elemento del mapa no lleva a ninguna parte, sobra.

**Qué se dibuja y qué no.** Solo las relaciones declaradas en `relations` —confirma,
anula, resuelve el recurso, ejecuta, cita—. Nunca se traza una arista porque dos
documentos compartan tema, emisor o año: eso no es una relación, y la línea afirmaría
algo que ningún documento dice. Con el corpus de hoy son 20 aristas, y hay documentos
sin ninguna: el hueco se declara en la página, no se disimula.

**La escala del tiempo miente en voz alta.** El corpus va de 1966 a 2026 y 34 de los 36
documentos caen entre 2002 y 2026. Los tramos de dos o más años consecutivos sin
ningún documento se comprimen a un hueco fijo con un corte visible; dentro de cada
tramo la distancia sí es proporcional. Un año suelto en blanco se dibuja entero:
cortar ahí sería ruido.

**Redundancia obligatoria.** Ni el color ni la posición son el único portador: la
familia documental va también en la forma del marcador, y bajo la figura está la misma
información en texto —cada cadena, documento a documento, con sus relaciones dichas en
palabras—. Esa lista no es un apaño de accesibilidad: es la versión que funciona en un
móvil de 360 px y la que encuentra la búsqueda del navegador.

**Cero JavaScript.** La figura es SVG generado en el build desde el grafo; ni una
coordenada escrita a mano. Se desplaza con `overflow-x` nativo, en una región
enfocable por teclado.

---

## 7. Cronología

El componente más importante del sitio. 48 acontecimientos, de 1971 a 2026, todos con cuerpo y con al menos una cita.

**Plegado:** fecha · tipo · título.
**Desplegado:** resumen, procedencia, afirmaciones asociadas, procedimiento, actores.

Con `<details>` nativo: sin JavaScript, accesible por teclado, funciona con la búsqueda del navegador.

**La incertidumbre de fecha se marca con texto, no con color.** 44 de los 48 acontecimientos tienen fecha firme; poner un código cromático para los otros cuatro convertiría la cronología en un árbol de Navidad. Una fecha discutida se muestra como *"24.2.2012 o 14.5.2012 · fecha discutida"*, que además explica la ordenación.

`/cronologia/` agrupa por década. Dentro de un tema, la cronología va filtrada y sin agrupar.

---

## 8. Preguntas

La gente no piensa en expedientes: piensa en *"¿está recepcionada la urbanización?"*.

Dos niveles por pregunta:

**Respuesta corta** — párrafos comprensibles, sin jerga.
**Ver fundamento** — las afirmaciones que la sostienen, cada una con su documento y su página.

Cuando la documentación no alcanza, la interfaz lo dice: **"No hay documentación suficiente para responder con certeza"**, y explica qué haría falta. Eso es mejor respuesta que una conclusión forzada.

`/preguntas/` agrupa por tema, con filtro cliente ligero sobre atributos `data-*`.

---

## 9. Desanexión

El corpus contiene hoy **una sola afirmación** sobre este asunto: en el acta de la EUC de 2015 su presidente expresó la posibilidad de "independizarnos" mediante una Entidad Local Menor, y la propia nota deja constancia de que no consta ningún paso posterior.

La página no finge tener contenido. Explica qué es la desanexión y qué la regularía, muestra la única cita documentada, y **declara con claridad qué no consta**: ningún expediente, ninguna solicitud, ningún acuerdo municipal, ningún dato oficial de población o dotaciones incorporado al corpus.

Es el banco de pruebas de todos los estados vacíos del sistema. Si esa página se lee bien y resulta honesta, el diseño es honesto.

---

## 10. Responsive

Diseño pensado primero para leer, y primero para móvil: mucha gente abrirá esto desde WhatsApp.

| Ancho | Comportamiento |
|---|---|
| < 640 px | Una columna. Aparato documental plegado bajo cada afirmación |
| 640-1024 px | Una columna más ancha, fichas en dos columnas |
| > 1024 px | Aparato documental en su columna lateral |

Se prueba a 320, 360, 390 y 768 px. Lo que más sufre en pantalla estrecha son la cronología, el árbol de procedimientos y las tablas de ficha: las tres se diseñan primero a 320 px.

---

## 11. Accesibilidad

Objetivo WCAG AA.

HTML semántico, un solo `h1` por página y jerarquía sin saltos. Contraste AA verificado sobre la paleta. Foco visible en todo elemento interactivo. Recorrido completo por teclado, con enlace de salto al contenido. `<details>`/`<summary>` nativos en lugar de acordeones a medida. Ningún estado codificado solo por color. Texto redimensionable sin pérdida. `prefers-reduced-motion` respetado.

La accesibilidad no se sacrifica por diseño: parte de la audiencia es mayor y lee en el móvil.

---

## 12. Rendimiento y despliegue

Sitio estático en GitHub Pages, bajo `/documentacion/` del dominio del portal. Sin JavaScript de aplicación: solo el filtro de dos índices y los tres ficheros del tema claro/oscuro, compartidos con el portal (§1.8). El mapa documental (§6.5) no lleva ninguno. Cero peticiones a terceros: tipografía autoalojada, sin analítica, sin CDN. El portal sí carga analítica; esta capa no, y el aviso legal lo dice.

Objetivo: portada por debajo de 150 KB con fuentes incluidas.

Como se sirve bajo un subdirectorio, **todo enlace interno pasa por un helper `url()`**, y `npm run check` incluye una guardia que falla si alguien escribe un `href` absoluto a mano.

Cada página emite título, descripción, canónica y OpenGraph propios, para que un enlace compartido por WhatsApp muestre algo comprensible. Una sola imagen OpenGraph en PNG —WhatsApp no renderiza SVG— y sitemap generado desde el grafo.

---

## 13. Qué mejora respecto a la web actual

| Hoy | Después |
|---|---|
| 26 páginas públicas de 433: la web es un esqueleto | ~290 páginas navegables |
| Cuatro `h2` sobre secciones vacías en cada tema | Ninguna sección sin datos se renderiza |
| Portada de 37 líneas que anuncia 150 afirmaciones inalcanzables | Portada que explica el proyecto y lleva a los cinco caminos principales |
| Ninguna página índice de ninguna colección | Índices de temas, preguntas, documentos, actores y procedimientos |
| Sin cronología global | `/cronologia/`, 1971-2026 |
| 327 referencias en la prosa renderizadas como código muerto | 327 enlaces reales |
| Cronología con fecha, tipo y enlace | Cronología con resumen, procedencia y afirmaciones |
| Menú de tres enlaces, uno con la URL incrustada a mano | Seis entradas desde un único mapa de rutas |
| `<head>` con cuatro etiquetas | Canónica, OpenGraph, favicon, sitemap |
| 19 documentos mostrarían su identificador crudo al lector | Etiquetas legibles: "Plan parcial, 1966" |
| Sin fuentes propias: la identidad cambia según el sistema operativo | Tipografía del portal, con la monoespaciada autoalojada para el aparato documental |
| Sin escala de espaciado ni tipográfica, sin breakpoints | Sistema de tokens y tres puntos de ruptura |
| Cronología escrita a mano en los temas *y* generada por plantilla | Una sola, generada; el build falla si alguien duplica |
| Sin 404, sin favicon, sin `public/`, sin despliegue | Todo ello, con workflow de GitHub Actions |

---

> Este documento describe la capa de presentación. Las reglas editoriales —qué se afirma, con qué respaldo y con qué cautelas— son las de `docs/CONTENT_MODEL.md` y no las modifica ninguna decisión de diseño.
