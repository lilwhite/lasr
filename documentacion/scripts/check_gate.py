#!/usr/bin/env python3
"""Comprueba sobre el `dist/` construido que el gate jurídico hizo su trabajo.

Confiar en veinte sitios de llamada es confiar en el próximo que edite una
plantilla. `policy.ts` decide, y esto verifica que la decisión llegó al sitio.

Como `check_links.py`, valida el artefacto y no el fuente: lo que importa no es
lo que el código pretendía, sino lo que salió. Y como él, no tiene dependencias
fuera de la biblioteca estándar.

Cinco comprobaciones, y la cuarta es la que evita el desastre silencioso:

  1. Una entrada `blocked` no genera página.
  2. Ningún HTML enlaza a una entrada `blocked`.
  3. El sitemap no la lista.
  4. Toda entrada NO bloqueada SÍ genera su página. Un filtro demasiado
     agresivo que se llevase doscientas por delante se caza aquí, no en
     producción.
  5. El eje jurídico no aparece en el HTML público: es interno.

    python3 scripts/check_gate.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CONTENT = RAIZ / "src" / "content"
DIST = RAIZ / "dist"

BLOCKED = "blocked"

# Mismas reglas que `graph.ts:ROUTE_PREFIX` y `entitySlug`. Se repiten aquí
# porque este script mira el resultado, no el código que lo produjo: si las dos
# dejaran de coincidir, la comprobación 4 lo diría.
PREFIJOS = {
    "topics": ("temas", None),
    "sources": ("documentos", "SRC-"),
    "notes": ("notas", "NOTE-"),
    "events": ("acontecimientos", "EVENT-"),
    "actors": ("actores", "ACTOR-"),
    "procedures": ("procedimientos", "PROC-"),
    "questions": ("preguntas", None),
}

RE_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
RE_LEGAL = re.compile(r"^legalStatus:\s*[\"']?([\w-]+)[\"']?\s*$", re.M)
RE_SLUG = re.compile(r"^slug:\s*[\"']?([\w-]+)[\"']?\s*$", re.M)
RE_ID = re.compile(r"^id:\s*[\"']?([A-Z0-9-]+)[\"']?\s*$", re.M)

FUGAS = ("legalStatus", "legalReview", "LEGAL-")


# La base la resuelve `check_links.py`, que ya aprendió que `BASE` manda sobre
# el literal del config. Duplicar esa lógica aquí fue un error: mi versión no
# entendía `process.env.BASE ?? '/documentacion'`, devolvía cadena vacía y daba
# por bueno un sitio con enlaces a páginas bloqueadas.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_links import base_from_config  # noqa: E402


def base_del_sitio() -> str:
    return base_from_config()


def entradas() -> list[tuple[str, str, str]]:
    """`(ruta relativa de la página, estado jurídico, fichero)`."""
    out = []
    for coleccion, (prefijo_ruta, prefijo_id) in PREFIJOS.items():
        for fichero in sorted((CONTENT / coleccion).glob("*.md")):
            texto = fichero.read_text(encoding="utf-8", errors="replace")
            cabecera = RE_FRONTMATTER.match(texto)
            if not cabecera:
                continue
            head = cabecera.group(1)
            estado = (RE_LEGAL.search(head) or [None, "unchecked"])[1] \
                if RE_LEGAL.search(head) else "unchecked"
            if prefijo_id is None:
                slug_match = RE_SLUG.search(head)
                if not slug_match:
                    continue
                slug = slug_match.group(1)
            else:
                id_match = RE_ID.search(head)
                if not id_match:
                    continue
                slug = id_match.group(1)[len(prefijo_id):].lower()
            out.append((f"{prefijo_ruta}/{slug}/", estado, fichero.name))
    return out


def main() -> int:
    if not DIST.is_dir():
        print("[error] No existe dist/. Ejecuta `npm run build` antes.", file=sys.stderr)
        return 2

    base = base_del_sitio()
    todas = entradas()
    bloqueadas = [(r, f) for r, e, f in todas if e == BLOCKED]
    publicables = [(r, f) for r, e, f in todas if e != BLOCKED]

    htmls = sorted(DIST.rglob("*.html"))
    cuerpo = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in htmls)
    sitemap_path = DIST / "sitemap.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.exists() else ""

    problemas: list[str] = []

    for ruta, fichero in bloqueadas:
        if (DIST / ruta / "index.html").is_file():
            problemas.append(f"«{fichero}» está blocked y su página existe en dist/{ruta}")
        if f'href="{base}/{ruta}"' in cuerpo:
            problemas.append(f"«{fichero}» está blocked y algún HTML sigue enlazándola")
        if f"{base}/{ruta}" in sitemap:
            problemas.append(f"«{fichero}» está blocked y el sitemap la lista")

    faltan = [(r, f) for r, f in publicables if not (DIST / r / "index.html").is_file()]
    if faltan:
        problemas.append(
            f"{len(faltan)} entradas publicables sin página en dist/. "
            "Un filtro de más se lleva el sitio por delante sin avisar:\n"
            + "\n".join(f"        {f} → dist/{r}" for r, f in faltan[:8])
            + (f"\n        … y {len(faltan) - 8} más" if len(faltan) > 8 else "")
        )

    for html in htmls:
        if "/revision/" in html.as_posix():
            continue
        texto = html.read_text(encoding="utf-8", errors="replace")
        for fuga in FUGAS:
            if fuga in texto:
                problemas.append(
                    f"«{fuga}» aparece en {html.relative_to(DIST)}. El eje jurídico es "
                    "interno: publicarlo señala qué páginas están sin revisar."
                )
                break

    if problemas:
        print(f"\n✘ {len(problemas)} problemas en la puerta de publicación:\n")
        for p in problemas:
            print(f"  · {p}\n")
        return 1

    print(
        f"✔ Puerta de publicación correcta ({len(publicables)} entradas publicadas, "
        f"{len(bloqueadas)} bloqueadas, {len(htmls)} páginas revisadas)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
