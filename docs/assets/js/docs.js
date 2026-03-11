/**
 * Documentacion - Renderizador Markdown
 */

(function () {
  'use strict';

  const documents = [
    { file: 'documentacion_relevante.md', slug: 'documentacion-relevante', title: 'Documentacion relevante', category: 'referencia', order: 0 }
  ];

  const routeAliases = {};

  function getRootPrefix() {
    return document.body.dataset.docRoot || '.';
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

    return 'documentacion-relevante';
  }

  function canonicalSlug(slug) {
    return routeAliases[slug] || slug;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function sanitizeUrl(url, options = {}) {
    if (typeof url !== 'string') return '';
    const trimmed = url.trim();
    if (!trimmed) return '';

    const allowRelative = options.allowRelative === true;
    const allowHash = options.allowHash === true;
    const allowMailto = options.allowMailto === true;

    if (allowHash && trimmed.startsWith('#')) return trimmed;

    if (allowRelative && !trimmed.includes(':') && !trimmed.startsWith('//')) {
      return trimmed;
    }

    try {
      const parsed = new URL(trimmed, window.location.origin);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        return parsed.href;
      }
      if (allowMailto && parsed.protocol === 'mailto:') {
        return parsed.href;
      }
    } catch (error) {
      return '';
    }

    return '';
  }

  function sanitizeRenderedHtml(html) {
    const template = document.createElement('template');
    template.innerHTML = html;

    const blockedSelectors = 'script, iframe, object, embed, form, input, button, link, meta, base';
    template.content.querySelectorAll(blockedSelectors).forEach((node) => node.remove());

    const nodes = template.content.querySelectorAll('*');
    nodes.forEach((node) => {
      Array.from(node.attributes).forEach((attr) => {
        const name = attr.name.toLowerCase();
        const value = attr.value || '';

        if (name.startsWith('on')) {
          node.removeAttribute(attr.name);
          return;
        }

        if (name === 'href' || name === 'src' || name === 'xlink:href') {
          const safe = sanitizeUrl(value, { allowRelative: true, allowHash: true, allowMailto: true });
          if (!safe) {
            node.removeAttribute(attr.name);
            return;
          }
          node.setAttribute(attr.name, safe);
        }
      });

      if (node.tagName === 'A' && node.getAttribute('target') === '_blank') {
        node.setAttribute('rel', 'noopener noreferrer');
      }
    });

    return template.innerHTML;
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
      <header class="header doc-header-top" id="header">
        <div class="header-container">
          <a href="${getRootPrefix()}/index.html" class="logo"><span class="logo-text">LASR</span></a>
          <nav class="doc-top-actions" aria-label="Acciones"><a class="btn btn-secondary doc-back-btn" href="${getRootPrefix()}/index.html#documentos">Volver al portal</a></nav>
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
            <div class="sidebar-toc" id="sidebarToc"></div>
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
            <div class="doc-body" id="docBody"></div>
            <section class="doc-related" id="docRelated"></section>
          </article>
        </div>
      </main>
      <footer class="footer">
        <div class="container">
          <p class="footer-text"><strong>Los Angeles de San Rafael</strong> — Portal informativo vecinal</p>
          <p class="footer-disclaimer">Este portal tiene caracter informativo y divulgativo. No constituye asesoramiento juridico.</p>
          <p class="footer-links">
            <a id="footerRepoLink" href="https://github.com/lilwhite/lasr" target="_blank" rel="noopener noreferrer">Ver repositorio</a>
            <span>·</span>
            <a id="footerLicenseLink" href="https://github.com/lilwhite/lasr/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">Licencia MIT</a>
          </p>
          <p class="footer-copy">© 2026 — Informacion actualizada a <span id="lastUpdatedDate">10/03/2026</span></p>
        </div>
      </footer>
    `;
  }

  function getElements() {
    return {
      title: document.getElementById('docTitle'),
      description: document.getElementById('docDescription'),
      date: document.getElementById('docDate'),
      category: document.getElementById('docCategory'),
      body: document.getElementById('docBody'),
      sidebar: document.getElementById('sidebarNav'),
      breadcrumb: document.getElementById('breadcrumbTitle'),
      toc: document.getElementById('sidebarToc'),
      related: document.getElementById('docRelated')
    };
  }

  async function updateFooterMeta() {
    const root = getRootPrefix();
    const repoLink = document.getElementById('footerRepoLink');
    const licenseLink = document.getElementById('footerLicenseLink');
    const dateNode = document.getElementById('lastUpdatedDate');

    try {
        const cfgRes = await fetch(`${root}/assets/config.json`);
        if (cfgRes.ok) {
          const cfg = await cfgRes.json();
          if (repoLink && cfg?.project?.repositoryUrl) {
            const safeRepoUrl = sanitizeUrl(cfg.project.repositoryUrl);
            if (safeRepoUrl) repoLink.href = safeRepoUrl;
          }
          if (licenseLink && cfg?.project?.licenseUrl) {
            const safeLicenseUrl = sanitizeUrl(cfg.project.licenseUrl);
            if (safeLicenseUrl) licenseLink.href = safeLicenseUrl;
          }
          if (licenseLink && cfg?.project?.license) licenseLink.textContent = `Licencia ${cfg.project.license}`;
        }
    } catch (e) {
      console.warn('No se pudo cargar config del sitio', e);
    }

    try {
      const metaRes = await fetch(`${root}/assets/build-meta.json`);
      if (metaRes.ok) {
        const meta = await metaRes.json();
        if (dateNode && meta?.updatedDate) dateNode.textContent = meta.updatedDate;
      }
    } catch (e) {
      console.warn('No se pudo cargar build-meta', e);
    }
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
        return `<li><a class="sidebar-link ${active}" href="${linkForSlug(doc.slug)}">${escapeHtml(doc.title)}</a></li>`;
      })
      .join('');
  }

  function addHeadingAnchors(container) {
    const headings = container.querySelectorAll('h2, h3, h4');
    headings.forEach((h, idx) => {
      if (!h.id) {
        const slug = h.textContent.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
        h.id = `${slug || 'seccion'}-${idx + 1}`;
      }
    });
    return headings;
  }

  function buildTocTree(headings) {
    const root = { level: 1, children: [] };
    const stack = [root];

    headings.forEach((heading) => {
      const level = Number(heading.tagName.substring(1));
      const node = {
        id: heading.id,
        title: (heading.textContent || '').trim(),
        level,
        children: []
      };

      while (stack.length > 1 && stack[stack.length - 1].level >= level) {
        stack.pop();
      }

      stack[stack.length - 1].children.push(node);
      stack.push(node);
    });

    return root.children;
  }

  function renderTocList(nodes, depth) {
    if (!nodes.length) return '';
    return `
      <ul class="doc-toc-list depth-${depth}">
        ${nodes
          .map(
            (node) => `
              <li class="doc-toc-item level-${node.level}">
                <a class="doc-toc-link" href="#${node.id}">${escapeHtml(node.title)}</a>
                ${renderTocList(node.children, depth + 1)}
              </li>
            `
          )
          .join('')}
      </ul>
    `;
  }

  function renderToc(elements) {
    const headings = addHeadingAnchors(elements.body);
    if (!headings.length) {
      elements.toc.innerHTML = '';
      return;
    }

    const tocTree = buildTocTree(Array.from(headings));
    elements.toc.innerHTML = `
      <nav class="doc-toc" aria-label="Tabla de contenidos">
        <h3 class="doc-toc-title">Índice</h3>
        ${renderTocList(tocTree, 1)}
      </nav>
    `;
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
          .map((d) => `<a class="doc-card" href="${linkForSlug(d.slug)}"><h4 class="doc-title">${escapeHtml(d.title)}</h4><p class="doc-description">${escapeHtml(d.category)}</p></a>`)
          .join('')}
      </div>
    `;
  }

  function sanitizeTableLinks(table) {
    const links = table.querySelectorAll('a[href]');
    links.forEach((link) => {
      const href = link.getAttribute('href') || '';
      const text = (link.textContent || '').trim();
      const looksLikeRawUrl = /^https?:\/\//i.test(text);
      const longRawText = text.length > 45;

      if ((looksLikeRawUrl || text === href) && longRawText) {
        link.dataset.originalText = text;
        link.textContent = 'Abrir fuente';
        link.classList.add('table-link-clean');
      }

      if (href.length > 60) {
        link.classList.add('table-link-long');
      }
    });
  }

  function highlightUrlColumn(table) {
    const headers = Array.from(table.querySelectorAll('thead th'));
    if (!headers.length) return;

    const urlIndex = headers.findIndex((th) => /^(url|enlace)$/i.test((th.textContent || '').trim()));
    if (urlIndex === -1) return;

    table.classList.add('has-url-column');
    const rows = table.querySelectorAll('tr');
    rows.forEach((row) => {
      const cells = row.querySelectorAll('th, td');
      if (cells[urlIndex]) {
        cells[urlIndex].classList.add('url-column-cell');
      }
    });
  }

  function enhanceTables(container) {
    const tables = container.querySelectorAll('table');
    tables.forEach((table) => {
      table.classList.add('markdown-table');
      sanitizeTableLinks(table);
      highlightUrlColumn(table);

      if (!table.parentElement.classList.contains('table-container')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-container';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }
    });
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
      elements.body.innerHTML = sanitizeRenderedHtml(html);
      enhanceTables(elements.body);

      elements.title.textContent = parsed.frontmatter.title || currentDoc.title;
      elements.breadcrumb.textContent = parsed.frontmatter.title || currentDoc.title;
      elements.description.textContent = parsed.frontmatter.description || '';
      elements.date.textContent = formatDate(parsed.frontmatter.updated);
      elements.category.textContent = parsed.frontmatter.category || currentDoc.category;
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
    document.addEventListener('DOMContentLoaded', async () => {
      await load();
      await updateFooterMeta();
    });
  } else {
    load().then(updateFooterMeta);
  }
})();
