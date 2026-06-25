# Skill: `ha-media-source-add`

Status: draft

## Context

`ha/media-source` defines the media source platform: an integration exposes browsable and playable media to the media browser by adding a `media_source.py` file in its integration directory. HA discovers the module automatically via the integration platform mechanism — no change to `manifest.json` is needed. The module exports the top-level async function `async_get_media_source(hass) -> MediaSource`, returning an instance of a `MediaSource` subclass. That subclass implements two mandatory methods: `async_browse_media(item)` returns a `BrowseMediaSource` tree, `async_resolve_media(item)` returns a `PlayMedia(url, mime_type)`. No skill augments this so far.

This skill augments a media source into an **existing** integration: the `media_source.py` module, the `async_get_media_source(hass)` function, the `MediaSource` subclass with `async_browse_media`/`async_resolve_media`, the correctly set `MediaClass` and `can_play`/`can_expand` fields per `BrowseMediaSource` node, URI construction via `generate_media_source_id`, and the translatable `Unresolvable`/`BrowseError` exceptions — conformant to `ha/media-source`.

## Scope

Augmenting exactly one media source per run into an existing `custom_components/<domain>/` integration: the `media_source.py` file, the `async_get_media_source(hass)` function, the `MediaSource` subclass, the two methods `async_browse_media(item)` and `async_resolve_media(item)`, the `MediaClass` and `can_play`/`can_expand` fields, the `identifier`/URI construction, and the translatable error exceptions. The skill reads `ha/media-source` and validates.

## Goals

- Augment a spec-conformant `media_source.py` from a described media hierarchy
- Enforce the top-level contract: `async_get_media_source(hass) -> MediaSource` exports a `MediaSource` subclass initialized via `super().__init__(DOMAIN)`
- Enforce the two mandatory methods as the binding interface: `async_browse_media(item)` returns a `BrowseMediaSource` tree (root when `identifier` is empty, otherwise children), `async_resolve_media(item)` returns a `PlayMedia(url, mime_type)`
- Enforce an appropriate `MediaClass` per browse node and correctly set `can_play`/`can_expand` flags; construct URIs via `generate_media_source_id`
- Wire up the translatable `Unresolvable`/`BrowseError` error paths

## Non-Goals

- The media player entity side that consumes media sources (`async_browse_media(hass, ...)` call path) — `ha/entity-architecture` / `ha/entity-platforms-media`
- Translation mechanics for `Unresolvable`/`BrowseError` in detail — `ha/translations`
- Thumbnail proxy and streaming endpoints (`/api/...` routes) — a separate HA mechanism, not covered by this platform
- Greenfield scaffolding of an integration — `ha-integration-scaffold`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a media source", "let users browse my media in the media browser", "expose a browsable media library"
  - "resolve my items to a playable URL in the media browser"
  - "füge eine Media-Source hinzu", "lass den User meine Medien im Media-Browser durchsuchen"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the media hierarchy (prose), from which the skill derives the browse structure and the resolution
- **MAY** capture: the source `name`, the per-level `MediaClass` mapping, the `identifier` encoding scheme, and the `mime_type` values of the playable items

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** check whether the need is a browsable/playable media source (media source) and **not** a media player entity that consumes foreign sources; on an entity need, point at `ha/entity-platforms-media`
- **MUST** read the `ha/media-source` spec
- **MUST NOT** overwrite an existing `media_source.py`; on collision abort

### Generation rules (from `ha/media-source`)

- **MUST** add a `media_source.py` file in the integration directory — HA discovers it automatically via the integration platform mechanism
- **MUST NOT** require a change to `manifest.json` for discovery — `media_source.py` is detected without a manifest entry
- **MUST** export the top-level async function `async_get_media_source(hass) -> MediaSource`, returning an instance of the `MediaSource` subclass
- **MUST** subclass the `MediaSource` base class, bind it to the domain via `super().__init__(DOMAIN)`, and implement the two methods `async_browse_media(item)` and `async_resolve_media(item)`
- **MUST** in `async_browse_media(item)` return the root node when `item.identifier` is empty and the children when `identifier` is non-empty, and raise `BrowseError` when the structure cannot be retrieved
- **MUST** in `async_resolve_media(item)` return a `PlayMedia(url, mime_type)` with a correct `mime_type` (e.g. `"audio/mpeg"`, `"video/mp4"`) and raise `Unresolvable` when the item cannot be resolved
- **MUST** set an appropriate `MediaClass` on every `BrowseMediaSource` node and set the `can_play`/`can_expand` flags correctly (`can_play` for playable items, `can_expand` for items browsable deeper); root items set `identifier=None`
- **SHOULD** use `generate_media_source_id(DOMAIN, identifier)` for URI construction and encode the path in the `identifier` for deep hierarchies
- **SHOULD** set the class attribute `name` to a human-readable source name — if absent, HA falls back to the domain string
- **MAY** set `thumbnail`, `children_media_class`, and `not_shown` on nodes and use `item.target_media_player` to customize the URL
- **MUST** raise `Unresolvable`/`BrowseError` with `translation_domain`/`translation_key`/`translation_placeholders` when the error message is to be translatable (see `ha/translations`), name identifiers per `ha/naming-conventions`, and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `media_source.py` exists; `async_get_media_source(hass) -> MediaSource` is top-level async and returns a `MediaSource` subclass; both methods are implemented; `async_browse_media` returns the root when `identifier` is empty and raises `BrowseError`; `async_resolve_media` returns a `PlayMedia` with `mime_type` and raises `Unresolvable`; every node carries a `MediaClass` and `can_play`/`can_expand`; root items set `identifier=None`; no `manifest.json` change was needed for discovery
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/media-source`, plus the changed file paths

### Prohibitions

- **MUST NOT** augment more than one media source per run
- **MUST NOT** implement the media player entity consumer side
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] `media_source.py` exists in the integration directory; no `manifest.json` change was needed for discovery
- [ ] `async_get_media_source(hass) -> MediaSource` is exported as a top-level async function and returns a `MediaSource` subclass (bound via `super().__init__(DOMAIN)`)
- [ ] The subclass implements `async_browse_media(item)` (returns `BrowseMediaSource`) and `async_resolve_media(item)` (returns `PlayMedia`)
- [ ] `async_browse_media` returns the root node when `item.identifier` is empty and raises `BrowseError` on a non-retrievable structure
- [ ] `async_resolve_media` returns a `PlayMedia(url, mime_type)` with a set MIME type and raises `Unresolvable` on a non-resolvable item
- [ ] Every `BrowseMediaSource` node carries a `MediaClass` and correctly set `can_play`/`can_expand` flags; root items set `identifier=None`, URIs are constructed via `generate_media_source_id`
- [ ] Report names the changed file paths

## Open questions

- **Hierarchy encoding**: `ha/media-source` names `/` in the `identifier` only as a common pattern (SHOULD). Should the skill mandate a binding separator scheme or stay at SHOULD? Currently it follows the spec and asks when in doubt.
- **`mime_type` derivation**: when does the skill derive the `mime_type` automatically from the file extension and when does it ask explicitly? Currently case-by-case.
- **`target_media_player` customization**: when is URL customization via the target player needed? `ha/media-source` formulates it as MAY; the skill asks only on a described need.
