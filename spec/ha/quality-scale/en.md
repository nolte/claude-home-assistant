# HA Integration: Quality Scale

Status: draft

## Context

The Integration Quality Scale is HA's framework that grades integrations along four axes: user experience, features, code quality, and developer experience. Grading runs through a tier system in which each level carries its own meaning and bundles a fixed set of rules.

There are four scaled tiers: 🥉 **Bronze**, 🥈 **Silver**, 🥇 **Gold**, and 🏆 **Platinum**. **Bronze** is the baseline standard and the minimum requirement for *all* new integrations — a new integration cannot be introduced without a score. To reach a tier, an integration must fulfill *all* rules of that tier **and** all tiers below it. Alongside these, the special tiers ❓ **No score** (not yet assessed / legacy state below Bronze, cannot be assigned to new integrations), 🏠 **Internal**, 💾 **Legacy**, and 📦 **Custom** exist for integrations that do not fit on the scaled list.

Declaration happens in two steps: a `quality_scale:` key in `manifest.json` names the achieved tier, and an accompanying `quality_scale.yaml` file carries the status per rule (`done`, or `exempt` with a justifying `comment`). This file documents the progress of implemented rules and the reason for exempted rules.

The other specs in this repo already carry a "quality scale marker" (for example `ha/coordinator-patterns` → **Silver**). This spec is the framework those markers refer to: it defines the tiers, the declaration artifacts, and the mapping of the key rules onto the existing repo specs that satisfy them.

## Goals

- Establish the four scaled tiers (Bronze / Silver / Gold / Platinum) and the special tiers as shared vocabulary for every integration scaffolded by the plugin
- Anchor Bronze as the binding minimum level for every newly generated integration
- Enforce the two-step declaration: `quality_scale:` in `manifest.json` plus a `quality_scale.yaml` with per-rule status (`done` / `exempt` / `todo`)
- Capture the cumulative tier semantics: a tier requires all of its own rules *and* all rules below it
- Map the key rules onto the existing repo specs that satisfy them, so quality-scale markers and requirements stay consistent
- Justify exempted rules through a documented `comment` instead of silently dropping them

## Non-Goals

- The verbatim reproduction of all 45 rules with example implementation — the canonical source remains the HA documentation; this spec links and groups instead of duplicating
- An automated rule checker (linter / `hassfest` equivalent) that validates `quality_scale.yaml` against the code — a separate follow-up spec once a tooling need becomes concrete
- Maintaining the HA checklist PR for a tier upgrade against the HA core repo — that is a contribution workflow, not a plugin artifact
- Tier assignments for integrations outside the scaled list (Internal, Legacy) — those tiers are managed by the HA project itself
- Defining the overall `manifest.json` structure beyond the `quality_scale` key — that belongs to `ha/integration-architecture`

## Requirements

### Tier targeting

- **MUST** target at least **Bronze** for every integration scaffolded by the plugin — that is the baseline standard for all new integrations
- **SHOULD** target **Silver** for every connection-based integration (one that talks to a device or cloud service over the network), since reauthentication and robust error handling then become mandatory
- **MAY** aim for **Gold** or **Platinum** when the integration provides discovery, full translatability, diagnostics, and complete typing
- **MUST NOT** ship a new integration without a score (`No score`) — new integrations cannot be assigned that tier

### Declaration

- **MUST** declare the achieved tier through a `quality_scale:` key in `manifest.json` (`bronze` / `silver` / `gold` / `platinum`)
- **MUST** keep a `quality_scale.yaml` in the integration directory that holds a status per rule under `rules:` (`done`, or `status: exempt` with `comment`)
- **MUST** provide a `comment` with the justification for every `exempt` rule — an exempted rule without justification is not allowed
- **SHOULD** mark still-open rules on the path to a higher tier as `todo` rather than omitting them from the file, so progress stays traceable
- **MUST NOT** declare a tier in `manifest.json` whose rules (including all tiers below) are not fully `done` or justifiably `exempt`

### Tier-to-spec mapping

- **MUST** satisfy the `runtime-data` rule via the spec `ha/runtime-data-pattern` (`ConfigEntry.runtime_data` for runtime data)
- **MUST** satisfy the `config-flow`, `test-before-configure`, `test-before-setup`, and `unique-config-entry` rules via the spec `ha/config-flow-patterns`
- **MUST** satisfy the `parallel-updates` rule via the specs `ha/entity-architecture` and `ha/coordinator-patterns` (`PARALLEL_UPDATES` per platform, `0` for read-only platforms when a coordinator is used)
- **MUST** satisfy the `entity-translations` and `exception-translations` rules via the spec `ha/translations`
- **MUST** satisfy the `diagnostics` rule via the spec `ha/diagnostics`
- **MUST** satisfy the `discovery` and `discovery-update-info` rules via the spec `ha/zeroconf-discovery`
- **SHOULD** check every new quality-scale marker in a sibling spec against the tiers listed here, so the marker and the actual tier do not drift apart

