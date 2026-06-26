# claude-home-assistant

[![ci](https://github.com/nolte/claude-home-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/nolte/claude-home-assistant/actions/workflows/ci.yml)

Claude Code plugin that bundles skills, agents, and specifications for efficient development of [Home Assistant](https://www.home-assistant.io/) artifacts — custom integrations, Lovelace cards, blueprints / automations, and more.

## Purpose

Building Home Assistant (HA) artifacts by hand means re-deriving the same config-flow, coordinator, entity, and quality-scale patterns every time. This plugin captures those patterns as reusable, spec-governed building blocks so [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) produces HA-conformant code instead of ad-hoc boilerplate.

- You describe a **result**; a `*-solution` front-door skill — the single entry point per use case — plans the work and dispatches the focused authoring skills, so you never pick the right primitive by hand.
- HA-internal contracts (config flow, coordinators, entities, services, quality scale) are codified as specs that every skill and agent obeys.
- The intended consumers are the maintainer dogfooding here and on `kamerplanter-ha` and — as the plugin matures — the wider HA integration- and card-author community.

## What you get

- **Skills** — focused, on-demand workflow primitives Claude Code pulls in when relevant. Each use case has a `*-solution` front-door skill that plans the work and dispatches the focused authoring skills.
- **Agents** — larger, autonomous helpers for multi-step tasks (provisioning a dev HA instance, deploying and verifying an integration, authoring a blueprint, running a full pre-release review).
- **Specifications** — bilingual source-of-truth documents under `spec/` that govern every skill and agent (`spec/ha/…` for HA-internal contracts, `spec/claude/…` for the skills/agents themselves).

## Use cases

What the plugin helps you accomplish, each with its front-door skill:

- **Build a custom integration (Python)** — `ha-integration-solution`: scaffold `custom_components/<domain>/`, then augment config flow, coordinators, entity platforms, services, diagnostics, discovery, repairs, translations, and tests.
- **Build a Lovelace frontend (TypeScript / JavaScript)** — `ha-lovelace-solution`: custom cards, visual config editors, tile features, badges, dashboard strategies, custom panels, and their WebSocket-command backends.
- **Author automations & blueprints (YAML)** — `ha-automation-solution`: automations, scripts, helpers, derived/statistical sensors, device automations, and shareable blueprints.
- **Drive a Divoom Pixoo display** — `ha-pixoo-solution`: information pages, detailed 64×64 pixel art (shading & contours), and animations, from a described requirement.
- **Run & test on a dev HA** — agents `ha-dev-instance-provision`, `ha-integration-deploy`, `ha-integration-verify` (local Kubernetes / Kind), plus `ha-test-harness-augment` for pytest coverage.
- **Review & harden before release** — `ha-quality-scale-audit`, `ha-security-audit`, and the bundled `ha-integration-review` agent.

> ESPHome custom components and Home Assistant add-on (Docker / s6) workflows are on the roadmap; no skills ship for them yet.

## Usage

Install the plugin into Claude Code via its marketplace mechanism, then invoke a skill with `/claude-home-assistant:<skill>` (for example `/claude-home-assistant:ha-integration-solution`).

### Work on the plugin itself (dogfooding)

Dogfooding means using the plugin to develop itself. Launch Claude Code with this repository loaded as a plugin:

```bash
claude --plugin-dir .
```

Use `/reload-plugins` inside the session to pick up changes without restarting. Local automation runs through `Taskfile.yml`:

```bash
task lint     # pre-commit checks
task test     # placeholder until runtime tests exist
task docs     # build the MkDocs site
```

## Documentation

Full documentation is published at <https://nolte.github.io/claude-home-assistant>. A complete capability map — every use case mapped to its skills, agents, and specs — lives under [Use cases](https://nolte.github.io/claude-home-assistant/use-cases/).

## Structure

```text
.claude-plugin/       # plugin.json + marketplace.json manifests
skills/<name>/        # one skill per folder (SKILL.md)
agents/<name>.md      # reusable sub-agents
spec/                 # bilingual specs (English canonical, German translation)
docs/                 # MkDocs source for the published site
Taskfile.yml          # lint / test / docs automation
```

## Related repositories

- [nolte/claude-shared](https://github.com/nolte/claude-shared) — hub plugin; shared skills/agents and the portfolio specs inherited by this repo
- [nolte/gh-plumbing](https://github.com/nolte/gh-plumbing) — reusable GitHub Actions workflows and commons repository settings
- [nolte/taskfiles](https://github.com/nolte/taskfiles) — shared Taskfile includes consumed by `Taskfile.yml`
- [nolte/kamerplanter-ha](https://github.com/nolte/kamerplanter-ha) — reference HA integration the `spec/ha/` patterns are distilled from

## Status

Actively developed. Ships skills and agents across the integration, Lovelace, automation, Pixoo, dev-lifecycle, and review use cases; specs are bilingual (English canonical, German translation). ESPHome / add-on coverage is on the roadmap.

## License

[MIT](LICENSE) — Copyright © 2026 nolte
