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

  function mentionLASR(item) {
    const text = `${item.title || ''} ${item.excerpt || ''}`.toLowerCase();
    return text.includes('los angeles de san rafael') || text.includes('los ángeles de san rafael');
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
          (item) => item && item.isRelevant !== true && mentionLASR(item)
        )
      );
      contextualFallback.forEach((item) => {
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
    const source = (filters.source || '').trim();
    const category = (filters.category || '').trim();
    const year = (filters.year || '').trim();
    const query = (filters.query || '').trim().toLowerCase();

    return sortNews(
      (Array.isArray(items) ? items : []).filter((item) => {
        if (source && item.source !== source) return false;
        if (category && item.category !== category) return false;
        if (year) {
          const parsed = parseDate(item.date);
          if (!parsed || String(parsed.getFullYear()) !== year) return false;
        }
        if (query) {
          const text = `${item.title || ''} ${item.excerpt || ''}`.toLowerCase();
          if (!text.includes(query)) return false;
        }
        return true;
      })
    );
  }

  window.PressUtils = {
    formatDate,
    getRelevantNews,
    getLandingFeaturedNews,
    getCategoryLabel,
    getFilterValues,
    getFilterYears,
    applyFilters,
    sortNews
  };
})();
