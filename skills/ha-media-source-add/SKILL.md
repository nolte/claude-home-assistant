---
name: ha-media-source-add
description: Augment an existing Home Assistant Custom Integration with a media source provider, conforming to spec/ha/media-source. Creates media_source.py with a top-level async_get_media_source(hass) -> MediaSource, a MediaSource subclass bound via super().__init__(DOMAIN), async_browse_media(item) returning a BrowseMediaSource tree (root node on empty identifier, children otherwise, BrowseError on failure), and async_resolve_media(item) returning a PlayMedia(url, mime_type) (Unresolvable on failure); sets a MediaClass plus correct can_play/can_expand per node, builds URIs via generate_media_source_id, and wires translatable Unresolvable/BrowseError exceptions. Discovery needs no manifest.json change. Activate on "add a media source", "let users browse my media in the media browser", "füge eine Media-Source hinzu", "lass den User meine Medien im Media-Browser durchsuchen". Do not activate for a media_player entity that consumes media sources (ha/entity-platforms-media), translation mechanics (ha/translations), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, media-source]
---

# HA Media Source Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-media-source-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-media-source-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a media hierarchy and reads back `media_source.py`, the browse tree shape, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`).
- **Mid-flow interactivity** — the media-source-vs-media-player-entity decision and the per-level `MediaClass`/`identifier` shape are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one `media_source.py` module with two methods fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the source-vs-entity decision and the hierarchy shaping belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add a media source provider to an existing integration — a `media_source.py` that exposes a browsable, playable media library to the Home Assistant media browser.

## When NOT to activate

- a `media_player` entity that consumes media sources (the `async_browse_media(hass, ...)` call path) → `ha/entity-platforms-media` / `ha/entity-architecture`
- translation mechanics for `Unresolvable`/`BrowseError` → `ha/translations`
- thumbnail proxy / streaming `/api/...` routes → out of scope
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One media source, one run.** No multi-source batches.
2. **Read [`ha/media-source`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/media-source/de.md) first.** Do not generate from memory.
3. **No manifest change for discovery.** HA discovers `media_source.py` automatically via the integration platform mechanism — **never** add a manifest entry for discovery.
4. **Top-level contract.** `media_source.py` exports the top-level async function `async_get_media_source(hass) -> MediaSource` returning an instance of the `MediaSource` subclass, which is bound to the domain via `super().__init__(DOMAIN)`.
5. **Two mandatory methods.** Implement `async_browse_media(item)` (returns a `BrowseMediaSource` tree — root node on empty `item.identifier`, children otherwise; raise `BrowseError` when the structure cannot be retrieved) and `async_resolve_media(item)` (returns a `PlayMedia(url, mime_type)` with a correct `mime_type`; raise `Unresolvable` when the item cannot be resolved).
6. **Node attributes.** Every `BrowseMediaSource` node carries an appropriate `MediaClass` and correctly set `can_play`/`can_expand` flags (`can_play` for playable items, `can_expand` for items browsable deeper); root items set `identifier=None`.
7. **URI construction.** Use `generate_media_source_id(DOMAIN, identifier)` to construct `media-source://` URIs; encode the path in the `identifier` for deep hierarchies.
8. **Translatable errors.** Raise `Unresolvable`/`BrowseError` with `translation_domain`/`translation_key`/`translation_placeholders` when the message is to be translatable (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)).
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `hierarchy` | yes | — | the media hierarchy and resolution, in prose |
| `name` | no | domain string | human-readable source name |
| `media_class_map` | no | inferred + confirmed | `MediaClass` per hierarchy level |
| `identifier_scheme` | no | derived | `identifier` encoding (path separator) |
| `mime_types` | no | derived/asked | `mime_type` of the playable items |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Confirm the need is a browsable/playable media source — not a media player entity consuming foreign sources. If it is the entity side, point at `ha/entity-platforms-media` and stop.
3. Read `ha/media-source`.
4. `custom_components/<domain>/media_source.py` does not already exist. If it does, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the source `name`, the browse hierarchy with its per-level `MediaClass` and `can_play`/`can_expand` shape, the `identifier` encoding, and the resolution (`mime_type`) in one paragraph. Wait for confirmation.

### 2) Generate

Write `custom_components/<domain>/media_source.py`:

- the top-level `async_get_media_source(hass) -> MediaSource`;
- the `MediaSource` subclass, `super().__init__(DOMAIN)`, optional class attribute `name`;
- `async_browse_media(item)` — root on empty `item.identifier`, children otherwise, `BrowseError` on failure; every `BrowseMediaSource` node with a `MediaClass` and `can_play`/`can_expand`; URIs via `generate_media_source_id`;
- `async_resolve_media(item)` — `PlayMedia(url, mime_type)`, `Unresolvable` on failure.

Add translatable `Unresolvable`/`BrowseError` strings to `strings.json` when the errors are to be translatable. Do **not** touch `manifest.json` for discovery.

### 3) Validate and report

Validate offline (`media_source.py` present; `async_get_media_source` top-level and returns a `MediaSource` subclass; both methods implemented; root on empty `identifier` + `BrowseError`; `PlayMedia` with `mime_type` + `Unresolvable`; every node carries `MediaClass` and `can_play`/`can_expand`; root `identifier=None`; no `manifest.json` change for discovery). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/media-source` acceptance criteria, plus the changed file paths.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Media player entity consuming sources → `ha/entity-platforms-media` / `ha/entity-architecture`
- Translation mechanics → `ha/translations`
- Thumbnail / streaming routes → out of scope
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
