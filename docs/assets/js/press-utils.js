(function () {
  'use strict';

  const CATEGORY_LABELS = {
    juntas_y_vecinos: 'Juntas y vecinos',
    urbanismo: 'Urbanismo',
    recepcion: 'Recepción',
    infraestructuras: 'Infraestructuras',
    servicios: 'Servicios',
    contexto_municipal: 'Contexto municipal',
    judicial: 'Judicial'
  };

  function parseDate(value) {
    if (!value || typeof value !== 'string') return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return parsed;
  }

  function normalizeSourceName(source) {
    if (typeof source !== 'string') return '';

    return source
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[\s\-_]+/g, ' ')
      .replace(/[^a-zA-Z0-9 ]/g, '')
      .trim()
      .toLowerCase();
  }

  function formatDate(value) {
    const parsed = parseDate(value);
    if (!parsed) return 'Fecha no disponible';
    return parsed.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }

  function sortNews(items) {
    return [...items].sort((a, b) => {
      const dateA = parseDate(a.date);
      const dateB = parseDate(b.date);

      if (dateA && dateB) {
        return dateB.getTime() - dateA.getTime();
      }
      if (dateA && !dateB) return -1;
      if (!dateA && dateB) return 1;

      // Sin fechas válidas no hay criterio: se conserva el orden de entrada.
      return 0;
    });
  }

  // La invariante ya no la lleva cada noticia en un campo: la lleva el fichero.
  // `fetch_press.py` no escribe lo que no es publicable, así que lo que llega
  // aquí ES la selección. Filtrar por un `isRelevant` que ya no existe dejaría
  // el archivo vacío.
  function getRelevantNews(items) {
    return sortNews(Array.isArray(items) ? items : []);
  }

  // El archivo publica solo las noticias del conflicto. Las candidatas
  // descartadas no se almacenan (ver fetch_press.py), así que aquí no hay
  // nada que reincorporar: el archivo es exactamente la selección relevante.
  function getArchiveNews(items) {
    return getRelevantNews(items);
  }

  function getLandingFeaturedNews(items, limit) {
    const max = Number(limit) || 3;
    const candidates = getArchiveNews(items).filter((item) => parseDate(item && item.date));
    const latestBySource = new Map();

    candidates.forEach((item) => {
      const normalizedSource = normalizeSourceName(item && item.source);
      if (!normalizedSource) return;

      const current = latestBySource.get(normalizedSource);
      if (!current) {
        latestBySource.set(normalizedSource, item);
        return;
      }

      const currentDate = parseDate(current.date);
      const itemDate = parseDate(item.date);
      if (!currentDate || !itemDate) return;
      if (itemDate.getTime() > currentDate.getTime()) {
        latestBySource.set(normalizedSource, item);
      }
    });

    return sortNews(Array.from(latestBySource.values())).slice(0, max);
  }

  function getCategoryLabel(value) {
    if (!value) return 'Sin categoría';
    return CATEGORY_LABELS[value] || value;
  }

  function getFilterValues(items, key) {
    const values = new Set();
    (Array.isArray(items) ? items : []).forEach((item) => {
      const raw = item && item[key];
      if (typeof raw === 'string' && raw.trim()) {
        values.add(raw.trim());
      }
    });
    return Array.from(values).sort((a, b) => a.localeCompare(b, 'es'));
  }

  function getFilterYears(items) {
    const years = new Set();
    (Array.isArray(items) ? items : []).forEach((item) => {
      const parsed = parseDate(item && item.date);
      if (parsed) years.add(String(parsed.getFullYear()));
    });
    return Array.from(years).sort((a, b) => Number(b) - Number(a));
  }

  function applyFilters(items, filters) {
    return applyFiltersTrace(items, filters).finalItems;
  }

  function normalizeFilterValues(filters) {
    const normalizeToken = (value) => (typeof value === 'string' ? value.trim().toLowerCase() : '');
    const isNeutralSelect = (value, neutralWords) => {
      const normalized = normalizeToken(value);
      if (!normalized) return true;
      return neutralWords.includes(normalized);
    };

    const sourceTypeNeutralWords = ['all', 'todas', 'todas las fuentes', 'todos', 'todas las fuentes informativas'];
    const sourceNeutralWords = ['all', 'todos', 'todos los medios', 'todas'];
    const categoryNeutralWords = ['all', 'todas', 'todas las categorías', 'todas las categorias', 'todos'];
    const yearNeutralWords = ['all', 'todos', 'todos los años', 'todos los anos'];

    return {
      sourceType: isNeutralSelect(filters.sourceType, sourceTypeNeutralWords)
        ? ''
        : (filters.sourceType || '').trim(),
      source: isNeutralSelect(filters.source, sourceNeutralWords)
        ? ''
        : (filters.source || '').trim(),
      category: isNeutralSelect(filters.category, categoryNeutralWords)
        ? ''
        : (filters.category || '').trim(),
      year: isNeutralSelect(filters.year, yearNeutralWords)
        ? ''
        : (filters.year || '').trim(),
      query: (filters.query || '').trim().toLowerCase()
    };
  }

  function applyFiltersTrace(items, filters) {
    const normalizedFilters = normalizeFilterValues(filters || {});
    const initialItems = Array.isArray(items) ? items : [];

    const afterSourceType = initialItems.filter((item) => {
      if (!normalizedFilters.sourceType) return true;
      return item.sourceType === normalizedFilters.sourceType;
    });

    const afterSource = afterSourceType.filter((item) => {
      if (!normalizedFilters.source) return true;
      return item.source === normalizedFilters.source;
    });

    const afterCategory = afterSource.filter((item) => {
      if (!normalizedFilters.category) return true;
      return item.category === normalizedFilters.category;
    });

    const afterYear = afterCategory.filter((item) => {
      if (!normalizedFilters.year) return true;
      const parsed = parseDate(item.date);
      return !!parsed && String(parsed.getFullYear()) === normalizedFilters.year;
    });

    const afterQuery = afterYear.filter((item) => {
      if (!normalizedFilters.query) return true;
      const text = `${item.title || ''} ${item.source || ''}`.toLowerCase();
      return text.includes(normalizedFilters.query);
    });

    // En runtime UI no hay deduplicación adicional: los datos llegan ya deduplicados.
    const afterDedupe = afterQuery;
    const finalItems = sortNews(afterDedupe);

    return {
      normalizedFilters,
      counts: {
        initial: initialItems.length,
        afterSourceType: afterSourceType.length,
        afterSource: afterSource.length,
        afterCategory: afterCategory.length,
        afterYear: afterYear.length,
        afterQuery: afterQuery.length,
        afterDedupe: afterDedupe.length,
        final: finalItems.length
      },
      finalItems
    };
  }

  window.PressUtils = {
    formatDate,
    getRelevantNews,
    getArchiveNews,
    getLandingFeaturedNews,
    getCategoryLabel,
    getFilterValues,
    getFilterYears,
    applyFilters,
    applyFiltersTrace,
    normalizeFilterValues,
    sortNews
  };
})();
