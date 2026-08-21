#!/usr/bin/env python3
"""
Comprueba los enlaces internos del sitio ya construido.

Sustituye a la guardia anterior, que buscaba `href="/…"` en el código fuente y
daba falsa confianza: no veía los enlaces construidos con expresiones. Un
componente que emitía `href={entityRoute(entry)}` en lugar de
`href={url(entityRoute(entry))}` generó 1.757 enlaces sin la base del sitio sin
que la comprobación dijera nada.

Revisa dos cosas sobre `dist/`:
  1. Que ningún enlace interno omita la base (rompería en GitHub Pages), salvo
     los que apuntan al portal vecinal de la raíz del dominio (ver PORTAL).
  2. Que todo enlace interno apunte a una página que existe.

Uso:  python3 scripts/check_links.py [dist]
"""

import os
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HREF = re.compile(r'href="([^"]+)"')
EXTS = (".svg", ".png", ".jpg", ".webp", ".xml", ".txt", ".css", ".js", ".woff", ".woff2", ".pdf", ".ico")

# Rutas del portal vecinal, que vive en la raíz del dominio y fuera de este
# build. Son los únicos enlaces internos que legítimamente no llevan la base:
# salen de esta capa. Se enumeran en vez de aceptar cualquier `/…` porque la
# comprobación de la base es la que cazó 1.757 enlaces mal construidos, y
# relajarla del todo la volvería inútil.
PORTAL = frozenset({
    "/",
    "/prensa/",
    "/parcelas/",
    "/actualizaciones/",
    "/documentacion-relevante/",
})


def base_from_config() -> str:
    """La misma base que usó el build.

    `BASE` manda sobre el literal del config, exactamente igual que en
    `astro.config.mjs`. Leer solo el fichero hacía que un build con la variable
    puesta se validara contra otra base y marcara como rotos los ~1.700 enlaces
    internos correctos.
    """
    env = os.environ.get("BASE")
    if env is not None:
        return env.rstrip("/")

    cfg = (REPO / "astro.config.mjs").read_text(encoding="utf-8")
    m = re.search(r"base:\s*process\.env\.BASE\s*\?\?\s*'([^']*)'", cfg) or re.search(r"base:\s*'([^']*)'", cfg)
    b = (m.group(1) if m else "/").rstrip("/")
    return b or ""


def main() -> int:
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "dist"
    if not dist.is_dir():
        print(f"No existe {dist}. Ejecuta antes `npm run build`.", file=sys.stderr)
        return 1

    base = base_from_config()

    # Rutas servibles: cada index.html es una página; los demás ficheros, activos.
    pages, assets = set(), set()
    for f in dist.rglob("*"):
        if not f.is_file():
            continue
        rel = "/" + str(f.relative_to(dist)).replace("\\", "/")
        if f.name == "index.html":
            pages.add(base + rel[: -len("index.html")])
        else:
            assets.add(base + rel)

    sin_base: dict[str, set[str]] = defaultdict(set)
    rotos: dict[str, set[str]] = defaultdict(set)

    for f in dist.rglob("*.html"):
        origen = str(f.relative_to(dist))
        for raw in HREF.findall(f.read_text(encoding="utf-8", errors="replace")):
            if raw.startswith(("http://", "https://", "mailto:", "#", "//")):
                continue
            href = urllib.parse.unquote(raw.split("#")[0].split("?")[0])
            if not href.startswith("/"):
                continue
            if href in PORTAL:
                continue
            if base and not (href == base or href.startswith(base + "/")):
                sin_base[href].add(origen)
                continue
            objetivo = href if href.endswith("/") or href.endswith(EXTS) else href + "/"
            if objetivo not in pages and href not in assets:
                rotos[href].add(origen)

    def informe(titulo: str, datos: dict[str, set[str]]) -> None:
        if not datos:
            return
        total = sum(len(v) for v in datos.values())
        print(f"\n{titulo}: {len(datos)} destinos, {total} apariciones")
        for destino, origenes in sorted(datos.items(), key=lambda kv: -len(kv[1]))[:15]:
            ejemplo = sorted(origenes)[0]
            print(f"  {len(origenes):>4}×  {destino}")
            print(f"         p. ej. en {ejemplo}")

    informe("Enlaces internos SIN la base del sitio", sin_base)
    informe("Enlaces a páginas que no existen", rotos)

    if not sin_base and not rotos:
        print(f"✔ Enlaces internos correctos ({len(pages)} páginas, base '{base or '/'}').")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
