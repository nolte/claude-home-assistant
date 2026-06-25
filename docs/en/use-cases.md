# Use cases

This plugin bundles skills, agents, and specs along six use cases. Each case has a **front-door skill** (`*-solution`) that turns a result-oriented requirement into the minimal combination of artifacts and invokes the focused skills — you don't have to know which skill produces which artifact.

The full, auto-generated catalog with a description of every skill and agent is under [Skills](skills/index.md) and [Agents](agents/index.md).

!!! info "Front-door vs. focused skills"
    The `*-solution` skills **generate nothing themselves** — they plan (with an approval gate) and dispatch. The focused skills each own one artifact and their own spec conformance. You can also use a focused skill directly when the need is unambiguous.

---

## 1. Build a custom integration (Python)

A complete, HACS-capable custom integration under `custom_components/<domain>/` — from skeleton to advanced platform features.

- **Front door:** `ha-integration-solution`
- **Skeleton:** `ha-integration-scaffold` (manifest, lifecycle, config flow, coordinator, entity, platforms, translations, icons, diagnostics, pytest harness)
- **Add / augment:** `ha-config-flow-augment`, `ha-coordinator-add`, `ha-entity-platform-add`, `ha-entity-description-mapper`, `ha-service-definition-generator`, `ha-diagnostics-augment`, `ha-discovery-augment`, `ha-bluetooth-augment`, `ha-oauth2-credentials-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-significant-change-add`, `ha-reproduce-state-add`, `ha-integration-events-add`, `ha-conversation-agent-augment`
- **Quality:** `ha-translation-sync`, `ha-test-harness-augment`
- **Specs:** `spec/ha/integration-architecture`, `…/config-flow-patterns`, `…/coordinator-patterns`, `…/entity-architecture`, and the other `spec/ha/*` integration topics

## 2. Build a Lovelace frontend (TypeScript / JavaScript)

Custom frontend for dashboards — cards, editors, features, panels, and their backends.

- **Front door:** `ha-lovelace-solution`
- **Building blocks:** `ha-lovelace-card-scaffold` (custom card), `ha-card-editor-add` (visual config editor), `ha-card-features-add` (tile features), `ha-badge-add` (badge), `ha-strategy-add` (dashboard strategy), `ha-panel-add` (custom panel), `ha-websocket-command-add` (Python WebSocket backend)
- **Specs:** `spec/ha/lovelace-card-patterns`, `…/lovelace-card-editor`, `…/lovelace-card-features`, `…/lovelace-badges`, `…/lovelace-strategies`, `…/lovelace-views-panels`, `…/frontend-websocket-commands`

## 3. Author automations & blueprints (YAML)

Automation logic and shareable blueprints for Home Assistant.

- **Front door:** `ha-automation-solution`
- **Building blocks:** `ha-automation-author` (automation / script / scene / template entity / command artifacts), `ha-helper-scaffold` (stateful helpers), `ha-derived-sensor-author` (derived/statistical sensors), `ha-device-automation-add` (device automations), `ha-blueprint-scaffold` (→ agent `ha-blueprint-author` for the draft)
- **Specs:** `spec/ha-automation/*` (usage corpus), `spec/ha/blueprint-patterns`

## 4. Drive a Divoom Pixoo display

Turn a requirement into a suitable display on the Divoom Pixoo 64's 64×64 LED matrix.

- **Front door:** `ha-pixoo-solution`
- **Building blocks:** `ha-pixoo-page-author` (info pages: components / special pages / native pages), `ha-pixoo-pixel-art-author` (detailed pixel art with shading & contours), `ha-pixoo-animation-author` (motion & color animation)
- **Specs:** `spec/ha/divoom-pixoo` (device & integration), `spec/ha/pixoo-pixel-art` (image craft), `spec/ha/pixoo-pixel-art-animation` (animation)

## 5. Run & test on a dev HA

Deploy, inspect, and test an integration on a disposable HA instance in a local Kubernetes (Kind) cluster — separate from production.

- **Building blocks (agents):** `ha-dev-instance-provision` (provision / tear down a dev HA), `ha-integration-deploy` (roll out via `kubectl cp`, `kill 1` restart), `ha-integration-verify` (read-only pod diagnosis)
- **Skill:** `ha-test-harness-augment` (pytest coverage for secondary code paths)
- **Specs:** `spec/ha/dev-environment`, `spec/ha/dev-instance-provisioning`, `spec/ha/test-harness`

## 6. Review & harden before release

Check an integration against quality and security standards before PR / release.

- **Building blocks:** `ha-quality-scale-audit` (quality-scale tier), `ha-security-audit` (security hardening), agent `ha-integration-review` (bundled whole-picture review)
- **Specs:** `spec/ha/quality-scale`, `spec/ha/security-hardening`

---

## Not covered yet

ESPHome custom components and Home Assistant add-ons (Docker / s6) are intended use cases, but the plugin ships **no** skills for them yet. The tagline's mention of ESPHome / add-ons describes the roadmap, not the current state.

## How it fits together

- **Skills & agents** are the executing building blocks — skills run interactively in the conversation, agents autonomously with a structured report.
- **Specs** under `spec/` are the source of truth: `spec/ha/*` for HA-internal contracts (verified against the official HA docs), `spec/claude/*` for the skills/agents themselves. Every skill and agent is bound to its spec.
- **`*-solution` front doors** are the recommended entry point per use case when more than one artifact is needed.
