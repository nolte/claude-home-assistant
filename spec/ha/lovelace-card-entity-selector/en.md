# HA Integration: Lovelace Card Entity Selector Filtering

Status: draft

## Context

A custom Lovelace card editor (`static getConfigElement()`) presents form fields for configuring the card — typically including one or more **entity selection dropdowns**. Home Assistant renders these via the `entity` selector (`ha-form` + `selector: { entity: {...} }`). Without a filter this selector lists **every** entity (or every entity of a domain) in the whole installation. On installations with hundreds of entities the choice is not only cluttered but invites **mis-selection**: the user grabs an entity that fits syntactically (`sensor.*`) but is not semantically what the card expects.

Concrete trigger from `nolte/kamerplanter-ha`: the care card expects its two fields to hold the **hub aggregate sensors** (`<domain>_tasks_due_today` / `<domain>_tasks_overdue`, recognizable by a `plants` list attribute). The unfiltered picker, however, also allowed **per-plant sensors** (pest pressure, Karenz waiting period, days-since-inspection). Those carry a single value with no `plants` attribute — the card can build no list from them and stays empty in the real dashboard, while the hard-coded editor preview still looks fine. The defect is therefore invisible until live operation.

`ha/lovelace-card-patterns` governs the card lifecycle and treats the card editor only as a minimum requirement (its non-goal: "custom card editor UIs beyond `getConfigElement`"). `ha/services` already requires an `entity` selector with an `integration` filter for `services.yaml`. This spec carries that selector discipline over to **card editors** and adds what static filters alone cannot deliver: precisely narrowing to an integration-owned entity **subtype**.

Quality-scale marker: **Bronze** (custom card editors sit outside the HA quality scale; the pattern is nolte-portfolio-specific).

## Goals

- Rule out unfiltered `entity` selectors in card editors
- Make a declarative integration base filter mandatory for every entity field
- Establish a sustainable, rename-stable way to narrow to a specific entity subtype (entity registry + `translation_key`)
- Catch mis-selection constructively: robust fallback, helper texts, defensive card render logic

## Non-Goals

- `services.yaml` selectors — governed by `ha/services`
- Config-flow selectors and Voluptuous schemas — governed by `ha/config-flow-patterns`
- General card lifecycle (`setConfig`, `set hass`, grid options) — governed by `ha/lovelace-card-patterns`
- Defining the entities themselves including `device_class` assignment — governed by `ha/entity-architecture`
- `target`, `area`, `device` and `label` selectors — a separate axis, here only as an outlook (Open Questions)

## Requirements

### Selector instead of free text

- **MUST** offer every entity field of a card editor via the `entity` selector (`ha-form` + `selector: { entity: {...} }`), never as a free text field
- **SHOULD** build the editor with `ha-form` + schema — `computeLabel` and `computeHelper` are then natively supported; hand-built picker HTML is justified only for cases the schema cannot express

### Declarative base filter

- **MUST** restrict every `entity` selector at least to the own integration: `selector: { entity: { filter: [{ integration: "<domain>", domain: "<entity-domain>" }] } }`
- **MUST NOT** rely on `domain: ["sensor"]` (or similar) alone — that admits all foreign sensors of the installation and is the primary cause of mis-selection
- Note: `filter` is an object **or a list** of criteria objects (combined with OR); permitted criteria are `integration`, `domain`, `device_class`, `supported_features`

### Precisely narrowing to the matching entity subtype

When the own integration provides several entity types of which only one fits the field, the integration base filter is not enough.

- **MUST** narrow further in this case — the base filter alone is then insufficient
- **SHOULD** filter declaratively via `device_class` / `supported_features` **when** the target entities carry a selector-supported **standard** `device_class`
- **SHOULD** otherwise — the common case for integration-owned subtypes — build `include_entities` dynamically at editor runtime from the **entity registry** (`hass.entities`), filtered by `platform === "<domain>"` **and** the target entities' stable `translation_key`:

  ```js
  // translation_key survives user renames and multiple instances,
  // unlike an entity_id string match.
  function pickByTranslationKey(hass, keys) {
    return Object.values(hass.entities)
      .filter((e) => e.platform === DOMAIN && keys.includes(e.translation_key))
      .map((e) => e.entity_id);
  }
  const ids = pickByTranslationKey(hass, ["tasks_due_today"]);
  const selector = ids.length
    ? { entity: { include_entities: ids } }
    : { entity: { filter: [{ integration: DOMAIN, domain: "sensor" }] } }; // fallback
  ```

- **MAY** filter heuristically via a stable state/attribute trait as a last resort (e.g. presence of a list attribute) when no `translation_key` applies
- **MUST NOT** derive `include_entities` from fragile `entity_id` string patterns — these break on user rename and on multiple integration instances (`_2` suffix)

### Dynamic schema

- **MUST** rebuild the editor schema per render from the current `hass` (a function, not a module constant) as soon as `include_entities` is runtime-dependent — otherwise the picker does not reflect the entity registry while entities are still loading when the editor opens

### Robust fallback

- **MUST** fall back to the declarative base filter when the dynamic candidate list is empty (entities not yet loaded, or none found)
- **MUST NOT** set `include_entities: []` in that case — an empty include makes the picker unusable and is worse than no filter at all

### Helper text, defaults and defensive card

- **MUST** give every optional or potentially ambiguous entity field a helper text (`computeHelper`) that names the expected/default sensor and warns about the typical mis-selection
- **SHOULD** carry a sensible default `entity_id` for optional entity fields; an empty field **MUST** fall back to that default
- **MUST** make the card render logic deal defensively with a missing or wrongly chosen entity — no crash, but an empty or explanatory rendering; the editor preview **MUST NOT** use hard-coded demo data to suggest a working configuration in a way that is not recognizable as a preview

## Acceptance Criteria

- [ ] No card editor uses an `entity` selector without a filter
- [ ] Every `entity` selector filters at least on `integration: "<domain>"`
- [ ] Fields with an ambiguous subtype narrow further via `translation_key`-based `include_entities` (or `device_class`)
- [ ] On an empty candidate list the selector falls back to the integration filter; never an empty picker
- [ ] Schemas with runtime-dependent `include_entities` are built per render
- [ ] Every ambiguous entity field carries a helper text with default/expectation
- [ ] A `grep` for `domain:` without an accompanying `integration`/`include_entities` filter yields no hits in card editors
- [ ] Quality-scale marker: **Bronze**

## Open Questions

- **Label filter**: the `entity` selector currently supports no `label` filter (only `integration`/`domain`/`device_class`/`supported_features`). Once HA adds it, an integration-owned label would be the cleanest declarative subtype filter — switch this spec to it then?
- **Integration filter even for unambiguous fields**: must the integration filter apply even when only a single matching type exists, or is SHOULD enough there?
- **Shared editor util**: is a common JS helper module (`pickByTranslationKey`, schema builder with fallback) across all cards of the integration worth it, instead of repeating the pattern per card?
- **Relationship to `ha/lovelace-card-patterns`**: does this spec effectively make `getConfigElement` a MUST as soon as a card has any entity fields (its currently open question "card editor mandatory depth")?
