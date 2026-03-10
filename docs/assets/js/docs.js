/**
 * Documentación - Renderizador de Markdown
 * Carga y renderiza documentos Markdown con frontmatter
 */

(function() {
    'use strict';

    // Documentos disponibles
    const documents = [
        { file: 'urbanizacion_los_angeles_san_rafael.md', slug: 'documento-principal', title: 'Documento Principal', category: 'principal', order: 0 },
        { file: 'contexto_general.md', slug: 'contexto-general', title: 'Contexto General', category: 'análisis', order: 1 },
        { file: 'timeline_conflicto.md', slug: 'linea-temporal', title: 'Línea Temporal', category: 'cronología', order: 2 },
        { file: 'problemas_detectados.md', slug: 'problemas-detectados', title: 'Problemas Detectados', category: 'análisis', order: 3 },
        { file: 'actores.md', slug: 'actores', title: 'Actores', category: 'referencia', order: 4 },
        { file: 'opciones_legales.md', slug: 'opciones-legales', title: 'Opciones Legales', category: 'legal', order: 5 },
        { file: 'preguntas_abiertas.md', slug: 'preguntas-abiertas', title: 'Preguntas Abiertas', category: 'análisis', order: 6 }
    ];

    // Elementos del DOM
    const elements = {
        title: document.getElementById('docTitle'),
        description: document.getElementById('docDescription'),
        date: document.getElementById('docDate'),
        category: document.getElementById('docCategory'),
        body: document.getElementById('docBody'),
        source: document.getElementById('docSource'),
        sidebar: document.getElementById('sidebarNav'),
        breadcrumb: document.getElementById('breadcrumbTitle')
    };

    // Obtener slug de la URL
    function getSlugFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('slug') || documents[0].slug;
    }

    // Parsear frontmatter YAML simple
    function parseFrontmatter(content) {
        const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
        const match = content.match(frontmatterRegex);
        
        if (!match) {
            return { frontmatter: {}, content: content };
        }

        const fmText = match[1];
        const fm = {};
        
        fmText.split('\n').forEach(line => {
            const colonIndex = line.indexOf(':');
            if (colonIndex > 0) {
                const key = line.substring(0, colonIndex).trim();
                let value = line.substring(colonIndex + 1).trim();
                // Quitar comillas
                value = value.replace(/^["']|["']$/g, '');
                fm[key] = value;
            }
        });

        return {
            frontmatter: fm,
            content: content.substring(match[0].length)
        };
    }

    // Formatear fecha
    function formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Renderizar sidebar
    function renderSidebar(currentSlug) {
        // Ordenar documentos
        const sorted = [...documents].sort((a, b) => a.order - b.order);
        
        let html = '';
        sorted.forEach(doc => {
            const active = doc.slug === currentSlug ? 'active' : '';
            html += `
                <li>
                    <a href="doc.html?slug=${doc.slug}" class="sidebar-link ${active}">
                        ${doc.title}
                    </a>
                </li>
            `;
        });
        
        if (elements.sidebar) {
            elements.sidebar.innerHTML = html;
        }
    }

    // Cargar documento
    async function loadDocument(slug) {
        const doc = documents.find(d => d.slug === slug) || documents[0];
        
        try {
            const response = await fetch(doc.file);
            if (!response.ok) throw new Error('Documento no encontrado');
            
            const markdown = await response.text();
            const { frontmatter, content } = parseFrontmatter(markdown);
            
            // Renderizar contenido
            const htmlContent = marked.parse(content);
            
            // Actualizar metadatos
            if (elements.title) {
                elements.title.textContent = frontmatter.title || doc.title;
            }
            if (elements.breadcrumb) {
                elements.breadcrumb.textContent = frontmatter.title || doc.title;
            }
            if (elements.description) {
                elements.description.textContent = frontmatter.description || '';
            }
            if (elements.date) {
                elements.date.textContent = formatDate(frontmatter.updated);
            }
            if (elements.category) {
                elements.category.textContent = frontmatter.category || '';
            }
            if (elements.body) {
                elements.body.innerHTML = htmlContent;
            }
            if (elements.source) {
                // Enlace al archivo fuente (ajustar según el repositorio)
                const repoUrl = 'https://github.com/tu-usuario/tu-repo/blob/main/docs/';
                elements.source.href = repoUrl + doc.file;
            }
            
            // Actualizar título de página
            document.title = `${frontmatter.title || doc.title} - Los Ángeles de San Rafael`;
            
            // Renderizar sidebar
            renderSidebar(slug);
            
        } catch (error) {
            console.error('Error cargando documento:', error);
            if (elements.body) {
                elements.body.innerHTML = '<p class="error">Error al cargar el documento.</p>';
            }
        }
    }

    // Inicializar
    function init() {
        const slug = getSlugFromURL();
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => loadDocument(slug));
        } else {
            loadDocument(slug);
        }
    }

    init();

})();
