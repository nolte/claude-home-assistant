# HA Integration: Entity Platforms (Media)

Status: draft

## Context

Some devices deliver not a scalar measurement but **media- or image-centric capabilities**: a playable player, a camera with a live image and video stream, or a periodically refreshed still image. Home Assistant models these through dedicated platform base classes — `MediaPlayerEntity`, `Camera`, `ImageEntity` — each carrying a different data format (player state and metadata, JPEG bytes plus stream URL, a static image) and a different frontend integration. The generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, the `EntityDescription` pattern, entity categories, coordinator binding) is fixed in `ha/entity-architecture` and is **not repeated here**; the cross-platform typing mechanics (`device_class`, `supported_features` bitmasks, feature-↔-method coupling) live in `ha/entity-platform-types`.

This spec is the **concrete catalog** for the media-/image-centric platforms. It binds each capability to its base class and fixes which methods and properties the respective platform doc marks as mandatory or optional. Three platforms are covered. **Media player** (`MediaPlayerEntity`) controls a player via `state`, transport methods (`async_media_play`/`pause`/`stop`), volume, source selection, and — when `BROWSE_MEDIA` is set — browsing and playing media sources. **Camera** (`Camera`) delivers a still image via `async_camera_image` and optionally a video stream via `stream_source`. **Image** (`ImageEntity`) is the simplified variant of the camera for a static image via `async_image` or an `image_url`.

The media-player platform is also the **primary consumer** of `ha/media-source`: its `async_browse_media`/`async_play_media` implementation delegates browsing and resolving media sources to the `media_source` integration. The browsing mechanics themselves (`BrowseMedia` shape, `async_browse_media`/`async_resolve_media` helpers) belong in `ha/media-source` and are only **referenced** here, not duplicated.

## Goals

