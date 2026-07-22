# Skill: `ha-options-flow-augment`

Status: draft

## Context

The initial scaffold (`ha-integration-scaffold`) ships a base `OptionsFlow`, and `ha-coordinator-add` extends it with the one option it owns — the coordinator poll interval. But a real integration keeps growing post-setup settings — a toggle, a threshold, a display mode, a feature switch — and there is no skill that retrofits a *generic* option into an existing integration. That gap forces the developer back into hand-editing the options flow, where the common mistakes are: storing the option in `entry.data` instead of `entry.options`, reading it without a safe default, and forgetting to reload the entry when the option changes setup.

This skill closes that gap: it augments **one** generic config option into an existing integration's `OptionsFlow`, stored in `entry.options`, with a typed selector, `strings.json`/translation entries, the reload-on-change wiring, and a test — non-destructively. It is the options-flow sibling of `ha-config-flow-augment` (which owns setup-time config-flow patterns). Quality-scale marker: options flow is not a standalone quality-scale rule, but post-setup configurability supports the Silver/Gold user-experience bar; the skill lives outside a specific tier.

## Scope

Augmenting exactly one post-setup option per run into an existing `custom_components/<domain>/` integration: the `OptionsFlow` (created via `async_get_options_flow` when absent, else its `async_step_init` schema extended) with a typed selector for the new `option_key`, the `entry.options` storage and safe-default runtime read, the reload-on-change wiring (`entry.add_update_listener` + `async_reload`) when the option affects setup, the `options.step.init.data.<key>` strings + translations, and an options-flow test. The skill reads no setup-time `entry.data`, decides `reload_on_change`, and validates offline.

## Goals

- Retrofit one generic post-setup option without forcing the user back through the initial scaffold, and delimited from `ha-config-flow-augment` (setup patterns) and `ha-coordinator-add` (the poll-interval option)
- Store and read the option through `entry.options` with a safe default, never `entry.data`
- Use a typed selector for the option instead of a free string when a bounded type fits
- Wire the entry reload when the option affects setup, or state explicitly that a live read needs no reload
- Land code, strings, translations, and a test together — no half augment

## Non-Goals

- Greenfield scaffold and the base options flow — `ha-integration-scaffold`
- Config-flow **setup** patterns (tenant step, reauth, reconfigure, zeroconf, OAuth) — `ha-config-flow-augment`
- The coordinator **poll-interval** option specifically — `ha-coordinator-add` (owns it)
- `entry.data`/`entry.options` shape migration across a version bump — `ha-config-entry-migrate`
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add an option for X to the integration", "let the user configure X after setup", "retrofit an options flow"
  - "füge eine Option für X hinzu", "erweitere den Options-Flow"
- **MUST NOT** activate for greenfield scaffold (`ha-integration-scaffold`), setup-time config-flow patterns (`ha-config-flow-augment`), or the coordinator poll-interval option (`ha-coordinator-add`)

### Inputs

- **MUST** capture: `target_dir` (repo root), `option_key` (lowercase snake_case), `option_type` (selector/bounded type), and `default`
- **MAY** capture: `reload_on_change` (else inferred and confirmed) and a `label`

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo with a clean working tree and that `custom_components/<domain>/config_flow.py` exists; read `domain` from `manifest.json`
- **MUST NOT** proceed when `option_key` already exists in the options schema — abort with "option already present"

### Generation rules

- **MUST** store and read the option through `entry.options`, never `entry.data`; runtime reads use `entry.options.get(<key>, <default>)` with a default matching the schema
- **MUST** create `async_get_options_flow(config_entry)` returning an `OptionsFlow` when absent, else extend the existing `async_step_init` schema; use a typed selector (never a free string when a bounded type fits)
- **MUST** wire the reload-on-change when the option affects setup — `entry.async_on_unload(entry.add_update_listener(_async_update_listener))` with a listener calling `await hass.config_entries.async_reload(entry.entry_id)` — or state explicitly that a live-read option needs no reload
- **MUST** add `options.step.init.data.<key>` and `data_description.<key>` to `strings.json` and every `translations/<lang>.json`, and an options-flow test in `tests/test_config_flow.py` that sets the option and asserts it lands in `entry.options`
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the option is in `entry.options` (not `entry.data`); the selector is typed; the runtime read carries a safe default; the reload wiring is present when `reload_on_change`; strings, translations, and the test are present
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to these acceptance criteria plus the changed file paths

### Prohibitions

- **MUST NOT** augment more than one option per run, or overwrite an existing option key/value
- **MUST NOT** store the option in `entry.data`
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] The option is stored in and read from `entry.options` with a safe default; `entry.data` is untouched
- [ ] The `OptionsFlow` is created (`async_get_options_flow`) or its schema extended with a typed selector
- [ ] Reload-on-change is wired when the option affects setup, or a no-reload note is stated for a live-read option
- [ ] `strings.json` + every `translations/<lang>.json` carry `options.step.init.data.<key>` (+ `data_description`)
- [ ] An options-flow test sets the option and asserts `entry.options[<key>]`
- [ ] Report names the changed file paths; existing options stay unchanged

## Open questions

- **Multi-option batches**: a single run adds one option. When several options are added at once, is a batch mode worthwhile, or does one-per-run keep the review surface clean?
- **Reload heuristic**: `reload_on_change` is inferred and confirmed. Is there a codifiable rule for which option classes always/never need a reload?
- **Selector coverage**: the skill maps `option_type` to a selector. Which HA selectors are in the default mapping, and when does a bespoke `vol` schema win over a `selector({...})`?
