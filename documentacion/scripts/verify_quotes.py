#!/usr/bin/env python3
"""
Comprueba que cada cita literal aparece en la página que dice citar.

Es el punto más tedioso del checklist de revisión (CONTENT_MODEL §7): "la cita
corresponde a la página indicada". Comprobarlo a mano son 202 citas repartidas
por 36 documentos escaneados. Comprobarlo a máquina cuesta unos segundos.

Lo que este script NO hace, y por eso no promociona nada a `reviewed`:
no juzga si la nota representa fielmente la fuente, ni si se ha colado una
conclusión no sustentada, ni si `type` y `basis` son correctos. Eso es
criterio humano y sigue haciendo falta.

Uso:
    python3 scripts/verify_quotes.py            # informe por consola
    python3 scripts/verify_quotes.py --json     # salida procesable
    python3 scripts/verify_quotes.py --failures # solo lo que no casa
"""

import argparse
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "src" / "content" / "sources"
CACHE = REPO / "private-sources" / "text"
COLLECTIONS = ["notes", "events"]

# Por debajo de esto la cita no se da por encontrada. El OCR de estos escaneos
# confunde letras con frecuencia ("abugo" por "abuso"), así que exigir
# coincidencia exacta daría falsos negativos en masa.
THRESHOLD = 0.82


