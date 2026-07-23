---
name: ha-config-entry-migrate
description: Add or extend async_migrate_entry in an existing Home Assistant Custom Integration to migrate stored config entries across a schema change — bump ConfigFlow.VERSION (breaking) or MINOR_VERSION (backward-compatible), transform entry.data / entry.options (rename, move, default, split keys) via hass.config_entries.async_update_entry, reject a newer-than-current entry by returning False, and add a migration test. Non-destructive to unrelated keys; never drops data silently. Activate on phrasings like "migrate the config entry to the new schema", "I renamed a config key and need a migration", "bump the config entry version", "migriere den Config-Entry auf das neue Schema", "füge eine async_migrate_entry hinzu". Do not activate for greenfield scaffolding (ha-integration-scaffold), setup-time config-flow patterns (ha-config-flow-augment), adding a new option (ha-options-flow-augment), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, config-flow, migration]
phase: design
summary: "Adds or extends async_migrate_entry to migrate stored config entries across a schema change — bumping VERSION/MINOR_VERSION, transforming entry.data/options, and adding a test."
summary_de: "Ergänzt oder erweitert async_migrate_entry, um Config-Entries über einen Schema-Wechsel zu migrieren — bumpt VERSION/MINOR_VERSION, transformiert entry.data/options und fügt einen Test hinzu."
use_when:
  - "you want to migrate a config entry to a new schema"
  - "you renamed a config key and need a migration"
  - "you want to bump the config entry version"
dont_use_when:
  - situation: "You are scaffolding a brand-new integration from scratch"
    alternative: ha-integration-scaffold
  - situation: "You need a setup-time config-flow pattern, not a migration"
    alternative: ha-config-flow-augment
  - situation: "You are adding a new post-setup option, not migrating entries"
    alternative: ha-options-flow-augment
see_also:
  - ha-config-flow-augment
  - ha-options-flow-augment
  - ha-integration-scaffold
---

# HA Config Entry Migrate

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-config-entry-migrate/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-config-entry-migrate/en.md).

This skill owns the config-entry **migration** path — `async_migrate_entry` plus the `VERSION` / `MINOR_VERSION` bump — that no other skill covers. It sits between `ha-config-flow-augment` (which explicitly excludes destructive refactors) and the initial scaffold, and is the maintenance move an integration needs whenever its stored `entry.data` / `entry.options` shape changes.

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the schema change and reads back the `async_migrate_entry` body, the version bump, and the migration test; a skill keeps this on the visible command surface, like the sibling `ha-config-flow-augment`.
- **Mid-flow interactivity** — whether the change is breaking (major `VERSION`) or backward-compatible (minor `MINOR_VERSION`), and the exact key transforms, are per-run dialogues the user confirms before generation.
- **Bounded, inline generation** — one migration function plus the version bump and a test fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the breaking-vs-minor decision and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill when an existing integration's stored config-entry shape changed — a renamed key, a moved value (`data` → `options`), a new required default, a split field — and old entries on disk must be migrated forward on load.

## When NOT to activate

- greenfield integration setup → `ha-integration-scaffold`
- setup-time config-flow patterns (tenant / reauth / reconfigure / zeroconf / oauth) → `ha-config-flow-augment`
- adding a new post-setup option (no migration of existing entries) → `ha-options-flow-augment`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **One migration, one version step, one run.** Migrate to the next version; never batch several schema generations into one function without the intermediate steps.
2. **Bump the right version.** A breaking shape change bumps `ConfigFlow.VERSION` (major); a backward-compatible additive change bumps `MINOR_VERSION` (minor). State which and why.
3. **Reject a newer entry.** `async_migrate_entry` returns `False` when `config_entry.version > <current major>` (a downgrade the running code cannot handle) so HA marks the entry as migration-failed rather than corrupting it.
4. **Transform, never drop.** Rename / move / default / split keys explicitly and write them back via `hass.config_entries.async_update_entry(entry, data=new_data, options=new_options, version=…, minor_version=…)`. Unrelated keys are carried over verbatim; no key is dropped silently.
5. **Idempotent and ordered.** Guard each step by the source version (`if entry.version == 1: …`) so re-running the migration is safe and multi-step upgrades apply in order.
6. **Land the test.** Add a `tests/test_init.py` (or `tests/test_migration.py`) test that seeds an old-version `MockConfigEntry`, runs setup, and asserts the entry is migrated to the new `version`/`minor_version` with the transformed keys.
7. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the existing integration |
| `change` | yes | — | the schema change in prose (which keys rename / move / split / default) |
| `breaking` | no | inferred + confirmed | breaking (major `VERSION`) vs. backward-compatible (`MINOR_VERSION`) |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and a clean working tree.
2. `custom_components/<domain>/config_flow.py` and `__init__.py` exist; read `domain`, the current `VERSION`/`MINOR_VERSION`, and the existing `entry.data`/`entry.options` shape.
3. Resolve `breaking` (infer + confirm) and the concrete key transforms.

## Workflow

### 1) Resolve and confirm

State `domain`, the from/to version, whether it is breaking, and the exact key transforms in one paragraph. Wait for confirmation.

### 2) Apply

- `config_flow.py` — bump `VERSION` (and/or `MINOR_VERSION`) on the `ConfigFlow`
- `__init__.py` — add or extend `async def async_migrate_entry(hass, config_entry) -> bool`, version-guarded, returning `False` on a newer entry and writing the transformed entry via `async_update_entry(...)`
- `tests/test_init.py` (or `tests/test_migration.py`) — the old-entry → migrated-entry test

### 3) Validate & report

Validate offline (version bumped; `async_migrate_entry` present, version-guarded, returns `False` on a newer entry, writes via `async_update_entry`, drops no key; the migration test is present) and emit a CONFORMANT / NEEDS-WORK report keyed to the acceptance criteria, plus the changed file paths.

## Boundaries

- Setup-time config-flow patterns → `ha-config-flow-augment`
- Adding a new option without migrating existing entries → `ha-options-flow-augment`
- Reauth/reconfigure flows (not a stored-shape migration) → `ha-config-flow-augment`
