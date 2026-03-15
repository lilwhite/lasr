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

    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return DARK;
    }
    return LIGHT;
  }

  function applyTheme(theme) {
    const value = theme === DARK ? DARK : LIGHT;
    document.documentElement.setAttribute('data-theme', value);
    document.documentElement.style.colorScheme = value;

    const btn = document.querySelector('[data-theme-toggle]');
    if (btn) {
      const label = value === DARK ? 'Oscuro' : 'Claro';
      const icon = value === DARK ? '🌙' : '☀️';
      btn.setAttribute('aria-label', `Cambiar tema (actual: ${label})`);
      btn.setAttribute('aria-pressed', value === DARK ? 'true' : 'false');
      const iconNode = btn.querySelector('.theme-toggle-icon');
      const labelNode = btn.querySelector('.theme-toggle-label');
      if (iconNode) iconNode.textContent = icon;
      if (labelNode) labelNode.textContent = label;
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
