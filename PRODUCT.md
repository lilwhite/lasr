# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Propietarios y vecinos de la urbanización Los Ángeles de San Rafael (El Espinar, Segovia). Mayoría no experta en derecho urbanístico; rango de edad amplio con peso significativo de personas mayores [inferido del contexto: urbanización residencial consolidada]. Situación típica: quieren entender qué pasa con su urbanización, qué dice la sentencia y qué pueden hacer, sin pagar asesoramiento para orientarse.

## Product Purpose

Portal informativo estático (GitHub Pages, dominio lasr-info.es) que explica la situación urbanística y jurídica del conflicto: sentencia firme del TSJCyL sobre la recepción de las fases I y II, cronología, incumplimientos, vías de actuación, hemeroteca de prensa actualizada a diario y un buscador catastral de las 2.112 parcelas. Éxito = un vecino entiende el conflicto y sabe qué puede hacer, sin intermediarios.

## Positioning

Único sitio que combina la documentación completa del conflicto con datos catastrales reales (WFS INSPIRE + DNPRC, mayo 2026): 2.112 parcelas indexadas con mapa, superficie y umbrales del art. 16.2 LPH calculados (528 propietarios o 375.710 m² para convocar Junta Extraordinaria). Un medio o un despacho no tienen esto reunido.

## Operating Context

Se consulta desde móvil y escritorio, a menudo llegando desde grupos vecinales de WhatsApp o buscadores [inferido]. Contenido dinámico (secciones del portal, prensa) se inyecta por JS desde `docs/assets/content.json` y `docs/data/`. Actualización de prensa automatizada a diario vía GitHub Actions.

## Capabilities and Constraints

- Sitio 100% estático servido por GitHub Pages; sin backend.
- CSP estricta: `font-src 'self' data:` — toda tipografía debe autoalojarse; sin CDNs de fuentes.
- El buscador de parcelas usa Leaflet (unpkg permitido en la CSP de esa página) y un dataset embebido en `docs/assets/js/parcelas.js`.
- Tono divulgativo, no jurídico: el portal repite en varios puntos que no constituye asesoramiento jurídico y no representa a ninguna organización formal. Esas notas legales deben preservarse.
- Idioma: español. Terminología propia: sentencia firme, recepción de la urbanización, fases I y II, art. 16.2 LPH, referencia catastral.

## Brand Commitments

Nombre: LASR / Los Ángeles de San Rafael. Dirección visual elegida por el usuario (agosto 2026): «Sierra vecinal» — mundo material de la sierra de Guadarrama (granito, pinar, luz de montaña), tono cercano de asamblea vecinal, con la accesibilidad de lectura como compromiso explícito (audiencia con peso de lectores mayores). Modo claro y oscuro obligatorios.

## Evidence on Hand

- Sentencia y documentación original en `docs/sentencia-tsjcyl/`, `docs/documentacion-relevante/`, `docs/recepcion-urbanizacion/`.
- Cronología en `docs/cronologia/`, hemeroteca en `docs/prensa/` (actualización diaria real).
- Dataset catastral real: 2.112 parcelas (1.571 refs de parcela + 541 de inmueble) en `docs/assets/js/parcelas.js`; pipeline en `catastro/`.
- Cifras reales del hero actual: sentencia de hace 10+ años, cumplimiento efectivo 0. No inventar métricas nuevas.

## Product Principles

1. Claridad antes que exhaustividad: cada sección responde una pregunta concreta del vecino.
2. Todo afirmable debe ser documentable: enlazar al documento original o al dato catastral.
3. Neutralidad informativa: informar y orientar, no representar ni asesorar.
4. Accesibilidad real: legible para lectores mayores, en móvil, con conexión modesta.
5. Sin dependencias externas evitables: estático, autoalojado, rápido.

## Accessibility & Inclusion

Audiencia con peso significativo de personas mayores: cuerpo de texto generoso, contraste AA como mínimo, foco visible, `prefers-reduced-motion` respetado. [Compromiso adoptado con la dirección «Sierra vecinal»: tipografía de cuerpo Atkinson Hyperlegible.]
