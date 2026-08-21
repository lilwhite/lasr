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
REGISTRY_IN = REPO / "docs" / "document_registry.json"
REGISTRY_MD = REPO / "docs" / "DOCUMENT_REGISTRY.md"

DOC_TYPE_HINTS = [
    (r"sentencia|setencia", "sentencia"),
    (r"solicitud|apelaci|amparo|recurso|demanda", "escrito-de-parte"),
    (r"auto", "auto"),
    (r"estatutos", "estatutos"),
    (r"acta|asamb", "acta"),
    (r"acuerdo|convenio", "convenio"),
    (r"presup", "presupuesto"),
    (r"circular", "circular"),
    (r"carta|burofax|comunicaci", "comunicacion"),
    (r"informe", "informe"),
    (r"plan parcial|plan general|proyecto de urbanizaci", "instrumento-urbanistico"),
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


def text_chars(path: Path, pages: int | None = None) -> int:
    """Caracteres útiles por página, muestreando principio, medio y final.

    Mirar solo las primeras páginas engaña con los documentos escaneados que
    llevan una portada generada por ordenador: el plan parcial tiene texto en
    la página 1 y las otras 137 son imagen.
    """
    if pages is None:
        pages = pdf_pages(path) or 1
    sample = sorted({1, max(1, pages // 2), pages})
    total = 0
    for n in sample:
        try:
            out = subprocess.run(
                ["pdftotext", "-f", str(n), "-l", str(n), str(path), "-"],
                capture_output=True, text=True, timeout=120,
            )
            total += len(re.sub(r"\s", "", out.stdout))
        except Exception:
            pass
    return total // len(sample)


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
            entry["textChars"] = text_chars(p, entry["pages"])
            entry["hasTextLayer"] = entry["textChars"] > 180
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


REGISTRY_STATUS = {
    "duplicate-of": "duplicado-registrado",
    "fragment-of": "fragmento-registrado",
    "annex-of": "anexo-registrado",
    "reference-material": "material-de-referencia",
    "unidentified": "sin-identificar-registrado",
}


def load_registry() -> dict[str, dict]:
    """sha256 -> entrada de docs/document_registry.json.

    Sin este registro, un re-escaneo de un documento ya fichado aparecería como
    pendiente para siempre: su sha256 no coincide con el de ninguna ficha.
    """
    if not REGISTRY_IN.exists():
        return {}
    data = json.loads(REGISTRY_IN.read_text(encoding="utf-8"))
    return {e["sha256"]: e for e in data.get("entries", [])}


def write_registry_md(registry: dict[str, dict]) -> None:
    lines = [
        "# Registro de documentos no fichables",
        "",
        "Generado por `scripts/inventory.py` a partir de `docs/document_registry.json`,",
        "que es la fuente de verdad y se edita a mano. Recoge los ficheros originales que",
        "**no** dan lugar a un `Source`, con la evidencia de por qué. Ver `docs/CONTENT_MODEL.md` §3.1.",
        "",
        "| Fichero | SHA-256 (8) | Motivo | Documento | Evidencia |",
        "|---|---|---|---|---|",
    ]
    for e in sorted(registry.values(), key=lambda x: (x["reason"], x["filename"])):
        lines.append(
            f"| `{e['filename']}` | `{e['sha256'][:8]}` | {e['reason']} | "
            f"{e['target'] or '—'} | {e['evidence']} |"
        )
    lines += ["", "## Notas", ""]
    for e in sorted(registry.values(), key=lambda x: x["filename"]):
        if e.get("note"):
            lines.append(f"- **`{e['filename']}`** — {e['note']}")
    lines.append("")
    REGISTRY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not MASTER.is_dir():
        sys.exit(f"Carpeta maestra no accesible: {MASTER}")
    master = scan(MASTER, "master")
    work = scan(WORK, "work")
    sources_by_sha = parse_sources()
    registry = load_registry()

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
        reg = registry.get(m["sha256"])
        if reg:
            m["status"] = REGISTRY_STATUS[reg["reason"]]
            m["registryTarget"] = reg["target"]
        elif len(master_by_sha[m["sha256"]]) > 1:
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
        reg = registry.get(w["sha256"])
        if src:
            w["status"] = "procesado"
        elif reg:
            w["status"] = REGISTRY_STATUS[reg["reason"]]
            w["registryTarget"] = reg["target"]
        else:
            w["status"] = "pendiente-de-analisis"

    data = {
        "master": {"path": str(MASTER), "files": master},
        "work": {"path": str(WORK), "files": work},
        "registry": sorted(registry.values(), key=lambda e: e["filename"]),
    }
    write_registry_md(registry)
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
        "## No fichables (registro documental)",
        "",
        "Ficheros que no dan lugar a un `Source`: duplicados, fragmentos, anexos y",
        "normativa. El detalle y la evidencia de cada uno, en `docs/DOCUMENT_REGISTRY.md`.",
        "",
        "| Fichero | SHA-256 (8) | Motivo | Documento |",
        "|---|---|---|---|",
    ]
    for e in sorted(registry.values(), key=lambda x: x["filename"]):
        lines.append(
            f"| `{e['filename']}` | `{e['sha256'][:8]}` | {REGISTRY_STATUS[e['reason']]} | "
            f"{e['target'] or '—'} |"
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
    pending = [w["name"] for w in work if w["status"] == "pendiente-de-analisis"]
    print(f"Pendientes de analizar ({len(pending)}): {pending}")


if __name__ == "__main__":
    main()
