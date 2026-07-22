# Skill: `ha-config-entry-migrate`

Status: draft

## Context

A config entry stores its data under a `version` / `minor_version`. When an integration changes the shape of what it persists — renames a key, moves a value from `entry.data` to `entry.options`, adds a required default, splits a field — every entry already on a user's disk must be migrated forward when HA loads it, through `async_migrate_entry(hass, config_entry)` plus a bump of `ConfigFlow.VERSION` (breaking) or `MINOR_VERSION` (backward-compatible). No existing skill owns this: `ha-config-flow-augment` explicitly excludes destructive refactors, and the initial scaffold ships only `VERSION = 1` with no migration. The common failures are forgetting the version bump, dropping unrelated keys, not guarding by source version (so a re-run corrupts data), and not rejecting a newer-than-current entry.

This skill closes that gap: it adds or extends `async_migrate_entry` to migrate stored config entries across one schema step, with the correct version bump and a migration test — non-destructive to unrelated keys. It is the maintenance sibling of `ha-config-flow-augment`, focused on the stored-shape migration path.

## Scope

Adding or extending exactly one config-entry migration step per run in an existing `custom_components/<domain>/` integration: the `VERSION`/`MINOR_VERSION` bump on the `ConfigFlow`, the `async_migrate_entry(hass, config_entry) -> bool` function (version-guarded, rejecting a newer entry with `False`, writing the transformed `entry.data`/`entry.options` via `hass.config_entries.async_update_entry`), and a migration test. The skill reads the current version and stored shape, decides breaking vs. backward-compatible, and validates offline.

## Goals

- Own the config-entry migration path (`async_migrate_entry` + version bump) that sits between `ha-config-flow-augment` (no destructive refactors) and the scaffold
- Bump the correct version — major `VERSION` for a breaking shape change, `MINOR_VERSION` for a backward-compatible one
- Transform keys (rename / move / default / split) without dropping unrelated keys, writing back via `async_update_entry`
- Guard each step by source version so the migration is idempotent and ordered, and reject a newer-than-current entry with `False`
- Land the version bump, the migration function, and a migration test together

## Non-Goals

- Greenfield scaffold — `ha-integration-scaffold`
- Setup-time config-flow patterns (tenant / reauth / reconfigure / zeroconf / oauth) — `ha-config-flow-augment`
- Adding a new post-setup option without migrating existing entries — `ha-options-flow-augment`
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "migrate the config entry to the new schema", "I renamed a config key and need a migration", "bump the config entry version"
  - "migriere den Config-Entry auf das neue Schema", "füge eine async_migrate_entry hinzu"
- **MUST NOT** activate for greenfield scaffold (`ha-integration-scaffold`), setup-time config-flow patterns (`ha-config-flow-augment`), or adding a new option (`ha-options-flow-augment`)

### Inputs

- **MUST** capture: `target_dir` (repo root) and `change` (the schema change in prose — which keys rename / move / split / default)
- **MAY** capture: `breaking` (else inferred and confirmed) — breaking (major `VERSION`) vs. backward-compatible (`MINOR_VERSION`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo with a clean working tree and that `config_flow.py` + `__init__.py` exist; read `domain`, the current `VERSION`/`MINOR_VERSION`, and the stored `entry.data`/`entry.options` shape
- **MUST** resolve `breaking` (infer + confirm) and the concrete key transforms before generating

### Generation rules

- **MUST** bump `ConfigFlow.VERSION` for a breaking shape change and `MINOR_VERSION` for a backward-compatible one, and state which and why
- **MUST** add or extend `async_migrate_entry(hass, config_entry) -> bool` that returns `False` when `config_entry.version` is newer than the running major (a downgrade the code cannot handle)
- **MUST** transform keys explicitly (rename / move / default / split) and write them back via `hass.config_entries.async_update_entry(entry, data=…, options=…, version=…, minor_version=…)`; unrelated keys are carried over verbatim and **no** key is dropped silently
- **MUST** guard each step by source version (`if entry.version == 1: …`) so a re-run is idempotent and multi-step upgrades apply in order
- **MUST** add a migration test (`tests/test_init.py` or `tests/test_migration.py`) that seeds an old-version `MockConfigEntry`, runs setup, and asserts the entry is migrated to the new `version`/`minor_version` with the transformed keys
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the version is bumped; `async_migrate_entry` is present, version-guarded, returns `False` on a newer entry, writes via `async_update_entry`, and drops no key; the migration test is present
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to these acceptance criteria plus the changed file paths

### Prohibitions

- **MUST NOT** migrate across more than one version step per run without the intermediate guards
- **MUST NOT** drop unrelated keys or corrupt a newer-than-current entry
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] `ConfigFlow.VERSION` (breaking) or `MINOR_VERSION` (backward-compatible) is bumped, with the rationale stated
- [ ] `async_migrate_entry` is version-guarded, returns `False` on a newer entry, and writes via `async_update_entry`
- [ ] Key transforms are explicit; unrelated keys are carried over; no key is dropped silently
- [ ] A migration test seeds an old-version entry and asserts the migrated `version`/`minor_version` and transformed keys
- [ ] Report names the changed file paths

## Open questions

- **Multi-step chains**: a run migrates one version step. When an integration jumps several versions, is a guarded chain generated in one run, or one skill run per step?
- **`minor_version` support floor**: `MINOR_VERSION` exists in newer HA cores. Does the skill detect the HA version floor before using it, or assume it is available?
- **Options vs. data moves**: moving a key from `entry.data` to `entry.options` is a common migration. Is there a codifiable default for which keys belong where?
