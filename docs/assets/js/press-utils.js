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

      return (Number(b.relevanceScore) || 0) - (Number(a.relevanceScore) || 0);
    });
  }

  function getRelevantNews(items) {
    return sortNews(
      (Array.isArray(items) ? items : []).filter((item) => item && item.isRelevant === true)
    );
  }

  function isSupplementalMultiSourceCandidate(item) {
    if (!item || item.isRelevant === true) return false;
    const sourceType = (item.sourceType || '').toLowerCase();
    if (sourceType === 'local') return false;

    const score = Number(item.relevanceScore ?? item.score) || 0;
    if (score < 0) return false;

    const text = `${item.title || ''} ${item.summary || ''} ${item.excerpt || ''}`.toLowerCase();
    const contextTerms = [
      'el espinar',
      'los angeles de san rafael',
      'los ángeles de san rafael'
    ];
    const thematicTerms = [
      'urbanismo',
      'urbanizacion',
      'urbanización',
      'consultorio',
      'sanidad',
      'seguridad',
      'ocupacion',
      'okupacion',
      'infraestructuras',
      'n-603',
      'presa del tejo',
      'mancomunidad',
      'euc',
      'entidad urbanistica de conservacion',
      'entidad urbanística de conservación',
      'agua',
      'saneamiento'
    ];

    const hasContext = contextTerms.some((term) => text.includes(term));
    const hasTheme = thematicTerms.some((term) => text.includes(term));
    return hasContext && hasTheme;
  }

  function getArchiveNews(items) {
    const relevant = getRelevantNews(items);
    const supplementalBySource = new Map();

    const strictContextualSupplement = sortNews(Array.isArray(items) ? items : []).filter((item) =>
      isSupplementalMultiSourceCandidate(item)
    );

    const fallbackBySource = sortNews(Array.isArray(items) ? items : []).filter((item) => {
      if (!item || item.isRelevant === true) return false;
      const sourceType = (item.sourceType || '').toLowerCase();
      if (sourceType === 'local') return false;
      const score = Number(item.relevanceScore ?? item.score) || 0;
      if (score < 0) return false;
      const text = `${item.title || ''} ${item.summary || ''} ${item.excerpt || ''}`.toLowerCase();
      return text.includes('el espinar');
    });

    [...strictContextualSupplement, ...fallbackBySource].forEach((item) => {
      const source = (item.source || '').trim();
      if (!source) return;
      const existing = supplementalBySource.get(source) || [];
      if (existing.length >= 1) return;
      existing.push(item);
      supplementalBySource.set(source, existing);
    });

    const supplemental = [];
    supplementalBySource.forEach((rows) => supplemental.push(...rows));

    const output = [];
    const seen = new Set();
    [...relevant, ...supplemental].forEach((item) => {
      if (!item || !item.id || seen.has(item.id)) return;
      seen.add(item.id);
      output.push(item);
    });

    return sortNews(output);
  }

  function mentionLASR(item) {
    const text = `${item.title || ''} ${item.excerpt || ''}`.toLowerCase();
    return text.includes('los angeles de san rafael') || text.includes('los ángeles de san rafael');
  }

  function isContextualFallbackCandidate(item) {
    if (!item || item.isRelevant === true) return false;

    const allowedCategories = new Set([
      'juntas_y_vecinos',
      'urbanismo',
      'recepcion',
      'infraestructuras',
      'servicios',
      'judicial',
      'contexto_municipal'
    ]);

    const text = `${item.title || ''} ${item.excerpt || ''}`.toLowerCase();
    const contextTerms = [
      'urbanizacion',
      'urbanización',
      'copropietarios',
      'propietarios',
      'vecinos',
      'euc',
      'eucc',
      'recepcion',
      'recepción',
      'sentencia',
      'ayuntamiento',
      'infraestructuras',
      'servicios'
    ];

    const hasContextTerm = contextTerms.some((term) => text.includes(term));
    const hasAllowedCategory = allowedCategories.has(item.category);
    const hasEnoughScore = (Number(item.relevanceScore) || 0) >= 4;

    return hasAllowedCategory && hasContextTerm && hasEnoughScore;
  }

  function isStrongFallbackCandidate(item) {
    if (!item || item.isRelevant === true) return false;
    const score = Number(item.relevanceScore) || 0;
    return isContextualFallbackCandidate(item) && score >= 7;
  }

  function getLandingFeaturedNews(items, limit) {
    const max = Number(limit) || 3;
    const relevant = getRelevantNews(items);
    const featuredRelevant = relevant.filter((item) => item.featured === true);
    const regularRelevant = relevant.filter((item) => item.featured !== true);

    const output = [];
    featuredRelevant.forEach((item) => {
      if (output.length < max) output.push(item);
    });
    regularRelevant.forEach((item) => {
      if (output.length < max) output.push(item);
    });

    if (output.length < max) {
      const contextualFallback = sortNews(
        (Array.isArray(items) ? items : []).filter(
          (item) => mentionLASR(item) && isContextualFallbackCandidate(item)
        )
      );
      contextualFallback.forEach((item) => {
        if (output.length < max && !output.find((existing) => existing.id === item.id)) {
          output.push(item);
        }
      });
    }

    if (output.length < max) {
      const strongFallback = sortNews(
        (Array.isArray(items) ? items : []).filter((item) => isStrongFallbackCandidate(item))
      );
      strongFallback.forEach((item) => {
        if (output.length < max && !output.find((existing) => existing.id === item.id)) {
          output.push(item);
        }
      });
    }

    return output.slice(0, max);
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
      const text = `${item.title || ''} ${item.excerpt || ''}`.toLowerCase();
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
