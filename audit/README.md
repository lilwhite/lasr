# audit/

Estado jurídico del sitio y trazabilidad de las decisiones de publicación.

**Este directorio no se publica.** Vive fuera de `docs/` a propósito: el
despliegue solo copia lo que declara `portal-manifest.json`, y un informe que
enumera dónde está lo sensible sería un mapa para quien lo buscara.

**Nada de lo que se escriba aquí puede contener el valor de un dato personal,
solo su categoría.** Un motivo se escribe «se retiró un número de documento de
identidad», nunca el número. `legal_scan.py` se pasa también sobre `audit/**`:
la herramienta tiene que poder auditar su propio informe.

| Fichero | Qué es |
|---|---|
| `LEGAL_PUBLICATION_AUDIT.md` | El informe: hallazgos, gravedad y acción recomendada |
| `portal-manifest.json` | Estado jurídico de cada pieza de `docs/`, y lista blanca de despliegue |
| `legal-baseline.json` | Hallazgos ya valorados que el escáner no debe volver a levantar |

El repositorio es público, así que GitHub sí sirve estos ficheros aunque
lasr-info.es no lo haga. Un informe que enumera hallazgos es prueba de
conocimiento, y eso corta en dos direcciones: por eso cita identificadores de
regla, rutas y recuentos con sus fechas, y nunca valores ni nombres de las
personas afectadas.
