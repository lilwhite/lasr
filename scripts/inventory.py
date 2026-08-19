#!/usr/bin/env python3
"""
Inventario reproducible del corpus documental de LASR-Web.

Compara la carpeta maestra (OneDrive, SOLO LECTURA) con private-sources/pdf y
con los Sources ya creados en src/content/sources/, cruzando por SHA-256.

- NUNCA modifica la carpeta maestra (solo la lee).
- Es seguro ejecutarlo tantas veces como se quiera.
- Regenera docs/sources_inventory.json y docs/SOURCES_INVENTORY.md.

Uso:
    python3 scripts/inventory.py [ruta-carpeta-maestra]
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MASTER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/c/Users/mario/OneDrive/LASR-DOC")
WORK = REPO / "private-sources" / "pdf"
SOURCES_DIR = REPO / "src" / "content" / "sources"
JSON_OUT = REPO / "docs" / "sources_inventory.json"
MD_OUT = REPO / "docs" / "SOURCES_INVENTORY.md"

DOC_TYPE_HINTS = [
    (r"sentencia|setencia", "sentencia"),
    (r"auto", "auto"),
    (r"estatutos", "estatutos"),
    (r"acta|asamb", "acta"),
    (r"acuerdo|convenio", "convenio"),
    (r"presup", "presupuesto"),
    (r"circular", "circular"),
    (r"carta|burofax|comunicaci", "comunicacion"),
    (r"informe", "informe"),
    (r"solicitud", "solicitud"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_pages(path: Path) -> int | None:
    try:
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=60)
        m = re.search(r"^Pages:\s+(\d+)", out.stdout, re.M)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def text_chars(path: Path, pages: int = 5) -> int:
    try:
        out = subprocess.run(
            ["pdftotext", "-l", str(pages), str(path), "-"],
            capture_output=True, text=True, timeout=120,
        )
        return len(re.sub(r"\s", "", out.stdout))
    except Exception:
        return 0


def guess_type(name: str) -> str:
    low = name.lower()
    for pat, t in DOC_TYPE_HINTS:
        if re.search(pat, low):
            return t
    return "desconocido"


def scan(folder: Path, kind: str) -> list[dict]:
    items = []
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or p.name in {"desktop.ini", "README.md"}:
            continue
        entry = {
            "kind": kind,
            "name": p.name,
            "relpath": str(p.relative_to(folder)),
            "ext": p.suffix.lower(),
            "size": p.stat().st_size,
            "sha256": sha256(p),
        }
        if entry["ext"] == ".pdf":
            entry["pages"] = pdf_pages(p)
            entry["textChars"] = text_chars(p)
            entry["hasTextLayer"] = entry["textChars"] > 100
        entry["docTypeGuess"] = guess_type(p.name)
        items.append(entry)
    return items


def parse_sources() -> dict[str, dict]:
    """sha256 -> {id, file, originalFilename} de los Sources existentes."""
    out = {}
    for f in sorted(SOURCES_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm = text.split("---")[1] if text.startswith("---") else ""
        sid = re.search(r"^id:\s*(\S+)", fm, re.M)
        sha = re.search(r"^sha256:\s*([0-9a-f]{64})", fm, re.M)
        if sid and sha:
            out[sha.group(1)] = {"id": sid.group(1), "sourceFile": f.name}
    return out


def main() -> None:
    if not MASTER.is_dir():
        sys.exit(f"Carpeta maestra no accesible: {MASTER}")
    master = scan(MASTER, "master")
    work = scan(WORK, "work")
    sources_by_sha = parse_sources()

    work_by_sha: dict[str, list[dict]] = {}
    for w in work:
        work_by_sha.setdefault(w["sha256"], []).append(w)

    master_by_sha: dict[str, list[dict]] = {}
    for m in master:
        master_by_sha.setdefault(m["sha256"], []).append(m)

    # Estado de cada fichero de la maestra
    for m in master:
        matches = work_by_sha.get(m["sha256"], [])
        m["canonical"] = matches[0]["name"] if matches else None
        if len(master_by_sha[m["sha256"]]) > 1:
            m["status"] = "duplicado-exacto-en-maestra"
        elif matches:
            m["status"] = "procesado" if m["sha256"] in sources_by_sha else "ya-existente"
        else:
            m["status"] = "nuevo"
        # posible duplicado: mismas páginas y tamaño parecido con distinto sha
        if m["status"] == "nuevo" and m.get("pages"):
            for w in work:
                if (
                    w.get("pages") == m["pages"]
                    and abs(w["size"] - m["size"]) < max(m["size"], w["size"]) * 0.15
                ):
                    m["status"] = "posible-duplicado"
                    m["possibleMatch"] = w["name"]
                    break

    # Estado de cada fichero de trabajo
    for w in work:
        src = sources_by_sha.get(w["sha256"])
        w["inMaster"] = w["sha256"] in master_by_sha
        w["sourceId"] = src["id"] if src else None
        w["status"] = "procesado" if src else "pendiente-de-analisis"

    data = {
        "master": {"path": str(MASTER), "files": master},
        "work": {"path": str(WORK), "files": work},
    }
    JSON_OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Markdown ---
    lines = [
        "# Inventario de documentos originales",
        "",
        "Generado por `scripts/inventory.py` (seguro de re-ejecutar; nunca escribe en la carpeta",
        f"maestra). Carpeta maestra: `{MASTER}` (SOLO LECTURA). Los PDFs de trabajo viven en",
        "`private-sources/pdf/`, carpeta excluida de Git: pueden contener datos personales y no se",
        "versionan ni se publican.",
        "",
        "## Ficheros de trabajo (`private-sources/pdf/`)",
        "",
        "| Fichero canónico | SHA-256 (8) | Págs. | Texto | Source | Estado | ¿En maestra? |",
        "|---|---|---|---|---|---|---|",
    ]
    for w in work:
        lines.append(
            f"| `{w['name']}` | `{w['sha256'][:8]}` | {w.get('pages','—')} | "
            f"{'sí' if w.get('hasTextLayer') else 'no'} | {w['sourceId'] or '—'} | "
            f"{w['status']} | {'sí' if w['inMaster'] else 'NO'} |"
        )
    lines += [
        "",
        "## Carpeta maestra (LASR-DOC)",
        "",
        "| Nombre original | SHA-256 (8) | Págs. | Texto | Tipo (guess) | Estado | Canónico |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in master:
        lines.append(
            f"| `{m['name']}` | `{m['sha256'][:8]}` | {m.get('pages','—')} | "
            f"{'sí' if m.get('hasTextLayer') else 'no'} | {m['docTypeGuess']} | {m['status']}"
            f"{' → ' + m['possibleMatch'] if m.get('possibleMatch') else ''} | {m['canonical'] or '—'} |"
        )
    lines += [
        "",
        "Los nombres canónicos siguen la convención del proyecto: `src-<año>-<órgano>-<número>.pdf`",
        "cuando el documento tiene Source verificado; nombre descriptivo provisional en caso contrario.",
        "El estado `procesado` significa que existe un Source con ese SHA-256 en `src/content/sources/`.",
        "",
    ]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    # --- Resumen en consola ---
    st = {}
    for m in master:
        st[m["status"]] = st.get(m["status"], 0) + 1
    print(f"Maestra: {len(master)} ficheros → {st}")
    missing = [w["name"] for w in work if not w["inMaster"]]
    print(f"Trabajo: {len(work)} ficheros; sin copia en maestra: {missing}")
    news = [m["name"] for m in master if m["status"] in ("nuevo", "posible-duplicado")]
    print(f"Candidatos a copiar: {news}")


if __name__ == "__main__":
    main()
