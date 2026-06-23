---
name: ha-translation-sync
description: Detect and fix structural drift between strings.json and every translations/<lang>.json in an HA Custom Integration. Fill missing keys with TODO markers, surface orphaned keys for confirmation, and additionally report icons.json drift. Activate on phrasings like "sync the translations", "check translation drift", "align strings.json with translations", "prüfe Translation-Drift". Do not activate for machine translation, value changes, or new-language creation.
tags: [home-assistant, custom-integration, translations]
---

# HA Translation Sync

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-translation-sync/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-translation-sync/en.md).

## When this skill activates

Use this skill to align `strings.json` with every `translations/<lang>.json` file in an HA Custom Integration and to surface drift against `icons.json`.

## When NOT to activate

- machine translation → out of scope
- changing existing translation values → manual code edit
- creating a new language file from scratch → user decision; not this skill
- string content changes → covered by the producing skill (`ha-integration-scaffold`, `ha-entity-description-mapper`, …)

## Hard rules

1. **Never overwrite existing translation values.** Only missing keys are added; existing values stay untouched.
2. **Never silently delete orphaned keys.** Surface them; ask for confirmation.
3. **Never apply machine translations.** `<TODO: translate '<EN value>'>` is the only automatic placeholder.
4. **Always run `report` first.** Default mode is `report`; `apply` is opt-in.
5. **Always include `icons.json` drift.** A translation key without an icon (or vice versa) is a defect even when both files are internally consistent.

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

Print the drift report.

### 2) Confirm (only in `apply` mode)

- list orphaned keys explicitly with their current value; ask for keep / remove per language
- summarise the missing-key list with the `<TODO>` placeholder that will be inserted

### 3) Apply (only in `apply` mode)

- write each `translations/<lang>.json` with the new key set: existing values verbatim, missing keys as `<TODO: translate '<EN value>'>`, orphaned keys removed when the user agreed
- preserve key ordering identical to `strings.json`

### 4) Report

- counts of missing / orphaned / structural-gap entries per language
- counts of `icons.json` mismatches
- list of `<TODO>` placeholders the user now needs to fill in

## Boundaries

- New language file → user decision; manual init
- Machine translation → out of scope
- `icons.json` sync (auto-fill) → separate spec planned (`ha-icons-sync`)
