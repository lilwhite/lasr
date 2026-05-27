"""
Cliente para la API WFS INSPIRE del Catastro.

Obtiene todas las parcelas catastrales dentro del bounding box de ASR
en UNA SOLA llamada (el servidor ignora COUNT/STARTINDEX y devuelve todo).

El filtro real de pertenencia a ASR se hace en main.py mediante DNPRC
(municipio = EL ESPINAR + uso = Residencial).
"""

import logging
from typing import List
from xml.etree import ElementTree as ET

import requests

from models import Parcela

logger = logging.getLogger(__name__)

WFS_URL = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"

# Bounding box que cubre toda la zona de ASR / El Espinar
# lat_min,lon_min,lat_max,lon_max,EPSG:4326
BBOX = "40.757,-4.255,40.801,-4.210,EPSG:4326"

WFS_TIMEOUT = 120  # segundos — la respuesta completa puede ser grande

# Namespaces del XML de respuesta
NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "cp": "http://inspire.ec.europa.eu/schemas/cp/4.0",
    "gml": "http://www.opengis.net/gml/3.2",
}


def obtener_parcelas_bbox() -> List[Parcela]:
    """
    Descarga todas las parcelas del bbox en una sola llamada WFS INSPIRE.
    El servidor del Catastro ignora COUNT/STARTINDEX y devuelve el conjunto completo.
    """
    logger.info(f"Consultando WFS INSPIRE bbox={BBOX}...")
    params = {
        "SERVICE": "WFS",
        "REQUEST": "GetFeature",
        "TYPENAMES": "CP:CadastralParcel",
        "BBOX": BBOX,
    }
    resp = requests.get(WFS_URL, params=params, timeout=WFS_TIMEOUT)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)  # content para manejar encoding ISO-8859-1

    total_matched = root.attrib.get("numberMatched", "?")
    total_returned = root.attrib.get("numberReturned", "?")
    logger.info(f"  numberMatched={total_matched}, numberReturned={total_returned}")

    parcelas = []
    vistas = set()

    for member in root.findall("wfs:member", NS):
        parcel = member.find("cp:CadastralParcel", NS)
        if parcel is None:
            continue

        ref_el = parcel.find("cp:nationalCadastralReference", NS)
        if ref_el is None or not ref_el.text:
            continue
        ref = ref_el.text.strip()

        # Deduplicar
        if ref in vistas:
            continue
        vistas.add(ref)

        area_el = parcel.find("cp:areaValue", NS)
        try:
            area = float(area_el.text.strip()) if area_el is not None and area_el.text else 0.0
        except ValueError:
            area = 0.0

        # Punto de referencia
        pos_el = parcel.find(".//cp:referencePoint//gml:pos", NS)
        if pos_el is None or not pos_el.text:
            continue
        try:
            lat_str, lon_str = pos_el.text.strip().split()
            lat, lon = float(lat_str), float(lon_str)
        except ValueError:
            continue

        # pc1 = primeros 7 chars, pc2 = resto (hasta char 14)
        pc1 = ref[:7] if len(ref) >= 7 else ref
        pc2 = ref[7:14] if len(ref) >= 14 else ref[7:] if len(ref) > 7 else ""

        parcelas.append(Parcela(
            referencia=ref,
            pc1=pc1,
            pc2=pc2,
            lat=lat,
            lon=lon,
            area_m2=area,
        ))

    logger.info(f"Parcelas únicas descargadas: {len(parcelas)}")
    return parcelas
