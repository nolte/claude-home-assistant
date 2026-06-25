# HA-Integration: Media-Source

Status: draft

## Kontext

Die Media-Source-Plattform erlaubt einer Integration, durchsuchbare und abspielbare Medien an Home Assistant zu exportieren. Media-Sources erscheinen im Media-Browser-UI; der User navigiert hierarchische Medienbibliotheken und spielt Inhalte auf Media-Player-Geräten ab.

Eine Integration aktiviert diese Plattform, indem sie eine `media_source.py`-Datei im Integrations-Ordner anlegt. HA entdeckt `media_source.py`-Module automatisch über den Integration-Platform-Mechanismus — eine Änderung an `manifest.json` ist dafür nicht nötig. Das Modul exportiert `async_get_media_source(hass)`, das eine Instanz einer `MediaSource`-Subklasse liefert. Diese Subklasse implementiert zwei Methoden: `async_browse_media(item)` liefert einen `BrowseMediaSource`-Baum, `async_resolve_media(item)` liefert ein `PlayMedia(url, mime_type)`.

Andere Integrationen — typischerweise Media-Player — konsumieren Media-Sources über die Helfer `async_browse_media(hass, ...)` und `async_resolve_media(hass, ...)`; diese Entity-Seite gehört zu `ha/entity-architecture`. Die Platform-Discovery folgt dem allgemeinen Integration-Platform-Mechanismus aus `ha/integration-architecture`. Übersetzbare Fehlermeldungen (`Unresolvable`, `BrowseError`) folgen der Schwester-Spec `ha/translations`. Diese Spec überführt die Plattform-Konvention in eine generische Verpflichtung.

## Ziele

- `media_source.py` als Standard-Modul für jede Integration etablieren, die durchsuchbare oder abspielbare Medien anbietet
- Die zwei Pflicht-Methoden `async_browse_media` und `async_resolve_media` als verbindliche Schnittstelle der `MediaSource`-Subklasse festschreiben
- Die korrekte Verwendung von `MediaClass`, `MediaType`, `identifier` sowie der Flags `can_play`/`can_expand` für Browse-Knoten verbindlich machen
- Die `media-source://`-URI-Konvention und die zugehörigen Helfer (`generate_media_source_id`, `is_media_source_id`) als Standard-Pfad zur ID-Konstruktion definieren

## Nicht-Ziele

- Die Media-Player-Entity-Seite, die Media-Sources konsumiert (`async_browse_media(hass, ...)`-Aufruf-Pfad) — gehört zu `ha/entity-architecture`
- Übersetzungs-Mechanik für `Unresolvable`/`BrowseError` im Detail — gehört zu `ha/translations`
- Thumbnail-Proxy- und Streaming-Endpunkte (`/api/...`-Routen, die Thumbnails oder Streams ausliefern) — eigener HA-Mechanismus, nicht von dieser Plattform abgedeckt
- Lokale Datei-Sources und das `path`-Feld von `PlayMedia` im Detail — der Quell-Doc nennt es nur als optionalen Local-File-Hinweis, kein eigenes Spec-Thema

## Anforderungen

### Zweck

- **MUSS [MUST]** eine `media_source.py`-Plattform bereitstellen, sobald die Integration durchsuchbare oder abspielbare Medien an den Media-Browser exportieren soll
- **SOLLTE [SHOULD]** die Klassen-Attribut-`name` auf einen menschenlesbaren Source-Namen setzen — fehlt es, fällt HA auf den Integrations-Domain-String zurück
- **KANN [MAY]** die Media-Source-Helfer (`async_browse_media`, `async_resolve_media`, `is_media_source_id`) aus einer anderen Integration heraus nutzen, um fremde Media-Sources zu durchsuchen und aufzulösen

### `media_source.py`-Platform

- **MUSS [MUST]** eine `media_source.py`-Datei im Integrations-Ordner anlegen — HA entdeckt das Modul automatisch über den Integration-Platform-Mechanismus
- **MUSS NICHT [MUST NOT]** für die Discovery eine Änderung an `manifest.json` verlangen — `media_source.py` wird ohne Manifest-Eintrag erkannt
- **MUSS [MUST]** in `media_source.py` die Top-Level-Async-Funktion `async_get_media_source(hass) -> MediaSource` exportieren, die eine Instanz der `MediaSource`-Subklasse liefert
- **MUSS [MUST]** die `MediaSource`-Basisklasse subklassen und die zwei Methoden `async_browse_media(item)` und `async_resolve_media(item)` implementieren

### Browsing (`async_browse_media`)

- **MUSS [MUST]** aus `async_browse_media(item)` einen `BrowseMediaSource`-Baum liefern, der die durchsuchbare Struktur am übergebenen Item repräsentiert
- **MUSS [MUST]** bei leerem `item.identifier` den Wurzelknoten der Medien-Hierarchie liefern und bei nicht-leerem `identifier` die Kinder dieses Items
- **MUSS [MUST]** `BrowseError` werfen, wenn die Medien-Struktur nicht abgerufen werden kann (z. B. unbekanntes Item)
- **SOLLTE [SHOULD]** für tiefe Hierarchien den Pfad im `identifier` kodieren — gängig ist `/` als Separator innerhalb des Identifiers
- **KANN [MAY]** `thumbnail`, `children_media_class` und `not_shown` an `BrowseMediaSource`-Knoten setzen; `children` wird nur am tatsächlich durchsuchten Eltern-Knoten gesetzt