### Bronze mandatory rules

- **MUST** satisfy all Bronze rules: `action-setup`, `appropriate-polling`, `brands`, `common-modules`, `config-flow-test-coverage`, `config-flow`, `dependency-transparency`, `docs-actions`, `docs-high-level-description`, `docs-installation-instructions`, `docs-removal-instructions`, `entity-event-setup`, `entity-unique-id`, `has-entity-name`, `runtime-data`, `test-before-configure`, `test-before-setup`, `unique-config-entry`
- **MUST** additionally use `data_description` to contextualize the fields and correctly separate `ConfigEntry.data` from `ConfigEntry.options` for `config-flow` (subchecks of the rule)
- **MUST** set `_attr_has_entity_name = True` on every entity for `has-entity-name`, so names are composed logically from device and entity name
- **MUST** provide automated tests that guard the setup of the integration (`config-flow-test-coverage`, `test-before-setup`)

### Silver mandatory rules

- **MUST** satisfy all Silver rules: `action-exceptions`, `config-entry-unloading`, `docs-configuration-parameters`, `docs-installation-parameters`, `entity-unavailable`, `integration-owner`, `log-when-unavailable`, `parallel-updates`, `reauthentication-flow`, `test-coverage`
- **MUST** raise an exception on action failures (`action-exceptions`): `ServiceValidationError` on incorrect input, `HomeAssistantError` on an error in the action itself
- **MUST** mark devices that have gone offline as `entity-unavailable` and return cleanly on recovery without flooding the logs with repetitions (`log-when-unavailable`)
- **MUST** provide a `reauthentication-flow` that triggers automatically on auth failures (see error mapping in `ha/coordinator-patterns`)
- **MUST** carry at least one active code owner (`integration-owner`)

### Gold/Platinum outlook

- **SHOULD** extend the rules with devices and discovery for Gold: `devices`, `diagnostics`, `discovery`, `discovery-update-info`, `dynamic-devices`, `stale-devices`, `reconfiguration-flow`, `repair-issues`
- **SHOULD** establish full translatability and categorization for Gold: `entity-translations`, `exception-translations`, `icon-translations`, `entity-category`, `entity-device-class`, `entity-disabled-by-default`
- **SHOULD** complete the end-user documentation for Gold: `docs-data-update`, `docs-examples`, `docs-known-limitations`, `docs-supported-devices`, `docs-supported-functions`, `docs-troubleshooting`, `docs-use-cases`
- **MAY** demonstrate technical excellence for Platinum: `async-dependency`, `inject-websession`, `strict-typing` (fully asynchronous, fully typed, resource-efficient code base)

## Acceptance Criteria

- [ ] `quality_scale:` is declared in `manifest.json` and names one of `bronze` / `silver` / `gold` / `platinum`
- [ ] A `quality_scale.yaml` exists with a per-rule status under `rules:`
- [ ] Every `exempt` rule carries a `comment` with a justification
- [ ] All Bronze mandatory rules are `done` or justifiably `exempt`
- [ ] The `config-flow` subchecks (`data_description`, `data`/`options` separation) are satisfied
- [ ] For a target tier ≥ Silver, all Silver rules are additionally `done` or justifiably `exempt`
- [ ] The declared tier is satisfied cumulatively (all rules below as well)
- [ ] Every key rule with a sibling spec is traceable to the spec listed in the mapping
- [ ] No new integration ships with `No score`

## Open Questions

- **Target-tier policy**: Should the plugin hard-force connection-based integrations to Silver, or does Silver remain a `SHOULD` recommendation? Currently it is `SHOULD`.
- **Automatic rule verification**: How is `quality_scale.yaml` verified against the actual code? HA core uses `hassfest`; a plugin-side equivalent for custom integrations is missing.
- **Exempt justification standard**: What minimum quality must an `exempt` `comment` have? Currently only existence, not expressiveness, is enforced.
- **`quality_scale.yaml` drift**: How is the file kept from going stale after code changes (for example a `done` rule broken by a refactor)? A drift check would be a follow-up spec.
- **Marker synchronization**: Should the quality-scale marker of every sibling spec be checked automatically against tiers.json, or does that remain a manual review task?
