"""Extracción de texto y metadatos por tipo de fichero.

El contrato de este módulo es la pieza que impide el error más peligroso de un
escáner: confundir «no pude leerlo» con «está limpio». `extract()` devuelve
`(None, motivo)` cuando el contenido no es inspeccionable, y quien lo llama
tiene que sintetizar el `needs-human-review` ANTES de invocar a ningún
detector. Un detector que devuelve lista vacía no puede parecerse a un fichero
que no se abrió.

Los PDF se abren con poppler por subprocess, nunca con librería Python: es la
convención del repositorio (`documentacion/README.md`, skill
`github-validation-guard`). Si poppler no está, el programa sale con 2.
"""

from __future__ import annotations

import re
import struct
import subprocess
import zlib
from pathlib import Path

TEXT_SUFFIXES = {
    ".md", ".markdown", ".txt", ".html", ".htm", ".xml", ".svg", ".css",
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".astro", ".json", ".jsonc",
    ".yml", ".yaml", ".py", ".sh", ".toml", ".cfg", ".ini", ".csv",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".ico"}

# Mismo umbral que `documentacion/scripts/ocr.py`: por debajo de esto, la capa
# de texto de un PDF no sirve y estamos ante un escaneo.
TEXT_THRESHOLD_PER_PAGE = 180


class PopplerMissing(RuntimeError):
    """Poppler no está instalado. Saltarse los PDF en silencio sería peor que
    no tener escáner: los dos incidentes reales del proyecto fueron un PDF."""


def _run(args: list[str]) -> str:
    try:
        out = subprocess.run(args, capture_output=True, timeout=60)
    except FileNotFoundError as exc:
        raise PopplerMissing(f"Falta el binario «{args[0]}» (paquete poppler-utils)") from exc
    except subprocess.TimeoutExpired:
        return ""
    return out.stdout.decode("utf-8", errors="replace")


def check_tools() -> None:
    for tool in ("pdfinfo", "pdftotext"):
        try:
            subprocess.run([tool, "-v"], capture_output=True, timeout=20)
        except FileNotFoundError as exc:
            raise PopplerMissing(
                f"Falta «{tool}». Instala poppler-utils: sudo apt install poppler-utils"
            ) from exc


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------

def pdf_metadata(path: Path) -> dict[str, str]:
    """Autor, creador, productor y palabras clave. Es el vector de fuga que
    nadie mira: un PDF exportado desde Word lleva dentro el nombre de quien lo
    escribió aunque el texto visible esté anonimizado."""
    interesting = {"Author", "Creator", "Producer", "Keywords", "Title", "Subject"}
    data: dict[str, str] = {}
    for line in _run(["pdfinfo", str(path)]).splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key in interesting and value:
            data[key] = value
    return data


def pdf_text(path: Path) -> tuple[str | None, str]:
    info = _run(["pdfinfo", str(path)])
    pages_match = re.search(r"^Pages:\s+(\d+)$", info, re.M)
    pages = int(pages_match.group(1)) if pages_match else 1
    text = _run(["pdftotext", "-layout", str(path), "-"])
    dense = len(re.sub(r"\s", "", text))
    if pages and dense < TEXT_THRESHOLD_PER_PAGE * pages:
        return None, (
            f"PDF sin capa de texto útil ({dense} caracteres en {pages} páginas): "
            "es un escaneo y su contenido no es inspeccionable automáticamente"
        )
    return text, "capa de texto"


# --------------------------------------------------------------------------
# Imágenes: EXIF y metadatos, con biblioteca estándar
# --------------------------------------------------------------------------

_TIFF_TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

_IFD0_TAGS = {
    0x010E: "ImageDescription", 0x010F: "Make", 0x0110: "Model",
    0x013B: "Artist", 0x8298: "Copyright", 0x0131: "Software",
}
_EXIF_TAGS = {0x9286: "UserComment", 0x9003: "DateTimeOriginal"}
_GPS_TAGS = {
    0x0001: "GPSLatitudeRef", 0x0002: "GPSLatitude",
    0x0003: "GPSLongitudeRef", 0x0004: "GPSLongitude",
}


