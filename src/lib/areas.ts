/**
 * Las dos grandes áreas temáticas de la interfaz.
 *
 * Son agrupación de navegación, no jerarquía del grafo: no existe ruta propia
 * ni pertenencia transitiva. Una afirmación puede aparecer en varios contextos
 * sin duplicarse. Ver docs/WEB_DESIGN.md §2.2.
 */

export type AreaId = 'comunidad-y-recepcion' | 'desanexion';

export interface Area {
  id: AreaId;
  label: string;
  lead: string;
  order: number;
}

export const AREAS: Record<AreaId, Area> = {
  'comunidad-y-recepcion': {
    id: 'comunidad-y-recepcion',
    label: 'Comunidad y recepción de LASR',
    lead:
      'Cómo se gestiona y conserva la urbanización, y cómo pasó de manos privadas a ' +
      'obligación municipal: la recepción, la entidad de conservación, el agua y las ' +
      'juntas de la Comunidad de Propietarios.',
    order: 1,
  },
  desanexion: {
    id: 'desanexion',
    label: 'Desanexión',
    lead:
      'La posibilidad de que Los Ángeles de San Rafael se separe administrativamente ' +
      'del término municipal de El Espinar. Es la cuestión de la que menos ' +
      'documentación tenemos.',
    order: 2,
  },
};

export const AREA_ORDER: AreaId[] = (Object.values(AREAS) as Area[])
  .sort((a, b) => a.order - b.order)
  .map((a) => a.id);
