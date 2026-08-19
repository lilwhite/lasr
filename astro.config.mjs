// @ts-check
import { defineConfig } from 'astro/config';

// Generación estática pura, compatible con GitHub Pages.
// `site` y `base` definitivos se configurarán en la fase de despliegue.
export default defineConfig({
  output: 'static',
  site: 'https://example.github.io',
  trailingSlash: 'ignore',
});
