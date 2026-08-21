"""Reglas deterministas de riesgo jurídico.

Un match NO es una conclusión jurídica: es un hallazgo que alguien tiene que
mirar. Por eso cada regla declara su severidad y, cuando la decisión depende de
una ponderación —si un nombre es de un particular, si una frase imputa algo a
alguien—, la regla nunca produce `error`: produce `needs-human-review`.

Ninguna función de este módulo devuelve el valor detectado. Las coincidencias
salen siempre enmascaradas y con una huella irreversible. Ver `mask()` y
`fingerprint()`, y la invariante A de `test_legal_gate.py`.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Callable, Iterable, Iterator

# Estados de un hallazgo. `needs-human-review` no es una severidad: es la
# declaración de que la herramienta se niega a decidir.
OPEN = "open"
NEEDS_HUMAN_REVIEW = "needs-human-review"
ACCEPTED = "accepted"

SEVERITY_ORDER = {"info": 0, "warn": 1, "error": 2}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    column: int
    fingerprint: str
    masked: str
    context: str
    message: str
    status: str = OPEN

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    title: str
    message: str
    scan: Callable[[str], Iterator[tuple[int, int, str]]]
    human_review: bool = False

    def status(self) -> str:
        return NEEDS_HUMAN_REVIEW if self.human_review else OPEN


# --------------------------------------------------------------------------
# Enmascarado
# --------------------------------------------------------------------------

def fingerprint(value: str) -> str:
    """Huella estable e irreversible. Es la clave del baseline: permite aceptar
    un hallazgo conocido sin que su valor toque nunca el disco."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def mask(value: str, rule_id: str) -> str:
    """Deja visible lo justo para triar, nunca lo que identifica."""
    if rule_id == "LEGAL-PRIVACY-001":          # DNI/NIE: solo la letra de control
        return "•" * (len(value) - 1) + value[-1]
    if rule_id == "LEGAL-PRIVACY-002":          # IBAN: país y dígitos de control
        return value[:4] + "•" * (len(value) - 4)
    if rule_id == "LEGAL-PRIVACY-004":          # correo: solo el dominio
        _, _, domain = value.partition("@")
        return "•••@" + domain
    if rule_id == "LEGAL-SECRET-001":           # token: solo el prefijo que lo identifica
        return value[:4] + "•" * max(len(value) - 4, 4)
    if rule_id == "LEGAL-THIRDPARTY-001":       # el hallazgo ES el dominio: sin enmascarar
        return value
    return "•" * len(value)


def _context(text: str, start: int, end: int, spans: list[tuple[int, int, str]],
             width: int = 40) -> str:
    """±40 caracteres alrededor, con TODOS los valores detectados en el fichero
    sustituidos por su máscara — no solo el de este hallazgo.

    Enmascarar únicamente el valor propio dejaba escapar los ajenos: dos datos
    a menos de cuarenta caracteres el uno del otro, y el contexto del primero
    publicaba el segundo en claro. Lo encontró la invariante A."""
    lo, hi = max(0, start - width), end + width
    pieces, cursor = [], lo
    for s_start, s_end, s_masked in spans:
        if s_end <= lo or s_start >= hi:
            continue
        if s_start > cursor:
            pieces.append(text[cursor:s_start])
        pieces.append(s_masked)
        cursor = max(cursor, s_end)
    if cursor < hi:
        pieces.append(text[cursor:hi])
    joined = "".join(pieces).replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", joined).strip()


def _line_col(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_nl = text.rfind("\n", 0, index)
    return line, index - last_nl


# --------------------------------------------------------------------------
# Validadores. Son lo que separa un detector de un buscador de expresiones.
# --------------------------------------------------------------------------

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
NIE_PREFIX = {"X": "0", "Y": "1", "Z": "2"}


def valid_dni(number: str, letter: str) -> bool:
    return DNI_LETTERS[int(number) % 23] == letter.upper()


def valid_nie(prefix: str, number: str, letter: str) -> bool:
    return valid_dni(NIE_PREFIX[prefix.upper()] + number, letter)


def valid_iban(iban: str) -> bool:
    compact = re.sub(r"\s", "", iban).upper()
    if len(compact) < 15:
        return False
    rotated = compact[4:] + compact[:4]
    expanded = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rotated)
    if not expanded.isdigit():
        return False
    return int(expanded) % 97 == 1


def valid_luhn(digits: str) -> bool:
    compact = re.sub(r"[ -]", "", digits)
    if not compact.isdigit() or not 13 <= len(compact) <= 19:
        return False
    total, parity = 0, len(compact) % 2
    for i, ch in enumerate(compact):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


