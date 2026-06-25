---
name: ha-strategy-add
description: Augment an existing Home Assistant frontend module with one custom Lovelace strategy — a dashboard strategy or a view strategy — conforming to spec/ha/lovelace-strategies. Creates the strategy class with the static async generate(config, hass) returning the kind-correct shape (a dashboard strategy returns { views: [...] }, a view strategy returns { cards: [...] } and never a views array), the customElements.define("ll-strategy-dashboard-<id>"/"ll-strategy-view-<id>", …) registration, the dashboard-resource loading, the strategy.type custom:<id> reference, hass.callWS registry access with Promise.all, optional getConfigElement/getCreateSuggestions, and — for dashboard strategies — the window.customStrategies push for the community-dashboard dialog. Activate on "add a dashboard strategy", "auto-generate views with a strategy", "create a custom Lovelace strategy", "füge eine Strategy hinzu". Do not activate for a static card (ha-lovelace-card-scaffold), custom view-layout elements or panels (ha/lovelace-views-panels), badges (ha/lovelace-badges), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, lovelace]
---

# HA Strategy Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-strategy-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-strategy-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the generation intent and reads back the strategy class, the registration, and the conformance report; a skill keeps this on the visible command surface, like the sibling frontend skill `ha-lovelace-card-scaffold`.
- **Mid-flow interactivity** — the dashboard-vs-view decision and the registry-access / community-dashboard choices are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one strategy class plus its registration, resource entry, and optional config element fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the kind decision and the resource-wiring advice belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** custom Lovelace strategy — a dashboard strategy (`generate → { views }`) or a view strategy (`generate → { cards }`) — to an existing frontend module, when the user wants a dashboard or view **generated programmatically** rather than declared statically.

## When NOT to activate

- a static custom card (one card, no generator) → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- custom view-layout elements or full-takeover panels → `ha/lovelace-views-panels`
- custom badges → `ha/lovelace-badges`
- the frontend data-API pattern in detail → `ha/frontend-data-api`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One strategy, one run.** No multi-strategy batches; a dashboard strategy and the view strategy it delegates to are two runs.
2. **Read [`ha/lovelace-strategies`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-strategies/de.md) first.** Do not generate from memory.
3. **`generate` contract.** `static async generate(config, hass)` is static and async; a dashboard strategy returns `{ views: [...] }`, a view strategy returns `{ cards: [...] }`. A view strategy **never** returns a `views` array.
4. **Derive the full structure from `config`, with defaults.** Expand the small strategy `config` into the full structure and guard values with defaults (e.g. `const title = config.title || "…"`) so the strategy renders without a complete config.
5. **Register with the correct prefix and load as a resource.** `customElements.define("ll-strategy-dashboard-<id>", …)` (dashboard) or `ll-strategy-view-<id>` (view); load the strategy as a dashboard resource (module). Reference it via `strategy.type: custom:<id>` — `<id>` without the `ll-strategy-…` prefix. Without a loaded resource the strategy is not resolvable.
6. **Registry access via `hass.callWS`, parallelised.** When generation needs areas/devices/entities, query `config/area_registry/list` / `config/device_registry/list` / `config/entity_registry/list` via `hass.callWS(...)`; parallelise independent queries with `Promise.all([...])`. Keep generation deterministic and fast — it blocks the initial dashboard rendering.
7. **Graphical config, when present.** `static getConfigElement()` returns an element implementing `setConfig(config)` and emitting a `config-changed` custom event (`bubbles: true, composed: true, detail: { config: newConfig }`); set `configRequired = true` when the strategy needs config, otherwise `noEditor = true`.
8. **Community dashboard, when a dashboard strategy.** A `window.customStrategies.push({...})` carries `type` (without `custom:`) and `strategyType: "dashboard"` (both required); `name`/`description`/`documentationURL` and `static getCreateSuggestions(hass)` (default `title`/`icon`) are optional.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; an existing frontend module (e.g. `custom_components/<domain>/manifest.json`) |
| `intent` | yes | — | the generation intent (what dashboard/view to generate), in prose |
| `kind` | no | inferred + confirmed | `dashboard` / `view` |
| `id` | no | derived | the strategy `<id>` (registration suffix + `custom:<id>` reference) |
| `registry_data` | no | asked when needed | which of areas/devices/entities generation needs |
| `config_element` | no | asked when needed | whether a graphical `getConfigElement` is provided |
| `community_dashboard` | no | asked (dashboard only) | whether to push to `window.customStrategies` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir` is an existing frontend module (e.g. `custom_components/<domain>/manifest.json` exists; read `domain` if present).
2. Resolve `kind` (infer + confirm): a dashboard strategy generates the view list; a view strategy generates the cards of a single view.
3. Read `ha/lovelace-strategies`.
4. The strategy / `<id>` / `customElements.define` registration is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain` (if any), the resolved `kind`, the `<id>`, which registry data generation needs, whether a config element and (for dashboard strategies) a `window.customStrategies` push are wanted, in one paragraph. Wait for confirmation.

### 2) Generate

| Kind | Element tag | `generate` returns | Community dialog |
|---|---|---|---|
| dashboard | `ll-strategy-dashboard-<id>` | `{ views: [...] }` | `window.customStrategies` push (`type` + `strategyType: "dashboard"`) |
| view | `ll-strategy-view-<id>` | `{ cards: [...] }` (never `views`) | n/a |

Wire the `customElements.define` registration and the dashboard-resource loading (e.g. a `StaticPathConfig` entry in `__init__.py`); document the `strategy.type: custom:<id>` reference. Add `hass.callWS` registry access with `Promise.all` only when generation needs it. Add `getConfigElement` (+ `setConfig` + `config-changed`) and `getCreateSuggestions` only when wanted.

### 3) Validate and report

Validate offline (`generate` is static + async and returns the kind-correct shape; a view strategy returns no `views`; the `customElements.define` prefix is correct; the strategy is loaded as a dashboard resource; `strategy.type: custom:<id>` is documented; registry access runs via `hass.callWS` with `Promise.all`; a present config element supplies `setConfig` + `config-changed`; a present `window.customStrategies` push carries `type` + `strategyType: "dashboard"`). Emit a CONFORMANT / NEEDS-WORK report keyed to the `ha/lovelace-strategies` acceptance criteria, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**, portfolio-specific).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- A static custom card → `ha-lovelace-card-scaffold`
- Custom view-layout elements or panels → `ha/lovelace-views-panels`
- Custom badges → `ha/lovelace-badges`
- Frontend data-API detail → `ha/frontend-data-api`
- Deploy to live HA → out of scope
