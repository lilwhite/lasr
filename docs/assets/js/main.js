/**
 * Los Ángeles de San Rafael - Portal Informativo
 * Main JavaScript
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    const CONFIG = {
        contentPath: 'assets/content.json',
        configPath: 'assets/config.json',
        buildMetaPath: 'assets/build-meta.json',
        pressDataPath: 'data/prensa/curated_news.json',
        animationDelay: 100
    };

    // ============================================
    // State
    // ============================================
    let content = null;
    let pressNews = [];
    let isLoading = true;

    // ============================================
    // DOM Elements
    // ============================================
    const elements = {
        header: document.getElementById('header'),
        menuToggle: document.getElementById('menuToggle'),
        nav: document.getElementById('nav'),
        scrollTop: document.getElementById('scrollTop'),
        // Content containers
        situacionContent: document.getElementById('situacionContent'),
        timelineContent: document.getElementById('timelineContent'),
        sentenciaContent: document.getElementById('sentenciaContent'),
        sentenciaLinkCta: document.getElementById('sentenciaLinkCta'),
        sentenciaIdeaClave: document.getElementById('sentenciaIdeaClave'),
        incumplimientosContent: document.getElementById('incumplimientosContent'),
        actuacionesContent: document.getElementById('actuacionesContent'),
        documentosContent: document.getElementById('documentosContent'),
        faqContent: document.getElementById('faqContent'),
        contactoContent: document.getElementById('contactoContent')
    };

    // ============================================
    // Icons SVG
    // ============================================
    const icons = {
        clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
        scale: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M5 6l7-3 7 3"/><path d="M4 10v11"/><path d="M20 10v11"/><path d="M8 14v3"/><path d="M12 14v3"/><path d="M16 14v3"/></svg>`,
        alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
        building: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>`,
        city: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>`,
        document: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
        droplet: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`,
        users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
        home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
        external: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`,
        chevron: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`
    };

    // ============================================
    // Utility Functions
    // ============================================
    function getIcon(name) {
        return icons[name] || icons.document;
    }

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

    async function updateFooterMeta() {
        const repoLink = document.getElementById('footerRepoLink');
        const licenseLink = document.getElementById('footerLicenseLink');
        const lastUpdatedDate = document.getElementById('lastUpdatedDate');

        try {
            const configResponse = await fetch(CONFIG.configPath);
            if (configResponse.ok) {
                const config = await configResponse.json();
                if (repoLink && config?.project?.repositoryUrl) {
                    const safeRepoUrl = sanitizeExternalUrl(config.project.repositoryUrl);
                    if (safeRepoUrl) repoLink.href = safeRepoUrl;
                }
                if (licenseLink && config?.project?.licenseUrl) {
                    const safeLicenseUrl = sanitizeExternalUrl(config.project.licenseUrl);
                    if (safeLicenseUrl) licenseLink.href = safeLicenseUrl;
                }
                if (licenseLink && config?.project?.license) {
                    licenseLink.textContent = `Licencia ${config.project.license}`;
                }
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

    async function loadPressNews() {
        try {
            const response = await fetch(CONFIG.pressDataPath);
            if (!response.ok) {
                pressNews = [];
                return;
            }

            const payload = await response.json();
            pressNews = Array.isArray(payload) ? payload : [];
        } catch (error) {
            console.warn('No se pudo cargar curated_news.json', error);
            pressNews = [];
        }
    }

    // ============================================
    // Render Functions
    // ============================================
    function renderSituacion() {
        if (!content?.situacion) return;
        
        const data = content.situacion;
        let html = '';
        
        data.bloques.forEach(bloque => {
            html += `
                <div class="card fade-in">
                    <div class="card-header">
                        <div class="card-icon">
                            ${getIcon(bloque.icono)}
                        </div>
                        <h3 class="card-title">${escapeHtml(bloque.titulo)}</h3>
                    </div>
                    <p class="card-content">${escapeHtml(bloque.contenido)}</p>
                </div>
            `;
        });
        
        elements.situacionContent.innerHTML = html;
    }

    function renderTimeline() {
        if (!content?.historia) return;
        
        const data = content.historia;
        let html = '';
        
        data.eventos.forEach((evento, index) => {
            html += `
                <div class="timeline-item fade-in" style="animation-delay: ${index * 0.1}s">
                    <div class="timeline-dot"></div>
                    <span class="timeline-date">${escapeHtml(evento.fecha)}</span>
                    <h3 class="timeline-title">${escapeHtml(evento.titulo)}</h3>
                    <p class="timeline-description">${escapeHtml(evento.descripcion)}</p>
                </div>
            `;
        });
        
        elements.timelineContent.innerHTML = html;
    }

    function renderSentencia() {
        if (!content?.sentencia) return;
        
        const data = content.sentencia;
        let html = '';
        
        data.puntos.forEach(punto => {
            html += `
                <div class="card fade-in">
                    <div class="card-header">
                        <span class="card-title-number">${punto.numero}</span>
                        <h3 class="card-title">${escapeHtml(punto.titulo)}</h3>
                    </div>
                    <p class="card-content">${escapeHtml(punto.descripcion)}</p>
                </div>
            `;
        });
        
        elements.sentenciaContent.innerHTML = html;

        if (elements.sentenciaLinkCta) {
            const safeSentenciaUrl = sanitizeExternalUrl(data.enlace?.url || '');
            if (safeSentenciaUrl) {
                elements.sentenciaLinkCta.innerHTML = `
                    <div class="sentencia-cta fade-in">
                        <div class="sentencia-cta-content">
                            <h3 class="sentencia-cta-title">Texto completo de la sentencia</h3>
                            <p class="sentencia-cta-text">${escapeHtml(data.enlace.ayuda || 'Consulta la fuente oficial para revisar la resolución completa.')}</p>
                        </div>
                        <a href="${escapeHtml(safeSentenciaUrl)}" class="btn btn-secondary sentencia-cta-button" target="_blank" rel="noopener noreferrer">
                            ${escapeHtml(data.enlace.texto || 'Consultar sentencia')}
                        </a>
                    </div>
                `;
            } else {
                elements.sentenciaLinkCta.innerHTML = '';
            }
        }

        if (elements.sentenciaIdeaClave) {
            if (data.ideaClave) {
                elements.sentenciaIdeaClave.innerHTML = `
                    <div class="sentencia-key-idea fade-in">
                        <strong>Idea clave:</strong> ${escapeHtml(data.ideaClave.replace(/^Idea clave:\s*/i, ''))}
                    </div>
                `;
            } else {
                elements.sentenciaIdeaClave.innerHTML = '';
            }
        }
    }

    function renderIncumplimientos() {
        if (!content?.incumplimientos) return;
        
        const data = content.incumplimientos;
        let html = '';
        
        data.items.forEach(item => {
            html += `
                <div class="card fade-in">
                    <div class="card-header">
                        <div class="card-icon">
                            ${icons.alert}
                        </div>
                        <h3 class="card-title">${escapeHtml(item.titulo)}</h3>
                    </div>
                    <p class="card-content">${escapeHtml(item.descripcion)}</p>
                    <div class="doc-type" style="margin-top: 1rem; background-color: rgba(166, 75, 75, 0.1); color: var(--color-error);">
                        ${item.estado.toUpperCase()}
                    </div>
                </div>
            `;
        });
        
        elements.incumplimientosContent.innerHTML = html;
    }

    function renderActuaciones() {
        if (!content?.actuaciones) return;
        
        const data = content.actuaciones;
        let html = '';
        
        data.vias.forEach(via => {
            let opcionesHtml = via.opciones
                .map(opcion => `<li class="actuacion-item"><span class="actuacion-bullet" aria-hidden="true">•</span><span>${escapeHtml(opcion)}</span></li>`)
                .join('');
            
            html += `
                <div class="card fade-in">
                    <div class="card-header">
                        <div class="card-icon">
                            ${getIcon(via.icono)}
                        </div>
                        <h3 class="card-title">${escapeHtml(via.titulo)}</h3>
                    </div>
                    <ul class="card-content actuaciones-list" aria-label="Opciones de ${escapeHtml(via.titulo)}">
                        ${opcionesHtml}
                    </ul>
                </div>
            `;
        });
        
        elements.actuacionesContent.innerHTML = html;
    }

    function renderDocumentos() {
        if (!content?.documentos) return;
        
        const data = content.documentos;
        let html = '';

        const groups = Array.isArray(data.grupos) ? data.grupos : [
            {
                titulo: 'Documentación',
                descripcion: '',
                items: Array.isArray(data.items) ? data.items : []
            }
        ];

        groups.forEach((group, groupIndex) => {
            const groupKey = (group.key || '').toString().toLowerCase();
            const isPressGroup = groupKey === 'prensa' || (group.titulo || '').toString().trim().toLowerCase() === 'prensa';
            const isNormativeGroup = (group.titulo || '').toString().trim().toLowerCase() === 'normativa';
            const groupItems = Array.isArray(group.items) ? group.items : [];
            const pressItems = isPressGroup && window.PressUtils
                ? window.PressUtils.getLandingFeaturedNews(pressNews, 3)
                : [];
            let groupCards = '';

            if (isPressGroup && pressItems.length === 0) {
                groupCards = `
                    <div class="doc-card fade-in">
                        <span class="doc-type prensa">Prensa</span>
                        <h3 class="doc-title">Sin noticias relevantes publicadas</h3>
                        <p class="doc-description">Estamos actualizando la recopilación periodística. Vuelve en próximos días para consultar nuevas referencias.</p>
                        <p class="doc-meta">Estado: pendiente de actualización</p>
                    </div>
                `;
            }

            const iterableItems = isPressGroup
                ? pressItems.map(item => ({
                    tipo: 'prensa',
                    source: item.source,
                    titulo: item.title,
                    descripcion: item.excerpt || 'Cobertura periodística relacionada con Los Ángeles de San Rafael.',
                    url: item.url,
                    fecha: window.PressUtils
                        ? `${window.PressUtils.formatDate(item.date)} · ${window.PressUtils.getCategoryLabel(item.category)}`
                        : (item.date || 'Fecha no disponible')
                }))
                : groupItems;

            if (isPressGroup) {
                while (iterableItems.length < 3) {
                    iterableItems.push({
                        tipo: 'prensa',
                        source: 'Selección editorial',
                        titulo: 'Nueva noticia en revisión editorial',
                        descripcion: 'Estamos incorporando nuevas referencias periodísticas relevantes para Los Ángeles de San Rafael.',
                        url: '',
                        fecha: 'Actualización en curso'
                    });
                }
            }

            iterableItems.forEach((doc, cardIndex) => {
                const typeClass = (doc.tipo || 'documento').toLowerCase();
                const safeDocUrl = sanitizeExternalUrl(doc.url || '');
                const linkLabel = (doc.cta || 'Ver fuente').toString().trim() || 'Ver fuente';
                const linkHtml = safeDocUrl
                    ? `<a href="${escapeHtml(safeDocUrl)}" class="doc-link" target="_blank" rel="noopener noreferrer">${escapeHtml(linkLabel)} ${icons.external}</a>`
                    : '';
                const articles = Array.isArray(doc.articulos) ? doc.articulos.filter(Boolean) : [];
                const articlesHtml = articles.length
                    ? `<ul class="doc-article-list">${articles.map(article => `<li>${escapeHtml(article)}</li>`).join('')}</ul>`
                    : '';
                const isEucReferenceCard = isNormativeGroup
                    && (doc.titulo || '').toString().trim().toLowerCase() === 'régimen de entidades urbanísticas de conservación';

                groupCards += `
                    <div class="doc-card ${isPressGroup ? 'press-featured-card' : ''} ${isEucReferenceCard ? 'is-euc-reference' : ''} fade-in" style="animation-delay: ${(groupIndex * 0.08) + (cardIndex * 0.04)}s">
                        <span class="doc-type ${typeClass}">${escapeHtml(doc.tipo || 'Documento')}</span>
                        ${doc.source ? `<span class="press-source-badge">${escapeHtml(doc.source)}</span>` : ''}
                        <h3 class="doc-title">${escapeHtml(doc.titulo)}</h3>
                        <p class="doc-description press-excerpt">${escapeHtml(doc.descripcion || '')}</p>
                        ${articlesHtml}
                        ${doc.fecha ? `<p class="doc-meta">${escapeHtml(doc.fecha)}</p>` : ''}
                        ${linkHtml}
                    </div>
                `;
            });

            if (isPressGroup) {
                groupCards += `
                    <div class="press-archive-link-wrap fade-in" style="animation-delay: ${(groupIndex * 0.08) + 0.18}s">
                        <a href="prensa/" class="btn btn-secondary">Ver archivo de prensa</a>
                    </div>
                `;
            }

            html += `
                <section class="doc-group">
                    <header class="doc-group-header">
                        <h3 class="doc-group-title">${escapeHtml(group.titulo || 'Documentación')}</h3>
                        ${group.descripcion ? `<p class="doc-group-description">${escapeHtml(group.descripcion)}</p>` : ''}
                    </header>
                    <div class="cards doc-group-cards ${isNormativeGroup ? 'is-normativa-grid' : ''}">
                        ${groupCards}
                    </div>
                </section>
            `;
        });
        
        elements.documentosContent.innerHTML = html;
    }

    function renderFaq() {
        if (!content?.faq) return;
        
        const data = content.faq;
        let html = '';
        
        data.preguntas.forEach((item, index) => {
            html += `
                <div class="faq-item fade-in" style="animation-delay: ${index * 0.05}s">
                    <button class="faq-question" aria-expanded="false">
                        <span>${escapeHtml(item.pregunta)}</span>
                        <span class="faq-icon">${icons.chevron}</span>
                    </button>
                    <div class="faq-answer">
                        <div class="faq-answer-content">
                            ${escapeHtml(item.respuesta)}
                        </div>
                    </div>
                </div>
            `;
        });
        
        elements.faqContent.innerHTML = html;
        
        // Add FAQ toggle functionality
        document.querySelectorAll('.faq-question').forEach(button => {
            button.addEventListener('click', () => {
                const item = button.parentElement;
                const isActive = item.classList.contains('active');
                
                // Close all
                document.querySelectorAll('.faq-item').forEach(i => {
                    i.classList.remove('active');
                    i.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
                });
                
                // Open clicked
                if (!isActive) {
                    item.classList.add('active');
                    button.setAttribute('aria-expanded', 'true');
                }
            });
        });
    }

    function renderContacto() {
        if (!content?.contacto) return;
        
        const data = content.contacto;
        let html = '';
        
        data.opciones.forEach(opcion => {
            html += `
                <div class="contact-card fade-in">
                    <h3 class="contact-card-title">${escapeHtml(opcion.titulo)}</h3>
                    <p class="contact-card-text">${escapeHtml(opcion.descripcion)}</p>
                    ${opcion.email ? `<span class="contact-email">${escapeHtml(opcion.email)}</span>` : ''}
                </div>
            `;
        });
        
        elements.contactoContent.innerHTML = html;
    }

    function renderAll() {
        renderSituacion();
        renderTimeline();
        renderSentencia();
        renderIncumplimientos();
        renderActuaciones();
        renderDocumentos();
        renderFaq();
        renderContacto();
    }

    // ============================================
    // Event Handlers
    // ============================================
    function handleScroll() {
        const scrollY = window.scrollY;
        
        // Header shadow
        if (elements.header) {
            if (scrollY > 10) {
                elements.header.classList.add('scrolled');
            } else {
                elements.header.classList.remove('scrolled');
            }
        }
        
        // Scroll to top button
        if (elements.scrollTop) {
            if (scrollY > 500) {
                elements.scrollTop.classList.add('visible');
            } else {
                elements.scrollTop.classList.remove('visible');
            }
        }
        
        // Update active nav link
        updateActiveNavLink();
    }

    function updateActiveNavLink() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
            
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    }

    function handleMenuToggle() {
        if (elements.menuToggle && elements.nav) {
            elements.menuToggle.classList.toggle('active');
            elements.nav.classList.toggle('active');
        }
    }

    function handleScrollTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    // Smooth scroll for anchor links
    function handleAnchorClick(e) {
        const href = e.currentTarget.getAttribute('href');
        
        if (href && href.startsWith('#')) {
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                const headerHeight = elements.header ? elements.header.offsetHeight : 0;
                const targetPosition = target.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Close mobile menu
                if (elements.nav && elements.nav.classList.contains('active')) {
                    handleMenuToggle();
                }
            }
        }
    }

    // ============================================
    // Initialization
    // ============================================
    async function init() {
        try {
            // Load content
            const response = await fetch(CONFIG.contentPath);
            content = await response.json();

            // Load press feed
            await loadPressNews();
            
            // Render content
            renderAll();
            
            // Setup event listeners
            setupEventListeners();

            if (window.LASRTheme && typeof window.LASRTheme.initThemeToggle === 'function') {
                window.LASRTheme.initThemeToggle();
            }
            
            // Initial scroll handler
            handleScroll();

            // Footer metadata
            await updateFooterMeta();
            
            isLoading = false;
            
        } catch (error) {
            console.error('Error loading content:', error);
            // Show error message
            document.body.innerHTML = `
                <div style="padding: 2rem; text-align: center;">
                    <h1>Error al cargar el contenido</h1>
                    <p>Por favor, recarga la página.</p>
                </div>
            `;
        }
    }

    function setupEventListeners() {
        // Scroll
        window.addEventListener('scroll', handleScroll, { passive: true });
        
        // Menu toggle
        if (elements.menuToggle) {
            elements.menuToggle.addEventListener('click', handleMenuToggle);
        }
        
        // Scroll to top
        if (elements.scrollTop) {
            elements.scrollTop.addEventListener('click', handleScrollTop);
        }
        
        // Anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', handleAnchorClick);
        });
        
        // Close mobile menu on resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768 && elements.nav) {
                elements.nav.classList.remove('active');
                if (elements.menuToggle) {
                    elements.menuToggle.classList.remove('active');
                }
            }
        });
    }

    // ============================================
    // Start
    // ============================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
