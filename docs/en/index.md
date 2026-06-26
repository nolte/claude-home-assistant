# claude-home-assistant

Claude Code plugin with skills and agents for the efficient development of [Home Assistant](https://www.home-assistant.io/) artifacts — custom integrations, Lovelace cards, blueprints / automations, and ESPHome / add-on work.

## Overview

This plugin provides reusable building blocks that let Claude Code deliver Home Assistant projects with less friction. You describe a **result** — the matching `*-solution` front-door skill plans the work and invokes the focused authoring skills.

## Use cases

What the plugin is for, each with its front-door skill:

- **Build a custom integration (Python)** — `ha-integration-solution`: scaffold `custom_components/<domain>/`, then add config flow, coordinators, entity platforms, services, diagnostics, discovery, repairs, translations, and tests.
- **Build a Lovelace frontend (TS / JS)** — `ha-lovelace-solution`: custom cards, visual config editors, tile features, badges, dashboard strategies, custom panels, and their WebSocket-command backends.
- **Author automations & blueprints (YAML)** — `ha-automation-solution`: automations, scripts, helpers, derived/statistical sensors, device automations, and shareable blueprints.
- **Drive a Divoom Pixoo display** — `ha-pixoo-solution`: information pages, detailed 64×64 pixel art (shading & contours), and animations, from a described requirement.
- **Run & test on a dev HA** — agents `ha-dev-instance-provision`, `ha-integration-deploy`, `ha-integration-verify` (local Kubernetes / Kind) plus `ha-test-harness-augment` for pytest coverage.
- **Review & harden before release** — `ha-quality-scale-audit`, `ha-security-audit`, and the bundled `ha-integration-review` agent.

The full overview — every use case mapped to its skills, agents, and specs — is under [Use cases](use-cases.md).

!!! note "Not covered yet"
    ESPHome custom components and Home Assistant add-ons (Docker / s6) are on the roadmap; no skills ship for them yet.

## Status

Actively in development. The plugin ships skills and agents across several use cases (integration, Lovelace, automation, Pixoo, dev lifecycle, review). Specs are maintained bilingually (EN canonical, DE translation); every skill and agent is bound to a spec under `spec/`.
