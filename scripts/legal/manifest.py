"""El manifiesto jurídico del portal.

`docs/` es HTML plano: no hay frontmatter donde colgar un estado. El manifiesto
cumple esa función y, de paso, una segunda: es la lista blanca del despliegue.
Hasta ahora `pages.yml` hacía `cp -r docs/* dist/` sin filtro, que es el
mecanismo exacto por el que se publicaron cuatro documentos internos en marzo y
un PDF con dos DNI en agosto. Declarar es ahora condición para publicar.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from detectors import RE_DNI, RE_EMAIL, RE_IBAN, valid_dni, valid_iban

STATES = ("unchecked", "cleared", "cleared-redacted", "needs-human-review", "blocked")
PUBLISHABLE_STATES = ("cleared", "cleared-redacted")

# Directorios y ficheros de `docs/` que no son contenido del portal.
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}


class ManifestError(Exception):
    pass


@dataclass
class Entry:
    path: str
    legal_status: str
    publish: bool = True
    reviewed_at: str | None = None
    reason: str | None = None
    redactions: list[str] = field(default_factory=list)
    accepted_rules: list[str] = field(default_factory=list)
    generator: str | None = None
    invariants: list[str] = field(default_factory=list)
    sha256: str | None = None

    @property
    def is_generated(self) -> bool:
        return self.generator is not None


@dataclass
class Manifest:
    version: int
    allowed_emails: list[str]
    assets: dict[str, Entry]
    sections: dict[str, Entry]
    path: Path

    def entry_for(self, relpath: str) -> Entry | None:
        return self.assets.get(relpath)

    def accepted_rules(self, relpath: str) -> set[str]:
        entry = self.assets.get(relpath)
        return set(entry.accepted_rules) if entry else set()


def contains_pii(value: str) -> str | None:
    """El motivo describe la CATEGORÍA del dato, nunca el dato. Guardia de
    última milla: la autoridad es `detectors.py`, aquí solo se comprueban las
    tres formas que jamás deben aparecer en un texto de trazabilidad."""
    for m in RE_DNI.finditer(value):
        if valid_dni(m.group(1), m.group(2)):
            return "un número de documento de identidad"
    for m in RE_IBAN.finditer(value):
        if valid_iban(m.group(1)):
            return "un IBAN"
    if RE_EMAIL.search(value):
        return "una dirección de correo"
    return None


def _entry(relpath: str, raw: dict, where: str, errors: list[str]) -> Entry:
    status = raw.get("legalStatus", "unchecked")
    if status not in STATES:
        errors.append(f"{where} «{relpath}»: legalStatus «{status}» no es un valor válido {STATES}")
    reason = raw.get("reason")
    redactions = list(raw.get("redactions", []))

    if status != "unchecked":
        if not raw.get("reviewedAt") and not raw.get("generator"):
            errors.append(f"{where} «{relpath}»: estado «{status}» sin reviewedAt")
        if not reason:
            errors.append(f"{where} «{relpath}»: estado «{status}» sin reason")
    if status == "cleared-redacted" and not redactions:
        errors.append(f"{where} «{relpath}»: «cleared-redacted» exige redactions no vacío")

    for text, label in [(reason, "reason")] + [(r, "redactions") for r in redactions]:
        if not text:
            continue
        found = contains_pii(text)
        if found:
            errors.append(
                f"{where} «{relpath}»: {label} contiene {found}. "
                "Se describe la categoría del dato, nunca su valor."
            )

    return Entry(
        path=relpath,
        legal_status=status,
        publish=bool(raw.get("publish", True)),
        reviewed_at=raw.get("reviewedAt"),
        reason=reason,
        redactions=redactions,
        accepted_rules=list(raw.get("acceptedRules", [])),
        generator=raw.get("generator"),
        invariants=list(raw.get("invariants", [])),
        sha256=raw.get("sha256"),
    )


def load(path: Path) -> tuple[Manifest, list[str]]:
    if not path.exists():
        raise ManifestError(
            f"No existe {path}. Créalo con `gate.py --check-manifest`, que imprime "
            "la plantilla de cada entrada que falta."
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{path} no es JSON válido: {exc}") from exc

    errors: list[str] = []
    assets = {
        rel: _entry(rel, data, "assets", errors)
        for rel, data in sorted(raw.get("assets", {}).items())
    }
    sections = {
        key: _entry(key, data, "content.sections", errors)
        for key, data in sorted(raw.get("content", {}).get("sections", {}).items())
    }
    manifest = Manifest(
        version=int(raw.get("version", 1)),
        allowed_emails=list(raw.get("allowedEmails", [])),
        assets=assets,
        sections=sections,
        path=path,
    )
    return manifest, errors


# --------------------------------------------------------------------------
# Completitud
# --------------------------------------------------------------------------

def portal_files(docs_dir: Path) -> list[str]:
    """Todo lo que hoy se publicaría. Los symlinks quedan fuera a propósito:
    no son contenido, y uno de ellos apunta al build de la guía."""
    out = []
    for p in sorted(docs_dir.rglob("*")):
        if p.is_symlink() or not p.is_file() or p.name in IGNORED_NAMES:
            continue
        out.append(p.relative_to(docs_dir.parent).as_posix())
    return out


def section_digest(value: object) -> str:
    import hashlib
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def check_completeness(manifest: Manifest, repo: Path) -> list[str]:
    problems: list[str] = []
    docs = repo / "docs"

    present = set(portal_files(docs))
    declared = set(manifest.assets)

    for missing in sorted(present - declared):
        problems.append(
            f"Sin declarar en el manifiesto: {missing}\n"
            f'    Añade:  "{missing}": {{"legalStatus": "unchecked", "reason": "…"}}'
        )
    for orphan in sorted(declared - present):
        problems.append(
            f"Declarado en el manifiesto pero no existe: {orphan}. "
            "¿Se renombró sin re-clavar la entrada?"
        )

    content_path = repo / "docs" / "assets" / "content.json"
    if content_path.exists():
        content = json.loads(content_path.read_text(encoding="utf-8"))
        for key, value in content.items():
            entry = manifest.sections.get(key)
            if entry is None:
                problems.append(
                    f"Sección de content.json sin declarar: «{key}»\n"
                    f'    Añade:  "{key}": {{"legalStatus": "unchecked", '
                    f'"sha256": "{section_digest(value)}", "reason": "…"}}'
                )
                continue
            if entry.is_generated:
                continue
            digest = section_digest(value)
            if entry.sha256 and entry.sha256 != digest:
                problems.append(
                    f"La sección «{key}» de content.json ha cambiado desde su revisión "
                    f"jurídica. Revísala y actualiza sha256 a {digest}"
                )
        for key in manifest.sections:
            if key not in content:
                problems.append(f"Sección declarada que ya no existe en content.json: «{key}»")

    return problems
