/**
 * Engancha el botón de tema de la capa documental.
 *
 * `theme.js` viene del portal y solo publica `window.LASRTheme`: allí es
 * `main.js` o `docs.js` quien llama a `initThemeToggle()`. Esta capa no tiene
 * JavaScript de aplicación, así que necesita esta línea. No puede ir en línea
 * en el HTML porque la CSP del sitio prohíbe los scripts incrustados.
 *
 * Es el único JavaScript propio de la capa documental, y no hace nada
 * funcional: solo respeta la preferencia de tema del resto del sitio.
 */
(function () {
  'use strict';

  function boot() {
    if (window.LASRTheme && typeof window.LASRTheme.initThemeToggle === 'function') {
      window.LASRTheme.initThemeToggle();
    }
  }

  // El script va al final del body, así que el botón ya existe; el guardia es
  // por si algún día se adelanta a la cabecera.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
