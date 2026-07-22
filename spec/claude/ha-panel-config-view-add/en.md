# Skill: `ha-panel-config-view-add`

Status: draft

## Context

`ha/lovelace-panel-config-view` defines the configuration/options surface of a custom panel — the split between deploy-time `panel.config` (set once at registration, read as `panel.config`, no write-back) and runtime-editable options, the two persistence paths (a custom WebSocket command for domain/shared state, the `frontend/*_user_data` store for per-user UI preferences), the `ha-form` + `ha-selector` form composition, and admin gating that must be enforced server-side in the command handler rather than only hidden in the UI. Panels scaffolded by `ha-panel-add` render data but frequently ship no options view at all, or ship one that persists nowhere (options lost on reload), persists through the wrong channel (installation-wide config in the per-user store), or gates admin only in the frontend.

This skill closes that gap: it gives an **existing** panel a complete, correct configuration/options view per `ha/lovelace-panel-config-view` — completing the missing pieces and validating them — and returns a conformance report. It is the panel-config sibling of `ha-card-editor-add` (which owns the card config editor). Quality-scale marker: custom panels are **not part of the HA quality scale**; the config view is a frontend delivery shape outside the scale.

## Scope

Adding or completing the configuration/options view of exactly one existing custom panel per run: classifying each configurable value as deploy-time config or runtime option, composing the options form from `ha-form` + `ha-selector`, wiring a persistence path (a custom WebSocket command via `hass.callWS`, or the `frontend/*_user_data` store), and gating admin-only options in the UI plus enforcing them server-side — then offline validation. The skill reads `ha/lovelace-panel-config-view`, does not scaffold the panel, and does not define the WebSocket command.

## Goals

- Separate deploy-time `panel.config` from runtime-editable options so no runtime value needs a YAML edit + restart
- Persist domain/shared options through a custom WebSocket command (`hass.callWS`, with a matching read and, where relevant, subscribe command) and per-user UI preferences through the `frontend/*_user_data` store
- Compose the options form from reused `ha-form` + `ha-selector` selectors instead of raw inputs
- Gate admin-only options in the UI (`require_admin` / `hass.user.is_admin`) and enforce them server-side in the command handler
- Honour the spec's evidence tiers — never present a `[src]`/`[unsupported]`/`[policy]` rule as a documented HA fact

## Non-Goals

- Scaffolding a brand-new panel — `ha-panel-add`
- Defining the backend WebSocket command (decorator, schema, `async_register_command`, subscription lifecycle) — `ha-websocket-command-add` / `ha/frontend-websocket-commands`
- The card graphical config editor (`getConfigElement` / `getConfigForm` / `config-changed`) — `ha-card-editor-add` / `ha/lovelace-card-editor`
- The backend integration config/options flow (`config_flow.py`, `OptionsFlow`) — `ha/config-flow-patterns`
- Panel registration and the element property contract — `ha/lovelace-views-panels`
- Theming, translations, and deploying/importing into a running HA instance — separate axes / generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a settings view to my panel", "let users configure my panel", "persist my panel options", "add an options page to the custom panel"
  - "füge dem Panel eine Konfigurationsansicht hinzu", "das Panel soll Einstellungen speichern"
- **MUST NOT** activate for scaffolding a new panel (`ha-panel-add`), defining the WebSocket command (`ha-websocket-command-add`), the card config editor (`ha-card-editor-add`), or the backend integration options flow (`ha/config-flow-patterns`)

### Inputs

- **MUST** capture: `target_dir` (repo root)
- **MAY** capture: `panel_file` (else discovered), `options` (the fields to expose, each classified deploy-time vs runtime), `persistence` (per option group — shared WebSocket command vs per-user user-data store), and `admin_only` (which options are admin-only)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo and locate the panel JS module; read its element, `panel`/`panel.config` reads, `route` handling, and any existing options UI or `hass.callWS` usage
- **MUST** read `ha/lovelace-panel-config-view` before generating and honour its `[doc]`/`[src]`/`[unsupported]`/`[policy]` tiers

### Generation rules

- **MUST** classify each configurable value as deploy-time config (→ `panel.config`) or runtime option (→ a persistence path); **MUST NOT** leave a value the user changes at runtime behind a `configuration.yaml` edit + restart
- **MUST** read `panel.config` at runtime as `panel.config` and **MUST NOT** mutate it in the element to persist state (`[unsupported]` no documented write-back path)
- **MUST** persist domain/shared options through a custom WebSocket command called with `hass.callWS`, with a matching read (and, where relevant, subscribe) command, and **MUST NOT** invent an ad-hoc HTTP endpoint or file write for it
- **MAY** persist per-user UI preferences through the `frontend/*_user_data` store, and **MUST NOT** store installation-wide config there (it is keyed per user)
- **MUST** compose the options form from `ha-form` bound to a schema of `ha-selector` selector configs, reusing HA selectors over raw inputs
- **MUST** gate admin-only controls on `hass.user.is_admin` in the UI **and** enforce admin-only writes server-side in the command handler (`require_admin` and `hass.user.is_admin` are frontend gates only)
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: every value is classified; `panel.config` is not mutated to persist; shared options go through a WebSocket command with a read path; per-user prefs go through the user-data store; the form uses `ha-form`/selectors; admin-only writes are enforced server-side
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to the `ha/lovelace-panel-config-view` acceptance criteria plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**)

### Prohibitions

- **MUST NOT** scaffold a new panel or define the WebSocket command itself
- **MUST NOT** persist a runtime option through `panel.config` mutation or a `configuration.yaml` edit
- **MUST NOT** enforce admin-only writes in the frontend only (server-side enforcement is mandatory)
- **MUST NOT** present a `[src]`/`[unsupported]`/`[policy]` rule as a documented HA fact
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] Every configurable value is classified deploy-time `panel.config` vs runtime option; no runtime option needs a YAML edit + restart
- [ ] `panel.config` is read as `panel.config` and never mutated to persist state
- [ ] Domain/shared options persist through a custom WebSocket command (`hass.callWS`) with a matching read (and, where relevant, subscribe) command
- [ ] Per-user UI preferences persist through the `frontend/*_user_data` store and no installation-wide config is stored there
- [ ] The options form is composed from `ha-form` + `ha-selector` selectors, not raw inputs
- [ ] Admin-only options are gated in the UI and enforced server-side in the command handler
- [ ] The report is keyed to `ha/lovelace-panel-config-view`, names the changed files, and marks not-part-of-the-quality-scale
- [ ] `[src]`/`[unsupported]`/`[policy]` rules are not presented as documented HA facts

## Open questions

- **WebSocket-command coupling**: the persistence command is owned by `ha-websocket-command-add` / `ha/frontend-websocket-commands`. When the panel has no command yet, does this skill hand off to `ha-websocket-command-add` for the backend half, or scaffold a stub and delegate the definition?
- **`route` sub-route vs same-page region**: the domain spec leaves `route`-driven sub-routing as an Open Question (source-verified). Should this skill default to a same-page options region and only use `route` when the panel already routes?
- **Static enforceability of server-side admin gating**: the "enforce admin server-side" rule spans the frontend call and the backend handler. Can this skill verify the handler check, or only flag it for `ha-websocket-command-add` to enforce?
