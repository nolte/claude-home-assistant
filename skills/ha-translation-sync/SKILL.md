---
name: ha-translation-sync
description: Detects and fixes structural drift between strings.json and every translations/<lang>.json in an HA Custom Integration. Fill missing keys with TODO markers, surface orphaned keys for confirmation, and additionally report icons.json drift. Activate on phrasings like "sync the translations", "check translation drift", "align strings.json with translations", "prüfe Translation-Drift". Do not activate for machine translation, value changes, or new-language creation.
tags: [home-assistant, custom-integration, translations]
phase: cross-cutting
summary: "Detects and fixes structural drift between strings.json and every translations/<lang>.json in an HA Custom Integration, and reports icons.json drift."
summary_de: "Erkennt und behebt strukturellen Drift zwischen strings.json und jeder translations/<lang>.json einer HA-Custom-Integration und meldet icons.json-Drift."
use_when:
  - "you want to sync an integration's translations"
  - "you want to check for translation drift"
  - "you want to align strings.json with the translation files"
dont_use_when:
  - situation: "You need to change actual string content, not sync structure"
    alternative: ha-integration-scaffold
  - situation: "Entity string content changed and needs re-mapping"
    alternative: ha-entity-description-map
see_also:
  - ha-integration-scaffold
  - ha-entity-description-map
  - ha-service-definition-add
  - ha-integration-solution
---

# HA Translation Sync

Spec: `spec/claude/ha-translation-sync/en.md` (EN canonical) / `spec/claude/ha-translation-sync/de.md` (DE translation).

## Why this is a skill, not an agent

- **Confirm-before-delete gate (decisive):** orphaned keys are surfaced for operator confirmation before removal — a mid-flow approval an agent's fire-and-forget shape would lose.
- **Quick, targeted change:** structural drift fixes touch strings.json and the translation files of the integration in scope; main-conversation territory per the change-scope dimension.
- **Counter-dimension considered:** drift detection is mechanical and self-contained (agent bias), but detection without the interactive disposition step is only half the contract — the gate outweighs isolation.

## When this skill activates

Use this skill to align `strings.json` with every `translations/<lang>.json` file in an HA Custom Integration and to surface drift against `icons.json`.

## When NOT to activate

- machine translation → out of scope
- changing existing translation values → manual edit (no owning skill; `ha-entity-description-map` when entity strings need re-mapping)
- creating a new language file from scratch → user decision; not this skill
- string content changes → covered by the producing skill (`ha-integration-scaffold`, `ha-entity-description-map`, …)

## Hard rules

1. **Never overwrite existing translation values.** Only missing keys are added; existing values stay untouched.
2. **Never silently delete orphaned keys.** Surface them; ask for confirmation.
3. **Never apply machine translations.** `<TODO: translate '<EN value>'>` is the only automatic placeholder.
4. **Always run `report` first.** Default mode is `report`; `apply` is opt-in.
5. **Always include `icons.json` drift — and fill it.** A translation key without an icon (or vice versa) is a defect even when both files are internally consistent; in `apply` mode, fill a missing `icons.json` entry with a `<TODO: icon>` marker via the same mechanism as `strings.json`, rather than only reporting it.
6. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see `spec/ha/upstream-docs-verification/en.md`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `mode` | no | `report` | `report` or `apply` |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` (and clean working tree in `apply` mode)
2. Read `domain` from `manifest.json`
3. `<target_dir>/custom_components/<domain>/strings.json` exists
4. `<target_dir>/custom_components/<domain>/translations/` carries at least one `*.json` file

## Workflow

### 1) Detect

For each `translations/<lang>.json`:

- compare key trees against `strings.json`
- list missing keys, orphaned keys, structural gaps

For `icons.json` vs. `strings.json`:

- list `entity.<platform>.<key>` mismatches
- list `services.<name>` mismatches

For `strings.json` config-flow completeness:

- flag config-flow steps whose `data` fields lack a matching `data_description` entry (a Bronze config-flow subcheck)

Print the drift report.

### 2) Confirm (only in `apply` mode)

- list orphaned keys explicitly with their current value; ask for keep / remove per language
- summarise the missing-key list with the `<TODO>` placeholder that will be inserted

### 3) Apply (only in `apply` mode)

- write each `translations/<lang>.json` with the new key set: existing values verbatim, missing keys as `<TODO: translate '<EN value>'>`, orphaned keys removed when the user agreed
- preserve key ordering identical to `strings.json`

### 4) Report

- counts of missing / orphaned / structural-gap entries per language
- counts of `icons.json` mismatches (and `<TODO: icon>` markers filled in `apply` mode)
- count of config-flow fields missing a `data_description` entry
- list of `<TODO>` placeholders the user now needs to fill in

## Boundaries

- New language file → user decision; manual init
- Machine translation → out of scope
- Icon-name choice / value localization (icon names are not translated) → out of scope; structural `icons.json` drift and TODO-fill of missing keys are handled by this skill
