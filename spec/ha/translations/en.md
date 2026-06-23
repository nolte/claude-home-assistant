# HA Integration: Translations

Status: draft

## Context

A Custom Integration translates two classes of strings: **config-flow strings** (step titles, field labels, error messages, abort reasons) and **entity / service strings** (display names, state translations, service descriptions). HA prescribes the format: a `strings.json` as the canonical source (English by convention) and `translations/<lang>.json` files per shipped language. Translation keys are hierarchical so HA can resolve targeted lookups (`entity.sensor.<key>.name`, `config.error.<key>`, `services.<name>.fields.<field>.name`).

`nolte/kamerplanter-ha` validates this schema with English (`strings.json` + `translations/en.json`) and German (`translations/de.json`) and codifies two non-obvious rules in `spec/style-guides/HA-INTEGRATION.md`: (1) **English as the HA system language** is required for stable `entity_id` slugs — the slug is built from the system-language display name and frozen at first registration; a German system-language slug breaks on later language switch; (2) `state:` maps under `entity.<platform>.<translation_key>.state.<value>` translate enum state values (for example phase stages) instead of rendering raw strings in the UI.

This spec lifts the convention into a generic obligation. Icons (`icons.json`) live in the parallel `ha/icons` spec.

Quality scale marker: **Bronze** (`strings.json` with an English source is a Bronze requirement; multi-language `translations/<lang>.json` per shipped language extends Bronze conformance without being formally Silver).

## Goals

- Make English the canonical source in `strings.json` — HA system language `en` is the precondition for stable, language-independent `entity_id` slugs
- Enforce hierarchical translation keys per HA convention so skills can generate against the schema deterministically
- Make the sync between `strings.json` and every `translations/<lang>.json` mandatory — structural drift (missing key in one language, different ordering) is caught via drift check
- Establish `state:` maps for enum sensors as the default pattern, instead of pushing raw backend strings to the frontend

## Non-Goals

- Translation engine itself (HA translates at runtime; the plugin only ships the strings) — not in this spec
- Translation workflow / tooling (for example crowdin, Lokalise) — tool choice; skills generate raw JSON files
- Icons — separate `ha/icons` spec
- Service-translation completeness depth (all fields vs. just top-level) — owned by `ha/services`; this spec only defines the format
- End-user language picker — that lives in the HA frontend UI, not the plugin

## Requirements

### `strings.json` as canonical source

- **MUST** include a `strings.json` in `custom_components/<domain>/` — it is the English source of truth for every translation key
- **MUST** carry English strings as values — HA implicitly demands that because it falls back to `strings.json` when a `translations/<lang>.json` is missing or lacks a key
- **MUST NOT** put localised strings (German, French, …) directly into `strings.json` — they belong in `translations/<lang>.json`

### `translations/<lang>.json` files

- **MUST** include a `translations/<lang>.json` for every shipped language (typically at least `en` and `de` in the nolte portfolio) that mirrors `strings.json` keys 1:1 with translated values
- **MUST** carry every key from `strings.json` in every `translations/<lang>.json` — missing keys lead to mixed-language UI (English fallback strings in the middle of the German UI)
- **SHOULD** ship `translations/en.json` in addition to `strings.json`, even when the values are identical — some HA versions read from `translations/en.json` explicitly instead of falling back to `strings.json`
- **MUST NOT** ship a `translations/<lang>.json` with only a subset of keys — the schema is all-or-nothing per language

### Translation-key schema

The key tree is dictated by HA. Skill output must support these top-level sections:

- **`config`** — config-flow strings:
  - `config.flow_title` — the title at the top of the config flow (typically `<Integration> ({url})` or similar)
  - `config.step.<step_id>.title` — the title per step (`user`, `reauth_confirm`, `reconfigure`, `tenant`, …)
  - `config.step.<step_id>.description` — optional explanatory description
  - `config.step.<step_id>.data.<field>` — field label per form field
  - `config.error.<key>` — error strings raised by the flow in the `errors` dict (`cannot_connect`, `invalid_auth`, …)
  - `config.abort.<key>` — abort reasons (`already_configured`, `reauth_successful`, …)
