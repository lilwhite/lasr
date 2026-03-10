/**
 * Documentacion - Renderizador Markdown
 * Mantiene los .md como fuente de verdad.
 */

(function () {
  'use strict';

  const documents = [
    { file: 'urbanizacion_los_angeles_san_rafael.md', slug: 'documento-principal', title: 'Documento principal', category: 'principal', order: 0 },
    { file: 'contexto_general.md', slug: 'contexto-general', title: 'Contexto general', category: 'analisis', order: 1 },
    { file: 'timeline_conflicto.md', slug: 'linea-temporal', title: 'Linea temporal', category: 'cronologia', order: 2 },
    { file: 'problemas_detectados.md', slug: 'problemas-detectados', title: 'Problemas detectados', category: 'analisis', order: 3 },
    { file: 'actores.md', slug: 'actores', title: 'Actores', category: 'referencia', order: 4 },
    { file: 'opciones_legales.md', slug: 'opciones-legales', title: 'Opciones legales', category: 'legal', order: 5 },
    { file: 'preguntas_abiertas.md', slug: 'preguntas-abiertas', title: 'Preguntas abiertas', category: 'analisis', order: 6 },
    { file: 'documentacion_relevante.md', slug: 'documentacion-relevante', title: 'Documentacion relevante', category: 'referencia', order: 7 }
  ];

  const routeAliases = {
    'cronologia': 'linea-temporal',
    'recepcion-urbanizacion': 'contexto-general',
    'sentencia-tsjcyl': 'opciones-legales'
  };

  function getRootPrefix() {
    return document.body.dataset.docRoot || '.';
  }

  function getRepoSourceBase() {
    return document.body.dataset.repoBase || 'https://github.com/tu-usuario/tu-repo/blob/main/docs/';
  }

  function getSlugFromPage() {
    const explicit = document.body.dataset.docSlug;
    if (explicit) return explicit;

    const params = new URLSearchParams(window.location.search);
    const querySlug = params.get('slug');
    if (querySlug) return querySlug;

    const parts = window.location.pathname.split('/').filter(Boolean);
    const maybeSlug = parts[parts.length - 1];
    if (maybeSlug && maybeSlug !== 'doc.html') return maybeSlug;

    return 'documento-principal';
  }

  function canonicalSlug(slug) {
    return routeAliases[slug] || slug;
  }

  function parseFrontmatter(content) {
    const fmRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
    const match = content.match(fmRegex);
    if (!match) return { frontmatter: {}, body: content };

    const frontmatter = {};
    match[1].split('\n').forEach((line) => {
      const idx = line.indexOf(':');
      if (idx > 0) {
        const key = line.slice(0, idx).trim();
        let value = line.slice(idx + 1).trim();
        value = value.replace(/^["']|["']$/g, '');
        frontmatter[key] = value;
      }
    });

    return { frontmatter, body: content.slice(match[0].length) };
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  function ensureShell() {
    if (document.getElementById('docBody')) return;

    document.body.innerHTML = `
      <header class="header" id="header">
        <div class="header-container">
          <a href="${getRootPrefix()}/index.html" class="logo"><span class="logo-text">LASR</span></a>
          <nav class="nav" id="nav"><ul class="nav-list"><li><a href="${getRootPrefix()}/index.html#documentacion" class="nav-link">Volver al portal</a></li></ul></nav>
        </div>
      </header>
      <main class="doc-page">
        <nav class="breadcrumb" aria-label="Navegacion">
          <a href="${getRootPrefix()}/index.html">Inicio</a>
          <span class="breadcrumb-separator">›</span>
          <span class="breadcrumb-current" id="breadcrumbTitle">Documentacion</span>
        </nav>
        <div class="doc-container">
          <aside class="doc-sidebar">
            <h3 class="sidebar-title">Documentos</h3>
            <ul class="sidebar-nav" id="sidebarNav"></ul>
          </aside>
          <article class="doc-content">
            <header class="doc-header">
              <h1 id="docTitle">Cargando...</h1>
              <p class="doc-description" id="docDescription"></p>
              <div class="doc-meta">
                <span class="doc-date">Actualizado: <time id="docDate"></time></span>
                <span class="doc-category" id="docCategory"></span>
              </div>
            </header>
            <aside class="doc-toc" id="docToc"></aside>
            <div class="doc-body" id="docBody"></div>
            <section class="doc-related" id="docRelated"></section>
            <footer class="doc-footer">
              <a href="#" class="doc-source" id="docSource" target="_blank" rel="noopener">Ver archivo fuente en GitHub</a>
            </footer>
          </article>
        </div>
      </main>
    `;
  }

  function getElements() {
    return {
      title: document.getElementById('docTitle'),
      description: document.getElementById('docDescription'),
      date: document.getElementById('docDate'),
      category: document.getElementById('docCategory'),
      body: document.getElementById('docBody'),
      source: document.getElementById('docSource'),
      sidebar: document.getElementById('sidebarNav'),
      breadcrumb: document.getElementById('breadcrumbTitle'),
      toc: document.getElementById('docToc'),
      related: document.getElementById('docRelated')
    };
  }

  function linkForSlug(slug) {
    const root = getRootPrefix();
    if (root === '.') return `${slug}/`;
    return `../${slug}/`;
  }

  function renderSidebar(elements, currentSlug) {
    const sorted = [...documents].sort((a, b) => a.order - b.order);
    elements.sidebar.innerHTML = sorted
      .map((doc) => {
        const active = doc.slug === currentSlug ? 'active' : '';
        return `<li><a class="sidebar-link ${active}" href="${linkForSlug(doc.slug)}">${doc.title}</a></li>`;
      })
      .join('');
  }

  function addHeadingAnchors(container) {
    const headings = container.querySelectorAll('h2, h3');
    headings.forEach((h, idx) => {
      if (!h.id) {
        const slug = h.textContent.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
        h.id = `${slug || 'seccion'}-${idx + 1}`;
      }
    });
    return headings;
  }

  function renderToc(elements) {
    const headings = addHeadingAnchors(elements.body);
    if (!headings.length) {
      elements.toc.innerHTML = '';
      return;
    }

    const links = Array.from(headings)
      .map((h) => `<li><a href="#${h.id}">${h.textContent}</a></li>`)
      .join('');

    elements.toc.innerHTML = `<h3 class="sidebar-title">Indice</h3><ul class="sidebar-nav">${links}</ul>`;
  }

  function renderRelated(elements, currentDoc) {
    const related = documents
      .filter((d) => d.slug !== currentDoc.slug)
      .filter((d) => d.category === currentDoc.category)
      .slice(0, 3);

    if (!related.length) {
      elements.related.innerHTML = '';
      return;
    }

    elements.related.innerHTML = `
      <h3 class="sidebar-title">Documentos relacionados</h3>
      <div class="cards">
        ${related
          .map((d) => `<a class="doc-card" href="${linkForSlug(d.slug)}"><h4 class="doc-title">${d.title}</h4><p class="doc-description">${d.category}</p></a>`)
          .join('')}
      </div>
    `;
  }

  async function load() {
    ensureShell();
    const elements = getElements();

    const slug = canonicalSlug(getSlugFromPage());
    const currentDoc = documents.find((d) => d.slug === slug) || documents[0];
    const root = getRootPrefix();

    try {
      const response = await fetch(`${root}/${currentDoc.file}`);
      if (!response.ok) throw new Error('Documento no encontrado');

      const raw = await response.text();
      const parsed = parseFrontmatter(raw);

      const html = window.marked ? window.marked.parse(parsed.body) : parsed.body;
      elements.body.innerHTML = html;

      elements.title.textContent = parsed.frontmatter.title || currentDoc.title;
      elements.breadcrumb.textContent = parsed.frontmatter.title || currentDoc.title;
      elements.description.textContent = parsed.frontmatter.description || '';
      elements.date.textContent = formatDate(parsed.frontmatter.updated);
      elements.category.textContent = parsed.frontmatter.category || currentDoc.category;
      elements.source.href = `${getRepoSourceBase()}${currentDoc.file}`;

      renderSidebar(elements, currentDoc.slug);
      renderToc(elements);
      renderRelated(elements, currentDoc);

      document.title = `${parsed.frontmatter.title || currentDoc.title} - Los Angeles de San Rafael`;
    } catch (err) {
      elements.body.innerHTML = '<p class="error">Error al cargar el documento.</p>';
      console.error(err);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