# --------------------------------------------------------------------------
# Escáneres por regla. Cada uno cede (inicio, fin, valor).
# --------------------------------------------------------------------------

def _finditer(pattern: re.Pattern, text: str, group: int = 0) -> Iterator[tuple[int, int, str]]:
    for m in pattern.finditer(text):
        yield m.start(group), m.end(group), m.group(group)


RE_DNI = re.compile(r"(?<![\w-])(\d{8})\s?-?\s?([A-HJ-NP-TV-Z])(?![\w-])")
RE_NIE = re.compile(r"(?<![\w-])([XYZ])\s?-?\s?(\d{7})\s?-?\s?([A-HJ-NP-TV-Z])(?![\w-])")


def scan_id_document(text: str) -> Iterator[tuple[int, int, str]]:
    """DNI y NIE, validados por la letra de control. Sin el mod 23, cualquier
    número de ocho cifras seguido de una letra sería un hallazgo: los números de
    protocolo, de expediente y de finca lo son constantemente."""
    for m in RE_DNI.finditer(text):
        if valid_dni(m.group(1), m.group(2)):
            yield m.start(), m.end(), m.group(0)
    for m in RE_NIE.finditer(text):
        if valid_nie(m.group(1), m.group(2), m.group(3)):
            yield m.start(), m.end(), m.group(0)


RE_IBAN = re.compile(r"(?<![A-Z0-9])([A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}\s?[A-Z0-9]{0,4})(?![A-Z0-9])")


def scan_iban(text: str) -> Iterator[tuple[int, int, str]]:
    for m in RE_IBAN.finditer(text):
        if valid_iban(m.group(1)):
            yield m.start(1), m.end(1), m.group(1)


RE_PHONE = re.compile(r"(?<![\w.,/-])(?:\+34[ -]?)?([6789]\d{2}(?:[ -]?\d{2}){3})(?![\w.,/-])")


def scan_phone(text: str) -> Iterator[tuple[int, int, str]]:
    """Solo `warn`: un teléfono no se distingue con certeza de un número de
    resolución o de un importe. `911/2012` es lo segundo."""
    yield from _finditer(RE_PHONE, text)


RE_EMAIL = re.compile(r"(?<![\w.+-])([\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,})(?![\w-])")


def scan_email(text: str) -> Iterator[tuple[int, int, str]]:
    yield from _finditer(RE_EMAIL, text, 1)


# Los separadores solo caben en grupos de cuatro, que es como se escribe una
# tarjeta. Admitirlos entre cualquier par de dígitos hacía que las coordenadas
# de un `<path d="…">` SVG —«9134246575343 514 632»— pasaran por numeración
# válida en cuanto Luhn cuadraba por casualidad. Y un dígito pegado a un punto
# decimal no empieza una tarjeta.
RE_CARD = re.compile(
    r"(?<![\d.,-])(\d{4}(?:[ -]?\d{4}){2,3}[ -]?\d{0,3})(?![\d.,-])"
)


def scan_card(text: str) -> Iterator[tuple[int, int, str]]:
    for m in RE_CARD.finditer(text):
        if valid_luhn(m.group(1)):
            yield m.start(1), m.end(1), m.group(1)


RE_PLATE = re.compile(r"(?<![\w-])(\d{4}\s?-?\s?[BCDFGHJKLMNPRSTVWXYZ]{3})(?![\w-])")


def scan_plate(text: str) -> Iterator[tuple[int, int, str]]:
    yield from _finditer(RE_PLATE, text, 1)


# Envolvente del parcelario del núcleo, con margen. Calculada sobre los 2.112
# inmuebles de `docs/assets/js/parcelas.js`: lat 40,7678-40,7855 · lon -4,2374
# a -4,2094. Una coordenada con cuatro decimales dentro de esta caja no señala
# un paraje: señala una vivienda concreta.
LAT_RANGE = (40.70, 40.86)
LON_RANGE = (-4.32, -4.14)
RE_COORD = re.compile(r"(-?\d{1,3}\.\d{4,})\s*[,;]\s*(-?\d{1,3}\.\d{4,})")


def scan_coordinates(text: str) -> Iterator[tuple[int, int, str]]:
    for m in RE_COORD.finditer(text):
        a, b = float(m.group(1)), float(m.group(2))
        pairs = ((a, b), (b, a))          # el orden lat/lon no está garantizado
        for lat, lon in pairs:
            if LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]:
                yield m.start(), m.end(), m.group(0)
                break