### Auflösen (`async_resolve_media`)

- **MUSS [MUST]** aus `async_resolve_media(item)` ein `PlayMedia(url, mime_type)` liefern, das das Item zu einer abspielbaren URL auflöst
- **MUSS [MUST]** `Unresolvable` werfen, wenn das Media-Item nicht zu einer abspielbaren URL aufgelöst werden kann
- **MUSS [MUST]** im `PlayMedia` einen korrekten `mime_type` setzen (z. B. `"audio/mpeg"`, `"video/mp4"`, `"image/jpeg"`)
- **KANN [MAY]** `item.target_media_player` (Entity-ID des abspielenden Media-Players) nutzen, um die aufgelöste URL zu individualisieren

### Media-Klassen & Identifier

- **MUSS [MUST]** an jedem `BrowseMediaSource`-Knoten eine passende `MediaClass` setzen (z. B. `MediaClass.APP`, `MediaClass.DIRECTORY`, `MediaClass.MUSIC`, `MediaClass.VIDEO`, `MediaClass.IMAGE`)
- **MUSS [MUST]** die Flags `can_play` und `can_expand` pro Knoten korrekt setzen — `can_play` für direkt abspielbare Items, `can_expand` für tiefer durchsuchbare Items mit Kindern
- **MUSS [MUST]** für Wurzel-Items `identifier=None` setzen und für untergeordnete Items einen Item-spezifischen `identifier` — `BrowseMediaSource` konstruiert die `media_content_id` automatisch aus `domain` und `identifier`
- **SOLLTE [SHOULD]** zur Konstruktion von Media-Source-URIs den Helfer `generate_media_source_id(DOMAIN, identifier)` nutzen, der eine `media-source://domain/identifier`-URI liefert
- **KANN [MAY]** mit `is_media_source_id(media_content_id)` prüfen, ob ein String eine gültige Media-Source-URI ist

### Voraussetzungen

- **MUSS [MUST]** `Unresolvable` und `BrowseError` mit `translation_domain`, `translation_key` und `translation_placeholders` werfen, wenn die Fehlermeldung übersetzbar sein soll — beide Exceptions unterstützen Translations (siehe `ha/translations`)
- **SOLLTE [SHOULD]** die `MediaSource`-Basisklasse mit `super().__init__(DOMAIN)` initialisieren, damit der Source an die Integrations-Domain gebunden ist
- **KANN [MAY]** eine Integration, die ausschließlich fremde Media-Sources konsumiert (statt eigene anzubieten), die Helfer `async_browse_media`/`async_resolve_media` nutzen, ohne selbst eine `MediaSource`-Subklasse zu führen

## Akzeptanzkriterien

- [ ] `media_source.py` existiert im Integrations-Ordner
- [ ] `async_get_media_source(hass) -> MediaSource` ist als Top-Level-Async-Funktion exportiert und liefert eine `MediaSource`-Subklasse
- [ ] Die Subklasse implementiert `async_browse_media(item)` (liefert `BrowseMediaSource`) und `async_resolve_media(item)` (liefert `PlayMedia`)
- [ ] `async_browse_media` liefert bei leerem `item.identifier` den Wurzelknoten und wirft `BrowseError` bei nicht abrufbarer Struktur
- [ ] `async_resolve_media` liefert ein `PlayMedia(url, mime_type)` mit gesetztem MIME-Type und wirft `Unresolvable` bei nicht auflösbarem Item
- [ ] Jeder `BrowseMediaSource`-Knoten trägt eine `MediaClass` sowie korrekt gesetzte `can_play`/`can_expand`-Flags
- [ ] Wurzel-Items setzen `identifier=None`; URIs werden über `generate_media_source_id` konstruiert
- [ ] Keine Änderung an `manifest.json` ist für die Media-Source-Discovery nötig

## Offene Fragen

- **Hierarchie-Encoding**: Der Quell-Doc nennt `/` im `identifier` nur als „gängiges Muster". Soll die Spec ein verbindliches Separator-Schema vorgeben oder bei SOLLTE bleiben?
- **`PlayMedia.path`**: Wann ist das optionale `path`-Feld zu setzen? Der Quell-Doc nennt es nur als Local-File-Hinweis ohne kalibrierten Trigger.
- **Thumbnail-Auslieferung**: Thumbnails verweisen auf `/api/...`-Routen. Wo verläuft die Grenze zwischen dieser Spec und einer eigenen Thumbnail-Proxy-Spec?
- **`target_media_player`-Nutzung**: Wann ist die URL-Individualisierung über den Ziel-Player Pflicht statt KANN? Aktuell als KANN formuliert.
