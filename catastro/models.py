from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Parcela:
    """Representa una parcela catastral de la urbanización ASR."""

    # Identificación
    referencia: str          # nationalCadastralReference (pc1+pc2), ej: "6745927UL9164N"
    pc1: str                 # Primeros 7 caracteres de la referencia
    pc2: str                 # Hoja catastral, ej: "UL9164N"

    # Geometría (punto de referencia del WFS)
    lat: float               # Latitud EPSG:4326
    lon: float               # Longitud EPSG:4326

    # Superficie (del WFS, areaValue)
    area_m2: float           # Superficie de la parcela en m²

    # Datos de DNPRC (pueden estar vacíos si la llamada falla)
    uso: Optional[str] = None          # ej: "Residencial", "Agrario", "Industrial"...
    municipio: Optional[str] = None    # nm, ej: "EL ESPINAR"
    direccion: Optional[str] = None    # ldt completa, ej: "AV LOS ANGELES 985 40424 EL ESPINAR (SEGOVIA)"
    nombre_via: Optional[str] = None   # nv, ej: "LOS ANGELES"
    tipo_via: Optional[str] = None     # tv, ej: "AV", "CL"
    numero: Optional[str] = None       # pnp, ej: "985"
    error_dnprc: Optional[str] = None  # Mensaje de error si la consulta DNPRC falló

    @property
    def es_residencial(self) -> bool:
        return self.uso is not None and "residencial" in self.uso.lower()

    @property
    def es_asr(self) -> bool:
        """True si la parcela pertenece a ASR: municipio El Espinar + uso Residencial."""
        return self.es_residencial and self.municipio is not None and "espinar" in self.municipio.lower()

    @property
    def referencia_completa(self) -> str:
        """Devuelve pc1+pc2 como referencia de 14 caracteres."""
        return f"{self.pc1}{self.pc2}"
