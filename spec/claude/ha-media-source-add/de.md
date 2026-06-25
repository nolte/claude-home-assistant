# Skill: `ha-media-source-add`

Status: draft

## Kontext

`ha/media-source` definiert die Media-Source-Plattform: eine Integration exportiert durchsuchbare und abspielbare Medien an den Media-Browser, indem sie eine `media_source.py`-Datei im Integrations-Ordner anlegt. HA entdeckt das Modul automatisch über den Integration-Platform-Mechanismus — eine Änderung an `manifest.json` ist dafür **nicht** nötig. Das Modul exportiert die Top-Level-Async-Funktion `async_get_media_source(hass) -> MediaSource`, die eine Instanz einer `MediaSource`-Subklasse liefert. Diese Subklasse implementiert zwei Pflicht-Methoden: `async_browse_media(item)` liefert einen `BrowseMediaSource`-Baum, `async_resolve_media(item)` liefert ein `PlayMedia(url, mime_type)`. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt eine Media-Source in einer **bestehenden** Integration: das `media_source.py`-Modul, die `async_get_media_source(hass)`-Funktion, die `MediaSource`-Subklasse mit `async_browse_media`/`async_resolve_media`, die korrekt gesetzten `MediaClass`- und `can_play`/`can_expand`-Felder pro `BrowseMediaSource`-Knoten, die URI-Konstruktion über `generate_media_source_id` und die übersetzbaren `Unresolvable`/`BrowseError`-Exceptions — spec-konform zu `ha/media-source`.

## Scope

Ergänzung genau einer Media-Source pro Lauf in einer bestehenden `custom_components/<domain>/`-Integration: die `media_source.py`-Datei, die `async_get_media_source(hass)`-Funktion, die `MediaSource`-Subklasse, die zwei Methoden `async_browse_media(item)` und `async_resolve_media(item)`, die `MediaClass`- und `can_play`/`can_expand`-Felder, die `identifier`-/URI-Konstruktion und die übersetzbaren Fehler-Exceptions. Der Skill liest `ha/media-source` und validiert.

## Ziele

- Aus einer beschriebenen Medien-Hierarchie eine spec-konforme `media_source.py` ergänzen
- Den Top-Level-Vertrag erzwingen: `async_get_media_source(hass) -> MediaSource` exportiert eine `MediaSource`-Subklasse, initialisiert über `super().__init__(DOMAIN)`
- Die zwei Pflicht-Methoden als verbindliche Schnittstelle erzwingen: `async_browse_media(item)` liefert einen `BrowseMediaSource`-Baum (Wurzel bei leerem `identifier`, sonst Kinder), `async_resolve_media(item)` liefert ein `PlayMedia(url, mime_type)`
- Pro Browse-Knoten eine passende `MediaClass` und korrekt gesetzte `can_play`/`can_expand`-Flags erzwingen; URIs über `generate_media_source_id` konstruieren
- Die übersetzbaren `Unresolvable`-/`BrowseError`-Fehlerpfade verdrahten

## Nicht-Ziele

- Die Media-Player-Entity-Seite, die Media-Sources konsumiert (`async_browse_media(hass, ...)`-Aufruf-Pfad) — `ha/entity-architecture` / `ha/entity-platforms-media`
- Übersetzungs-Mechanik für `Unresolvable`/`BrowseError` im Detail — `ha/translations`
- Thumbnail-Proxy- und Streaming-Endpunkte (`/api/...`-Routen) — eigener HA-Mechanismus, nicht von dieser Plattform abgedeckt
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a media source", „let users browse my media in the media browser", „expose a browsable media library"
  - „resolve my items to a playable URL in the media browser"
  - „füge eine Media-Source hinzu", „lass den User meine Medien im Media-Browser durchsuchen"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Medien-Hierarchie (Prosa), aus der der Skill die Browse-Struktur und die Auflösung ableitet
