#!/usr/bin/env python3

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
BUILD_META_PATH = ROOT / "docs/assets/build-meta.json"
CONTENT_PATH = ROOT / "docs/assets/content.json"


def run_git(args: List[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def get_last_version() -> str:
    tags = run_git(["tag", "--list", "v*", "--sort=-v:refname"]).splitlines()
    for tag in tags:
        if re.match(r"^v\d+\.\d+\.\d+$", tag):
            return tag
    return "v1.0.0"


def bump_patch(version: str) -> str:
    m = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", version)
    if not m:
        return "v1.0.0"
    major, minor, patch = map(int, m.groups())
    return f"v{major}.{minor}.{patch + 1}"


def collect_prs() -> List[Dict]:
    prs_file = os.environ.get("PRS_JSON_FILE")
    if prs_file and Path(prs_file).exists():
        return json.loads(Path(prs_file).read_text(encoding="utf-8"))

    prs_json = os.environ.get("PRS_JSON")
    if prs_json:
        return json.loads(prs_json)

    return []


def summarize_prs(prs: List[Dict], max_items: int = 6) -> List[str]:
    merged = [pr for pr in prs if pr.get("merged_at")]
    merged.sort(key=lambda pr: pr.get("merged_at", ""), reverse=True)
    lines = []
    for pr in merged[:max_items]:
        title = (pr.get("title") or "Sin título").strip()
        number = pr.get("number")
        if number:
            lines.append(f"- {title} (#{number})")
        else:
            lines.append(f"- {title}")
    return lines


def sanitize_release_changes(lines: List[str], max_items: int = 4) -> List[str]:
    cleaned = []
    for line in lines:
        text = line.strip()
        if text.startswith("- "):
            text = text[2:]
        text = re.sub(r"\s*\(#\d+\)\s*$", "", text)
        cleaned.append(text)
    return cleaned[:max_items]


def update_changelog(new_version: str, date_iso: str, changes: List[str]) -> None:
    if CHANGELOG_PATH.exists():
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
    else:
        existing = "# Changelog\n\nEste archivo recoge los cambios relevantes publicados en `main`.\n\n"

    entry = [
        f"## [{new_version}] - {date_iso}",
        "",
        "### Resumen",
    ]
    if changes:
        entry.extend(changes)
    else:
        entry.append("- Actualización de mantenimiento sin cambios destacados.")
    entry.append("")

    if f"## [{new_version}]" in existing:
        return

    if "\n## [" in existing:
        updated = existing.replace("\n## [", "\n" + "\n".join(entry) + "\n## [", 1)
    else:
        updated = existing.rstrip() + "\n\n" + "\n".join(entry) + "\n"

    CHANGELOG_PATH.write_text(updated, encoding="utf-8")


def update_build_meta(new_version: str, date_iso: str) -> None:
    updated_date = datetime.fromisoformat(date_iso).strftime("%d/%m/%Y")
    payload = {
        "updatedDate": updated_date,
        "source": "release",
        "version": new_version,
        "releaseDate": date_iso,
    }
    BUILD_META_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def update_content_release_section(
    new_version: str, date_iso: str, changes: List[str]
) -> None:
    if not CONTENT_PATH.exists():
        return
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    portal = data.get("portal", {})
    updates = portal.get("ultimas_actualizaciones", {})
    updates["version"] = new_version
    updates["fecha"] = date_iso
    normalized_changes = sanitize_release_changes(changes, max_items=4)
    if not normalized_changes:
        normalized_changes = ["Actualización de mantenimiento sin cambios destacados."]
    updates["cambios"] = normalized_changes
    portal["ultimas_actualizaciones"] = updates
    data["portal"] = portal
    CONTENT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build_release_notes(new_version: str, date_iso: str, changes: List[str]) -> str:
    note_changes = sanitize_release_changes(changes, max_items=6)
    if not note_changes:
        note_changes = ["Actualización de mantenimiento sin cambios destacados."]
    lines = [
        f"Release {new_version}",
        "",
        "Nueva versión del portal de Los Ángeles de San Rafael con mejoras funcionales y de contenido.",
        "",
        f"Fecha: {date_iso}",
        "",
        "Cambios incluidos:",
    ]
    for item in note_changes:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    last_version = get_last_version()
    new_version = bump_patch(last_version)
    prs = collect_prs()
    changes = summarize_prs(prs)

    update_changelog(new_version, today, changes)
    update_build_meta(new_version, today)
    update_content_release_section(new_version, today, changes)

    release_notes = build_release_notes(new_version, today, changes)
    (ROOT / "release-notes.md").write_text(release_notes + "\n", encoding="utf-8")
    (ROOT / "release-version.txt").write_text(new_version + "\n", encoding="utf-8")

    print(f"last_version={last_version}")
    print(f"new_version={new_version}")
    print(f"changes_count={len(changes)}")


if __name__ == "__main__":
    main()
