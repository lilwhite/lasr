"""
Expander de parcelas colectivas (bloques de pisos).

Algunas parcelas del WFS son "parcelas colectivas": un único registro
catastral agrupa múltiples bienes inmuebles (pisos, locales, garajes).
El DNPRC con la referencia de 14 chars devuelve una lista de subunidades
(car + cc1 + cc2) pero sin uso — hay que consultar cada subunidad por separado
con su referencia completa (20 chars).

Flujo:
  1. Lee el CSV generado por main.py
  2. Detecta parcelas con municipio=EL ESPINAR y uso vacío
  3. Para cada una, consulta DNPRC (14 chars) → lista de subunidades
  4. Consulta cada subunidad (referencia completa) → uso, dirección, superficie
  5. Reemplaza la parcela colectiva por sus subunidades residenciales en el CSV
  6. Actualiza resumen_25pct.txt

Uso:
  python expander.py
"""

import csv
import logging
import time
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DNPRC_URL = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/"
    "OVCCallejero.asmx/Consulta_DNPRC"
)
NS = {"c": "http://www.catastro.meh.es/"}
SLEEP = 0.3
OUTPUT_DIR = Path(__file__).parent / "output"
CSV_PATH = OUTPUT_DIR / "parcelas_asr.csv"
RESUMEN_PATH = OUTPUT_DIR / "resumen_25pct.txt"

CSV_FIELDS = [
    "referencia", "pc1", "pc2", "lat", "lon", "area_m2",
    "municipio", "uso", "tipo_via", "nombre_via", "numero",
    "direccion", "es_residencial", "es_asr", "error_dnprc",
]


# ── Helpers DNPRC ──────────────────────────────────────────────────────────

def _get_xml(ref: str) -> Optional[ET.Element]:
    """Consulta DNPRC y devuelve el root XML, o None si falla."""
    try:
        resp = requests.get(
            DNPRC_URL,
            params={"Provincia": "", "Municipio": "", "RC": ref},
            timeout=30,
        )
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as e:
        logger.warning(f"  [{ref}] Error: {e}")
        return None


def obtener_subunidades(ref14: str) -> list[dict]:
    """
    Consulta DNPRC con referencia de 14 chars.
    Devuelve lista de dicts con keys: ref_completa, car, cc1, cc2.
    """
    root = _get_xml(ref14)
    if root is None:
        return []

    subunidades = []
    for rcdnp in root.findall(".//c:rcdnp", NS):
        pc1 = rcdnp.findtext("c:rc/c:pc1", default="", namespaces=NS).strip()
        pc2 = rcdnp.findtext("c:rc/c:pc2", default="", namespaces=NS).strip()
        car = rcdnp.findtext("c:rc/c:car", default="", namespaces=NS).strip()
        cc1 = rcdnp.findtext("c:rc/c:cc1", default="", namespaces=NS).strip()
        cc2 = rcdnp.findtext("c:rc/c:cc2", default="", namespaces=NS).strip()
        if pc1 and pc2 and car:
            subunidades.append({
                "ref_completa": f"{pc1}{pc2}{car}{cc1}{cc2}",
                "car": car,
                "cc1": cc1,
                "cc2": cc2,
            })
    return subunidades