- **KANN [MAY]** erfassen: den Source-`name`, das `MediaClass`-Mapping pro Ebene, das `identifier`-Encoding-Schema und die `mime_type`-Werte der abspielbaren Items

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** prüfen, ob der Bedarf eine durchsuchbare/abspielbare Media-Quelle ist (Media-Source) und **nicht** eine Media-Player-Entity, die fremde Sources konsumiert; bei Entity-Bedarf auf `ha/entity-platforms-media` verweisen
- **MUSS [MUST]** die `ha/media-source`-Spec lesen
- **MUSS NICHT [MUST NOT]** eine bestehende `media_source.py` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/media-source`)

- **MUSS [MUST]** eine `media_source.py`-Datei im Integrations-Ordner anlegen — HA entdeckt sie automatisch über den Integration-Platform-Mechanismus
- **MUSS NICHT [MUST NOT]** für die Discovery eine Änderung an `manifest.json` verlangen — `media_source.py` wird ohne Manifest-Eintrag erkannt
- **MUSS [MUST]** die Top-Level-Async-Funktion `async_get_media_source(hass) -> MediaSource` exportieren, die eine Instanz der `MediaSource`-Subklasse liefert
- **MUSS [MUST]** die `MediaSource`-Basisklasse subklassen, sie über `super().__init__(DOMAIN)` an die Domain binden, und die zwei Methoden `async_browse_media(item)` und `async_resolve_media(item)` implementieren
- **MUSS [MUST]** in `async_browse_media(item)` bei leerem `item.identifier` den Wurzelknoten und bei nicht-leerem `identifier` die Kinder liefern, und `BrowseError` werfen, wenn die Struktur nicht abrufbar ist
- **MUSS [MUST]** in `async_resolve_media(item)` ein `PlayMedia(url, mime_type)` mit korrektem `mime_type` (z. B. `"audio/mpeg"`, `"video/mp4"`) liefern und `Unresolvable` werfen, wenn das Item nicht aufgelöst werden kann
- **MUSS [MUST]** an jedem `BrowseMediaSource`-Knoten eine passende `MediaClass` setzen und die Flags `can_play`/`can_expand` korrekt setzen (`can_play` für abspielbare Items, `can_expand` für tiefer durchsuchbare); Wurzel-Items setzen `identifier=None`
- **SOLLTE [SHOULD]** zur URI-Konstruktion `generate_media_source_id(DOMAIN, identifier)` nutzen und für tiefe Hierarchien den Pfad im `identifier` kodieren
- **SOLLTE [SHOULD]** das Klassen-Attribut `name` auf einen menschenlesbaren Source-Namen setzen — fehlt es, fällt HA auf den Domain-String zurück
- **KANN [MAY]** `thumbnail`, `children_media_class` und `not_shown` an Knoten setzen sowie `item.target_media_player` zur URL-Individualisierung nutzen
- **MUSS [MUST]** `Unresolvable`/`BrowseError` mit `translation_domain`/`translation_key`/`translation_placeholders` werfen, wenn die Fehlermeldung übersetzbar sein soll (siehe `ha/translations`), Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `media_source.py` existiert; `async_get_media_source(hass) -> MediaSource` ist Top-Level-Async und liefert eine `MediaSource`-Subklasse; beide Methoden sind implementiert; `async_browse_media` liefert die Wurzel bei leerem `identifier` und wirft `BrowseError`; `async_resolve_media` liefert ein `PlayMedia` mit `mime_type` und wirft `Unresolvable`; jeder Knoten trägt `MediaClass` und `can_play`/`can_expand`; Wurzel-Items setzen `identifier=None`; keine `manifest.json`-Änderung war für die Discovery nötig
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/media-source` liefern, plus die geänderten Datei-Pfade

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Media-Source pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** die Media-Player-Entity-Konsumentenseite implementieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] `media_source.py` existiert im Integrations-Ordner; keine `manifest.json`-Änderung war für die Discovery nötig
- [ ] `async_get_media_source(hass) -> MediaSource` ist als Top-Level-Async-Funktion exportiert und liefert eine `MediaSource`-Subklasse (über `super().__init__(DOMAIN)` gebunden)
- [ ] Die Subklasse implementiert `async_browse_media(item)` (liefert `BrowseMediaSource`) und `async_resolve_media(item)` (liefert `PlayMedia`)
- [ ] `async_browse_media` liefert bei leerem `item.identifier` den Wurzelknoten und wirft `BrowseError` bei nicht abrufbarer Struktur
- [ ] `async_resolve_media` liefert ein `PlayMedia(url, mime_type)` mit gesetztem MIME-Type und wirft `Unresolvable` bei nicht auflösbarem Item
- [ ] Jeder `BrowseMediaSource`-Knoten trägt eine `MediaClass` sowie korrekt gesetzte `can_play`/`can_expand`-Flags; Wurzel-Items setzen `identifier=None`, URIs werden über `generate_media_source_id` konstruiert
- [ ] Bericht nennt die geänderten Datei-Pfade

## Offene Fragen

- **Hierarchie-Encoding**: `ha/media-source` nennt `/` im `identifier` nur als gängiges Muster (SOLLTE). Soll der Skill ein verbindliches Separator-Schema vorgeben oder bei SOLLTE bleiben? Aktuell folgt er der Spec und fragt im Zweifel nach.
- **`mime_type`-Ableitung**: Wann leitet der Skill den `mime_type` automatisch aus der Dateiendung ab und wann fragt er ihn explizit ab? Aktuell fall-zu-fall.
- **`target_media_player`-Individualisierung**: Wann ist die URL-Individualisierung über den Ziel-Player nötig? `ha/media-source` formuliert es als KANN; der Skill fragt nur bei beschriebenem Bedarf.
