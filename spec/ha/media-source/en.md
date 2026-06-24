# HA Integration: Media Source

Status: draft

## Context

The media source platform lets an integration expose browsable and playable media to Home Assistant. Media sources appear in the media browser UI; the user navigates hierarchical media libraries and plays content on media player devices.

An integration activates this platform by adding a `media_source.py` file in its integration directory. HA discovers `media_source.py` modules automatically via the integration platform mechanism — no change to `manifest.json` is needed. The module exports `async_get_media_source(hass)`, returning an instance of a `MediaSource` subclass. That subclass implements two methods: `async_browse_media(item)` returns a `BrowseMediaSource` tree, `async_resolve_media(item)` returns a `PlayMedia(url, mime_type)`.

Other integrations — typically media players — consume media sources through the helpers `async_browse_media(hass, ...)` and `async_resolve_media(hass, ...)`; that entity side belongs to `ha/entity-architecture`. Platform discovery follows the general integration platform mechanism from `ha/integration-architecture`. Translatable error messages (`Unresolvable`, `BrowseError`) follow the sibling spec `ha/translations`. This spec lifts the platform convention into a generic obligation.

## Goals

- Establish `media_source.py` as the standard module for every integration that offers browsable or playable media
- Pin the two mandatory methods `async_browse_media` and `async_resolve_media` as the binding interface of the `MediaSource` subclass
- Make correct use of `MediaClass`, `MediaType`, `identifier`, and the `can_play`/`can_expand` flags mandatory for browse nodes
- Define the `media-source://` URI convention and its helpers (`generate_media_source_id`, `is_media_source_id`) as the standard path for ID construction

## Non-Goals

- The media player entity side that consumes media sources (`async_browse_media(hass, ...)` call path) — belongs to `ha/entity-architecture`
- Translation mechanics for `Unresolvable`/`BrowseError` in detail — belongs to `ha/translations`
- Thumbnail proxy and streaming endpoints (`/api/...` routes that serve thumbnails or streams) — a separate HA mechanism, not covered by this platform
- Local file sources and the `path` field of `PlayMedia` in detail — the source doc mentions it only as an optional local-file hint, not a spec topic of its own

## Requirements

### Purpose

- **MUST** provide a `media_source.py` platform once the integration is to expose browsable or playable media to the media browser
- **SHOULD** set the class attribute `name` to a human-readable source name — if absent, HA falls back to the integration domain string
- **MAY** use the media source helpers (`async_browse_media`, `async_resolve_media`, `is_media_source_id`) from within another integration to browse and resolve foreign media sources

### `media_source.py` platform

- **MUST** add a `media_source.py` file in the integration directory — HA discovers the module automatically via the integration platform mechanism
- **MUST NOT** require a change to `manifest.json` for discovery — `media_source.py` is detected without a manifest entry
- **MUST** export the top-level async function `async_get_media_source(hass) -> MediaSource` in `media_source.py`, returning an instance of the `MediaSource` subclass
- **MUST** subclass the `MediaSource` base class and implement the two methods `async_browse_media(item)` and `async_resolve_media(item)`

### Browsing (`async_browse_media`)

- **MUST** return a `BrowseMediaSource` tree from `async_browse_media(item)` that represents the browsable structure at the given item
- **MUST** return the root node of the media hierarchy when `item.identifier` is empty and the children of that item when `identifier` is non-empty
- **MUST** raise `BrowseError` when the media structure cannot be retrieved (for example an unknown item)
- **SHOULD** encode the path in the `identifier` for deep hierarchies — a common pattern is `/` as a separator within the identifier
- **MAY** set `thumbnail`, `children_media_class`, and `not_shown` on `BrowseMediaSource` nodes; `children` is set only on the parent node that is actually browsed

### Resolving (`async_resolve_media`)

- **MUST** return a `PlayMedia(url, mime_type)` from `async_resolve_media(item)` that resolves the item to a playable URL
- **MUST** raise `Unresolvable` when the media item cannot be resolved to a playable URL
- **MUST** set a correct `mime_type` in the `PlayMedia` (for example `"audio/mpeg"`, `"video/mp4"`, `"image/jpeg"`)
- **MAY** use `item.target_media_player` (entity ID of the playing media player) to customize the resolved URL

### Media classes & identifiers

- **MUST** set an appropriate `MediaClass` on every `BrowseMediaSource` node (for example `MediaClass.APP`, `MediaClass.DIRECTORY`, `MediaClass.MUSIC`, `MediaClass.VIDEO`, `MediaClass.IMAGE`)
- **MUST** set the `can_play` and `can_expand` flags correctly per node — `can_play` for directly playable items, `can_expand` for items that can be browsed deeper and have children
- **MUST** set `identifier=None` for root items and an item-specific `identifier` for child items — `BrowseMediaSource` constructs the `media_content_id` automatically from `domain` and `identifier`
- **SHOULD** use the helper `generate_media_source_id(DOMAIN, identifier)` to construct media source URIs, which returns a `media-source://domain/identifier` URI
- **MAY** check with `is_media_source_id(media_content_id)` whether a string is a valid media source URI

### Prerequisites

- **MUST** raise `Unresolvable` and `BrowseError` with `translation_domain`, `translation_key`, and `translation_placeholders` when the error message is to be translatable — both exceptions support translations (see `ha/translations`)
- **SHOULD** initialize the `MediaSource` base class with `super().__init__(DOMAIN)` so the source is bound to the integration domain
- **MAY** let an integration that exclusively consumes foreign media sources (instead of offering its own) use the helpers `async_browse_media`/`async_resolve_media` without carrying a `MediaSource` subclass of its own

## Acceptance Criteria

- [ ] `media_source.py` exists in the integration directory
- [ ] `async_get_media_source(hass) -> MediaSource` is exported as a top-level async function and returns a `MediaSource` subclass
- [ ] The subclass implements `async_browse_media(item)` (returns `BrowseMediaSource`) and `async_resolve_media(item)` (returns `PlayMedia`)
- [ ] `async_browse_media` returns the root node when `item.identifier` is empty and raises `BrowseError` on a non-retrievable structure
- [ ] `async_resolve_media` returns a `PlayMedia(url, mime_type)` with a set MIME type and raises `Unresolvable` on a non-resolvable item
- [ ] Every `BrowseMediaSource` node carries a `MediaClass` and correctly set `can_play`/`can_expand` flags
- [ ] Root items set `identifier=None`; URIs are constructed via `generate_media_source_id`
- [ ] No change to `manifest.json` is needed for media source discovery

## Open Questions

- **Hierarchy encoding**: The source doc names `/` in the `identifier` only as a "common pattern". Should the spec mandate a binding separator scheme or stay at SHOULD?
- **`PlayMedia.path`**: When is the optional `path` field to be set? The source doc names it only as a local-file hint without a calibrated trigger.
- **Thumbnail serving**: Thumbnails point at `/api/...` routes. Where does the boundary run between this spec and a dedicated thumbnail-proxy spec?
- **`target_media_player` usage**: When is URL customization via the target player mandatory rather than MAY? Currently formulated as MAY.
