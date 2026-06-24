# HA-Integration: Entity-Plattformen (Media)

Status: draft

## Kontext

Manche Geräte liefern nicht einen skalaren Messwert, sondern **medien- oder bild-zentrierte Capabilities**: ein abspielbarer Player, eine Kamera mit Live-Bild und Video-Stream, oder ein periodisch aktualisiertes Standbild. Home Assistant bildet diese über eigene Plattform-Basisklassen ab — `MediaPlayerEntity`, `Camera`, `ImageEntity` —, die jeweils ein anderes Datenformat (Player-Zustand und -Metadaten, JPEG-Bytes plus Stream-URL, statisches Bild) und eine andere Frontend-Anbindung tragen. Das generische Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) ist in `ha/entity-architecture` festgeschrieben und wird **hier nicht wiederholt**; die plattform-übergreifende Typisierungs-Mechanik (`device_class`, `supported_features`-Bitmasken, Feature-↔-Methoden-Kopplung) steht in `ha/entity-platform-types`.

Diese Spec ist der **konkrete Katalog** für die media-/bild-zentrierten Plattformen. Sie bindet jede Capability an ihre Basisklasse und schreibt fest, welche Methoden und Properties die jeweilige Plattform-Doku als verpflichtend oder optional markiert. Drei Plattformen werden behandelt. **Media-Player** (`MediaPlayerEntity`) steuert einen Player über `state`, Transport-Methoden (`async_media_play`/`pause`/`stop`), Lautstärke, Quellenwahl und — sofern `BROWSE_MEDIA` gesetzt ist — das Durchsuchen und Abspielen von Medienquellen. **Kamera** (`Camera`) liefert ein Standbild über `async_camera_image` und optional einen Video-Stream über `stream_source`. **Image** (`ImageEntity`) ist die vereinfachte Variante der Kamera für ein statisches Bild über `async_image` oder eine `image_url`.

Die Media-Player-Plattform ist zugleich der **Hauptkonsument** von `ha/media-source`: ihre `async_browse_media`-/`async_play_media`-Implementierung delegiert das Browsen und Auflösen von Medienquellen an die `media_source`-Integration. Die Browsing-Mechanik selbst (`BrowseMedia`-Aufbau, `async_browse_media`-/`async_resolve_media`-Helper) gehört in `ha/media-source` und wird hier nur **referenziert**, nicht dupliziert.

## Ziele

- Jede medien-/bild-zentrierte Capability an die korrekte Plattform-Basisklasse binden — abspielbarer Player → `MediaPlayerEntity`, Live-Kamera mit Stream → `Camera`, statisches/periodisches Bild → `ImageEntity`
- Die von der jeweiligen Plattform-Doku als „Required" markierten Methoden/Properties verpflichtend bereitstellen (z. B. `media_content_type` für den Player, `async_camera_image` für die Kamera, `async_image`/`image_url` für Image)
- `supported_features` je Plattform aus dem plattform-eigenen Feature-Enum setzen (`MediaPlayerEntityFeature`, `CameraEntityFeature`) und nur Flags beworben, deren Methode implementiert ist
- Media-Player-Browsing über `async_browse_media`/`async_play_media` an `ha/media-source` delegieren statt eigene Browsing-Logik zu erfinden
- Kamera vs. Image korrekt unterscheiden — Image ist die simplere Variante ohne Stream, für ein einzelnes Standbild
- Generierten Code so starten lassen, dass Player-, Kamera- und Image-Plattformen direkt aus dem Skill-Output frontend-funktionsfähig sind

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- Plattform-übergreifende Typisierungs-Mechanik (`device_class`-/`supported_features`-Setz-Mechanik, Feature-↔-Methoden-Kopplung als generisches Prinzip) — in `ha/entity-platform-types`; hier nur der konkrete Pro-Plattform-Katalog
- Die `media_source`-Browsing-Plattform selbst (`BrowseMedia`-Aufbau, `async_browse_media`-/`async_resolve_media`-Helper, Content-Filter) — eigene Spec `ha/media-source`; der Media-Player konsumiert sie nur
- HA-Translation-Format (`strings.json`, `entity.<platform>.<key>.name`, State-Übersetzungen) — eigene Spec `ha/translations`
- WebRTC-Provider-Registrierung (`CameraWebRTCProvider`, `async_register_webrtc_provider`) und die übrigen Skalar-/Aktor-Plattformen (`sensor`, `light`, `climate`, …) im Detail — Letztere in `ha/entity-platform-types`

## Anforderungen

### Media-Player (`MediaPlayerEntity`)

