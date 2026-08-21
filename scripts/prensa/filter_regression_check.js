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

// El fichero publicado solo contiene noticias del conflicto, así que los
// recuentos se derivan de los datos: el cron los regenera a diario.
// La invariante se mudó del campo al fichero: ya no hay `isRelevant` que
// comprobar, lo que hay publicado ES lo publicable. Lo que sí se comprueba es
// que no se cuele de vuelta ni texto del medio ni andamiaje editorial interno.
const CAMPOS_PUBLICABLES = new Set(['title', 'source', 'date', 'url', 'sourceType', 'category']);
const intrusos = [...new Set(news.flatMap((item) => Object.keys(item)))]
  .filter((k) => !CAMPOS_PUBLICABLES.has(k));
assert(intrusos.length === 0, `El fichero publica solo los seis campos previstos (sobran: ${intrusos})`);
assert(news.every((item) => !('excerpt' in item) && !('summary' in item)), 'El fichero no reproduce entradillas de los medios');
assert(news.every((item) => item.title && item.source && item.date && item.url),
  'Toda noticia conserva lo que la hace verificable: titular, medio, fecha y enlace');
assertEqual(archiveNews.length, news.length, 'El archivo es exactamente la selección publicada');

// Se elige el medio con más noticias para que el caso tenga volumen real.
const countBySource = new Map();
news.forEach((item) => countBySource.set(item.source, (countBySource.get(item.source) || 0) + 1));
const [mainSource, expectedBySource] = [...countBySource.entries()].sort((a, b) => b[1] - a[1])[0];
const mainSourceType = news.find((item) => item.source === mainSource).sourceType;

const caseA = u.applyFiltersTrace(allNews, {
  sourceType: mainSourceType,
  source: '',
  category: '',
  year: '',
  query: ''
});
assertEqual(
  caseA.finalItems.length,
  news.filter((item) => item.sourceType === mainSourceType).length,
  `Tipo de fuente ${mainSourceType} + Todos los medios (neutral vacío)`
);

const caseB = u.applyFiltersTrace(allNews, {
  sourceType: mainSourceType,
  source: mainSource,
  category: '',
  year: '',
  query: ''
});
assertEqual(caseB.finalItems.length, expectedBySource, `${mainSourceType} + ${mainSource}`);

const caseCLiteral = u.applyFiltersTrace(allNews, {
  sourceType: mainSourceType,
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
  sourceType: mainSourceType,
  source: '',
  category: '',
  year: '',
  query: 'espinar'
});
assert(caseF.finalItems.length <= caseA.finalItems.length, 'Búsqueda textual restringe dentro del tipo de fuente');

const landingFixture = [
  {
    id: 'a-1',
    source: 'Medio A',
    date: '2026-03-10T09:00:00Z',
    title: 'A reciente',
    category: 'urbanismo',
  },
  {
    id: 'a-2',
    source: 'medio   a',
    date: '2026-03-05T09:00:00Z',
    title: 'A antigua',
    category: 'juntas_y_vecinos',
  },
  {
    id: 'b-1',
    source: 'Medio B',
    date: '2026-03-09T09:00:00Z',
    title: 'B reciente',
    category: 'servicios',
  },
  {
    id: 'c-1',
    source: 'Medio C',
    date: '2026-03-08T09:00:00Z',
    title: 'C reciente',
    category: 'infraestructuras',
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
    category: 'urbanismo',
  },
  {
    id: 'valid-a',
    source: 'Medio E',
    date: '2026-03-07T09:00:00Z',
    title: 'Fecha válida',
    category: 'urbanismo',
  }
];

const invalidDateResult = u.getLandingFeaturedNews(invalidDateFixture, 3);
assertEqual(invalidDateResult.length, 1, 'Landing ignora entradas sin fecha válida para ordenar');
assertEqual(invalidDateResult[0].id, 'valid-a', 'Landing conserva noticias con fecha válida');

// sanity: file still parses with browser-like environment
vm.runInContext(archiveCode, sandbox);
console.log('[OK] prensa-archive.js carga en entorno simulado sin errores de sintaxis');
console.log('[OK] Validaciones de regresión completadas');