def _read_ifd(blob: bytes, offset: int, endian: str, tags: dict[int, str]) -> tuple[dict[str, str], dict[int, int]]:
    """Devuelve (valores legibles, punteros a sub-IFD)."""
    values: dict[str, str] = {}
    pointers: dict[int, int] = {}
    if offset + 2 > len(blob):
        return values, pointers
    (count,) = struct.unpack_from(endian + "H", blob, offset)
    for i in range(count):
        entry = offset + 2 + i * 12
        if entry + 12 > len(blob):
            break
        tag, typ, num = struct.unpack_from(endian + "HHI", blob, entry)
        size = _TIFF_TYPE_SIZE.get(typ, 0) * num
        if size == 0:
            continue
        if size <= 4:
            raw = blob[entry + 8:entry + 8 + size]
        else:
            (ptr,) = struct.unpack_from(endian + "I", blob, entry + 8)
            raw = blob[ptr:ptr + size]
        if tag in (0x8769, 0x8825):                      # punteros a Exif IFD y GPS IFD
            (ptr,) = struct.unpack_from(endian + "I", blob, entry + 8)
            pointers[tag] = ptr
            continue
        if tag not in tags:
            continue
        if typ == 2:
            values[tags[tag]] = raw.split(b"\x00", 1)[0].decode("utf-8", "replace")
        elif typ == 5 and num == 3:                      # coordenada: grados, minutos, segundos
            parts = struct.unpack_from(endian + "IIIIII", raw, 0)
            try:
                deg = parts[0] / parts[1] + parts[2] / parts[3] / 60 + parts[4] / parts[5] / 3600
            except ZeroDivisionError:
                continue
            values[tags[tag]] = f"{deg:.6f}"
        else:
            values[tags[tag]] = raw.hex()[:32]
    return values, pointers


def _jpeg_exif(data: bytes) -> dict[str, str]:
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            break
        marker = data[pos + 1]
        (length,) = struct.unpack_from(">H", data, pos + 2)
        if marker == 0xE1 and data[pos + 4:pos + 10] == b"Exif\x00\x00":
            blob = data[pos + 10:pos + 2 + length]
            if len(blob) < 8:
                return {}
            endian = "<" if blob[:2] == b"II" else ">"
            (ifd0,) = struct.unpack_from(endian + "I", blob, 4)
            values, pointers = _read_ifd(blob, ifd0, endian, _IFD0_TAGS)
            if 0x8769 in pointers:
                sub, _ = _read_ifd(blob, pointers[0x8769], endian, _EXIF_TAGS)
                values.update(sub)
            if 0x8825 in pointers:
                gps, _ = _read_ifd(blob, pointers[0x8825], endian, _GPS_TAGS)
                values.update(gps)
            return values
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        pos += 2 + length
    return {}


def _png_text(data: bytes) -> dict[str, str]:
    values: dict[str, str] = {}
    pos = 8
    while pos + 8 <= len(data):
        (length,) = struct.unpack_from(">I", data, pos)
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        if kind in (b"tEXt", b"iTXt"):
            key, _, value = payload.partition(b"\x00")
            values[key.decode("latin-1", "replace")] = value.decode("utf-8", "replace")[:200]
        elif kind == b"zTXt":
            key, _, rest = payload.partition(b"\x00")
            try:
                values[key.decode("latin-1", "replace")] = zlib.decompress(rest[1:]).decode("utf-8", "replace")[:200]
            except zlib.error:
                pass
        pos += 12 + length
        if kind == b"IEND":
            break
    return values


def image_metadata(path: Path) -> dict[str, str]:
    try:
        data = path.read_bytes()
    except OSError:
        return {}
    if data[:2] == b"\xff\xd8":
        return _jpeg_exif(data)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return _png_text(data)
    return {}


# --------------------------------------------------------------------------
# Despacho
# --------------------------------------------------------------------------

def extract(path: Path) -> tuple[str | None, str]:
    """Devuelve `(texto, motivo)`. `texto is None` significa NO INSPECCIONABLE,
    que nunca equivale a limpio."""
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        try:
            return path.read_text(encoding="utf-8", errors="replace"), "texto"
        except OSError as exc:
            return None, f"no se pudo leer: {exc}"
    if suffix == ".pdf":
        return pdf_text(path)
    if suffix in IMAGE_SUFFIXES:
        return None, "imagen: los píxeles no son inspeccionables automáticamente"
    try:
        head = path.open("rb").read(4096)
    except OSError as exc:
        return None, f"no se pudo leer: {exc}"
    if b"\x00" not in head:
        try:
            return path.read_text(encoding="utf-8", errors="replace"), "texto sin extensión conocida"
        except OSError as exc:
            return None, f"no se pudo leer: {exc}"
    return None, f"binario de tipo «{suffix or 'sin extensión'}»: no inspeccionable"
