#!/usr/bin/env node

const fs = require('fs');
const vm = require('vm');

const pressUtilsCode = fs.readFileSync('docs/assets/js/press-utils.js', 'utf8');
const archiveCode = fs.readFileSync('docs/assets/js/prensa-archive.js', 'utf8');
const news = JSON.parse(fs.readFileSync('docs/data/prensa/curated_news.json', 'utf8'));

const sandbox = {
  window: {
    location: { search: '' }
  },
  document: {
    createElement: () => ({
      _text: '',
      set textContent(v) { this._text = String(v); },
      get innerHTML() {
        return this._text
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');
      }
    }),
    getElementById: () => null,
    readyState: 'loading',
    addEventListener: () => {}
  },
  console
};

vm.createContext(sandbox);
vm.runInContext(pressUtilsCode, sandbox);
const u = sandbox.window.PressUtils;

function assert(condition, label) {
  if (!condition) throw new Error(`[FAIL] ${label}`);
  console.log(`[OK] ${label}`);
}

function assertEqual(a, b, label) {
  if (a !== b) throw new Error(`[FAIL] ${label}: ${a} !== ${b}`);
  console.log(`[OK] ${label}: ${a}`);
}

const allNews = u.sortNews(news);
const archiveNews = u.getArchiveNews(news);

const caseA = u.applyFiltersTrace(allNews, {
  sourceType: 'institucional',
  source: '',
  category: '',
  year: '',
  query: ''
});
assertEqual(caseA.finalItems.length, 10, 'Institucional + Todos los medios (neutral vacío)');

const caseB = u.applyFiltersTrace(allNews, {
  sourceType: 'institucional',
  source: 'Ayuntamiento de El Espinar',
  category: '',
  year: '',
  query: ''
});
assertEqual(caseB.finalItems.length, 10, 'Institucional + Ayuntamiento de El Espinar');

const caseCLiteral = u.applyFiltersTrace(allNews, {
  sourceType: 'institucional',
  source: 'Todos los medios',
  category: '',
  year: '',
  query: ''
});
assertEqual(caseCLiteral.finalItems.length, caseA.finalItems.length, 'Neutralidad literal Todos los medios');

const caseD = u.applyFiltersTrace(allNews, {
  sourceType: '',
  source: '',
  category: 'Todas las categorías',
  year: 'Todos los años',
  query: ''
});
assertEqual(caseD.finalItems.length, allNews.length, 'Neutralidad literal categoría/año');

const caseE = u.applyFiltersTrace(archiveNews, {
  sourceType: '',
  source: '',
  category: '',
  year: '',
  query: ''
});
assertEqual(caseE.finalItems.length, archiveNews.length, 'Archivo por defecto usa base archiveNews');

const caseF = u.applyFiltersTrace(allNews, {
  sourceType: 'institucional',
  source: '',
  category: '',
  year: '',
  query: 'segovia'
});
assert(caseF.finalItems.length <= caseA.finalItems.length, 'Búsqueda textual restringe en institucional');

const landingFixture = [
  {
    id: 'a-1',
    source: 'Medio A',
    date: '2026-03-10T09:00:00Z',
    title: 'A reciente',
    excerpt: 'Los Ángeles de San Rafael y urbanización',
    category: 'urbanismo',
    isRelevant: true,
    relevanceScore: 9
  },
  {
    id: 'a-2',
    source: 'medio   a',
    date: '2026-03-05T09:00:00Z',
    title: 'A antigua',
    excerpt: 'Los Ángeles de San Rafael y vecinos',
    category: 'juntas_y_vecinos',
    isRelevant: true,
    relevanceScore: 8
  },
  {
    id: 'b-1',
    source: 'Medio B',
    date: '2026-03-09T09:00:00Z',
    title: 'B reciente',
    excerpt: 'Los Ángeles de San Rafael y servicios',
    category: 'servicios',
    isRelevant: true,
    relevanceScore: 7
  },
  {
    id: 'c-1',
    source: 'Medio C',
    date: '2026-03-08T09:00:00Z',
    title: 'C reciente',
    excerpt: 'Los Ángeles de San Rafael y infraestructuras',
    category: 'infraestructuras',
    isRelevant: true,
    relevanceScore: 6
  }
];

const landingCards = u.getLandingFeaturedNews(landingFixture, 3);
assertEqual(landingCards.length, 3, 'Landing limitada al número de cards');
assertEqual(landingCards[0].id, 'a-1', 'Landing elige la noticia más reciente de Medio A');
assertEqual(landingCards[1].id, 'b-1', 'Landing mantiene Medio B en segundo lugar');
assertEqual(landingCards[2].id, 'c-1', 'Landing mantiene Medio C en tercer lugar');

const normalizedSources = landingCards.map((item) => (item.source || '').toLowerCase().replace(/\s+/g, ' ').trim());
assertEqual(new Set(normalizedSources).size, landingCards.length, 'Landing no repite medio si hay alternativas');

const landingDates = landingCards.map((item) => new Date(item.date).getTime());
assert(landingDates[0] >= landingDates[1] && landingDates[1] >= landingDates[2], 'Landing ordenada por fecha descendente');

const invalidDateFixture = [
  {
    id: 'invalid-a',
    source: 'Medio D',
    date: 'sin-fecha',
    title: 'Fecha inválida',
    excerpt: 'Los Ángeles de San Rafael',
    category: 'urbanismo',
    isRelevant: true,
    relevanceScore: 10
  },
  {
    id: 'valid-a',
    source: 'Medio E',
    date: '2026-03-07T09:00:00Z',
    title: 'Fecha válida',
    excerpt: 'Los Ángeles de San Rafael',
    category: 'urbanismo',
    isRelevant: true,
    relevanceScore: 8
  }
];

const invalidDateResult = u.getLandingFeaturedNews(invalidDateFixture, 3);
assertEqual(invalidDateResult.length, 1, 'Landing ignora entradas sin fecha válida para ordenar');
assertEqual(invalidDateResult[0].id, 'valid-a', 'Landing conserva noticias con fecha válida');

// sanity: file still parses with browser-like environment
vm.runInContext(archiveCode, sandbox);
console.log('[OK] prensa-archive.js carga en entorno simulado sin errores de sintaxis');
console.log('[OK] Validaciones de regresión completadas');