RE_SECRETS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{28,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password|passwd)\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']"),
]


def scan_secrets(text: str) -> Iterator[tuple[int, int, str]]:
    for pattern in RE_SECRETS:
        yield from _finditer(pattern, text)


RE_LOCAL_PATH = re.compile(
    r"(?:/mnt/[a-z]/[\w./-]+|/home/[^/\s\"']+/[\w./-]*|/Users/[^/\s\"']+/[\w./-]*"
    r"|[A-Z]:\\\\?Users\\\\?[^\\\s\"']+|OneDrive[\w/\\-]*)"
)


def scan_local_paths(text: str) -> Iterator[tuple[int, int, str]]:
    """Una ruta local vincula el sitio a una persona concreta — justo lo que un
    aviso legal sin datos personales trata de evitar."""
    yield from _finditer(RE_LOCAL_PATH, text)


RE_PRIVATE_LEFTOVER = re.compile(r"private-sources|LASR-DOC|\.ocr-manifest")


# El esquema EXIGE que cada ficha de fuente declare dónde vive su original.
# Ese campo no es una fuga: es la trazabilidad del modelo, y el fichero no está
# ni estuvo nunca en el repositorio. Lo que sí delata es una referencia en
# prosa, en un inventario o en un script — que describe qué contiene cada
# original, o dónde encontrarlo.
#
# Sin esta distinción la regla marcaba 36 hallazgos graves, uno por fuente, y
# cada documento nuevo habría hecho fallar el CI por rellenar un campo
# obligatorio. Un gate así se desactiva a la semana.
RE_CAMPO_DECLARATIVO = re.compile(r"^\s*(?:file|originalFilename)\s*:", re.M)


def scan_private_leftovers(text: str) -> Iterator[tuple[int, int, str]]:
    for start, end, value in _finditer(RE_PRIVATE_LEFTOVER, text):
        inicio_linea = text.rfind("\n", 0, start) + 1
        if RE_CAMPO_DECLARATIVO.match(text, inicio_linea):
            continue
        yield start, end, value


# El navegador de quien visita el sitio pide estos recursos por su cuenta, así
# que el tercero recibe su IP, su user-agent y qué página estaba mirando. Una
# CSP autoriza la petición; no la evita. Solo se miran SUBRECURSOS —lo que la
# página carga sola—, nunca los enlaces: un `<a href>` no revela nada hasta que
# alguien lo pulsa.
RE_SUBRESOURCE = re.compile(
    r"""(?is)<(?:script|img|iframe|source|video|audio|embed|link)\b[^>]*?"""
    r"""(?:src|href)\s*=\s*["'](https?://([^/"'\s]+))"""
)
RE_TILE_TEMPLATE = re.compile(r"""["'](https?://(?:\{s\}\.)?([^/"'\s{]+)[^"']*\{z\}[^"']*)["']""")
RE_CSS_IMPORT = re.compile(r"""@import\s+(?:url\()?["'](https?://([^/"'\s]+))""")

DEFAULT_OWN_HOSTS = ("lasr-info.es", "www.lasr-info.es")


def third_party_subresources(text: str, own_hosts: tuple[str, ...]) -> Iterator[tuple[int, int, str]]:
    seen: set[str] = set()
    for pattern in (RE_SUBRESOURCE, RE_TILE_TEMPLATE, RE_CSS_IMPORT):
        for m in pattern.finditer(text):
            host = m.group(2).lower().lstrip("*.")
            if any(host == own or host.endswith("." + own) for own in own_hosts):
                continue
            if host in seen:
                continue
            seen.add(host)
            yield m.start(2), m.end(2), host


# --- Reglas no deterministas: siempre `needs-human-review` ------------------

MINOR_TERMS = re.compile(
    r"(?i)\b(?:menor(?:es)? de edad|menor de \d{1,2} años|mi hij[ao]|su hij[ao] menor"
    r"|alumn[ao] de|escolar de \d{1,2}|nacid[ao] en 20\d\d|de \d{1,2} años de edad)\b"
)


def scan_minors(text: str) -> Iterator[tuple[int, int, str]]:
    """Nunca se resuelve sola. Un menor identificable es el supuesto donde el
    coste de equivocarse es más alto y la ponderación menos automatizable."""
    yield from _finditer(MINOR_TERMS, text)