- Bind each media-/image-centric capability to the correct platform base class — playable player → `MediaPlayerEntity`, live camera with stream → `Camera`, static/periodic image → `ImageEntity`
- Mandatorily provide the methods/properties the respective platform doc marks "Required" (for example `media_content_type` for the player, `async_camera_image` for the camera, `async_image`/`image_url` for image)
- Set `supported_features` per platform from the platform-owned feature enum (`MediaPlayerEntityFeature`, `CameraEntityFeature`) and advertise only flags whose method is implemented
- Delegate media-player browsing via `async_browse_media`/`async_play_media` to `ha/media-source` instead of inventing custom browsing logic
- Distinguish camera vs. image correctly — image is the simpler variant without a stream, for a single still
- Have generated code start so that player, camera, and image platforms are frontend-functional straight from skill output

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, the `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- Cross-platform typing mechanics (`device_class`/`supported_features` setting mechanics, feature-↔-method coupling as a generic principle) — in `ha/entity-platform-types`; here only the concrete per-platform catalog
- The `media_source` browsing platform itself (`BrowseMedia` shape, `async_browse_media`/`async_resolve_media` helpers, content filters) — separate `ha/media-source` spec; the media player only consumes it
- HA translation format (`strings.json`, `entity.<platform>.<key>.name`, state translations) — separate `ha/translations` spec
- WebRTC provider registration (`CameraWebRTCProvider`, `async_register_webrtc_provider`) and the remaining scalar/actuator platforms (`sensor`, `light`, `climate`, …) in detail — the latter in `ha/entity-platform-types`

## Requirements

### Media player (`MediaPlayerEntity`)

- **MUST** derive the platform entity from `MediaPlayerEntity` for a controllable media player — this platform covers transport, volume, source and sound-mode selection, and media browsing
- **MUST** return the state via the `state` property as a `MediaPlayerState` member (`OFF`, `ON`, `IDLE`, `PLAYING`, `PAUSED`, `BUFFERING`) — the state string is the lowercase of the enum name
- **MUST** choose `device_class`, when set, only from `MediaPlayerDeviceClass` (`tv`, `speaker`, `receiver`, `projector`) — the docs bind it to Google device types
- **MUST** set `supported_features` as a bitwise `|` combination from `MediaPlayerEntityFeature` (for example `PLAY`, `PAUSE`, `STOP`, `VOLUME_SET`, `SELECT_SOURCE`, `BROWSE_MEDIA`, `PLAY_MEDIA`) and advertise only flags whose method is implemented
- **MUST** provide the corresponding method for every set transport/control flag — `PLAY` → `async_media_play`, `PAUSE` → `async_media_pause`, `STOP` → `async_media_stop`, `VOLUME_SET` → `async_set_volume_level`
- **MUST** return `media_content_type` as a `MediaType` member (or a matching string) — the docs mark this property "Required"
- **MUST** implement `async_browse_media` when `MediaPlayerEntityFeature.BROWSE_MEDIA` is set and `async_play_media` when `PLAY_MEDIA` is set, and delegate browsing/resolving of media sources to `ha/media-source` (`media_source.async_browse_media`/`async_resolve_media`)
- **SHOULD** provide media metadata (`media_title`, `media_artist`, `media_album_name`, `media_duration`, `media_position` + `media_position_updated_at`, `media_image_url`) insofar as the device supplies it — they carry the frontend representation
- **SHOULD** provide a join and an unjoin method (`async_join_players`/`async_unjoin_player`) and `group_members` when `MediaPlayerEntityFeature.GROUPING` is set
- **MUST NOT** pass a URL as `media_image_id` into the album-art proxy method — the docs warn this would allow an attacker to fetch arbitrary data from the local network

### Camera (`Camera`)

- **MUST** derive the platform entity from `Camera` for a device that delivers a live image and optionally a video stream
- **MUST** implement at least `async_camera_image` (or the synchronous `camera_image`), returning the bytes of the camera image — when `width`/`height` are passed, scale best-effort and aspect-ratio-preserving
- **MUST** set `supported_features` from `CameraEntityFeature` — `CameraEntityFeature.ON_OFF` for `turn_on`/`turn_off`, `CameraEntityFeature.STREAM` for streaming — and advertise only flags whose method is implemented
- **MUST** implement `stream_source` when `CameraEntityFeature.STREAM` is set, returning a URL usable by ffmpeg (for example an RTSP URL); by default the camera then uses `StreamType.HLS`
- **SHOULD** implement `async_handle_async_webrtc_offer` and `async_on_webrtc_candidate` for a native WebRTC integration (also under `CameraEntityFeature.STREAM`) — by implementing them the frontend assumes pure WebRTC and does not fall back to HLS
- **SHOULD** provide `async_turn_on`/`async_turn_off` when `CameraEntityFeature.ON_OFF` is set and, where the device can, `async_enable_motion_detection`/`async_disable_motion_detection`
- **MUST NOT** perform blocking I/O from a property inside the image/stream methods — properties only return information from memory; data is fetched via `update`/`async_update`

### Image (`ImageEntity`)

- **MUST** derive the platform entity from `ImageEntity` for a static or periodically refreshed single image without a live stream — image is the simplified variant of the camera
- **MUST** either implement `async_image` (or `image`), returning the image bytes, **or** provide an `image_url` from which HA fetches and caches the image automatically
- **MUST** maintain `image_last_updated` (a `datetime`) as the timestamp of the last image update — the frontend only re-calls `image`/`async_image` after this value changes
- **MUST NOT** bump `image_last_updated` inside `async_image` — the timestamp is to be updated when a new image is available (for example in the coordinator update), not on serving
- **SHOULD** set `content_type` when the image is not `image/jpeg` — when provided via `image_url` the content type is set automatically
- **SHOULD** set the cached entry (`self._cached_image`) to `None` to invalidate the cache when the image changes and it is provided via `image_url`

## Acceptance Criteria

- [ ] Each capability is modeled on the correct platform base class — player → `MediaPlayerEntity`, live camera with stream → `Camera`, static image → `ImageEntity`
- [ ] The media player returns `state` as a `MediaPlayerState` member and provides `media_content_type` as a `MediaType`
- [ ] `supported_features` is set per platform as a bitwise `|` combination from the platform-owned enum (`MediaPlayerEntityFeature`, `CameraEntityFeature`), never as a raw integer
- [ ] For every set player transport flag the method exists (`PLAY`→`async_media_play`, `PAUSE`→`async_media_pause`, `STOP`→`async_media_stop`, `VOLUME_SET`→`async_set_volume_level`)
- [ ] With `BROWSE_MEDIA`/`PLAY_MEDIA`, `async_browse_media`/`async_play_media` delegate browsing/resolving to `ha/media-source` instead of inventing custom browsing logic
- [ ] The camera implements `async_camera_image`; when `CameraEntityFeature.STREAM` is set, `stream_source` returns an ffmpeg-usable URL
- [ ] `CameraEntityFeature.ON_OFF` is set only when `async_turn_on`/`async_turn_off` are implemented
- [ ] No URL is passed as `media_image_id` into the album-art proxy method
- [ ] The image entity implements `async_image` or provides `image_url` and maintains `image_last_updated`; `image_last_updated` is not bumped inside `async_image`
- [ ] `content_type` is set where the image is not `image/jpeg`

## Open Questions

- **Depth of player-metadata obligation**: The player docs list many optional metadata properties. Should the skill enforce a minimum set (`media_title`, `media_position`, `media_image_url`), or does it stay fully optional?
- **WebRTC vs. HLS as default**: Native WebRTC excludes the HLS fallback. Should the spec fix a default recommendation (HLS unless WebRTC is mandatory) or leave it to the device profile?
- **Album-art proxy threshold**: The docs require the proxy only for external requests (`is_local_request`). Should the skill generate this condition or leave the proxy method optional?
- **Image refresh interval**: `image_last_updated` drives the refetch. Does a convention for the update interval (coordinator-driven) belong in this spec or in `ha/coordinator-patterns`?
- **`SEARCH_MEDIA`/`MEDIA_ENQUEUE` coverage**: The player docs list further optional features (`async_search_media`, enqueue/announce). Should these get their own MUST rules or remain under the generic feature-↔-method coupling from `ha/entity-platform-types`?
