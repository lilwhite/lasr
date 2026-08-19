#!/usr/bin/env python3
"""
Caché de texto de los PDFs de trabajo de LASR-Web.

Produce, para cada PDF de private-sources/pdf/, un .txt en private-sources/text/
con el texto de TODAS sus páginas y un marcador por página. El número del
marcador es exactamente el `pdfPages` que debe llevar una citation: por eso el
marcador se emite también para las páginas vacías. Omitir una sola página
desplazaría toda la numeración posterior y contaminaría cada cita del documento.

Cada página se resuelve por separado: si el PDF ya trae capa de texto utilizable
se usa esa (rápida y fiel); si no, se rasteriza y se pasa por tesseract. El
marcador dice cuál de las dos rutas se usó, porque en las páginas OCR los
dígitos NO son fiables y toda cita literal debe cotejarse contra el PDF.

La caché es una ayuda de trabajo, nunca una fuente. Vive bajo private-sources/,
excluida de Git: puede contener datos personales.

Uso:
    python3 scripts/ocr.py                      # todos los PDFs pendientes
    python3 scripts/ocr.py private-sources/pdf/src-2012-tsjcyl-581.pdf
    python3 scripts/ocr.py --force-ocr fichero.pdf   # ignora la capa de texto
    python3 scripts/ocr.py --jobs 4 --from 1 --to 50 fichero.pdf
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "private-sources" / "pdf"
CACHE = REPO / "private-sources" / "text"
MANIFEST = CACHE / ".ocr-manifest.json"

# Caracteres no-espacio por debajo de los cuales una página se considera sin
# texto aprovechable. Una página de sentencia ronda los 1500-3000; un sello o
# un pie de escaneo, menos de 100. El umbral deja fuera las carátulas con
# cuatro palabras sueltas, que conviene rasterizar.
TEXT_THRESHOLD = 180

DPI = 300
LANG = "spa"
PSM_PRIMARY = "1"    # incluye OSD: necesario para páginas apaisadas o giradas
PSM_FALLBACK = "3"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_pages(path: Path) -> int:
    out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=120)
    m = re.search(r"^Pages:\s+(\d+)", out.stdout, re.M)
    if not m:
        raise RuntimeError(f"pdfinfo no devuelve páginas para {path.name}")
    return int(m.group(1))


def embedded_text(path: Path, page: int) -> str:
    out = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(path), "-"],
        capture_output=True, text=True, timeout=120,
    )
    return out.stdout


def useful_chars(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def ocr_page(path: Path, page: int) -> tuple[str, str]:
    """Rasteriza y OCRea una página. Devuelve (texto, etiqueta del marcador)."""
    # Directorio temporal propio: pdftoppm escribe ficheros con el prefijo que
    # se le pase, y un prefijo relativo mal formado ensucia el directorio de
    # trabajo (o, peor, la carpeta de originales).
    with tempfile.TemporaryDirectory(prefix="lasr-ocr-") as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            ["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(DPI),
             "-gray", "-png", str(path), str(prefix)],
            capture_output=True, timeout=600, check=True,
        )
        images = sorted(Path(tmp).glob("page*.png"))
        if not images:
            return "", "ocr sin imagen"
        for psm in (PSM_PRIMARY, PSM_FALLBACK):
            out = subprocess.run(
                ["tesseract", str(images[0]), "-", "-l", LANG, "--psm", psm],
                capture_output=True, text=True, timeout=600,
            )
            if useful_chars(out.stdout) >= 20:
                return out.stdout, f"ocr r={DPI} psm={psm}"
        return "", "ocr sin resultado"


def render_page(args: tuple[str, int, bool]) -> tuple[int, str, str]:
    """Resuelve una página. Aislada en función propia para poder paralelizar."""
    path_str, page, force_ocr = args
    path = Path(path_str)
    if not force_ocr:
        text = embedded_text(path, page)
        if useful_chars(text) >= TEXT_THRESHOLD:
            return page, text, "texto embebido"
    text, label = ocr_page(path, page)
    return page, text, label


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict) -> None:
    """Guarda fusionando con lo que haya en disco.

    Dos ejecuciones concurrentes (lo normal: los documentos largos en segundo
    plano mientras se procesan los cortos) cargan el manifiesto al arrancar y
    lo escriben al terminar. Sin fusionar, el último en escribir borra las
    entradas del otro y esos documentos se vuelven a OCRear al renombrarlos.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    merged = load_manifest()
    merged.update(manifest)
    manifest.update(merged)
    MANIFEST.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")


