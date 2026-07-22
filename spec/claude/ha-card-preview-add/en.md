# Skill: `ha-card-preview-add`

Status: draft

## Context

`ha/lovelace-card-preview` defines the two preview surfaces of a custom Lovelace card — the card-picker gallery tile (a live preview when `preview: true` is set on the `window.customCards` entry, else `description` text) and the editor live preview (`hui-card` bound to the current config, re-rendered on `config-changed`) — plus the `preview` element property HA sets in the editor-preview context and the portfolio's preview-correctness rules (no real side-effects while previewing, a graceful placeholder over a thrown render). The scaffold (`ha-lovelace-card-scaffold`) sets `preview` and `getStubConfig` at greenfield, but existing cards regularly ship an incomplete or broken preview: `preview` missing so the picker shows only text, no `getStubConfig` so the tile renders an error card, a render that ignores later `setConfig` so the editor preview freezes, or an un-guarded `callService` that fires a real action while previewing.

This skill closes that gap: it makes an **existing** card's preview complete and correct per `ha/lovelace-card-preview` — completing the missing preview pieces and validating them — and returns a conformance report. It is the preview sibling of `ha-card-editor-add` (which owns the config editor). Quality-scale marker: custom cards are **not part of the HA quality scale**; the preview is a frontend delivery shape outside the scale.

## Scope

Ensuring the preview of exactly one existing custom card per run: the `window.customCards` `preview` flag (when a live picker preview is intended), a `getStubConfig` that returns a `setConfig`-valid config, a render deterministic from `setConfig`/`hass` for the editor live preview, reading the `preview`/`editMode` element property, guarding real service calls/actions behind that property, and a graceful placeholder over a thrown render — then offline validation. The skill reads `ha/lovelace-card-preview`, does not scaffold the card, and does not build the editor.

## Goals

- Make an existing card's card-picker preview real — `preview: true` plus a `setConfig`-valid `getStubConfig` so the tile is a live preview, not an error card or bare text
- Make the editor live preview track the config — a render deterministic from `setConfig`/`hass` that reflects each `config-changed`
- Read the `preview` (and legacy `editMode`) property to detect the editor-preview context
- Enforce preview correctness — no real service call/action/side-effect while previewing, and a graceful placeholder over a thrown render for a missing entity or incomplete config
- Honour the spec's evidence tiers — never present a `[src]`/`[policy]` rule as a documented HA fact

## Non-Goals

- Scaffolding a brand-new card — `ha-lovelace-card-scaffold`
- The graphical config editor (`getConfigElement` / `getConfigForm`) and the `getStubConfig` field detail — `ha-card-editor-add` / `ha/lovelace-card-editor`
- Card sizing / grid / layout — `ha/lovelace-layout-antipatterns`
- Theming and translations — separate axes
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "make my card show a preview in the card picker", "the card preview is broken / empty", "ensure the card preview is implemented correctly"
  - "füge eine Vorschau für die Card hinzu", "die Card-Vorschau funktioniert nicht"
- **MUST NOT** activate for scaffolding a new card (`ha-lovelace-card-scaffold`), building the config editor (`ha-card-editor-add`), or card layout/sizing (`ha/lovelace-layout-antipatterns`)

### Inputs

- **MUST** capture: `target_dir` (repo root)
- **MAY** capture: `card_file` (else discovered), `picker_preview` (default `true`), and `stub_entity` (a stable demo/representative entity or placeholder for `getStubConfig`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo and locate the card JS module; read its `window.customCards` push, `setConfig`, render, and any `getStubConfig`
- **MUST** read `ha/lovelace-card-preview` before generating and honour its `[doc]`/`[src]`/`[policy]` tiers

### Generation rules

- **MUST** set `preview: true` on the `window.customCards` entry when `picker_preview`, and keep `description` set as the fallback text
- **MUST** ensure a `getStubConfig` returns a config the card's `setConfig` accepts (a representative `stub_entity` or placeholder), so the `preview: true` tile renders without an error card
- **MUST** keep the render deterministic from `setConfig`/`hass` so the editor live preview reflects each `config-changed`; **MUST NOT** cache first-render state that ignores a later `setConfig`
- **MUST** read the `preview` element property (and the legacy `editMode` alias) to detect the editor-preview context, and **MUST NOT** assume the picker tile sets `preview`
- **MUST** guard every real service call / action / side-effect behind a `!preview && !editMode` check (`[policy]` no side-effects while previewing), and **MUST** render a graceful placeholder rather than throwing for a missing entity or incomplete config
- **MUST NOT** size the picker tile via `getCardSize`/`getGridOptions` (`[src]` the gallery tile is CSS-governed)
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the `preview` flag is present when intended; `getStubConfig` returns a `setConfig`-valid config; the `preview`/`editMode` guard wraps every side-effect; a missing-entity/incomplete config renders a placeholder, not a throw
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to the `ha/lovelace-card-preview` acceptance criteria plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**)

### Prohibitions

- **MUST NOT** scaffold a new card or build the config editor
- **MUST NOT** leave a real side-effect un-guarded so it fires while previewing
- **MUST NOT** present a `[src]`/`[policy]` rule as a documented HA fact
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] `preview: true` is set on `window.customCards` when a live picker preview is intended; `description` is kept as the fallback
- [ ] `getStubConfig` returns a config the card's `setConfig` accepts (representative entity/placeholder)
- [ ] The render is deterministic from `setConfig`/`hass`; the editor live preview reflects each `config-changed`
- [ ] The card reads the `preview` (and legacy `editMode`) property; the picker tile is not assumed to set it
- [ ] Every real service call/action is guarded so none fires while previewing; a missing-entity/incomplete config renders a placeholder, not a throw
- [ ] The report is keyed to `ha/lovelace-card-preview`, names the changed files, and marks not-part-of-the-quality-scale
- [ ] `[src]`/`[policy]` rules are not presented as documented HA facts

## Open questions

- **Static enforceability of preview correctness**: the no-side-effects rule is `[policy]`. Can the skill verify it by grepping for `callService`/action calls not guarded by a `preview`/`editMode` check, or does it need a rendered check?
- **`preview` vs. `editMode` floor**: `editMode` is a backward-compatibility alias. When can the skill emit only the `preview` read and drop `editMode` (which HA frontend floor)?
- **Editor coupling**: `getStubConfig` detail is owned by `ha-card-editor-add` / `ha/lovelace-card-editor`. When the card has no editor at all, does this skill still add `getStubConfig`, or hand off to `ha-card-editor-add`?