CRIMINAL_TERMS = (
    "estafa", "fraude", "apropiación indebida", "apropiacion indebida",
    "malversación", "malversacion", "prevaricación", "prevaricacion",
    "delito", "querella", "denuncia penal", "falsedad documental",
    "dolo", "mala fe", "cohecho", "soborno", "blanqueo",
)

RE_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n{2,}")

# Dos palabras capitalizadas seguidas. La variante con partícula —«Archivo de
# Planeamiento», «Junta de Castilla»— se descarta salvo que vaya precedida de un
# tratamiento o de un cargo, porque en este corpus casi siempre nombra a una
# institución y no a una persona.
RE_CAPITALIZED = re.compile(
    r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,})\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,})\b"
)
# Un apellido puede ir solo cuando lo precede un término de parentesco: «la
# familia Gil», «los herederos de Pérez». La heurística de dos palabras
# capitalizadas no lo veía, y ese era exactamente el caso real del corpus.
RE_KINSHIP_NAME = re.compile(
    r"(?i)\b(?:familias?|hermanos?|herederos?|sucesores?|viuda de|hij[oa]s? de|"
    r"c[oó]nyuge de|esposa de|esposo de)\s+(?:de\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,})\b"
)
RE_TITLED_NAME = re.compile(
    r"(?i)\b(?:don|do[ñn]a|sr\.?|sra\.?|se[ñn]or(?:a)?|letrad[oa]|procurador(?:a)?|"
    r"abogad[oa]|perit[oa]|notari[oa]|magistrad[oa])\s+"
    r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}(?:\s+(?:de|del|la|las|los|y)?\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}){1,3})"
)


def _normalize(value: str) -> str:
    stripped = unicodedata.normalize("NFD", value.lower())
    return "".join(c for c in stripped if unicodedata.category(c) != "Mn")


# Términos que empiezan por mayúscula y no son nombres de persona. La lista
# corta el grueso del ruido; el resto lo corta la lista blanca de actores.
STOPLIST = {
    _normalize(t) for t in (
        "Los Ángeles", "San Rafael", "El Espinar", "Castilla León", "Castilla y León",
        "Tribunal Supremo", "Tribunal Superior", "Audiencia Provincial", "Juzgado Primera",
        "Comunidad Propietarios", "Comunidad de Propietarios", "Entidad Urbanística",
        "Entidad Urbanistica", "Junta General", "Junta General Ordinaria",
        "Plan Parcial", "Ayuntamiento El Espinar", "Ayuntamiento de El Espinar",
        "Norte Castilla", "Norte de Castilla", "Voz Espinar", "Voz de El Espinar",
        "Adelantado Segovia", "Adelantado de Segovia", "Registro Propiedad",
        "Dirección General", "Direccion General", "Ley Propiedad", "Ley de Propiedad",
        "Código Civil", "Codigo Civil", "Real Decreto", "Boletín Oficial", "Boletin Oficial",
        "Fundamento Jurídico", "Fundamento Juridico", "Fundamento Tres", "Fundamento Segundo",
        "Sentencia Firme", "Recurso Apelación", "Recurso Apelacion", "Diputación Segovia",
        "Diputacion Segovia", "Junta Castilla", "Consejería Fomento", "Consejeria Fomento",
        "Promotora Inmobiliaria", "Inmobiliaria Mezquita", "La Mezquita", "Matas Verdes",
        "Asociación Copropietarios", "Asociacion Copropietarios", "Fase Segunda", "Fase Primera",
    )
}


def _starts_sentence(text: str, index: int) -> bool:
    """En castellano la primera palabra de una frase va en mayúscula por
    gramática, no por ser un nombre. Sin esta comprobación, «Cada afirmación
    indica» es un candidato."""
    before = text[:index].rstrip()
    return not before or before[-1] in ".!?:;\n•-–—|>"


