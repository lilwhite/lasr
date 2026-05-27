"""
Script principal — Catastro ASR

Flujo:
  1. WFS INSPIRE → obtiene todas las parcelas del bbox de ASR
  2. DNPRC por cada parcela → uso, municipio, dirección
  3. Filtro: municipio=El Espinar + uso=Residencial (→ es_asr)
  4. Exporta CSV completo y resumen con el umbral del 25% (art. 16.2 LPH)

Uso:
  python main.py [--skip-dnprc]

  --skip-dnprc  Salta las consultas DNPRC (útil para pruebas rápidas).
                El CSV se genera sin datos de uso/municipio/dirección.
"""

import argparse
import logging
import sys
import time
from typing import List

from dnprc_client import SLEEP_ENTRE_LLAMADAS, enriquecer_parcela
from exporter import exportar_csv, exportar_resumen
from models import Parcela
from wfs_client import obtener_parcelas_bbox

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def barra_progreso(actual: int, total: int, ancho: int = 40) -> str:
    """Genera una barra de progreso simple."""
    pct = actual / total if total > 0 else 0
    llenas = int(ancho * pct)
    barra = "█" * llenas + "░" * (ancho - llenas)
    return f"[{barra}] {actual}/{total} ({pct*100:.1f}%)"


def enriquecer_parcelas(parcelas: List[Parcela]) -> None:
    """Llama a DNPRC para cada parcela con barra de progreso."""
    total = len(parcelas)
    logger.info(f"Consultando DNPRC para {total} parcelas (≈{total * SLEEP_ENTRE_LLAMADAS:.0f}s)...")

    for i, parcela in enumerate(parcelas, start=1):
        enriquecer_parcela(parcela)
        time.sleep(SLEEP_ENTRE_LLAMADAS)

        # Mostrar progreso cada 25 parcelas o en la última
        if i % 25 == 0 or i == total:
            print(f"\r  {barra_progreso(i, total)}", end="", flush=True)

    print()  # salto de línea tras la barra


def main() -> int:
    parser = argparse.ArgumentParser(description="Catastro ASR — extracción de parcelas")
    parser.add_argument(
        "--skip-dnprc",
        action="store_true",
        help="Omite las consultas DNPRC (prueba rápida, sin uso/dirección)",
    )
    args = parser.parse_args()

    # 1. Obtener parcelas en el bbox de ASR (WFS INSPIRE, sin filtro geográfico)
    try:
        parcelas = obtener_parcelas_bbox()
    except Exception as e:
        logger.error(f"Error obteniendo parcelas WFS: {e}")
        return 1

    if not parcelas:
        logger.error("No se encontraron parcelas en el bbox.")
        return 1

    logger.info(f"Parcelas descargadas del bbox: {len(parcelas)}")

    # 2. Enriquecer con DNPRC (uso, municipio, dirección)
    if args.skip_dnprc:
        logger.warning("--skip-dnprc activo: no se consultará DNPRC.")
    else:
        enriquecer_parcelas(parcelas)

        # Resumen rápido de usos y municipios
        usos = {}
        municipios = {}
        for p in parcelas:
            uso = p.uso or ("ERROR" if p.error_dnprc else "SIN_DATOS")
            usos[uso] = usos.get(uso, 0) + 1
            mun = p.municipio or ("ERROR" if p.error_dnprc else "SIN_DATOS")
            municipios[mun] = municipios.get(mun, 0) + 1

        logger.info("Distribución de usos:")
        for uso, count in sorted(usos.items(), key=lambda x: -x[1]):
            logger.info(f"  {uso}: {count}")

        logger.info("Distribución de municipios:")
        for mun, count in sorted(municipios.items(), key=lambda x: -x[1]):
            logger.info(f"  {mun}: {count}")

        asr_count = sum(1 for p in parcelas if p.es_asr)
        logger.info(f"Parcelas ASR (El Espinar + Residencial): {asr_count}")

    # 3. Exportar CSV completo (todas las parcelas del bbox)
    exportar_csv(parcelas)

    # 4. Exportar resumen con umbral del 25% (filtra es_asr internamente)
    exportar_resumen(parcelas)

    return 0


if __name__ == "__main__":
    sys.exit(main())
