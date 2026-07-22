# HA Integration: Lovelace Card Preview

Status: draft

## Context

A custom Lovelace card is shown in **two** preview surfaces, and getting them right is what makes a card feel finished in the dashboard:

1. The **card-picker gallery tile** — when the card registers `preview: true` on its `window.customCards` entry, the picker renders a **live instance** of the card in the tile; otherwise the tile shows only the card's `description` text.
2. The **editor live preview** — while the user edits the card (`getConfigElement` / `getConfigForm`), HA renders a live `hui-card` preview bound to the current config and re-renders it on every `config-changed` event.

Both previews render the card through its normal `setConfig` / `set hass` lifecycle; the config the picker tile renders comes from `getStubConfig`. In the **editor** preview HA additionally sets a boolean `preview` property (and, for backward compatibility, a legacy `editMode` property) on the card element, so the card can tell it is being previewed and adapt.

This spec covers the **preview behaviour specifically**. It delimits against its siblings and references them by slug rather than duplicating: the base card lifecycle (`setConfig`, `set hass`, shadow DOM, `getCardSize`/`getGridOptions`, `window.customCards` registration, `getStubConfig`) is `ha/lovelace-card-patterns`; the editor element, `getConfigElement`/`getConfigForm`, `config-changed`, and `getStubConfig` detail are `ha/lovelace-card-editor`; card sizing/layout is `ha/lovelace-layout-antipatterns`.

**Evidence tiers.** HA-internal facts must be verified against the official docs, not asserted from memory (`ha/upstream-docs-verification`). The preview surface is unusually thin in the official docs — the developer card doc mentions `preview` only as an inline `preview: false // Optional` comment and documents no card-element `preview` property and no preview-correctness rules. Each rule below is tagged:

- `[doc]` — stated in the official developer docs (`developers.home-assistant.io/docs/frontend/custom-ui/custom-card/`); quoted or paraphrased.
- `[src]` — verified against the HA frontend source (`github.com/home-assistant/frontend`) because the docs are silent; the source is the authority for the exact identifier/behaviour.
- `[policy]` — a nolte-portfolio rule (for example preview correctness); **not** an HA-documented requirement, marked as such.

Quality scale marker: custom cards are **not part of the HA quality scale**; the preview is a frontend delivery-shape concern and lives outside the scale.

## Goals

- Make the card-picker preview deliberate — `preview: true` plus a `getStubConfig` that renders a real, non-error tile — rather than leaving the tile as bare description text by default
- Make the editor live preview reliable — a render deterministic from `setConfig`/`hass` so the preview reflects the current config immediately on each `config-changed`
- Establish that the card reads the `preview` (and legacy `editMode`) property to detect the editor-preview context
- Forbid real side-effects (service calls, actions) while previewing, and require a graceful placeholder over a thrown error for an incomplete or empty-entity config — the portfolio's preview-correctness bar
- Keep HA facts and frontend-source facts and portfolio policy cleanly separated so no rule rests on an undocumented assumption presented as documented

## Non-Goals

- The base card lifecycle and `window.customCards` registration mechanics — `ha/lovelace-card-patterns`
- The editor element, `getConfigElement`/`getConfigForm`, the `config-changed` contract, and `getStubConfig` field detail — `ha/lovelace-card-editor` (this spec references them for the preview effect, not their definition)
- Card sizing and grid/layout behaviour — `ha/lovelace-layout-antipatterns` and `ha/lovelace-card-patterns`
- Theming, translations, and `getEntitySuggestion` (the Community card-suggestion mechanism) — separate axes
- Custom panels and their config/options view — a separate frontend surface

## Requirements

### Card-picker preview (`window.customCards` `preview`)

- **MUST** set `preview: true` on the card's `window.customCards` entry when the card should render a **live preview** in the card picker — `[doc]` documents the field (`preview: false // Optional - defaults to false`); `[src]` the picker maps `preview` to `showElement` and only then instantiates a real card element in the tile, otherwise it renders the `description` text (`hui-card-picker.ts`)
- **MUST** provide a `getStubConfig` (per `ha/lovelace-card-editor`) that returns a config the card's `setConfig` accepts, so the `preview: true` tile renders a real, non-error preview rather than an error card — `[src]` the picker builds the preview element's config from `getStubConfig` when no explicit config is supplied
- **SHOULD** set `description` regardless — it is the picker-tile fallback text when `preview` is `false` and the help text in the card editor `[doc]`
- **MUST NOT** rely on `getCardSize()` / `getGridOptions()` to size the **picker tile** — the gallery tile is CSS-governed, not sized by those methods; they govern the editor preview and the real dashboard, not the picker tile `[src]`

