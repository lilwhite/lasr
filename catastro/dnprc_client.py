"""
Cliente para la API Consulta_DNPRC del Catastro.

Dado una referencia catastral (pc1+pc2, 14 chars), devuelve
uso, dirección y nombre de vía de la parcela.
"""

import logging
import time
from typing import Optional
from xml.etree import ElementTree as ET

import requests

from models import Parcela

logger = logging.getLogger(__name__)

DNPRC_URL = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/"
    "OVCCallejero.asmx/Consulta_DNPRC"
)

# Namespace del XML de respuesta del Catastro
NS = {"c": "http://www.catastro.meh.es/"}

# Pausa entre llamadas para no sobrecargar la API (segundos)
SLEEP_ENTRE_LLAMADAS = 0.25

# Reintentos en caso de error de red
MAX_REINTENTOS = 3
SLEEP_REINTENTO = 2.0


def enriquecer_parcela(parcela: Parcela) -> None:
    """
    Consulta DNPRC para la referencia de la parcela y rellena in-place
    los campos: uso, direccion, nombre_via, tipo_via, numero.
    En caso de error rellena error_dnprc con el mensaje.
    """
    ref = parcela.referencia  # 14 chars: pc1 (7) + pc2 (7)
    params = {
        "Provincia": "",
        "Municipio": "",
        "RC": ref,
    }

    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            resp = requests.get(DNPRC_URL, params=params, timeout=30)
            resp.raise_for_status()
            _parsear_dnprc(resp.text, parcela)
            return
        except requests.RequestException as e:
            logger.warning(f"[{ref}] Intento {intento}/{MAX_REINTENTOS} fallido: {e}")
            if intento < MAX_REINTENTOS:
                time.sleep(SLEEP_REINTENTO)
            else:
                parcela.error_dnprc = str(e)
        except ET.ParseError as e:
            logger.warning(f"[{ref}] Error parseando XML: {e}")
            parcela.error_dnprc = f"ParseError: {e}"
            return


def _parsear_dnprc(xml_text: str, parcela: Parcela) -> None:
    """Parsea el XML de DNPRC y rellena los campos de la parcela."""
    root = ET.fromstring(xml_text.encode("utf-8"))

    # Comprobar si hay error en la respuesta
    err = root.find(".//c:lerr/c:err/c:des", NS)
    if err is not None and err.text:
        parcela.error_dnprc = err.text.strip()
        return

    # Uso del suelo
    luso = root.find(".//c:debi/c:luso", NS)
    if luso is not None and luso.text:
        parcela.uso = luso.text.strip()

    # Municipio
    nm = root.find(".//c:dt/c:nm", NS)
    if nm is not None and nm.text:
        parcela.municipio = nm.text.strip()

    # Dirección completa
    ldt = root.find(".//c:bi/c:ldt", NS)
    if ldt is not None and ldt.text:
        parcela.direccion = ldt.text.strip()

    # Tipo de vía
    tv = root.find(".//c:locs/c:lous/c:lourb/c:dir/c:tv", NS)
    if tv is not None and tv.text:
        parcela.tipo_via = tv.text.strip()

    # Nombre de vía
    nv = root.find(".//c:locs/c:lous/c:lourb/c:dir/c:nv", NS)
    if nv is not None and nv.text:
        parcela.nombre_via = nv.text.strip()

    # Número de portal
    pnp = root.find(".//c:locs/c:lous/c:lourb/c:dir/c:pnp", NS)
    if pnp is not None and pnp.text:
        parcela.numero = pnp.text.strip()
