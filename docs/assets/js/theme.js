(function () {
  'use strict';

  const STORAGE_KEY = 'lasr-theme';
  const DARK = 'dark';
  const LIGHT = 'light';

  function preferredTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === DARK || saved === LIGHT) return saved;
    } catch (error) {
      // ignore
    }

    return LIGHT;
  }

  function applyTheme(theme) {
    const value = theme === DARK ? DARK : LIGHT;
    document.documentElement.setAttribute('data-theme', value);
    document.documentElement.style.colorScheme = value;

    const btn = document.querySelector('[data-theme-toggle]');
    if (btn) {
      const label = value === DARK ? 'oscuro' : 'claro';
      const next = value === DARK ? 'claro' : 'oscuro';
      btn.setAttribute('aria-label', `Cambiar a modo ${next}`);
      btn.setAttribute('title', `Tema actual: ${label}. Pulsar para cambiar a ${next}.`);
      btn.setAttribute('aria-pressed', value === DARK ? 'true' : 'false');
      btn.classList.toggle('is-dark', value === DARK);
    }
  }

  function persistTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // ignore
    }
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') === DARK ? DARK : LIGHT;
    const next = current === DARK ? LIGHT : DARK;
    applyTheme(next);
    persistTheme(next);
  }

  function initThemeToggle() {
    const btn = document.querySelector('[data-theme-toggle]');
    if (!btn) return;
    btn.addEventListener('click', toggleTheme);
    applyTheme(document.documentElement.getAttribute('data-theme') || preferredTheme());
  }

  window.LASRTheme = {
    preferredTheme,
    applyTheme,
    initThemeToggle
  };
})();
