/**
 * Copia del portal a la capa documental los activos que ambos comparten.
 *
 * La alternativa —referenciar `/assets/css/tokens.css` con una ruta absoluta de
 * raíz— no sirve: `astro dev` sirve solo este subproyecto, así que el bucle de
 * desarrollo diario quedaría sin colores ni tema. Copiar en el prebuild
 * mantiene una sola fuente de verdad y un desarrollo que se parece a producción.
 *
 * El CSS va a `src/styles/` para que lo empaquete Vite (orden de cascada
 * garantizado, sin petición extra). El JS va a `public/` porque tiene que ser un
 * fichero servible: `theme-init.js` se carga en el `<head>` antes del primer
 * pintado y no puede ir en un bundle diferido.
 *
 * Los destinos están en .gitignore: son copias, no fuentes. Si este script no
 * corre, el `@import` de `global.css` falla y el build se para, que es
 * exactamente lo que debe pasar.
 */
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCUMENTACION = resolve(HERE, '..');
const PORTAL = resolve(DOCUMENTACION, '..', 'docs');

const AVISO = '/* GENERADO por scripts/sync-portal-assets.mjs — NO EDITAR.\n   La fuente es docs/assets/css/tokens.css, en la raíz del repositorio. */\n\n';

/** Ficheros que se copian tal cual. */
const COPIAS = [
  ['assets/js/theme-init.js', 'public/assets/js/theme-init.js'],
  ['assets/js/theme.js', 'public/assets/js/theme.js'],
  // Una sola imagen OpenGraph para todo el dominio: lo que se comparte por
  // WhatsApp es el mismo sitio, venga de la portada o de una ficha documental.
  ['assets/images/og-image.png', 'public/og.png'],
];

async function main() {
  // El CSS se copia con una cabecera de aviso: acabará abierto en un editor y
  // hay que dejar claro que editarlo ahí no cambia nada.
  const tokens = await readFile(resolve(PORTAL, 'assets/css/tokens.css'), 'utf8');
  const destinoCss = resolve(DOCUMENTACION, 'src/styles/portal-tokens.css');
  await mkdir(dirname(destinoCss), { recursive: true });
  await writeFile(destinoCss, AVISO + tokens, 'utf8');

  for (const [origen, destino] of COPIAS) {
    const abs = resolve(DOCUMENTACION, destino);
    await mkdir(dirname(abs), { recursive: true });
    await copyFile(resolve(PORTAL, origen), abs);
  }

  console.log(`✔ Activos del portal sincronizados (${COPIAS.length + 1} ficheros).`);
}

main().catch((err) => {
  console.error('✖ No se han podido sincronizar los activos del portal.');
  console.error(`  ¿Existe ${PORTAL}? El build de la capa documental lo necesita.`);
  console.error(err.message);
  process.exit(1);
});