- **MUSS [MUST]** für einen steuerbaren Medien-Player die Plattform-Entity von `MediaPlayerEntity` ableiten — diese Plattform deckt Transport, Lautstärke, Quellen- und Sound-Mode-Wahl sowie Medien-Browsing ab
- **MUSS [MUST]** den Zustand über die `state`-Property als `MediaPlayerState`-Member zurückgeben (`OFF`, `ON`, `IDLE`, `PLAYING`, `PAUSED`, `BUFFERING`) — der State-String ist die Kleinschreibung des Enum-Namens
- **MUSS [MUST]** `device_class`, sofern gesetzt, ausschließlich aus `MediaPlayerDeviceClass` wählen (`tv`, `speaker`, `receiver`, `projector`) — die Doku bindet sie an Google-Gerätetypen
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `MediaPlayerEntityFeature` setzen (z. B. `PLAY`, `PAUSE`, `STOP`, `VOLUME_SET`, `SELECT_SOURCE`, `BROWSE_MEDIA`, `PLAY_MEDIA`) und nur Flags beworben, deren Methode implementiert ist
- **MUSS [MUST]** für jedes gesetzte Transport-/Steuerungs-Flag die korrespondierende Methode bereitstellen — `PLAY` → `async_media_play`, `PAUSE` → `async_media_pause`, `STOP` → `async_media_stop`, `VOLUME_SET` → `async_set_volume_level`
- **MUSS [MUST]** `media_content_type` als einen `MediaType`-Member (oder einen passenden String) zurückgeben — die Doku markiert diese Property als „Required"
- **MUSS [MUST]** bei gesetztem `MediaPlayerEntityFeature.BROWSE_MEDIA` `async_browse_media` und bei `PLAY_MEDIA` `async_play_media` implementieren und das Browsen/Auflösen von Medienquellen an `ha/media-source` delegieren (`media_source.async_browse_media`/`async_resolve_media`)
- **SOLLTE [SHOULD]** Medien-Metadaten (`media_title`, `media_artist`, `media_album_name`, `media_duration`, `media_position` + `media_position_updated_at`, `media_image_url`) bereitstellen, soweit das Gerät sie liefert — sie tragen die Frontend-Darstellung
- **SOLLTE [SHOULD]** bei gesetztem `MediaPlayerEntityFeature.GROUPING` je eine Join- und eine Unjoin-Methode (`async_join_players`/`async_unjoin_player`) und `group_members` bereitstellen
- **MUSS NICHT [MUST NOT]** eine URL als `media_image_id` an die Album-Art-Proxy-Methode durchreichen — die Doku warnt, dass dies einem Angreifer das Abrufen beliebiger Daten aus dem lokalen Netz erlauben würde

### Kamera (`Camera`)

- **MUSS [MUST]** für ein Gerät, das ein Live-Bild und optional einen Video-Stream liefert, die Plattform-Entity von `Camera` ableiten
- **MUSS [MUST]** mindestens `async_camera_image` (oder die synchrone `camera_image`) implementieren, das die Bytes des Kamerabilds zurückgibt — bei übergebener `width`/`height` ist best-effort und seitenverhältnis-erhaltend zu skalieren
- **MUSS [MUST]** `supported_features` aus `CameraEntityFeature` setzen — `CameraEntityFeature.ON_OFF` für `turn_on`/`turn_off`, `CameraEntityFeature.STREAM` für Streaming — und nur Flags beworben, deren Methode implementiert ist
- **MUSS [MUST]** bei gesetztem `CameraEntityFeature.STREAM` `stream_source` implementieren, das eine für ffmpeg nutzbare URL zurückgibt (z. B. eine RTSP-URL); per Default nutzt die Kamera dann `StreamType.HLS`
- **SOLLTE [SHOULD]** für eine native WebRTC-Anbindung (ebenfalls unter `CameraEntityFeature.STREAM`) `async_handle_async_webrtc_offer` und `async_on_webrtc_candidate` implementieren — durch deren Implementierung nimmt das Frontend reines WebRTC an und fällt nicht auf HLS zurück
- **SOLLTE [SHOULD]** bei gesetztem `CameraEntityFeature.ON_OFF` `async_turn_on`/`async_turn_off` und, wo das Gerät es kann, `async_enable_motion_detection`/`async_disable_motion_detection` bereitstellen
- **MUSS NICHT [MUST NOT]** in den Bild-/Stream-Methoden blockierendes I/O aus einer Property heraus ausführen — Properties geben nur Information aus dem Speicher zurück; Daten werden über `update`/`async_update` geholt

### Image (`ImageEntity`)

