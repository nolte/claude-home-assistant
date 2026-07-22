---
name: ha-options-flow-augment
description: Augment an existing Home Assistant Custom Integration with one generic config option retrofitted into its OptionsFlow — a post-setup setting stored in entry.options (never entry.data), with a typed selector, strings + translations, an entry-reload-on-change wiring, and a test. Non-destructive: existing options stay untouched. Activate on "add an option for X to the integration", "let the user configure the poll behaviour / a threshold / a toggle after setup", "retrofit an options flow", "füge eine Option für X hinzu", "erweitere den Options-Flow". Do not activate for greenfield scaffolding (ha-integration-scaffold, which ships the base options flow), config-flow setup patterns like tenant/reauth/reconfigure/zeroconf/oauth (ha-config-flow-augment), the coordinator poll-interval option specifically (ha-coordinator-add owns it), config-entry data migration (ha-config-entry-migrate), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, config-flow, options]
---

# HA Options Flow Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-options-flow-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-options-flow-augment/en.md).

This skill retrofits **one** generic, post-setup config **option** into an existing integration's `OptionsFlow` — the piece the initial scaffold's options flow cannot cover generically and that no other skill owns (the coordinator poll-interval is the one exception, owned by `ha-coordinator-add`).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes an option and reads back the `OptionsFlow` change, the `strings.json`/translation entries, and the reload wiring; a skill keeps this on the visible command surface, like the sibling `ha-config-flow-augment`.
- **Mid-flow interactivity** — the option key, its selector, its default, and whether a change must reload the entry are per-run dialogues the user confirms before generation.
- **Bounded, inline generation** — one option plus its schema, strings, and test fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the selector/default decisions and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** post-setup option to an existing integration — a toggle, a threshold, a mode, a display preference — surfaced through the integration's `OptionsFlow` and read from `entry.options` at runtime.

## When NOT to activate

- greenfield integration setup (the base options flow is scaffolded there) → `ha-integration-scaffold`
- config-flow **setup** patterns (tenant step, reauth, reconfigure, zeroconf, OAuth) → `ha-config-flow-augment`
- the coordinator **poll-interval** option specifically → `ha-coordinator-add` (owns it)
- migrating `entry.data`/`entry.options` shape across a version bump → `ha-config-entry-migrate`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **One option, one run.** No multi-option batches; never rewrite existing options.
2. **Additive only.** If the option key already exists in the `OptionsFlow` schema, abort with "option already present". Existing option keys and values stay untouched.
3. **`entry.options`, never `entry.data`.** The option is stored in and read from `entry.options` (post-setup config); `entry.data` is setup-time data and is not touched.
4. **Create or extend the `OptionsFlow`.** Add `async_get_options_flow(config_entry)` returning an `OptionsFlow` when absent; otherwise extend the existing `async_step_init` schema with the new key. Use a typed selector (`selector({...})` / `vol` with a bounded type), never a free string when a bounded type fits.
5. **Read with a safe default.** Runtime reads use `entry.options.get(<key>, <default>)`; the default matches the one advertised in the schema so a not-yet-set option behaves deterministically.
6. **Wire the reload-on-change.** When the option affects setup (coordinator interval, entity set, connection), register `entry.async_on_unload(entry.add_update_listener(_async_update_listener))` with an `_async_update_listener` that calls `await hass.config_entries.async_reload(entry.entry_id)`; when it is read live on every use, state explicitly that no reload is needed.
7. **Strings, translations, and a test land together.** Add `options.step.init.data.<key>` (+ `data_description`) to `strings.json` and every `translations/<lang>.json`, and a `tests/test_config_flow.py` options-flow test (set the option, assert it lands in `entry.options`).
8. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the existing integration |
| `option_key` | yes | — | lowercase snake_case key stored in `entry.options` |
| `option_type` | yes | — | selector/type (`bool`, `int` min/max/step, `select` options, `str`, …) |
| `default` | yes | — | default when the option is not set |
| `reload_on_change` | no | inferred + confirmed | whether changing the option reloads the entry |
| `label` | no | derived | English option label for `strings.json` |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and a clean working tree.
2. `custom_components/<domain>/config_flow.py` exists; read `domain` from `manifest.json`.
3. The `option_key` is not already in the options schema (else abort "option already present").

## Workflow

### 1) Resolve and confirm

State `domain`, the `option_key`, its selector/default, whether it reloads the entry, and every assumed default in one paragraph. Wait for confirmation.

### 2) Apply

- `config_flow.py` — create/extend `async_get_options_flow` + the `OptionsFlow` `async_step_init` schema with the typed selector; add the update listener when `reload_on_change`
- `__init__.py` — register `entry.add_update_listener` via `entry.async_on_unload(...)` when `reload_on_change` (and the runtime read of `entry.options.get(<key>, <default>)`)
- `strings.json` + every `translations/<lang>.json` — `options.step.init.data.<key>` and `data_description.<key>`
- `tests/test_config_flow.py` — an options-flow test that sets the option and asserts `entry.options[<key>]`

### 3) Validate & report

Validate offline (option in `entry.options` not `entry.data`; typed selector; safe-default read; reload wiring present when `reload_on_change`; strings/translations/test present) and emit a CONFORMANT / NEEDS-WORK report keyed to the acceptance criteria, plus the changed file paths and the quality-scale marker (**not a standalone quality-scale rule; supports Silver/Gold configurability**).

## Boundaries

- Config-flow setup patterns (tenant/reauth/reconfigure/zeroconf/oauth) → `ha-config-flow-augment`
- Coordinator poll-interval option → `ha-coordinator-add`
- `entry.data`/`entry.options` shape migration across a version bump → `ha-config-entry-migrate`
