#!/usr/bin/env python3
"""Pruebas del escáner y de la puerta de publicación.

Sin pytest, a propósito: `documentacion/README.md` declara que este proyecto no
tiene tests porque su garantía es que el build se niega a terminar. Esto no lo
contradice, lo matiza — un detector sí necesita que alguien compruebe que
distingue lo que dice distinguir. El molde es el de
`scripts/prensa/filter_regression_check.js`: assert casera, `[OK]`/`[FAIL]`, y
sale con 1 al primer fallo.

    python3 scripts/legal/test_legal_gate.py

Todos los datos son inventados. Los fixtures llevan un marcador que hace que el
escáner los salte cuando barre el repositorio de verdad.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from detectors import NEEDS_HUMAN_REVIEW, build_rules, run_rules  # noqa: E402
from extract import extract, image_metadata  # noqa: E402
import legal_scan  # noqa: E402

FIXTURES = HERE / "fixtures"
REPO = HERE.parents[1]

failures = 0


def ok(condition: bool, label: str) -> None:
    global failures
    if condition:
        print(f"[OK] {label}")
    else:
        print(f"[FAIL] {label}")
        failures += 1


def scan_fixture(name: str, rules=None) -> list:
    path = FIXTURES / name
    text, reason = extract(path)
    if text is None:
        return []
    return run_rules(text, name, rules or RULES)


def rules_of(findings) -> set[str]:
    return {f.rule for f in findings}


# La lista blanca de nombres del proyecto real: los fixtures usan nombres que no
# figuran en ella, que es exactamente el caso que la regla tiene que ver.
RULES = build_rules(allowed_emails=["info@lasr-info.es"], actor_names=legal_scan.actor_names())


print("== Detectores ==")

f01 = scan_fixture("01-dni-en-nota.md")
ok("LEGAL-PRIVACY-001" in rules_of(f01), "01 · DNI con letra válida se detecta")
dni = [f for f in f01 if f.rule == "LEGAL-PRIVACY-001"]
ok(len(dni) == 1, f"01 · el DNI con letra incorrecta NO se reporta (hallazgos: {len(dni)})")
ok(all(f.masked.endswith("R") and "00000001" not in f.masked for f in dni),
   "01 · el DNI sale enmascarado, solo con su letra de control")

f02 = scan_fixture("02-iban-en-presupuesto.md")
iban = [f for f in f02 if f.rule == "LEGAL-PRIVACY-002"]
ok(len(iban) == 1, f"02 · solo el IBAN con módulo 97 correcto se reporta ({len(iban)})")

f03 = scan_fixture("03-email-particular.html")
mails = [f for f in f03 if f.rule == "LEGAL-PRIVACY-004"]
ok(len(mails) == 1, f"03 · el correo del proyecto no se reporta, el del particular sí ({len(mails)})")
ok(all("vecino" not in f.masked for f in mails), "03 · del correo solo sobrevive el dominio")

f04 = scan_fixture("04-sentencia-con-particular.md")
ok({"LEGAL-PRIVACY-001", "LEGAL-NAME-001"} <= rules_of(f04),
   "04 · sentencia con particular: documento y nombre")
ok(all(f.status == NEEDS_HUMAN_REVIEW for f in f04 if f.rule == "LEGAL-NAME-001"),
   "04 · el nombre nunca se resuelve solo: revisión humana")

f05 = scan_fixture("05-acusacion-sin-atribuir.md")
ok("LEGAL-ATTRIB-001" not in rules_of(f05),
   "05 · un fraude sin sujeto identificable NO es una imputación")

f06 = scan_fixture("06-acusacion-atribuida.md")
ok("LEGAL-ATTRIB-001" in rules_of(f06),
   "06 · nombre y término penal en la misma frase sí lo es")
ok(all(f.status == NEEDS_HUMAN_REVIEW for f in f06 if f.rule == "LEGAL-ATTRIB-001"),
   "06 · la imputación exige revisión humana, nunca es un error automático")

f07 = scan_fixture("07-menor.md")
menores = [f for f in f07 if f.rule == "LEGAL-MINOR-001"]
ok(bool(menores), "07 · la referencia a un menor se detecta")
ok(all(f.status == NEEDS_HUMAN_REVIEW for f in menores),
   "07 · un menor SIEMPRE escala a revisión humana")

text08, reason08 = extract(FIXTURES / "08-escaneo-sin-texto.pdf")
ok(text08 is None, "08 · un PDF sin capa de texto no es inspeccionable")
ok("escaneo" in reason08, "08 · y el motivo lo dice con esas palabras")

f09 = scan_fixture("09-referencia-a-private-sources.md")
ok({"LEGAL-LEAK-001", "LEGAL-LEAK-002"} <= rules_of(f09),
   "09 · ruta personal y referencia a los originales")

f10 = (FIXTURES / "10-documento-anonimizado.md").read_text(encoding="utf-8")
ok("legalStatus: cleared-redacted" in f10 and "redactions:" in f10,
   "10 · el documento anonimizado declara qué se suprimió")
ok("00000" not in f10, "10 · y no repite el dato que retiró")

f12 = scan_fixture("12-prensa-integra.json")
press12 = legal_scan.press_findings(
    FIXTURES / "12-prensa-integra.json", "12", (FIXTURES / "12-prensa-integra.json").read_text(encoding="utf-8"))
ok(bool(press12), "12 · reproducir el cuerpo de una noticia es un hallazgo")

press13 = legal_scan.press_findings(
    FIXTURES / "13-enlace-a-articulo.json", "13", (FIXTURES / "13-enlace-a-articulo.json").read_text(encoding="utf-8"))
ok(not press13, "13 · titular, medio, fecha y enlace están limpios")

f14 = scan_fixture("14-recurso-de-tercero.html")
hosts = {f.masked for f in f14 if f.rule == "LEGAL-THIRDPARTY-001"}
ok(hosts == {"cdn.ejemplo.invalid", "analitica.ejemplo.invalid", "tiles.ejemplo.invalid"},
   f"14 · se ven los tres subrecursos externos, incluida la plantilla de teselas ({sorted(hosts)})")
ok("www.boe.es" not in hosts,
   "14 · un enlace no es un subrecurso: no revela nada hasta que alguien lo pulsa")
ok(not [f for f in f14 if f.rule == "LEGAL-PRIVACY-004"],
   "14 · «leaflet@1.9.4» y compañía ya no pasan por direcciones de correo")

f15 = scan_fixture("15-token.txt")
secrets = [f for f in f15 if f.rule == "LEGAL-SECRET-001"]
ok(len(secrets) >= 3, f"15 · tokens y claves se detectan ({len(secrets)})")
ok(all("aaaaaaaa" not in f.masked for f in secrets), "15 · el token sale enmascarado")


print("\n== Invariante A · ningún valor crudo sale del programa ==")

SECRET_VALUES = [
    "00000001R", "ES5500000000000000000001", "vecino@correo.example",
    "00000042L", "ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "AKIAAAAAAAAAAAAAAAAA",
    "/mnt/c/Users/ejemplo/OneDrive/LASR-DOC",
]
todas = []
for name in sorted(p.name for p in FIXTURES.iterdir() if p.is_file()):
    todas += scan_fixture(name)
payload = json.dumps([f.as_dict() for f in todas], ensure_ascii=False)
leaked = [v for v in SECRET_VALUES if v in payload]
ok(not leaked, f"ningún valor detectado aparece en la salida (fugas: {leaked})")


print("\n== Invariante B · determinismo de la huella ==")
a = scan_fixture("01-dni-en-nota.md")
b = scan_fixture("01-dni-en-nota.md")
ok([f.fingerprint for f in a] == [f.fingerprint for f in b], "dos ejecuciones dan las mismas huellas")
ok(len({f.fingerprint for f in todas}) > 1, "valores distintos dan huellas distintas")


print("\n== Invariante C · no inspeccionable nunca es limpio ==")
with tempfile.TemporaryDirectory() as tmp:
    opaque = Path(tmp) / "adjunto.bin"
    opaque.write_bytes(b"\x00\x01\x02binario opaco\x00" * 20)
    text, reason = extract(opaque)
    ok(text is None, "un binario desconocido no es inspeccionable")
    findings = legal_scan.scan([opaque], RULES, None, [])
    ok(len(findings) == 1 and findings[0].rule == "LEGAL-OPAQUE-001",
       "produce exactamente un hallazgo, no cero")
    ok(findings[0].status == NEEDS_HUMAN_REVIEW, "y ese hallazgo es revisión humana")

    # Invariante C bis: EXIF con GPS, generado aquí para no versionar un binario
    # opaco. JPEG mínimo con un APP1 que lleva latitud y longitud.
    jpeg = Path(tmp) / "foto.jpg"
    jpeg.write_bytes(base64.b64decode(
        "/9j/4QBiRXhpZgAATU0AKgAAAAgAAQiFAAMAAAABAAAAAAAAAAAAAAABAAAAAQAAAAEAAAABAAAA"
        "AQAAAAEAAAABAAAAAQAAAAH/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
        "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAf/AABEIAAEAAQMBIgACEQEDEQH/xAAfAAABBQEB"
        "AQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYT"
        "UWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZX"
        "WFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPE"
        "xcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/2gAMAwEAAhEDEQA/AP7+KKKKAP/Z"
    ))
    meta = image_metadata(jpeg)
    ok(isinstance(meta, dict), "14 · el lector de EXIF no revienta con una imagen mínima")


print("\n== Invariante D · gate incremental ==")
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

    def git(*args):
        return subprocess.run(["git", *args], cwd=root, env=env, capture_output=True, text=True)

    git("init", "-q", "-b", "dev")
    content = root / "documentacion" / "src" / "content" / "notes"
    content.mkdir(parents=True)
    (root / "audit").mkdir()
    (root / "audit" / "portal-manifest.json").write_text(
        json.dumps({"version": 1, "allowedEmails": [], "assets": {}, "content": {"sections": {}}}),
        encoding="utf-8")
    (root / "docs").mkdir()
    git("add", "-A"); git("commit", "-qm", "base")
    git("checkout", "-qb", "rama")

    nota = content / "note-prueba.md"
    nota.write_text("---\nid: NOTE-PRUEBA\ntitle: Prueba\n---\n\nCuerpo.\n", encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "sin estado")

    gate = HERE / "gate.py"
    run = subprocess.run([sys.executable, str(gate), "--diff", "--base", "dev"],
                         cwd=root, capture_output=True, text=True,
                         env={**env, "PYTHONPATH": str(HERE)})
    ok(run.returncode == 1, f"una nota tocada sin legalStatus tumba el gate (código {run.returncode})")

    nota.write_text(
        "---\nid: NOTE-PRUEBA\ntitle: Prueba\nlegalStatus: cleared\n"
        "legalReview:\n  reviewedAt: 2026-08-21\n  reason: 'sin datos de particulares'\n---\n\nCuerpo.\n",
        encoding="utf-8")
    git("add", "-A"); git("commit", "-qm", "con estado")
    run = subprocess.run([sys.executable, str(gate), "--diff", "--base", "dev"],
                         cwd=root, capture_output=True, text=True,
                         env={**env, "PYTHONPATH": str(HERE)})
    ok(run.returncode == 0, f"declarada «cleared», el gate pasa (código {run.returncode})")

    run = subprocess.run([sys.executable, str(gate), "--diff", "--base", "no-existe"],
                         cwd=root, capture_output=True, text=True,
                         env={**env, "PYTHONPATH": str(HERE)})
    ok(run.returncode == 2, "una base irresoluble sale con 2, nunca con 0")


print("\n== Invariante E · el escáner se salta sus propios fixtures ==")
ok(all(legal_scan.is_fixture(p) for p in FIXTURES.iterdir() if p.is_file()),
   "todos los fixtures llevan el marcador")
ok(not legal_scan.scan(sorted(p for p in FIXTURES.iterdir() if p.is_file()), RULES, None, []),
   "escanearlos uno a uno no produce ni un hallazgo")


print("\n== Invariante G · un symlink materializado no es contenido ==")
with tempfile.TemporaryDirectory() as tmp:
    import manifest as manifest_mod
    falso = Path(tmp) / "docs"
    falso.mkdir()
    (falso / "index.html").write_text("<html></html>", encoding="utf-8")
    # Lo que git escribe cuando core.symlinks=false: el destino, como texto.
    (falso / "documentacion").write_text("../documentacion/dist", encoding="utf-8")
    listado = manifest_mod.portal_files(falso)
    ok("docs/index.html" in listado, "el contenido de verdad sí se inventaría")
    ok("docs/documentacion" not in listado,
       f"el symlink materializado no entra en el inventario ({listado})")


print("\n== Invariante F · el baseline acota por fichero ==")
uno = scan_fixture("09-referencia-a-private-sources.md")
fuga = next(f for f in uno if f.rule == "LEGAL-LEAK-002")
otro_fichero = [{"fingerprint": fuga.fingerprint, "rule": fuga.rule, "path": "otro.md"}]
mismo_fichero = [{"fingerprint": fuga.fingerprint, "rule": fuga.rule, "path": fuga.path}]
ok(legal_scan.is_accepted(fuga, mismo_fichero), "aceptado en su fichero, se calla")
ok(not legal_scan.is_accepted(fuga, otro_fichero), "el mismo valor en otro fichero sigue saltando")
ok(not legal_scan.is_accepted(fuga, [{"reason": "sin acotador"}]),
   "una entrada sin huella ni ruta no acepta nada")


print()
if failures:
    print(f"[FAIL] {failures} comprobaciones fallidas")
    sys.exit(1)
print("[OK] Todas las comprobaciones pasan")