- **MUSS [MUST]** für ein statisches oder periodisch aktualisiertes Einzelbild ohne Live-Stream die Plattform-Entity von `ImageEntity` ableiten — Image ist die vereinfachte Variante der Kamera
- **MUSS [MUST]** entweder `async_image` (bzw. `image`) implementieren, das die Bild-Bytes zurückgibt, **oder** eine `image_url` bereitstellen, von der HA das Bild automatisch holt und cacht
- **MUSS [MUST]** `image_last_updated` (ein `datetime`) als Zeitstempel des letzten Bild-Updates pflegen — das Frontend ruft `image`/`async_image` erst nach Änderung dieses Werts erneut auf
- **MUSS NICHT [MUST NOT]** `image_last_updated` innerhalb von `async_image` hochzählen — der Zeitstempel ist zu aktualisieren, wenn ein neues Bild vorliegt (z. B. im Coordinator-Update), nicht beim Ausliefern
- **SOLLTE [SHOULD]** `content_type` setzen, wenn das Bild kein `image/jpeg` ist — bei Bereitstellung über `image_url` wird der Content-Type automatisch gesetzt
- **SOLLTE [SHOULD]** bei Bereitstellung über `image_url` den gecachten Eintrag (`self._cached_image`) auf `None` setzen, um den Cache zu invalidieren, wenn das Bild sich ändert

## Akzeptanzkriterien

- [ ] Jede Capability ist auf der korrekten Plattform-Basisklasse abgebildet — Player → `MediaPlayerEntity`, Live-Kamera mit Stream → `Camera`, statisches Bild → `ImageEntity`
- [ ] Der Media-Player gibt `state` als `MediaPlayerState`-Member zurück und stellt `media_content_type` als `MediaType` bereit
- [ ] `supported_features` ist je Plattform als bitweise-`|`-Kombination aus dem plattform-eigenen Enum (`MediaPlayerEntityFeature`, `CameraEntityFeature`) gesetzt, nie als rohe Ganzzahl
- [ ] Für jedes gesetzte Player-Transport-Flag existiert die Methode (`PLAY`→`async_media_play`, `PAUSE`→`async_media_pause`, `STOP`→`async_media_stop`, `VOLUME_SET`→`async_set_volume_level`)
- [ ] Bei `BROWSE_MEDIA`/`PLAY_MEDIA` delegiert `async_browse_media`/`async_play_media` das Browsen/Auflösen an `ha/media-source`, statt eigene Browsing-Logik zu erfinden
- [ ] Die Kamera implementiert `async_camera_image`; bei gesetztem `CameraEntityFeature.STREAM` liefert `stream_source` eine ffmpeg-nutzbare URL
- [ ] `CameraEntityFeature.ON_OFF` ist nur gesetzt, wenn `async_turn_on`/`async_turn_off` implementiert sind
- [ ] Keine URL wird als `media_image_id` an die Album-Art-Proxy-Methode durchgereicht
- [ ] Die Image-Entity implementiert `async_image` oder stellt `image_url` bereit und pflegt `image_last_updated`; `image_last_updated` wird nicht innerhalb von `async_image` hochgezählt
- [ ] `content_type` ist gesetzt, wo das Bild kein `image/jpeg` ist

## Offene Fragen

- **Tiefe der Player-Metadaten-Pflicht**: Die Player-Doku listet viele optionale Metadaten-Properties. Soll der Skill einen Mindestsatz (`media_title`, `media_position`, `media_image_url`) erzwingen, oder bleibt das vollständig optional?
- **WebRTC vs. HLS als Default**: Native WebRTC schließt den HLS-Fallback aus. Soll die Spec eine Default-Empfehlung (HLS sofern nicht zwingend WebRTC) festschreiben oder dem Geräteprofil überlassen?
- **Album-Art-Proxy-Schwelle**: Die Doku verlangt den Proxy nur für externe Anfragen (`is_local_request`). Soll der Skill diese Bedingung generieren oder die Proxy-Methode optional lassen?
- **Image-Refresh-Intervall**: `image_last_updated` steuert das Refetch. Gehört eine Konvention für das Update-Intervall (Coordinator-getrieben) in diese Spec oder in `ha/coordinator-patterns`?
- **`SEARCH_MEDIA`/`MEDIA_ENQUEUE`-Abdeckung**: Die Player-Doku führt weitere optionale Features (`async_search_media`, Enqueue/Announce). Sollen diese eigene MUST-Regeln erhalten oder unter der generischen Feature-↔-Methoden-Kopplung aus `ha/entity-platform-types` verbleiben?
