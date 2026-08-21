#!/usr/bin/env python3
"""Escáner determinista de riesgo jurídico previo a publicación.

Qué hace: encuentra en el contenido patrones que casi siempre son un problema
—documentos de identidad, cuentas, secretos, rutas personales— y señala los que
casi nunca puede resolver una máquina —nombres de particulares, imputaciones,
menores—, para que los mire una persona.

Qué NO hace, y no va a hacer: no promociona nada a `cleared`, no tiene `--fix`
y no emite un juicio jurídico. Un match es un hallazgo, no una conclusión. La
decisión de publicar es humana, exactamente por la misma razón por la que
`verify_quotes.py` no promociona nada a `reviewed`.

Ningún valor detectado sale de este programa: ni por consola, ni en `--json`,
ni en el informe. Solo su máscara y una huella irreversible.

    python3 scripts/legal/legal_scan.py --paths docs documentacion/src
    python3 scripts/legal/legal_scan.py --diff-only --base origin/dev
    python3 scripts/legal/legal_scan.py --build dist --severity-threshold error
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from detectors import (
    NEEDS_HUMAN_REVIEW, OPEN, SEVERITY_ORDER, Finding, build_rules, fingerprint, run_rules,
)
from extract import PopplerMissing, check_tools, extract, image_metadata, pdf_metadata


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
BASELINE_PATH = REPO / "audit" / "legal-baseline.json"

# Los ficheros de prueba llevan datos inventados que, por construcción, disparan
# las reglas. Sin este marcador el escáner se detectaría a sí mismo.
FIXTURE_MARKER = b"LASR-FIXTURE"

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".astro", ".venv", "dist", "build",
    "fixtures",
}

EXIF_GPS_KEYS = {"GPSLatitude", "GPSLongitude"}
EXIF_AUTHOR_KEYS = {"Artist", "Copyright", "ImageDescription", "UserComment", "Make", "Model", "Software"}


# --------------------------------------------------------------------------
# Selección de ficheros
# --------------------------------------------------------------------------

def is_fixture(path: Path) -> bool:
    try:
        return FIXTURE_MARKER in path.open("rb").read(512)
    except OSError:
        return False


def walk(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root.is_file():
            out.append(root)
            continue
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            out.append(path)
    return out


def changed_files(base: str) -> list[Path]:
    merge_base = subprocess.run(
        ["git", "merge-base", base, "HEAD"], capture_output=True, text=True, cwd=REPO
    )
    if merge_base.returncode != 0:
        raise SystemExit(
            f"[error] No se pudo resolver la base «{base}». En CI hace falta "
            "`fetch-depth: 0`; un checkout superficial deja el gate sin nada con "
            "lo que comparar, y un gate que no puede comparar no es un gate."
        )
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", merge_base.stdout.strip(), "HEAD"],
        capture_output=True, text=True, cwd=REPO,
    )
    return [REPO / line for line in diff.stdout.splitlines() if (REPO / line).is_file()]


# --------------------------------------------------------------------------
# Contexto del proyecto
# --------------------------------------------------------------------------

def actor_names() -> list[str]:
    """Los 21 actores declarados son la lista blanca de `LEGAL-NAME-001`: si un
    nombre está en el corpus como entidad, ya se decidió que puede estar."""
    names: list[str] = []
    actors_dir = REPO / "documentacion" / "src" / "content" / "actors"
    for path in sorted(actors_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        head = text.split("---", 2)[1] if text.startswith("---") else text
        name = re.search(r"^name:\s*(.+)$", head, re.M)
        if name:
            names.append(name.group(1).strip().strip("\"'"))
        aliases = re.search(r"^aliases:\s*\[(.*)\]", head, re.M)
        if aliases:
            names += [a.strip().strip("\"'") for a in aliases.group(1).split(",") if a.strip()]
    return names


def load_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["fingerprint"] for item in data.get("accepted", [])}


# --------------------------------------------------------------------------
# Escaneo
# --------------------------------------------------------------------------

def opaque(path: str, reason: str, rule: str) -> Finding:
    """El hallazgo que impide confundir «no pude leerlo» con «está limpio». Se
    sintetiza en el despachador, antes de llamar a ningún detector."""
    return Finding(
        rule=rule, severity="warn", path=path, line=1, column=1,
        fingerprint=fingerprint(path + reason), masked="—",
        context=reason, message="Contenido no inspeccionable automáticamente",
        status=NEEDS_HUMAN_REVIEW,
    )


def metadata_findings(path: Path, relpath: str) -> list[Finding]:
    out: list[Finding] = []
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        for key, value in pdf_metadata(path).items():
            out.append(Finding(
                rule="LEGAL-PDF-001", severity="warn", path=relpath, line=1, column=1,
                fingerprint=fingerprint(f"{relpath}:{key}:{value}"),
                masked="•" * len(value), context=f"{key}: •••",
                message=f"El PDF conserva el metadato «{key}»: puede nombrar a quien lo creó",
                status=OPEN,
            ))
    elif suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        meta = image_metadata(path)
        if EXIF_GPS_KEYS & set(meta):
            out.append(Finding(
                rule="LEGAL-EXIF-001", severity="error", path=relpath, line=1, column=1,
                fingerprint=fingerprint(f"{relpath}:gps"), masked="•••",
                context="EXIF con coordenadas GPS",
                message="La imagen lleva dentro dónde se tomó", status=OPEN,
            ))
        for key in sorted(EXIF_AUTHOR_KEYS & set(meta)):
            out.append(Finding(
                rule="LEGAL-EXIF-001", severity="warn", path=relpath, line=1, column=1,
                fingerprint=fingerprint(f"{relpath}:{key}"), masked="•" * len(meta[key]),
                context=f"EXIF {key}: •••",
                message=f"La imagen conserva el metadato «{key}»", status=OPEN,
            ))
    return out


PRESS_BODY_KEYS = ("body", "excerpt", "summary", "content", "contenido", "entradilla")
PRESS_MIN_CHARS = 60


def press_findings(path: Path, relpath: str, text: str) -> list[Finding]:
    """Reproducir el cuerpo de una noticia no es citar. La invariante es la que
    `scripts/prensa/filter_regression_check.js` ya defiende sobre el fichero
    publicado; aquí se comprueba sobre cualquier JSON de prensa."""
    if path.suffix.lower() != ".json":
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    items = data if isinstance(data, list) else data.get("items", [])
    if not isinstance(items, list):
        return []
    out: list[Finding] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not (item.get("url") or item.get("source")):
            continue
        for key in PRESS_BODY_KEYS:
            value = item.get(key)
            if isinstance(value, str) and len(value) >= PRESS_MIN_CHARS:
                out.append(Finding(
                    rule="LEGAL-PRESS-001", severity="error", path=relpath,
                    line=1, column=1,
                    fingerprint=fingerprint(f"{relpath}:{index}:{key}"),
                    masked="•" * len(value), context=f"entrada {index}, campo «{key}»",
                    message="Se reproduce texto del medio: titular, medio, fecha y enlace bastan",
                    status=OPEN,
                ))
    return out


def scan(paths: list[Path], rules, manifest, baseline: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file() or is_fixture(path):
            continue
        relpath = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path)
        text, reason = extract(path)
        if text is None:
            rule = "LEGAL-OPAQUE-002" if path.suffix.lower() == ".pdf" else "LEGAL-OPAQUE-001"
            findings.append(opaque(relpath, reason, rule))
        else:
            findings += run_rules(text, relpath, rules)
            findings += press_findings(path, relpath, text)
        findings += metadata_findings(path, relpath)

    accepted = manifest.accepted_rules if manifest else (lambda _: set())
    out = []
    for f in findings:
        if f.fingerprint in baseline or f.rule in accepted(f.path):
            continue
        out.append(f)
    return out


# --------------------------------------------------------------------------
# Informe
# --------------------------------------------------------------------------

SEVERITY_LABEL = {"error": "GRAVE", "warn": "MEDIO", "info": "LEVE"}


def report(findings: list[Finding], inspected: int, opaque_count: int) -> None:
    if not findings:
        print(f"✔ Sin hallazgos ({inspected} ficheros inspeccionados, {opaque_count} no inspeccionables)")
        return

    by_rule: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_rule[f.rule].append(f)

    print(f"\n{len(findings)} hallazgos en {len({f.path for f in findings})} ficheros\n")
    order = sorted(by_rule.items(), key=lambda kv: (-SEVERITY_ORDER[kv[1][0].severity], -len(kv[1])))
    for rule, group in order:
        head = group[0]
        marker = "REVISIÓN HUMANA" if head.status == NEEDS_HUMAN_REVIEW else SEVERITY_LABEL[head.severity]
        print(f"[{marker}] {rule} — {head.message} ({len(group)})")
        for f in group[:6]:
            print(f"    {f.path}:{f.line}:{f.column}  {f.masked}")
            print(f"        …{f.context}…")
        if len(group) > 6:
            print(f"    … y {len(group) - 6} más")
        print()

    counts = Counter(f.severity for f in findings)
    human = sum(1 for f in findings if f.status == NEEDS_HUMAN_REVIEW)
    print(f"Resumen: {counts['error']} graves · {counts['warn']} medios · "
          f"{counts['info']} leves · {human} exigen revisión humana")


def markdown(findings: list[Finding]) -> str:
    lines = ["| Regla | Gravedad | Fichero | Línea | Estado |", "|---|---|---|---|---|"]
    for f in sorted(findings, key=lambda x: (-SEVERITY_ORDER[x.severity], x.path, x.line)):
        lines.append(f"| `{f.rule}` | {SEVERITY_LABEL[f.severity]} | `{f.path}` | {f.line} | {f.status} |")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Escáner de riesgo jurídico previo a publicación.")
    p.add_argument("--paths", nargs="*", default=[], help="Rutas a escanear")
    p.add_argument("--diff-only", action="store_true", help="Solo lo que la rama toca")
    p.add_argument("--base", default="origin/dev", help="Base de comparación para --diff-only")
    p.add_argument("--build", metavar="DIST", help="Escanear el sitio ya construido")
    p.add_argument("--baseline", default=str(BASELINE_PATH))
    p.add_argument("--severity-threshold", choices=("info", "warn", "error"), default="error")
    p.add_argument("--json", action="store_true")
    p.add_argument("--md", action="store_true")
    p.add_argument("--rules", action="store_true", help="Listar el catálogo y salir")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        import manifest as manifest_mod
        loaded, manifest_errors = manifest_mod.load(MANIFEST_PATH)
    except Exception:
        loaded, manifest_errors = None, []

    allowed_emails = loaded.allowed_emails if loaded else []
    rules = build_rules(allowed_emails, actor_names())

    if args.rules:
        print("Catálogo de reglas\n")
        for r in rules:
            mark = " · revisión humana" if r.human_review else ""
            print(f"  {r.id:22} {SEVERITY_LABEL[r.severity]:6} {r.title}{mark}")
            print(f"  {'':22} {r.message}")
        print("\nAdemás, sintetizadas por el despachador:")
        print("  LEGAL-OPAQUE-001       MEDIO  Binario no inspeccionable · revisión humana")
        print("  LEGAL-OPAQUE-002       MEDIO  PDF sin capa de texto · revisión humana")
        print("  LEGAL-PDF-001          MEDIO  Metadatos del PDF")
        print("  LEGAL-EXIF-001         GRAVE  EXIF con GPS o autoría")
        print("  LEGAL-PRESS-001        GRAVE  Texto del medio reproducido")
        print("\nLa lista blanca de correos y de dominios propios sale de")
        print("audit/portal-manifest.json; la de nombres, de los actores declarados.")
        return 0

    try:
        check_tools()
    except PopplerMissing as exc:
        print(f"[error] {exc}", file=sys.stderr)
        print("Un escáner que se salta los PDF en silencio es peor que no tenerlo.", file=sys.stderr)
        return 2

    if args.build:
        roots = [Path(args.build)]
    elif args.diff_only:
        roots = changed_files(args.base)
    elif args.paths:
        roots = [Path(p) if Path(p).is_absolute() else REPO / p for p in args.paths]
    else:
        print("[error] Indica --paths, --diff-only o --build", file=sys.stderr)
        return 2

    files = walk(roots)
    baseline = load_baseline(Path(args.baseline))
    findings = scan(files, rules, loaded, baseline)

    opaque_count = sum(1 for f in findings if f.rule.startswith("LEGAL-OPAQUE"))
    inspected = len(files) - opaque_count

    if args.json:
        print(json.dumps({
            "tool": "legal_scan", "version": 1,
            "scannedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scope": {"files": len(files), "base": args.base if args.diff_only else None},
            "summary": {
                "error": sum(1 for f in findings if f.severity == "error"),
                "warn": sum(1 for f in findings if f.severity == "warn"),
                "info": sum(1 for f in findings if f.severity == "info"),
                "needsHumanReview": sum(1 for f in findings if f.status == NEEDS_HUMAN_REVIEW),
                "filesInspected": inspected, "filesOpaque": opaque_count,
            },
            "findings": [f.as_dict() for f in findings],
        }, ensure_ascii=False, indent=2))
    elif args.md:
        print(markdown(findings))
    else:
        if manifest_errors:
            print("Problemas en el manifiesto:")
            for e in manifest_errors:
                print(f"  · {e}")
            print()
        report(findings, inspected, opaque_count)

    threshold = SEVERITY_ORDER[args.severity_threshold]
    blocking = [f for f in findings if SEVERITY_ORDER[f.severity] >= threshold]
    return 1 if blocking or manifest_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