# Palabras que en este corpus van en mayúscula por gramática, por ser tecnología
# o por ser vocabulario jurídico, y que nunca forman parte de un nombre propio.
SENTENCE_STARTERS = {
    _normalize(w) for w in (
        "Este", "Esta", "Estos", "Estas", "Ese", "Esa", "Aquel", "Cada", "Todo", "Toda",
        "Todos", "Todas", "Otro", "Otra", "Cuando", "Donde", "Como", "Porque", "Aunque",
        "Mientras", "Desde", "Hasta", "Entre", "Sobre", "Ante", "Bajo", "Tras", "Según",
        "Sin", "Con", "Para", "Por", "Que", "Quien", "Cual", "Cuyo", "Solo", "Solamente",
        "También", "Además", "Sino", "Pero", "Nunca", "Siempre", "Ahora", "Luego",
        "Antes", "Después", "Primero", "Segundo", "Tercero", "Nota", "Notas", "Fuente",
        "Fuentes", "Documento", "Documentos", "Página", "Páginas", "Fecha", "Estado",
        "Modelo", "Contenido", "Estructura", "Ejemplo", "Ejemplos", "Regla", "Reglas",
        "Campo", "Campos", "Tipo", "Tipos", "Valor", "Valores", "Texto", "Título",
        "Resumen", "Aviso", "Legal", "Web", "Sitio", "Portal", "Guía", "Capa", "Sección",
        "Astro", "Zod", "Git", "GitHub", "Markdown", "Python", "Node", "Docker", "JSON",
        "YAML", "HTML", "CSS", "PDF", "OCR", "URL", "SHA", "API", "CI", "Pages",
        "Collections", "Layout", "Prose", "Timeline", "Badge", "Card",
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
        "Septiembre", "Octubre", "Noviembre", "Diciembre",
        # Instituciones, órganos y vocabulario procesal: encabezan un nombre
        # propio, pero de entidad, y las entidades ya se declaran como Actor.
        "Archivo", "Registro", "Junta", "Consejería", "Consejeria", "Dirección",
        "Direccion", "Ministerio", "Tribunal", "Juzgado", "Audiencia", "Sala",
        "Ayuntamiento", "Diputación", "Diputacion", "Comunidad", "Entidad",
        "Asociación", "Asociacion", "Sociedad", "Promotora", "Inmobiliaria",
        "Servicio", "Instituto", "Colegio", "Cámara", "Camara", "Boletín", "Boletin",
        "Ley", "Real", "Plan", "Proyecto", "Expediente", "Acta", "Auto", "Sentencia",
        "Recurso", "Fase", "Anexo", "Capítulo", "Capitulo", "Artículo", "Articulo",
        "Pleno", "Asamblea", "Presidencia", "Secretaría", "Secretaria", "Gerencia",
        "Constitucional", "Supremo", "Superior", "Provincial", "Municipal", "General",
        "Urbanística", "Urbanistica", "Contencioso", "Administrativo", "Civil",
    )
}


def name_candidates(text: str, allowlist: frozenset[str]) -> Iterator[tuple[int, int, str]]:
    """Bigramas capitalizados que no figuran entre los actores declarados ni en
    el stoplist. Es una heurística, y por eso su severidad es `info` y su estado
    `needs-human-review`: propone a quién mirar, no afirma quién es.

    Se cede una sola vez por valor distinto: lo que hay que revisar es el
    candidato, y repetirlo cuarenta veces convierte el informe en ruido."""
    seen: set[str] = set()
    for pattern in (RE_KINSHIP_NAME, RE_TITLED_NAME):
        for m in pattern.finditer(text):
            candidate = _normalize(m.group(1))
            if candidate in SENTENCE_STARTERS or candidate in STOPLIST:
                continue
            if candidate in allowlist or candidate in seen:
                continue
            if any(candidate == known or f" {candidate}" in f" {known}" for known in allowlist):
                continue
            seen.add(candidate)
            yield m.start(1), m.end(1), m.group(1)
    for m in RE_CAPITALIZED.finditer(text):
        first, second = m.group(1), m.group(2)
        if _normalize(first) in SENTENCE_STARTERS or _normalize(second) in SENTENCE_STARTERS:
            continue
        if _starts_sentence(text, m.start()):
            continue
        candidate = _normalize(m.group(0))
        if candidate in STOPLIST or candidate in allowlist or candidate in seen:
            continue
        if any(candidate in known or known in candidate for known in allowlist):
            continue
        seen.add(candidate)
        yield m.start(), m.end(), m.group(0)


def attributed_accusations(text: str, allowlist: frozenset[str]) -> Iterator[tuple[int, int, str]]:
    """Coocurrencia, EN LA MISMA FRASE, de un candidato a nombre no declarado y
    un término de la lista cerrada. Sin la restricción de frase esto sería un
    buscador de palabras: un documento que hable de un fraude en un párrafo y
    nombre a alguien tres párrafos después no imputa nada a nadie."""
    offset = 0
    for sentence in RE_SENTENCE_SPLIT.split(text):
        # Un bloque de cuatro mil caracteres no es una frase: en un JSON sin
        # puntuación el texto entero cae en un solo trozo, y ahí la coocurrencia
        # de un nombre y un término penal no significa nada.
        if len(sentence) > 400:
            offset += len(sentence) + 1
            continue
        lowered = _normalize(sentence)
        if any(term in lowered for term in (_normalize(t) for t in CRIMINAL_TERMS)):
            for start, end, value in name_candidates(sentence, allowlist):
                yield offset + start, offset + end, value
        offset += len(sentence) + 1


