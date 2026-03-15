#!/usr/bin/env node

const fs = require('fs');
const vm = require('vm');

const pressUtilsCode = fs.readFileSync('docs/assets/js/press-utils.js', 'utf8');
const news = JSON.parse(fs.readFileSync('docs/data/prensa/curated_news.json', 'utf8'));

const sandbox = { window: {}, console };
vm.createContext(sandbox);
vm.runInContext(pressUtilsCode, sandbox);
const u = sandbox.window.PressUtils;

function assertEqual(label, a, b) {
  if (a !== b) {
    throw new Error(`[FAIL] ${label}: ${a} !== ${b}`);
  }
  console.log(`[OK] ${label}: ${a}`);
}

function assert(condition, label) {
  if (!condition) throw new Error(`[FAIL] ${label}`);
  console.log(`[OK] ${label}`);
}

const allNews = u.sortNews(news);
const archiveNews = u.getArchiveNews(news);

const institutionalAll = u.applyFilters(allNews, {
  sourceType: 'institucional',
  source: '',
  category: '',
  year: '',
  query: ''
});

const institutionalAyto = u.applyFilters(allNews, {
  sourceType: 'institucional',
  source: 'Ayuntamiento de El Espinar',
  category: '',
  year: '',
  query: ''
});

assert(institutionalAll.length >= institutionalAyto.length, 'Todos los medios incluye medio concreto');
assertEqual('Institucional + Ayuntamiento', institutionalAyto.length, 10);

const institutionalAllLiteral = u.applyFilters(allNews, {
  sourceType: 'institucional',
  source: 'Todos los medios',
  category: '',
  year: '',
  query: ''
});
assertEqual('Neutralidad literal "Todos los medios"', institutionalAllLiteral.length, institutionalAll.length);

const neutralCategories = u.applyFilters(allNews, {
  sourceType: '',
  source: '',
  category: 'Todas las categorías',
  year: 'Todos los años',
  query: ''
});
assertEqual('Neutralidad categorías/años literales', neutralCategories.length, allNews.length);

const filteredQuery = u.applyFilters(allNews, {
  sourceType: '',
  source: '',
  category: '',
  year: '',
  query: 'el espinar'
});
assert(filteredQuery.length <= allNews.length, 'Filtro de texto restringe o mantiene total');

const archiveDefault = u.applyFilters(archiveNews, {
  sourceType: '',
  source: '',
  category: '',
  year: '',
  query: ''
});
assertEqual('Archivo por defecto mantiene tamaño base', archiveDefault.length, archiveNews.length);

console.log('[OK] Validaciones de regresión completadas');
