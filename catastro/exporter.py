"""
Exportador de resultados.

Genera:
  - output/parcelas_asr.csv   : listado completo de parcelas con todos sus datos
  - output/resumen_25pct.txt  : resumen con el umbral del 25% calculado
"""

import csv
import logging
from pathlib import Path
from typing import List

from models import Parcela

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"
CSV_PATH = OUTPUT_DIR / "parcelas_asr.csv"
RESUMEN_PATH = OUTPUT_DIR / "resumen_25pct.txt"

CSV_FIELDS = [
    "referencia",
    "pc1",
    "pc2",
    "lat",
    "lon",
    "area_m2",
    "municipio",
    "uso",
    "tipo_via",
    "nombre_via",
    "numero",
    "direccion",
    "es_residencial",
    "es_asr",
    "error_dnprc",
]


def exportar_csv(parcelas: List[Parcela]) -> None:
    """Exporta todas las parcelas a CSV."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for p in parcelas:
            writer.writerow({
                "referencia": p.referencia,
                "pc1": p.pc1,
                "pc2": p.pc2,
                "lat": p.lat,
                "lon": p.lon,
                "area_m2": p.area_m2,
                "municipio": p.municipio or "",
                "uso": p.uso or "",
                "tipo_via": p.tipo_via or "",
                "nombre_via": p.nombre_via or "",
                "numero": p.numero or "",
                "direccion": p.direccion or "",
                "es_residencial": p.es_residencial,
                "es_asr": p.es_asr,
                "error_dnprc": p.error_dnprc or "",
            })
    logger.info(f"CSV exportado: {CSV_PATH} ({len(parcelas)} filas)")


def exportar_resumen(parcelas: List[Parcela]) -> None:
    """Calcula estadísticas y exporta el resumen del umbral del 25%."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    total_parcelas = len(parcelas)
    total_m2 = sum(p.area_m2 for p in parcelas)

    asr = [p for p in parcelas if p.es_asr]
    total_asr = len(asr)
    total_m2_asr = sum(p.area_m2 for p in asr)

    sin_datos = [p for p in parcelas if p.uso is None and p.error_dnprc is None]
    con_error = [p for p in parcelas if p.error_dnprc]

    # Umbral 25% — art. 16.2 LPH (condición alternativa: número O cuotas)
    umbral_numero = total_asr * 0.25
    umbral_m2 = total_m2_asr * 0.25

    # Cuota de la parcela del usuario (1.243 m² según nota simple)
    m2_usuario = 1243.0
    cuota_pct_usuario = (m2_usuario / total_m2_asr * 100) if total_m2_asr > 0 else 0

    lineas = [
        "=" * 60,
        "RESUMEN CATASTRAL — URBANIZACIÓN LOS ÁNGELES DE SAN RAFAEL",
        "=" * 60,
        "",
        "PARCELAS EN EL BBOX CONSULTADO",
        f"  Total parcelas:                {len(parcelas):>8}",
        "",
        "PARCELAS ASR (municipio=El Espinar + uso=Residencial)",
        f"  Total parcelas ASR:            {total_asr:>8}",
        f"  Total m² ASR:                  {total_m2_asr:>12,.0f} m²",
        f"  m² medio por parcela:          {(total_m2_asr/total_asr if total_asr else 0):>12,.1f} m²",
        "",
        "PARCELAS SIN DATOS DNPRC",
        f"  Sin consultar / sin respuesta: {len(sin_datos):>8}",
        f"  Con error en consulta:         {len(con_error):>8}",
        "",
        "UMBRAL ART. 16.2 LPH — 25% (condición alternativa)",
        f"  Por número de propietarios:    {umbral_numero:>8.1f} propietarios",
        f"  Por cuotas (m²):               {umbral_m2:>12,.0f} m²",
        "",
        "CUOTA DE LA PARCELA DEL SOLICITANTE",
        f"  Superficie parcela:            {m2_usuario:>8.0f} m²",
        f"  Cuota sobre total ASR:         {cuota_pct_usuario:>11.4f} %",
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
    logger.info(f"Resumen exportado: {RESUMEN_PATH}")
