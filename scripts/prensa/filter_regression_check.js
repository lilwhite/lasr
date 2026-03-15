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

// sanity: file still parses with browser-like environment
vm.runInContext(archiveCode, sandbox);
console.log('[OK] prensa-archive.js carga en entorno simulado sin errores de sintaxis');
console.log('[OK] Validaciones de regresión completadas');