def reindex() -> dict:
    """Reconstruye el manifiesto leyendo la cabecera de cada .txt de la caché.

    Cada volcado lleva su sha256 y su número de páginas en la cabecera, así que
    el manifiesto es reconstruible sin volver a procesar ningún PDF.
    """
    manifest = load_manifest()
    for txt in sorted(CACHE.glob("*.txt")):
        head = txt.read_text(encoding="utf-8", errors="replace")[:600]
        m_sha = re.search(r"^# sha256: ([0-9a-f]{64})$", head, re.M)
        m_pages = re.search(r"^# páginas: (\d+)", head, re.M)
        m_name = re.search(r"^# (.+\.pdf)$", head, re.M)
        if not m_sha:
            continue
        entry = manifest.setdefault(m_sha.group(1), {})
        entry["stem"] = txt.stem
        entry.setdefault("originalName", m_name.group(1) if m_name else txt.stem + ".pdf")
        if m_pages:
            entry.setdefault("pages", int(m_pages.group(1)))
        entry.setdefault("engine", f"tesseract-{LANG}")
        entry.setdefault("dpi", DPI)
        entry.setdefault("forceOcr", False)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def process(path: Path, manifest: dict, args) -> str:
    digest = sha256(path)
    stem = path.stem
    target = CACHE / f"{stem}.txt"
    entry = manifest.get(digest)

    # El manifiesto se indexa por hash, no por nombre: al renombrar un PDF a su
    # nombre canónico (paso rutinario en cuanto se fija el ID del Source) basta
    # con mover el .txt, sin volver a OCRear un documento de 200 páginas.
    if entry and not args.force:
        old_stem = entry["stem"]
        previous = CACHE / f"{old_stem}.txt"
        if old_stem != stem and previous.exists() and not target.exists():
            previous.rename(target)
            entry["stem"] = stem
            save_manifest(manifest)
            return f"renombrado ({old_stem}.txt → {stem}.txt), sin re-OCR"
        if target.exists() and entry.get("forceOcr") == args.force_ocr:
            return "ya en caché"

    total = pdf_pages(path)
    first = max(1, args.start or 1)
    last = min(total, args.end or total)
    if args.dry_run:
        return f"{total} págs.; procesaría {first}-{last}"

    jobs = [(str(path), p, args.force_ocr) for p in range(first, last + 1)]
    results: dict[int, tuple[str, str]] = {}
    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for page, text, label in pool.map(render_page, jobs):
                results[page] = (text, label)
    else:
        for job in jobs:
            page, text, label = render_page(job)
            results[page] = (text, label)

    CACHE.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {path.name}",
        f"# sha256: {digest}",
        f"# páginas: {total} (volcadas {first}-{last})",
        f"# generado: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "#",
        "# El número de cada marcador ES el pdfPages de la citation.",
        "# En las páginas marcadas [ocr] los dígitos no son fiables: toda cita",
        "# literal debe cotejarse contra el PDF antes de escribirla.",
        "",
    ]
    ocr_pages = 0
    for page in range(first, last + 1):
        text, label = results[page]
        if label.startswith("ocr"):
            ocr_pages += 1
        lines.append(f"=== PÁGINA {page} === [{label}]")
        lines.append(text.strip())
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")

    manifest[digest] = {
        "stem": stem,
        "originalName": path.name,
        "pages": total,
        "dumped": [first, last],
        "ocrPages": ocr_pages,
        "engine": f"tesseract-{LANG}",
        "dpi": DPI,
        "forceOcr": args.force_ocr,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_manifest(manifest)
    return f"{last - first + 1} págs. ({ocr_pages} por OCR) → {target.name}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="*", help="PDFs a procesar (por defecto, todos los de private-sources/pdf/)")
    parser.add_argument("--jobs", type=int, default=4, help="procesos en paralelo (4 por defecto)")
    parser.add_argument("--from", dest="start", type=int, help="primera página")
    parser.add_argument("--to", dest="end", type=int, help="última página")
    parser.add_argument("--force", action="store_true", help="re-procesa aunque esté en caché")
    parser.add_argument("--force-ocr", action="store_true", help="ignora la capa de texto y rasteriza siempre")
    parser.add_argument("--dry-run", action="store_true", help="solo informa de lo que haría")
    parser.add_argument("--reindex", action="store_true", help="reconstruye el manifiesto desde las cabeceras de la caché y sale")
    args = parser.parse_args()

    for tool in ("pdfinfo", "pdftotext", "pdftoppm", "tesseract"):
        if not shutil.which(tool):
            print(f"Falta la herramienta '{tool}'.", file=sys.stderr)
            return 1

    if args.reindex:
        manifest = reindex()
        print(f"Manifiesto reconstruido: {len(manifest)} entradas.")
        return 0

    targets = [Path(p).resolve() for p in args.pdfs] if args.pdfs else sorted(WORK.glob("*.pdf"))
    if not targets:
        print(f"No hay PDFs en {WORK}.")
        return 0

    # Guardarraíl: esta herramienta solo lee de la carpeta de trabajo. La
    # carpeta maestra es SOLO LECTURA y nada debe rasterizarse desde ella.
    work = WORK.resolve()
    for path in targets:
        if not path.is_relative_to(work):
            print(f"Rechazado: {path} no está bajo {work}.", file=sys.stderr)
            print("Copia el PDF a private-sources/pdf/ antes de procesarlo.", file=sys.stderr)
            return 1
        if not path.exists():
            print(f"No existe: {path}", file=sys.stderr)
            return 1

    manifest = load_manifest()
    for path in targets:
        try:
            print(f"{path.name}: {process(path, manifest, args)}")
        except Exception as exc:  # noqa: BLE001 — un PDF corrupto no debe abortar el lote
            print(f"{path.name}: ERROR — {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
