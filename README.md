# claude-home-assistant

[![ci](https://github.com/nolte/claude-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/nolte/claude-home-assistant/actions/workflows/ci.yml)

Claude Code plugin that bundles skills, agents, and specifications for efficient development of [Home Assistant](https://www.home-assistant.io/) artifacts — custom integrations, Lovelace cards, blueprints / automations, and ESPHome / add-on work.

## What you get

- **Skills** — focused, on-demand workflow primitives Claude Code pulls in when relevant. Each use case has a **`*-solution` front-door skill** that plans the work and dispatches the focused authoring skills, so you describe a result and never have to pick the right primitive yourself.
- **Agents** — larger, autonomous helpers for tasks that span multiple steps (provisioning a dev HA instance, deploying and verifying an integration, authoring a blueprint, running a full pre-release review)
- **Specifications** — bilingual source-of-truth documents under `spec/` that govern every skill and agent (`spec/ha/…` for HA-internal contracts, `spec/claude/…` for the skills/agents themselves)

## Use cases

What the plugin helps you accomplish, each with its front-door skill:

- **Build a custom integration (Python)** — `ha-integration-solution`: scaffold `custom_components/<domain>/`, then augment config flow, coordinators, entity platforms, services, diagnostics, discovery, repairs, translations, and tests.
- **Build a Lovelace frontend (TS / JS)** — `ha-lovelace-solution`: custom cards, visual config editors, tile features, badges, dashboard strategies, custom panels, and their WebSocket-command backends.
- **Author automations & blueprints (YAML)** — `ha-automation-solution`: automations, scripts, helpers, derived/statistical sensors, device automations, and shareable blueprints.
- **Drive a Divoom Pixoo display** — `ha-pixoo-solution`: information pages, detailed 64×64 pixel art (shading & contours), and animations, from a described requirement.
- **Run & test on a dev HA** — agents `ha-dev-instance-provision`, `ha-integration-deploy`, `ha-integration-verify` (local Kubernetes / Kind), plus `ha-test-harness-augment` for pytest coverage.
- **Review & harden before release** — `ha-quality-scale-audit`, `ha-security-audit`, and the bundled `ha-integration-review` agent.

> ESPHome custom components and Home Assistant add-on (Docker / s6) workflows are on the roadmap; no skills ship for them yet.

A complete capability map — every use case mapped to its skills, agents, and specs — lives in the documentation: <https://nolte.github.io/claude-home-assistant/use-cases/>.

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
