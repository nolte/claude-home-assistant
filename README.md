# claude-home-assistant

[![ci](https://github.com/nolte/claude-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/nolte/claude-home-assistant/actions/workflows/ci.yml)

Claude Code plugin that bundles skills, agents, and specifications for efficient development of [Home Assistant](https://www.home-assistant.io/) artifacts — custom integrations, Lovelace cards, blueprints / automations, and ESPHome / add-on work.

## What you get

- **Skills** — focused, on-demand workflow primitives Claude Code pulls in when relevant (config-flow scaffolding, Lovelace card boilerplate, blueprint authoring, ESPHome component patterns, …)
- **Agents** — larger, autonomous helpers for tasks that span multiple steps (e.g. wiring a new integration end-to-end, validating a card against a live HA instance)
- **Specifications** — bilingual source-of-truth documents under `spec/` that govern every skill and agent

## Scope

This plugin covers the four most common Home Assistant authoring surfaces:

- **Custom Integrations (Python)** — `custom_components/<domain>/`, config flows, coordinators, entities, tests against `pytest-homeassistant-custom-component`
- **Lovelace Cards (TypeScript / JavaScript)** — Lit-based custom cards, HACS-conformant packaging, `hass`-object usage, `card-mod` patterns
- **Blueprints & Automations (YAML)** — automation/script blueprints, Jinja templates, `packages/` layout
- **ESPHome / Add-ons** — ESPHome custom components, Home Assistant add-ons (Docker / s6)

## Quickstart

Install the plugin into Claude Code via its marketplace mechanism, or develop locally:

```bash
claude --plugin-dir .
```

Local automation runs through `Taskfile.yml`:

```bash
task lint     # pre-commit checks
task test     # placeholder until runtime tests exist
task docs     # build the MkDocs site
```

## Documentation

Full documentation lives under `docs/` and is published at <https://nolte.github.io/claude-home-assistant>.

## License

[MIT](LICENSE)
