(function () {
  'use strict';

  const CONFIG = {
    pressDataPath: '../data/prensa/curated_news.json',
    configPath: '../assets/config.json',
    buildMetaPath: '../assets/build-meta.json'
  };

  const elements = {
    sourceTypeFilter: document.getElementById('pressSourceTypeFilter'),
    sourceFilter: document.getElementById('pressSourceFilter'),
    categoryFilter: document.getElementById('pressCategoryFilter'),
    yearFilter: document.getElementById('pressYearFilter'),
    queryFilter: document.getElementById('pressQueryFilter'),
    list: document.getElementById('pressArchiveList'),
    count: document.getElementById('pressResultCount')
  };

  let archiveNews = [];
  let allNews = [];

  const SOURCE_TYPE_LABELS = {
    local: 'Local',
    provincial: 'Provincial',
    institucional: 'Institucional'
  };

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function sanitizeExternalUrl(url) {
    if (typeof url !== 'string') return '';
    const trimmed = url.trim();
    if (!trimmed) return '';
    try {
      const parsed = new URL(trimmed, window.location.origin);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        return parsed.href;
      }
    } catch (error) {
      return '';
    }
    return '';
  }

  function buildOptions(select, values, mapFn) {
    values.forEach((value) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = mapFn ? mapFn(value) : value;
      select.appendChild(option);
    });
  }

  function renderList(items) {
    if (!items.length) {
      elements.list.innerHTML = `
        <div class="press-empty-state">
          <h3>No hay resultados para estos filtros</h3>
          <p>Prueba a ampliar el rango temporal o quitar filtros para ver más noticias.</p>
        </div>
      `;
      elements.count.textContent = '0 resultados';
      return;
    }

    const rows = items.map((item) => {
      const safeUrl = sanitizeExternalUrl(item.url || '');
      if (!safeUrl) return '';
      const title = escapeHtml(item.title || 'Sin titular');
      const source = escapeHtml(item.source || 'Medio no disponible');
      const sourceType = escapeHtml(SOURCE_TYPE_LABELS[item.sourceType] || 'General');
      const category = escapeHtml(window.PressUtils.getCategoryLabel(item.category));
      const excerpt = escapeHtml((item.summary || item.excerpt || '').slice(0, 220));
      const date = escapeHtml(window.PressUtils.formatDate(item.date));

      return `
        <article class="press-row">
          <div class="press-row-main">
            <div class="press-row-meta" aria-label="Metadatos de la noticia">
              <span class="press-meta-date">${date}</span>
              <span class="press-meta-type press-meta-type-${(item.sourceType || 'general').toLowerCase()}">${sourceType}</span>
              <span class="press-meta-chip">${source}</span>
              <span class="press-meta-chip">${category}</span>
            </div>
            <h3 class="press-row-title">${title}</h3>
            ${excerpt ? `<p class="press-row-excerpt">${excerpt}</p>` : ''}
          </div>
          <div class="press-row-action">
            <a href="${escapeHtml(safeUrl)}" class="press-source-link" target="_blank" rel="noopener noreferrer">Ver fuente</a>
          </div>
        </article>
      `;
    });

    elements.list.innerHTML = rows.join('');
    elements.count.textContent = `${items.length} resultado${items.length === 1 ? '' : 's'}`;
  }

  function readFilters() {
    return {
      sourceType: elements.sourceTypeFilter.value,
      source: elements.sourceFilter.value,
      category: elements.categoryFilter.value,
      year: elements.yearFilter.value,
      query: elements.queryFilter.value
    };
  }

  function applyCurrentFilters() {
    const filters = readFilters();
    const baseItems = filters.source ? allNews : archiveNews;
    const filtered = window.PressUtils.applyFilters(baseItems, filters);
    renderList(filtered);
  }

  async function loadPressNews() {
    const response = await fetch(CONFIG.pressDataPath);
    if (!response.ok) throw new Error('No se pudo cargar curated_news.json');
    const payload = await response.json();
    allNews = window.PressUtils.sortNews(Array.isArray(payload) ? payload : []);
    archiveNews = window.PressUtils.getArchiveNews(payload);
  }

  function setupFilters() {
    buildOptions(elements.sourceFilter, window.PressUtils.getFilterValues(allNews, 'source'));
    buildOptions(elements.categoryFilter, window.PressUtils.getFilterValues(archiveNews, 'category'), window.PressUtils.getCategoryLabel);
    buildOptions(elements.yearFilter, window.PressUtils.getFilterYears(archiveNews));

    [elements.sourceTypeFilter, elements.sourceFilter, elements.categoryFilter, elements.yearFilter].forEach((node) => {
      node.addEventListener('change', applyCurrentFilters);
    });
    elements.queryFilter.addEventListener('input', applyCurrentFilters);
  }

  async function updateFooterMeta() {
    const repoLink = document.getElementById('footerRepoLink');
    const licenseLink = document.getElementById('footerLicenseLink');
    const lastUpdatedDate = document.getElementById('lastUpdatedDate');

    try {
      const configResponse = await fetch(CONFIG.configPath);
      if (configResponse.ok) {
        const config = await configResponse.json();
        if (repoLink && config?.project?.repositoryUrl) repoLink.href = config.project.repositoryUrl;
        if (licenseLink && config?.project?.licenseUrl) licenseLink.href = config.project.licenseUrl;
        if (licenseLink && config?.project?.license) licenseLink.textContent = `Licencia ${config.project.license}`;
      }
    } catch (error) {
      console.warn('No se pudo cargar config.json', error);
    }

    try {
      const buildMetaResponse = await fetch(CONFIG.buildMetaPath);
      if (buildMetaResponse.ok) {
        const buildMeta = await buildMetaResponse.json();
        if (lastUpdatedDate && buildMeta?.updatedDate) {
          lastUpdatedDate.textContent = buildMeta.updatedDate;
        }
      }
    } catch (error) {
      console.warn('No se pudo cargar build-meta.json', error);
    }
  }

  async function init() {
    try {
      await loadPressNews();
      setupFilters();
      applyCurrentFilters();
      await updateFooterMeta();
    } catch (error) {
      elements.list.innerHTML = `
        <div class="press-empty-state">
          <h3>No se pudo cargar el archivo de prensa</h3>
          <p>Reintenta más tarde o revisa la generación de datos en curated_news.json.</p>
        </div>
      `;
      elements.count.textContent = 'Error de carga';
      console.error(error);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
