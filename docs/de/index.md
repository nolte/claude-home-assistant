# claude-home-assistant

Claude-Code-Plugin mit Skills und Agents für die effiziente Entwicklung von [Home-Assistant](https://www.home-assistant.io/)-Artefakten — Custom Integrations, Lovelace Cards, Blueprints / Automations sowie ESPHome- und Add-on-Arbeit.

## Worum es geht

Dieses Plugin liefert wiederverwendbare Bausteine, mit denen Claude Code Home-Assistant-Projekte mit weniger Reibung umsetzt. Abgedeckt werden die vier häufigsten Authoring-Oberflächen:

- **Custom Integrations (Python)** — `custom_components/<domain>/`, Config-Flow, Coordinators, Entities, Tests gegen `pytest-homeassistant-custom-component`.
- **Lovelace Cards (TypeScript / JavaScript)** — Lit-basierte Custom Cards, HACS-konforme Auslieferung, `hass`-Objekt, `card-mod`.
- **Blueprints & Automations (YAML)** — Automation- und Script-Blueprints, Jinja-Templates, `packages/`-Layout.
- **ESPHome / Add-ons** — ESPHome-Custom-Components und Home-Assistant-Add-ons (Docker / s6).

## Status

Frühphase. Projektstruktur und Plugin-Manifest stehen; Skills und Agents folgen iterativ. Specs werden bilingual geführt (DE kanonisch, EN als Übersetzung).
