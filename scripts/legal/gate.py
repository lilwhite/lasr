#!/usr/bin/env python3
"""La puerta de publicación.

Cuatro trabajos, todos negativos: ninguno autoriza nada, todos se limitan a
impedir que algo salga sin haber sido declarado.

    --diff --base origin/dev   lo que la rama toca debe tener estado jurídico
    --check-schema             las ocho colecciones declaran el eje
    --check-manifest           todo lo que hay en docs/ está declarado
    --copy-portal DEST         copia a DEST solo lo declarado publicable

El gate es incremental a propósito: exige decisión sobre lo que una rama
modifica, no sobre las 285 entradas del corpus. Lo preexistente se publica y
queda inventariado como deuda. Un gate que exigiera clasificarlo todo antes del
próximo despliegue se desactivaría el primer día.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import manifest as manifest_mod


def _repo_root() -> Path:
    """La raíz del repositorio donde se está trabajando. Se deduce de git y no
    de la ubicación del script, para que las pruebas puedan ejercitar el gate
    sobre un repositorio temporal sin tocar el real."""
    found = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
    if found.returncode == 0 and found.stdout.strip():
        return Path(found.stdout.strip())
    return Path(__file__).resolve().parents[2]


REPO = _repo_root()
MANIFEST_PATH = REPO / "audit" / "portal-manifest.json"
CONTENT_CONFIG = REPO / "documentacion" / "src" / "content.config.ts"
CONTENT_DIR = REPO / "documentacion" / "src" / "content"

COLLECTIONS = 8
NEEDS_DECISION = ("unchecked", "needs-human-review")

# Ficheros obligatorios del portal: si tras copiar falta alguno, el despliegue
# se aborta en vez de publicar un sitio incompleto.
REQUIRED = (
    "index.html", "assets/config.json", "assets/content.json",
    "assets/css/styles.css", "assets/js/main.js",
)
MIN_FILES = 20

RE_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
RE_LEGAL_STATUS = re.compile(r"^legalStatus:\s*[\"']?([\w-]+)[\"']?\s*$", re.M)


def fail(message: str) -> None:
    print(f"[error] {message}", file=sys.stderr)


# --------------------------------------------------------------------------
# Lectura del frontmatter. Con regex a propósito: no hay PyYAML en este
# proyecto y no lo va a haber (solo biblioteca estándar). Por eso `legalStatus`
# es un escalar de primer nivel y no una clave anidada.
# --------------------------------------------------------------------------

def legal_status_of(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unchecked"
    head = RE_FRONTMATTER.match(text)
    if not head:
        return "unchecked"
    found = RE_LEGAL_STATUS.search(head.group(1))
    return found.group(1) if found else "unchecked"


# --------------------------------------------------------------------------
# --diff
# --------------------------------------------------------------------------

def merge_base(base: str) -> str:
    result = subprocess.run(["git", "merge-base", base, "HEAD"],
                            capture_output=True, text=True, cwd=REPO)
    if result.returncode != 0:
        fail(
            f"No se pudo resolver la base «{base}».\n"
            "        En CI hace falta `fetch-depth: 0`: un checkout superficial deja "
            "el gate sin nada con lo que comparar, y un gate que no puede comparar "
            "pasa siempre. Se sale con 2, nunca con 0."
        )
        raise SystemExit(2)
    return result.stdout.strip()


def diff_entries(base: str) -> list[tuple[str, str]]:
    """`(estado, ruta)`. Un renombrado puro no cuenta como tocado: una rama que
    solo mueve una carpeta no debería obligar a revisar treinta ficheros."""
    out = subprocess.run(
        ["git", "diff", "--name-status", "-M", "-C", merge_base(base), "HEAD"],
        capture_output=True, text=True, cwd=REPO,
    ).stdout
    entries = []
    for line in out.splitlines():
        parts = line.split("\t")
        code = parts[0]
        if code.startswith("R") and code != "R100" or code.startswith("C"):
            entries.append((code, parts[-1]))
        elif code == "R100":
            entries.append(("R100", parts[-1]))
        elif code in ("A", "M"):
            entries.append((code, parts[1]))
    return entries


def check_diff(base: str) -> int:
    try:
        loaded, manifest_errors = manifest_mod.load(MANIFEST_PATH)
    except manifest_mod.ManifestError as exc:
        fail(str(exc))
        return 2

    problems: list[str] = []
    touched = 0

    for code, rel in diff_entries(base):
        path = REPO / rel
        if not path.is_file():
            continue

        if rel.startswith("documentacion/src/content/") and rel.endswith(".md"):
            if code == "R100":
                continue
            touched += 1
            status = legal_status_of(path)
            if status in NEEDS_DECISION:
                problems.append(
                    f"{rel}\n"
                    f"        Modificado en esta rama y su legalStatus sigue en «{status}».\n"
                    f"        Declara cleared / cleared-redacted / blocked con legalReview."
                )
            elif status == "blocked":
                print(f"  · {rel} está «blocked»: no generará página.")

        elif rel.startswith("docs/"):
            touched += 1
            entry = loaded.entry_for(rel)
            if entry is None:
                problems.append(
                    f"{rel}\n"
                    f"        No está declarado en audit/portal-manifest.json.\n"
                    f'        Añade:  "{rel}": {{"legalStatus": "unchecked", "reason": "…"}}'
                )
            elif entry.is_generated:
                continue                      # se gobierna por invariantes, no por firma
            elif entry.legal_status in NEEDS_DECISION:
                problems.append(
                    f"{rel}\n"
                    f"        Modificado en esta rama y su estado en el manifiesto sigue "
                    f"en «{entry.legal_status}»."
                )

    if manifest_errors:
        problems += manifest_errors

    if problems:
        print(f"\n{len(problems)} cosas sin decidir en lo que esta rama toca:\n")
        for p in problems:
            print(f"  · {p}\n")
        return 1

    print(f"✔ {touched} ficheros tocados, todos con estado jurídico declarado")
    return 0


# --------------------------------------------------------------------------
# --check-schema
# --------------------------------------------------------------------------

def check_schema() -> int:
    """Olvidar `...legalFields` en una colección no rompe nada: esa colección
    simplemente se queda sin eje jurídico para siempre. Por eso se cuenta."""
    if not CONTENT_CONFIG.exists():
        fail(f"No existe {CONTENT_CONFIG}")
        return 2
    text = CONTENT_CONFIG.read_text(encoding="utf-8")
    count = len(re.findall(r"\.\.\.legalFields", text))
    if count != COLLECTIONS:
        fail(
            f"`...legalFields` aparece {count} veces en content.config.ts y hay "
            f"{COLLECTIONS} colecciones.\n"
            "        Una colección sin el eje jurídico nunca puede bloquearse, y no "
            "avisa de ello: falla en silencio para siempre."
        )
        return 1
    print(f"✔ Las {COLLECTIONS} colecciones declaran el eje jurídico")
    return 0


# --------------------------------------------------------------------------
# --check-manifest
# --------------------------------------------------------------------------

def check_manifest() -> int:
    try:
        loaded, errors = manifest_mod.load(MANIFEST_PATH)
    except manifest_mod.ManifestError as exc:
        fail(str(exc))
        return 2
    problems = errors + manifest_mod.check_completeness(loaded, REPO)
    if problems:
        print(f"\n{len(problems)} problemas en el manifiesto del portal:\n")
        for p in problems:
            print(f"  · {p}\n")
        return 1
    print(f"✔ Manifiesto completo: {len(loaded.assets)} assets, {len(loaded.sections)} secciones")
    return 0


# --------------------------------------------------------------------------
# --copy-portal
# --------------------------------------------------------------------------

def copy_portal(dest: Path) -> int:
    """Sustituye a `cp -r docs/* dist/`. Copiar sin filtro es el mecanismo por
    el que se publicaron cuatro documentos internos en marzo y un PDF con dos
    DNI en agosto: declarar pasa a ser condición para publicar."""
    try:
        loaded, errors = manifest_mod.load(MANIFEST_PATH)
    except manifest_mod.ManifestError as exc:
        fail(str(exc))
        return 2
    if errors:
        for e in errors:
            fail(e)
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    copied = skipped = 0
    for rel, entry in sorted(loaded.assets.items()):
        source = REPO / rel
        if not source.is_file():
            fail(f"Declarado pero ausente: {rel}")
            return 1
        if not entry.publish:
            skipped += 1
            continue
        target = dest / Path(rel).relative_to("docs")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1

    missing = [name for name in REQUIRED if not (dest / name).is_file()]
    if missing:
        fail(f"Tras copiar faltan ficheros obligatorios: {', '.join(missing)}")
        return 1
    if copied < MIN_FILES:
        fail(f"Solo se copiaron {copied} ficheros (mínimo {MIN_FILES}). "
             "Abortar es mejor que publicar un sitio vacío.")
        return 1

    print(f"✔ {copied} ficheros copiados a {dest} · {skipped} declarados no publicables")
    return 0


# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Puerta de publicación jurídica.")
    p.add_argument("--diff", action="store_true", help="Exigir estado a lo que la rama toca")
    p.add_argument("--base", default="origin/dev")
    p.add_argument("--check-schema", action="store_true")
    p.add_argument("--check-manifest", action="store_true")
    p.add_argument("--copy-portal", metavar="DEST")
    args = p.parse_args(argv)

    codes = []
    if args.check_schema:
        codes.append(check_schema())
    if args.check_manifest:
        codes.append(check_manifest())
    if args.diff:
        codes.append(check_diff(args.base))
    if args.copy_portal:
        codes.append(copy_portal(Path(args.copy_portal)))

    if not codes:
        p.print_help()
        return 2
    return max(codes)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