def consultar_subunidad(ref_completa: str, lat: float, lon: float) -> Optional[dict]:
    """
    Consulta DNPRC con referencia completa (20 chars).
    Devuelve dict con datos de la subunidad, o None si falla.
    """
    root = _get_xml(ref_completa)
    if root is None:
        return None

    # Comprobar error
    err = root.findtext(".//c:lerr/c:err/c:des", default="", namespaces=NS).strip()
    if err:
        return None

    uso    = root.findtext(".//c:debi/c:luso",             default="", namespaces=NS).strip()
    nm     = root.findtext(".//c:dt/c:nm",                  default="", namespaces=NS).strip()
    ldt    = root.findtext(".//c:ldt",                      default="", namespaces=NS).strip()
    tv     = root.findtext(".//c:locs//c:dir/c:tv",         default="", namespaces=NS).strip()
    nv     = root.findtext(".//c:locs//c:dir/c:nv",         default="", namespaces=NS).strip()
    pnp    = root.findtext(".//c:locs//c:dir/c:pnp",        default="", namespaces=NS).strip()
    area_s = root.findtext(".//c:debi/c:sfc",               default="0", namespaces=NS).strip()

    try:
        area = float(area_s.replace(",", "."))
    except ValueError:
        area = 0.0

    pc1 = ref_completa[:7]
    pc2 = ref_completa[7:14]

    return {
        "referencia": ref_completa,
        "pc1": pc1,
        "pc2": pc2,
        "lat": lat,
        "lon": lon,
        "area_m2": area,
        "municipio": nm,
        "uso": uso,
        "tipo_via": tv,
        "nombre_via": nv,
        "numero": pnp,
        "direccion": ldt,
        "es_residencial": "residencial" in uso.lower() if uso else False,
        "es_asr": ("residencial" in uso.lower() and "espinar" in nm.lower()) if uso and nm else False,
        "error_dnprc": "",
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    logger.info(f"Leyendo {CSV_PATH}...")
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    logger.info(f"Total filas: {len(filas)}")

    # Detectar parcelas colectivas: municipio=EL ESPINAR, uso vacío, sin error
    candidatas = [
        r for r in filas
        if r["municipio"] == "EL ESPINAR"
        and not r["uso"]
        and not r["error_dnprc"]
    ]
    logger.info(f"Parcelas candidatas a expandir: {len(candidatas)}")

    nuevas_filas = []   # filas que sustituirán a las colectivas
    refs_a_eliminar = set()
    total_subunidades = 0
    total_residenciales = 0

    for i, fila in enumerate(candidatas):
        ref14 = fila["referencia"]
        lat = float(fila["lat"])
        lon = float(fila["lon"])
        logger.info(f"[{i+1}/{len(candidatas)}] {ref14} — {fila['nombre_via']} {fila['numero']}")

        # Paso 1: obtener lista de subunidades
        time.sleep(SLEEP)
        subs = obtener_subunidades(ref14)

        if not subs:
            logger.info(f"  Sin subunidades — se conserva la fila original")
            continue

        logger.info(f"  {len(subs)} subunidades encontradas")
        refs_a_eliminar.add(ref14)

        # Paso 2: consultar cada subunidad
        for j, sub in enumerate(subs):
            time.sleep(SLEEP)
            datos = consultar_subunidad(sub["ref_completa"], lat, lon)
            if datos is None:
                logger.debug(f"  [{j+1}] {sub['ref_completa']} — sin datos")
                continue
            total_subunidades += 1
            if datos["es_asr"]:
                total_residenciales += 1
            nuevas_filas.append(datos)

        logger.info(
            f"  → {sum(1 for d in nuevas_filas[-len(subs):] if d['es_asr'])} residenciales / "
            f"{len(subs)} subunidades"
        )

    logger.info(f"\nResumen expansión:")
    logger.info(f"  Parcelas colectivas expandidas: {len(refs_a_eliminar)}")
    logger.info(f"  Subunidades obtenidas: {total_subunidades}")
    logger.info(f"  Subunidades residenciales ASR: {total_residenciales}")

    if not refs_a_eliminar:
        logger.info("Nada que actualizar.")
        return

    # Reconstruir CSV: conservar filas no expandidas + nuevas subunidades
    filas_finales = [r for r in filas if r["referencia"] not in refs_a_eliminar]

    # Convertir nuevas_filas a formato CSV (mismo esquema)
    for d in nuevas_filas:
        filas_finales.append({
            "referencia": d["referencia"],
            "pc1": d["pc1"],
            "pc2": d["pc2"],
            "lat": d["lat"],
            "lon": d["lon"],
            "area_m2": d["area_m2"],
            "municipio": d["municipio"],
            "uso": d["uso"],
            "tipo_via": d["tipo_via"],
            "nombre_via": d["nombre_via"],
            "numero": d["numero"],
            "direccion": d["direccion"],
            "es_residencial": d["es_residencial"],
            "es_asr": d["es_asr"],
            "error_dnprc": d["error_dnprc"],
        })

    logger.info(f"Filas CSV finales: {len(filas_finales)} (antes: {len(filas)})")

    # Guardar CSV actualizado
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(filas_finales)
    logger.info(f"CSV actualizado: {CSV_PATH}")

    # Recalcular resumen
    asr = [r for r in filas_finales if str(r["es_asr"]) == "True"]
    total_asr = len(asr)
    total_m2_asr = sum(float(r["area_m2"]) for r in asr)
    umbral_num = total_asr * 0.25
    umbral_m2  = total_m2_asr * 0.25
    m2_usuario = 1243.0
    cuota_pct  = (m2_usuario / total_m2_asr * 100) if total_m2_asr > 0 else 0

    sin_datos = [r for r in filas_finales if not r["uso"] and not r["error_dnprc"]]
    con_error = [r for r in filas_finales if r["error_dnprc"]]

    lineas = [
        "=" * 60,
        "RESUMEN CATASTRAL — URBANIZACIÓN LOS ÁNGELES DE SAN RAFAEL",
        "=" * 60,
        "",
        "PARCELAS / UNIDADES EN EL BBOX CONSULTADO",
        f"  Total registros:               {len(filas_finales):>8}",
        "",
        "UNIDADES ASR (municipio=El Espinar + uso=Residencial)",
        f"  Total unidades ASR:            {total_asr:>8}",
        f"  Total m² ASR:                  {total_m2_asr:>12,.0f} m²",
        f"  m² medio por unidad:           {(total_m2_asr/total_asr if total_asr else 0):>12,.1f} m²",
        "",
        "REGISTROS SIN DATOS DNPRC",
        f"  Sin uso / sin respuesta:       {len(sin_datos):>8}",
        f"  Con error en consulta:         {len(con_error):>8}",
        "",
        "UMBRAL ART. 16.2 LPH — 25% (condición alternativa)",
        f"  Por número de propietarios:    {umbral_num:>8.1f} propietarios",
        f"  Por cuotas (m²):               {umbral_m2:>12,.0f} m²",
        "",
        "CUOTA DE LA PARCELA DEL SOLICITANTE",
        f"  Superficie parcela:            {m2_usuario:>8.0f} m²",
        f"  Cuota sobre total ASR:         {cuota_pct:>11.4f} %",
        "",
        "NOTA: Las cuotas de participación de ASR son proporcionales",
        "a la superficie de cada parcela (según nota simple registral).",
        "El umbral del 25% puede alcanzarse POR NÚMERO de propietarios",
        "O POR CUOTAS — basta cumplir UNA de las dos condiciones.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    with open(RESUMEN_PATH, "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)
    logger.info(f"Resumen actualizado: {RESUMEN_PATH}")


if __name__ == "__main__":
    main()
