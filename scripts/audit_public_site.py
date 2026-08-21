#!/usr/bin/env python3
"""Audita la superficie pública: qué se puede descubrir en lo que se publica.

Se mira el artefacto como lo miraría alguien de fuera, no el código que lo
produjo. Lo que importa no es lo que las plantillas pretendían: es lo que salió.

Tres preguntas, y la tercera es la que evita el desastre silencioso:

  1. ¿Existe algo que nunca debió publicarse?
  2. ¿Aparece en el texto algo interno —el eje jurídico, una ruta local, una
     credencial, el nombre de la carpeta de originales—?
  3. ¿Siguen existiendo las páginas que sí deben existir?

La tercera no es simetría decorativa. Un filtro de más que se llevara media web
por delante pasaría las dos primeras con matrícula de honor.

    python3 scripts/audit_public_site.py dist
    python3 scripts/audit_public_site.py dist --url https://lasr-info.es
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Rutas que se retiraron a propósito. Que devuelvan 404 no basta: no debe
# existir ningún enlace público que lleve hasta ellas.
RETIRADAS = (
    "documentacion/revision/",
    "audit/",
    "documentacion-relevante/estatutos-euc.pdf",
    "DEPLOY.md",
    "WORKFLOW.md",
    "RELEASES.md",
    "automatizacion-prensa.md",
    "data/prensa/sources.json",
)

# Lo que debe seguir en pie. Sin esto, borrar el sitio entero sería un éxito.
IMPRESCINDIBLES = (
    "index.html",
    "prensa/index.html",
    "parcelas/index.html",
    "CNAME",
    "robots.txt",
    "sitemap.xml",
    "assets/config.json",
    "assets/content.json",
    "assets/css/styles.css",
    "assets/js/main.js",
    "documentacion/index.html",
    "documentacion/cronologia/index.html",
    "documentacion/temas/recepcion-de-la-urbanizacion/index.html",
    "documentacion/documentos/2011-tsjcyl-271/index.html",
)
MINIMO_PAGINAS = 250

# Cadenas que delatan que algo interno se escapó al texto publicado.
PROHIBIDAS: tuple[tuple[str, str], ...] = (
    ("legalStatus", "el eje jurídico es interno: publicarlo señala qué páginas están sin revisar"),
    ("legalReview", "ídem"),
    ("LEGAL-", "identificador de regla de auditoría"),
    ("private-sources", "nombre de la carpeta de originales"),
    ("LASR-DOC", "nombre de la carpeta maestra"),
    ("portal-manifest", "el manifiesto es interno"),
    ("LEGAL_PUBLICATION_AUDIT", "el informe es interno"),
)

PATRONES = (
    (re.compile(r"/mnt/[a-z]/|/home/[^/\s\"']+/|[A-Z]:\\\\?Users\\\\?|OneDrive"),
     "ruta del sistema de ficheros de una persona"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{28,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"),
     "credencial"),
    (re.compile(r"sourceMappingURL"), "referencia a un source map"),
)

INSPECCIONABLES = {".html", ".htm", ".json", ".js", ".mjs", ".css", ".xml", ".txt", ".md", ".svg"}

# El área de revisión no debe estar en el artefacto; si aparece, la comprobación
# 1 ya lo dice. No se exime de nada.
EXENTAS: tuple[str, ...] = ()


def revisar_ficheros(raiz: Path) -> list[str]:
    problemas: list[str] = []

    for ruta in RETIRADAS:
        destino = raiz / ruta
        if destino.exists():
            problemas.append(f"Existe en el artefacto algo retirado: {ruta}")

    for ruta in IMPRESCINDIBLES:
        if not (raiz / ruta).exists():
            problemas.append(
                f"FALTA una página que debe existir: {ruta}. "
                "Un filtro de más se lleva el sitio por delante sin avisar."
            )

    paginas = len(list(raiz.rglob("*.html")))
    if paginas < MINIMO_PAGINAS:
        problemas.append(
            f"Solo hay {paginas} páginas en el artefacto (mínimo {MINIMO_PAGINAS}). "
            "Abortar es mejor que publicar un sitio a medias."
        )

    mapas = list(raiz.rglob("*.map"))
    if mapas:
        problemas.append(
            f"{len(mapas)} source maps en el artefacto: revelan rutas y código "
            f"interno. P. ej. {mapas[0].relative_to(raiz)}"
        )

    return problemas


def revisar_texto(raiz: Path) -> list[str]:
    problemas: list[str] = []
    for fichero in sorted(raiz.rglob("*")):
        if not fichero.is_file() or fichero.suffix.lower() not in INSPECCIONABLES:
            continue
        rel = fichero.relative_to(raiz).as_posix()
        if any(rel.startswith(e) for e in EXENTAS):
            continue
        try:
            texto = fichero.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for cadena, motivo in PROHIBIDAS:
            if cadena in texto:
                problemas.append(f"«{cadena}» aparece en {rel} — {motivo}")
        for patron, motivo in PATRONES:
            if patron.search(texto):
                problemas.append(f"{rel} contiene {motivo}")
    return problemas


def revisar_produccion(base: str) -> list[str]:
    """Contra el sitio vivo. Complementa al artefacto: comprueba lo que de
    verdad se está sirviendo, que es lo único que ve un visitante."""
    problemas: list[str] = []
    base = base.rstrip("/")

    def estado(ruta: str) -> int:
        peticion = urllib.request.Request(f"{base}/{ruta}", method="HEAD",
                                          headers={"User-Agent": "lasr-audit"})
        try:
            with urllib.request.urlopen(peticion, timeout=20) as respuesta:
                return respuesta.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except (urllib.error.URLError, OSError):
            return 0

    for ruta in RETIRADAS:
        code = estado(ruta)
        if code == 200:
            problemas.append(f"/{ruta} responde 200 en producción y no debería existir")
        elif code == 0:
            problemas.append(f"/{ruta}: no se pudo comprobar")

    for ruta in ("", "prensa/", "parcelas/", "documentacion/", "documentacion/cronologia/"):
        code = estado(ruta)
        if code != 200:
            problemas.append(f"/{ruta} responde {code} en producción y debería estar en pie")

    return problemas


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Auditoría de la superficie pública.")
    p.add_argument("dist", help="Directorio del artefacto construido")
    p.add_argument("--url", help="Comprobar además el sitio en producción")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    raiz = Path(args.dist)
    if not raiz.is_dir():
        print(f"[error] No existe {raiz}. Construye el artefacto antes.", file=sys.stderr)
        return 2

    problemas = revisar_ficheros(raiz) + revisar_texto(raiz)
    if args.url:
        problemas += revisar_produccion(args.url)

    if args.json:
        print(json.dumps({"dist": str(raiz), "problemas": problemas},
                         ensure_ascii=False, indent=2))
    elif problemas:
        print(f"\n✘ {len(problemas)} problemas en la superficie pública:\n")
        for problema in problemas:
            print(f"  · {problema}")
        print()
    else:
        paginas = len(list(raiz.rglob("*.html")))
        ficheros = sum(1 for f in raiz.rglob("*") if f.is_file())
        print(f"✔ Superficie pública correcta ({paginas} páginas, {ficheros} ficheros, "
              f"{len(RETIRADAS)} rutas retiradas ausentes)")

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