def normalize(text: str) -> str:
    """Minúsculas, sin tildes, sin puntuación, espacios colapsados."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9ñ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def frontmatter(path: Path) -> str:
    parts = path.read_text(encoding="utf-8").split("---")
    return parts[1] if len(parts) > 2 else ""


def source_index() -> dict[str, str]:
    """id del Source → nombre base de su fichero de caché."""
    out = {}
    for f in sorted(SOURCES.glob("*.md")):
        fm = frontmatter(f)
        sid = re.search(r"^id:\s*(\S+)", fm, re.M)
        fil = re.search(r"^file:\s*(\S+)", fm, re.M)
        if sid and fil and fil.group(1) != "null":
            out[sid.group(1)] = Path(fil.group(1).strip('"')).stem
    return out


def pages_of(stem: str) -> dict[int, str]:
    """Texto por página desde la caché, usando sus marcadores."""
    txt = CACHE / f"{stem}.txt"
    if not txt.exists():
        return {}
    raw = txt.read_text(encoding="utf-8", errors="replace")
    out: dict[int, str] = {}
    for chunk in raw.split("=== PÁGINA ")[1:]:
        head, _, body = chunk.partition("===")
        try:
            out[int(head.strip())] = body
        except ValueError:
            continue
    return out


def parse_citations(path: Path) -> list[dict]:
    """Extrae las citas del frontmatter sin depender de un parser YAML."""
    fm = frontmatter(path)
    cites, cur = [], None
    for line in fm.splitlines():
        m = re.match(r"\s*-\s+source:\s*(\S+)", line)
        if m:
            if cur:
                cites.append(cur)
            cur = {"source": m.group(1), "pdfPages": [], "quote": None, "locator": None}
            continue
        if cur is None:
            continue
        m = re.match(r"\s*pdfPages:\s*\[([0-9,\s]+)\]", line)
        if m:
            cur["pdfPages"] = [int(x) for x in re.findall(r"\d+", m.group(1))]
            continue
        m = re.match(r"\s*locator:\s*[\"']?(.+?)[\"']?\s*$", line)
        if m:
            cur["locator"] = m.group(1)
            continue
        m = re.match(r"\s*quote:\s*(.*)$", line)
        if m:
            val = m.group(1).strip()
            cur["quote"] = "" if val in (">-", ">", "|", "|-") else val.strip('"')
            cur["_collecting"] = val in (">-", ">", "|", "|-")
            continue
        if cur.get("_collecting"):
            if re.match(r"\s*[a-zA-Z]+:", line) or re.match(r"\s*-\s", line):
                cur["_collecting"] = False
            elif line.strip():
                cur["quote"] = (cur["quote"] + " " + line.strip()).strip()
    if cur:
        cites.append(cur)
    return [c for c in cites if c.get("quote")]


def best_match(quote: str, page_text: str) -> float:
    """Mejor coincidencia de la cita dentro del texto de la página."""
    q, p = normalize(quote), normalize(page_text)
    if not q or not p:
        return 0.0
    # Las citas usan "…" para elidir; se comprueba cada fragmento por separado
    # y se devuelve el peor, que es el criterio prudente.
    fragments = [f for f in re.split(r"\s*\.\.\.\s*|\s*…\s*", quote) if len(normalize(f)) > 25]
    if len(fragments) > 1:
        return min(best_match(f, page_text) for f in fragments)
    if q in p:
        return 1.0
    # Ventana deslizante del tamaño de la cita.
    best, step = 0.0, max(1, len(q) // 4)
    for i in range(0, max(1, len(p) - len(q) + 1), step):
        window = p[i : i + len(q)]
        r = SequenceMatcher(None, q, window).ratio()
        if r > best:
            best = r
            if best >= 0.995:
                break
    return best


def word_coverage(quote: str, page_text: str) -> float:
    """Qué proporción de las palabras de la cita está en la página.

    Hace falta porque la extracción de algunos PDF devuelve las palabras
    desordenadas —columnas entrelazadas— y una comparación por secuencia falla
    aunque la cita sea literal y correcta. Si están todas las palabras pero en
    otro orden, el problema es de la extracción, no de la cita.
    """
    qs = [w for w in normalize(quote).split() if len(w) > 3]
    if not qs:
        return 0.0
    page = set(normalize(page_text).split())
    return sum(1 for w in qs if w in page) / len(qs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--failures", action="store_true", help="solo lo que no casa")
    args = ap.parse_args()

    idx = source_index()
    cache: dict[str, dict[int, str]] = {}
    results = []

    for coll in COLLECTIONS:
        for f in sorted((REPO / "src" / "content" / coll).glob("*.md")):
            owner = re.search(r"^id:\s*(\S+)", frontmatter(f), re.M)
            owner = owner.group(1) if owner else f.stem
            for c in parse_citations(f):
                stem = idx.get(c["source"])
                if not stem:
                    results.append({**c, "owner": owner, "status": "sin-fichero", "score": None})
                    continue
                if stem not in cache:
                    cache[stem] = pages_of(stem)
                pages = cache[stem]
                if not pages:
                    results.append({**c, "owner": owner, "status": "sin-cache", "score": None})
                    continue
                text = " ".join(pages.get(p, "") for p in c["pdfPages"])
                if not text.strip():
                    results.append({**c, "owner": owner, "status": "pagina-vacia", "score": None})
                    continue
                score = best_match(c["quote"], text)
                if score >= THRESHOLD:
                    status = "ok"
                else:
                    cov = word_coverage(c["quote"], text)
                    if cov >= 0.9:
                        status, score = "orden-alterado", cov
                    else:
                        status = "no-encontrada"
                results.append({**c, "owner": owner, "status": status, "score": round(score, 3)})

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(results)

    print(f"Citas con extracto literal: {total}")
    for k in ("ok", "orden-alterado", "no-encontrada", "sin-cache", "pagina-vacia", "sin-fichero"):
        if counts.get(k):
            pct = 100 * counts[k] / total
            print(f"  {k:<15} {counts[k]:>4}  ({pct:.0f}%)")

    problemas = [r for r in results if r["status"] not in ("ok", "orden-alterado")]
    if problemas and (args.failures or len(problemas) <= 40):
        print("\nPendientes de comprobar a ojo:")
        for r in sorted(problemas, key=lambda x: (x["status"], x["owner"])):
            sc = f" ~{r['score']:.2f}" if r["score"] is not None else ""
            print(f"  [{r['status']}{sc}] {r['owner']}")
            print(f"      {r['source']} pág. {r['pdfPages']} · {(r['locator'] or '')[:60]}")
            print(f"      «{r['quote'][:90]}…»")

    print(
        "\nEste informe cubre UN punto del checklist de revisión: que la cita esté "
        "donde dice estar.\nLos otros cuatro —fidelidad, ausencia de conclusiones no "
        "sustentadas, type y basis—\nsiguen exigiendo criterio humano (CONTENT_MODEL §7)."
    )
    return 1 if counts.get("no-encontrada") else 0


if __name__ == "__main__":
    sys.exit(main())