### Editor live preview & `config-changed`

- **MUST** keep the card's render deterministic from `setConfig(config)` and the `hass` setter, so the editor's live `hui-card` preview reflects the current config immediately — HA re-renders the preview whenever the editor dispatches `config-changed` `[doc]` (contract detailed in `ha/lovelace-card-editor`)
- **MUST NOT** cache first-render state in a way that ignores a later `setConfig` — the live preview replays `setConfig` as the user edits, so a config change that the card ignores makes the preview look broken `[src]`
- **SHOULD** rely on the entity-change detection from `ha/lovelace-card-patterns` so the live preview re-renders on config/state change without a blanket re-render every `hass` tick

### The `preview` element property (editor context)

- **MUST** read the boolean `preview` property HA sets on the card element to detect the **editor-preview** context — `[src]` the `hui-card` wrapper sets `element.preview` (`true` in the edit-card dialog's `<hui-card … preview>`); this property is **not** in the official docs
- **SHOULD** also honour the legacy `editMode` property, which HA sets to the same value "for backwards compatibility", when the card must run on older frontends `[src]`
- **MUST NOT** assume the **picker gallery tile** sets `preview` — `[src]` the picker path sets only `hass` on the tile element, not `preview`; only the editor preview sets it. A card that must behave specially in the picker tile therefore cannot detect that context via `preview`

### Preview correctness `[policy]`

- **MUST NOT** perform a real service call, action, or other externally-visible side-effect while `preview` (or the legacy `editMode`) is `true` — a preview must never toggle a real device, submit a form, or call a backend. `[policy]` — the HA docs impose no such rule; the `preview`/`editMode` property exists precisely so a card *can* suppress this, and the portfolio makes suppression mandatory
- **SHOULD** render representative, self-contained content in the preview — a `getStubConfig` that points at a stable demo entity (or synthesized placeholder data) so the picker tile and editor preview look meaningful even before the user picks a real entity `[policy]`
- **MUST** render a graceful placeholder (an "entity not found" / "configure me" message) rather than **throwing** when the stub or live config is incomplete or the referenced entity is missing/unavailable — a thrown render in the preview surfaces as a broken tile `[policy]`, consistent with the missing-entity handling shown in the HA example card `[doc]`

## Acceptance Criteria

- [ ] The card sets `preview: true` on its `window.customCards` entry when a live picker preview is intended (else it deliberately falls back to `description` text)
- [ ] A `getStubConfig` returns a config the card's `setConfig` accepts, so the `preview: true` tile renders without an error card
- [ ] The render is deterministic from `setConfig`/`hass`; the editor live preview reflects each `config-changed` without ignoring later `setConfig`
- [ ] The card reads the `preview` property (and, where needed, legacy `editMode`) to detect the editor-preview context
- [ ] No real service call / action / side-effect fires while `preview` (or `editMode`) is `true`
- [ ] An incomplete or missing-entity preview renders a graceful placeholder, never a thrown render
- [ ] Picker-tile sizing is not assumed to follow `getCardSize`/`getGridOptions`
- [ ] Every rule is tagged `[doc]` / `[src]` / `[policy]`; frontend-source and portfolio facts are not presented as documented HA facts
- [ ] Quality scale marker: not part of the HA quality scale (frontend delivery shape)

## Open Questions

- **Picker preview vs. editor preview divergence**: the `preview` element property is set only in the editor preview, not the picker tile (`[src]`). Should a card be able to detect "I am the picker gallery tile" at all, or is that intentionally opaque? No HA mechanism exposes it today.
- **`getStubConfig` as a hard requirement for the preview**: the "a valid `getStubConfig` is required for a non-error `preview: true` tile" rule is a source-level inference, not a documented HA rule. Is there a case where `preview: true` renders sensibly without `getStubConfig`?
- **`preview` vs. `editMode` lifetime**: `editMode` is documented as a backward-compatibility alias in the source. When can the portfolio drop the `editMode` read and rely on `preview` alone (which HA frontend floor)?
- **Preview-correctness enforceability**: the no-side-effects / representative-data rules are `[policy]` with no HA backing. Can they be checked statically (grep for `callService` guarded by a `preview`/`editMode` check), or do they need a runtime/rendered check?
- **Documentation drift**: almost the entire preview surface is source-verified, not doc-stated. If the HA docs later document the `preview` property or the picker behaviour, the `[src]` tags here should be re-checked and promoted to `[doc]`.
