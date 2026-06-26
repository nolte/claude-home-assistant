# claude-home-assistant

Claude-Code-Plugin mit Skills und Agents für die effiziente Entwicklung von [Home-Assistant](https://www.home-assistant.io/)-Artefakten — Custom Integrations, Lovelace Cards, Blueprints / Automations sowie ESPHome- und Add-on-Arbeit.

## Worum es geht

Dieses Plugin liefert wiederverwendbare Bausteine, mit denen Claude Code Home-Assistant-Projekte reibungsärmer umsetzt. Du beschreibst ein **Ergebnis** — die passende `*-solution`-Front-Door-Skill plant die Arbeit und ruft die fokussierten Authoring-Skills auf.

## Anwendungsfälle

Wofür das Plugin gedacht ist, jeweils mit der Front-Door-Skill:

- **Custom Integration bauen (Python)** — `ha-integration-solution`: `custom_components/<domain>/` scaffolden und anschließend Config-Flow, Coordinators, Entity-Plattformen, Services, Diagnostics, Discovery, Repairs, Translations und Tests ergänzen.
- **Lovelace-Frontend bauen (TypeScript / JavaScript)** — `ha-lovelace-solution`: Custom Cards, visuelle Config-Editoren, Tile-Features, Badges, Dashboard-Strategien, Custom-Panels und ihre WebSocket-Command-Backends.
- **Automations & Blueprints (YAML)** — `ha-automation-solution`: Automations, Scripts, Helper, abgeleitete/statistische Sensoren, Device-Automations und teilbare Blueprints.
- **Divoom-Pixoo-Display bauen** — `ha-pixoo-solution`: Info-Pages, detaillierte 64×64-Pixel-Art (Schattierung & Konturen) und Animationen aus einer Anforderung.
- **Auf einer Dev-HA betreiben & testen** — Agents `ha-dev-instance-provision`, `ha-integration-deploy`, `ha-integration-verify` (lokales Kubernetes / Kind) plus `ha-test-harness-augment` für pytest-Abdeckung.
- **Vor dem Release prüfen & härten** — `ha-quality-scale-audit`, `ha-security-audit` und der gebündelte Agent `ha-integration-review`.

Die vollständige Übersicht — jeder Anwendungsfall auf seine Skills, Agents und Specs abgebildet — steht unter [Anwendungsfälle](use-cases.md).

!!! note "Noch nicht abgedeckt"
    ESPHome-Custom-Components und Home-Assistant-Add-ons (Docker / s6) stehen auf der Roadmap; dafür liefert das Plugin bisher keine Skills.

## Status

Aktiv in Entwicklung. Das Plugin liefert Skills und Agents über mehrere Anwendungsfälle (Integration, Lovelace, Automation, Pixoo, Dev-Lifecycle, Review). Specs werden bilingual geführt (EN kanonisch, DE als Übersetzung); jede Skill und jeder Agent ist an eine Spec unter `spec/` gebunden.