# --------------------------------------------------------------------------
# Catálogo
# --------------------------------------------------------------------------

def build_rules(allowed_emails: Iterable[str] = (), actor_names: Iterable[str] = (),
                own_hosts: Iterable[str] = DEFAULT_OWN_HOSTS) -> list[Rule]:
    """El catálogo depende del proyecto: los correos legítimos salen del
    manifiesto, la lista blanca de nombres de los actores declarados y los
    dominios propios del sitio que se está auditando."""
    allowed = {e.strip().lower() for e in allowed_emails}
    own_hosts = tuple(h.lower() for h in own_hosts)
    allowlist = frozenset(_normalize(n) for n in actor_names if n)

    def scan_email_filtered(text: str) -> Iterator[tuple[int, int, str]]:
        for start, end, value in scan_email(text):
            if value.lower() not in allowed:
                yield start, end, value

    return [
        Rule("LEGAL-PRIVACY-001", "error", "Documento de identidad",
             "Número de DNI o NIE con letra de control válida", scan_id_document),
        Rule("LEGAL-PRIVACY-002", "error", "Cuenta bancaria",
             "IBAN con dígitos de control válidos", scan_iban),
        Rule("LEGAL-PRIVACY-003", "warn", "Teléfono",
             "Posible número de teléfono; puede ser un número de resolución", scan_phone),
        Rule("LEGAL-PRIVACY-004", "error", "Correo electrónico",
             "Dirección de correo no declarada como pública", scan_email_filtered),
        Rule("LEGAL-PRIVACY-005", "error", "Tarjeta de pago",
             "Numeración que supera la validación de Luhn", scan_card),
        Rule("LEGAL-PRIVACY-006", "warn", "Matrícula",
             "Posible matrícula de vehículo", scan_plate),
        Rule("LEGAL-PRIVACY-007", "warn", "Coordenadas de precisión métrica",
             "Coordenada dentro del parcelario del núcleo: localiza una vivienda",
             scan_coordinates),
        Rule("LEGAL-SECRET-001", "error", "Secreto",
             "Token, clave o credencial", scan_secrets),
        Rule("LEGAL-LEAK-001", "error", "Ruta local",
             "Ruta del sistema de ficheros de una persona concreta", scan_local_paths),
        Rule("LEGAL-LEAK-002", "error", "Resto de material privado",
             "Referencia a la carpeta de originales o a su caché", scan_private_leftovers),
        Rule("LEGAL-THIRDPARTY-001", "warn", "Recurso de un tercero",
             "La página carga sola un recurso externo: ese tercero recibe la IP de quien visita",
             lambda text: third_party_subresources(text, own_hosts)),
        Rule("LEGAL-NAME-001", "info", "Posible nombre de particular",
             "Nombre capitalizado que no figura entre los actores declarados",
             lambda text: name_candidates(text, allowlist), human_review=True),
        Rule("LEGAL-ATTRIB-001", "warn", "Imputación a persona identificable",
             "Nombre no declarado junto a un término penal en la misma frase",
             lambda text: attributed_accusations(text, allowlist), human_review=True),
        Rule("LEGAL-MINOR-001", "warn", "Posible referencia a un menor",
             "Expresión que sugiere la presencia de un menor de edad",
             scan_minors, human_review=True),
    ]


def run_rules(text: str, path: str, rules: Iterable[Rule]) -> list[Finding]:
    """Dos pasadas. La primera recoge cada coincidencia; la segunda construye
    los contextos, que no se pueden escribir hasta saber dónde está TODO lo
    detectado en el fichero."""
    hits: list[tuple[Rule, int, int, str, str]] = []
    for rule in rules:
        for start, end, value in rule.scan(text):
            hits.append((rule, start, end, value, mask(value, rule.id)))

    spans = sorted({(start, end, masked) for _, start, end, _, masked in hits})

    findings: list[Finding] = []
    for rule, start, end, value, masked in hits:
        line, column = _line_col(text, start)
        findings.append(Finding(
            rule=rule.id,
            severity=rule.severity,
            path=path,
            line=line,
            column=column,
            fingerprint=fingerprint(value),
            masked=masked,
            context=_context(text, start, end, spans),
            message=rule.message,
            status=rule.status(),
        ))
    return findings