- **`options`** — options-flow strings (parallel to `config.step.*` but under `options.step.<step_id>`)
- **`entity`** — entity display names, grouped per platform:
  - `entity.<platform>.<translation_key>.name` — the display name resolved from `_attr_translation_key`
  - `entity.<platform>.<translation_key>.state.<value>` — translation of enum states (see next section)
- **`services`** — service strings:
  - `services.<service>.name` — service display name
  - `services.<service>.description` — service description
  - `services.<service>.fields.<field>.name` — field display name per service field
  - `services.<service>.fields.<field>.description` — field description

- **MUST** carry every key in `strings.json` along this exact hierarchical path — flat keys or restructured hierarchies are not resolved by HA
- **MUST** keep keys lowercase and snake_case — HA convention; mixed casing is not allowed
- **MUST NOT** carry format strings with `{var}` placeholders in HTML; keep them plain text — HA renders translations as text, no markup

### Enum-state translation

- **SHOULD** include a `state:` map under `entity.<platform>.<translation_key>.state.<value>` for sensors with enum state (status values from a fixed set — for example phase stages, modes, device states), so the UI renders translated labels instead of raw backend strings
- **MUST** cover every possible `state.<value>` the sensor can return — missing values are rendered as raw strings by HA
- **MUST** add new backend values to `state.<value>` in `strings.json` and every `translations/<lang>.json` when they appear — otherwise silent gaps in the UI
- **MAY** omit the `state:` block for sensors with `device_class` (for example `device_class: enum` with declared `options:`) when HA's default translations suffice — they often do not

### Language convention

- **MUST** ensure that `strings.json` is written in English — the HA system-language default is `en`, and the `entity_id` slug is built from the system-language display name at first registration
- **MUST NOT** make `entity_id` stability dependent on the consumer installation's HA system language — a German system language produces German slugs (`sensor.tomate_1_tage_bis_giessen`) that become unstable on language switch or re-registry
- **SHOULD** document in consumer docs (for example the README) that HA should be run with `language: en` when the user wants to operate in German or another language — the end-user UI stays German (via the personal profile language); only the `entity_id` slug stays English

### Sync strategy

- **MUST** synchronously update every `translations/<lang>.json` on every change to `strings.json` (new key, changed English value, deleted key) — structural drift is a defect
- **SHOULD** have a drift-check mechanism (for example a CI job that diffs the key trees) — a concrete mechanism is a skill job, not a spec job
- **MUST NOT** auto-generate `translations/<lang>.json` values without review — machine translation produces literal mistranslations; every change should be reviewable

## Acceptance Criteria

- [ ] `custom_components/<domain>/strings.json` exists and carries English strings
- [ ] `custom_components/<domain>/translations/en.json` exists (even when values are identical to `strings.json`)
- [ ] For every additionally shipped language `custom_components/<domain>/translations/<lang>.json` exists
- [ ] Every `translations/<lang>.json` mirrors `strings.json`'s key structure 1:1
- [ ] Top-level sections are limited to `config`, `options`, `entity`, `services` (plus optional `selector` if skill sets supplement them)
- [ ] All keys are `snake_case`, lowercase
- [ ] Sensors with enum state include a `state:` block covering every possible backend value
- [ ] A `grep` for `_attr_name = "<hard-coded-string>"` in the platform modules returns no hits (see `ha/entity-architecture`)
- [ ] Quality scale marker: **Bronze**

## Open Questions

- **Drift-check mechanism**: Which concrete CI job or skill checks key parity between `strings.json` and every `translations/<lang>.json`? Currently formulated as "should exist".
- **Required language list**: Which languages does the plugin ship by default? `en` is mandatory; `de` is standard in the nolte portfolio. Should the spec require an additional language list (French, Spanish, …) or stay open per integration?
- **`selector` translations**: HA has additional selector translation keys (`selector.<key>.options.<value>`) for `select:` selectors with value lists. Should the spec list this section explicitly as a required area or keep it as MAY because it only applies to specific selector types?
- **Raw-English backend values**: When the backend already returns English strings (for example `"germination"`), should they be carried verbatim in the `state:` block, or should the integration capitalise / format them additionally?
- **HA system-language lockdown**: Should the skill-output README explicitly require `configuration.yaml: language: en`? Currently formulated as SHOULD in consumer docs; a "MUST" is conceivable but reaches into user configuration.
