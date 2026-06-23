# Skill: `ha-translation-sync`

Status: draft

## Context

`ha/translations` mandates: `strings.json` is the English source of truth; every `translations/<lang>.json` must mirror the key structure 1:1. Drift between the files (missing key in one language, different ordering, deleted key in one language) leads to mixed-language UI and is classified as a defect. Manual maintenance regularly forgets keys — particularly after refactors that rename or add a translation key.

This skill synchronises `strings.json` with every `translations/<lang>.json` file, fills in missing keys with `<TODO>` markers, removes orphaned keys (with user confirmation), and reports every drift.

## Scope

The skill performs **sync operations** on an existing translation structure. It does not produce new strings (that is the job of `ha-integration-scaffold`, `ha-entity-description-mapper`, `ha-service-definition-generator`, `ha-config-flow-augment`, `ha-coordinator-add`); it only ensures that whatever is already there stays consistent across languages.

## Goals

- Detect and fix structural drift between `strings.json` and `translations/<lang>.json` automatically
- Surface orphaned keys (in a translation but no longer in `strings.json`) — remove on user confirmation
- Fill in missing keys in `translations/<lang>.json` with `<TODO: translate '<EN value>'>` markers
- Report `icons.json` drift against `entity.<platform>.<key>` translation keys — an icon entry without a translation or vice versa is a bug

## Non-Goals

- Machine translation (DeepL, Google Translate) — out of scope; translations stay a user / reviewer task
- Changing string values — the skill does not touch values, only structure
- Multi-language extension (creating `translations/fr.json` from scratch) — the skill operates on existing languages; creating a new language is a user decision with a different workflow
- Translation workflow tooling (crowdin, Lokalise) — external stacks

## Requirements

### Activation triggers

- **MUST** activate on:
  - "sync the translations"
  - "check translation drift"
  - "align strings.json with translations"
  - "prüfe Translation-Drift"

### Inputs

- **MUST** collect: `target_dir` (repo root)
- **SHOULD** collect: `mode` — `report` (report only, no writes) or `apply` (perform sync); default `report`

### Pre-flight

- **MUST** check:
  1. `target_dir` is a git repo, clean (in `apply` mode; in `report` mode the repo detection suffices)
  2. `target_dir/custom_components/<domain>/strings.json` exists
  3. `target_dir/custom_components/<domain>/translations/` contains at least one `*.json` file

### Drift detection

- **MUST** check per `translations/<lang>.json` file:
  - **Missing keys**: keys present in `strings.json` but absent in `<lang>.json`
  - **Orphaned keys**: keys present in `<lang>.json` but no longer in `strings.json`
  - **Structural drift**: top-level sections (`config`, `options`, `entity`, `services`) absent in one of the languages
- **MUST** additionally check:
  - `icons.json:entity.<platform>.<key>` entries without a corresponding `strings.json:entity.<platform>.<key>.name`
  - `strings.json:entity.<platform>.<key>.name` entries without a corresponding `icons.json:entity.<platform>.<key>.default`
  - `icons.json:services.<name>` entries without a corresponding `strings.json:services.<name>.name`

### Sync operations (`apply` mode)

- **MUST** add an entry with `<TODO: translate '<EN value>'>` as placeholder for every missing key in `<lang>.json`
- **MUST** explicitly list orphaned keys before removing and obtain user confirmation — no silent delete
- **MUST** align key ordering in every `<lang>.json` with that of `strings.json` — JSON dicts are unordered in Python, but file writers typically preserve insertion order
- **MUST** report `icons.json` drift separately — `icons.json` sync is not part of this skill (separate `ha-icons-sync` skill conceivable)

### Forbidden

- **MUST NOT** overwrite existing translation values — the skill does not touch existing values; only missing keys are added
- **MUST NOT** remove orphaned keys without user confirmation
- **MUST NOT** apply machine translations — `<TODO: …>` is the only automatic action

## Acceptance Criteria

- [ ] Skill output carries the drift report with missing keys, orphaned keys, structural gaps
- [ ] Skill output carries the `icons.json` drift report (separate)
- [ ] In `apply` mode: every `translations/<lang>.json` carries every key from `strings.json` (as `<TODO>` when translation is missing)
- [ ] Orphaned keys are presented to the user before removal
- [ ] Existing translation values are unchanged after `apply`
- [ ] `pytest tests/` runs cleanly (when tests consume translation strings)

## Open Questions

- **Multi-repo sync**: When the plugin should sync translation strings of other consumer repos as well — separate spec?
- **Machine-translation pipeline**: Should an optional variant with DeepL API become accessible? Currently an explicit non-goal.
- **Language-list management**: How is a new language (for example `translations/fr.json`) added? Currently a user task; a guided variant is conceivable.
- **`icons.json` sync**: Dedicated `ha-icons-sync` skill, or does the report stay a hint?
