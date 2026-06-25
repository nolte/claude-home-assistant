# Skill: `ha-entity-platform-add`

Status: draft

## Kontext

`ha/entity-platform-types` klassifiziert den HA-Plattform-Katalog in **deklarative Read-Type-Plattformen** (`sensor`, `binary_sensor`, `button` über `EntityDescription`-Tabellen) und **aktive, befehlsgetriebene Plattformen**, deren Entity async **Command-/Set-Methoden** exponiert: `climate`, `cover`, `light`, `fan`, `lock`, `media_player`, `vacuum`, `valve`, `humidifier`, `water_heater`, `siren`, `lawn_mower` u. a. Bidirektionale Plattformen wie `switch`, `number`, `select`, `calendar`, `todo` sind ebenfalls aktiv — ihre Familien-Spec fordert eine Pflicht-Set-Methode (`async_set_native_value`/`async_select_option`/…) — lassen sich aber **entweder** rein deklarativ als `EntityDescription`-Tabelle (dann `ha-entity-description-mapper`) **oder** als volle aktive Entity-Klasse mit handgeschriebener Set-Methode (dann dieser Skill) ausführen; die Grenze ist die **Autoring-Form**, nicht die Domäne. Die aktiven Plattformen verteilen sich auf Familien-Specs: `ha/entity-platforms-controls` (`switch`/`button`/`scene`/`siren`/`valve`/`lock`/`remote`), `ha/entity-platforms-climate` (`fan`/`humidifier`/`water-heater`; `climate` selbst in `ha/entity-platform-types`), `ha/entity-platforms-devices` (`alarm_control_panel`/`vacuum`/`lawn_mower`/`calendar`/`todo`/Infrarot/Funk), `ha/entity-platforms-media` (`media_player`/`camera`/`image`), `ha/entity-platforms-voice` (`stt`/`tts`/`wake_word`/`assist_satellite`/`ai_task`/`notify`), `ha/entity-platforms-inputs` (`number`/`select`/`text`/`date`/`time`/`datetime`) und `ha/entity-platforms-sensors` (`weather`/`device_tracker`/`event`/`update`). Bislang gibt es keinen Skill, der eine aktive Plattform-Entity scaffoldet.

Dieser Skill scaffoldet **eine** aktive Plattform-Entity in einer **bestehenden** Integration: das Plattform-Modul `<platform>.py` mit der Entity-Subklasse (`ClimateEntity` / `CoverEntity` / `LightEntity` / …), die `EntityDescription` (wo die Familie eine nutzt), die `_attr_supported_features`-/`supported_features`-Bitmaske aus dem plattform-eigenen `*EntityFeature`-Enum, die von der Domäne geforderten async Command-Methoden (`async_turn_on`/`async_set_temperature`/`async_open_cover`/`async_set_hvac_mode` …), das `async_setup_entry`-Platform-Setup, das die Entities zum Coordinator hinzufügt, sowie die State-/Attribut-Properties — spec-konform zu `ha/entity-platform-types` plus der gewählten Familien-Spec. Der Skill **MUSS [MUST]** vor der Generierung Ziel-Domäne und Familie bestätigen lassen.

## Scope

Scaffolding genau einer aktiven Plattform-Entity pro Lauf in einer bestehenden `custom_components/<domain>/`-Integration: das Modul `<platform>.py` mit der Entity-Subklasse, optionaler `EntityDescription`, der `supported_features`-Bitmaske aus dem `*EntityFeature`-Enum, den geforderten async Command-Methoden, dem `async_setup_entry`-Platform-Setup und den State-/Attribut-Properties. Der Skill liest `ha/entity-platform-types` (Katalog: aktiv vs. deklarativ) und die zur gewählten Domäne passende Familien-Spec, und validiert.

## Ziele

- Aus einer beschriebenen Geräte-Capability die korrekte aktive Plattform (Domäne) und die zugehörige Familien-Spec wählen und spec-konform scaffolden
- Die Entity von der dokumentierten Plattform-Basisklasse ableiten (`ClimateEntity`/`CoverEntity`/`LightEntity`/`FanEntity`/`LockEntity`/`MediaPlayerEntity`/`StateVacuumEntity`/`ValveEntity`/`HumidifierEntity`/`WaterHeaterEntity`/`SirenEntity`/`LawnMowerEntity` …)
- `supported_features` als bitweise-`|`-Kombination aus dem plattform-eigenen `*EntityFeature`-Enum setzen, niemals als rohe Ganzzahl
- Für jedes gesetzte Feature-Flag die korrespondierende async Command-Methode implementieren — Eins-zu-eins-Kopplung Flag ↔ Methode, kein „auf Vorrat" gesetztes Flag
- Die je Domäne als **Required** markierten State-/Attribut-Properties bereitstellen und das `async_setup_entry`-Setup die Entities am Coordinator anhängen lassen

## Nicht-Ziele

- Rein deklarativ als `EntityDescription`-Tabelle ausgeführte Datapoints (Read-Type `sensor`/`binary_sensor`/`button` sowie die Tabellenform von `number`/`select`/`switch`/`calendar`/`todo` ohne handgeschriebene Command-/Set-Methode) — `ha-entity-description-mapper`
- Der Coordinator selbst (`DataUpdateCoordinator`-Anlage und Update-Mechanik) — `ha-coordinator-add`
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`
- Geräte-zentrierte Device-Automation-Trigger/Conditions/Actions — `ha-device-automation-add`
- Das generische Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`) und die Typisierungs-Mechanik im Detail — `ha/entity-architecture` bzw. `ha/entity-platform-types`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a climate / cover / light / fan / lock entity", „scaffold an active platform entity"
  - „implement async command methods for my <domain> entity"
  - „scaffolde eine aktive <Domain>-Entity", „füge eine Cover-/Light-/Fan-Entity hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Geräte-Capability (Prosa), aus der der Skill Plattform/Domäne und Familie ableitet
- **MUSS [MUST]** die Ziel-Domäne benennen und die Familie bestätigen lassen, bevor generiert wird
- **KANN [MAY]** erfassen: `platform`/`domain` direkt, die zu setzenden `*EntityFeature`-Flags, und ob die Familie eine `EntityDescription` nutzt

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** prüfen, dass die Entity als **aktive** Plattform-Klasse mit handgeschriebener async Command-/Set-Methode angelegt wird; ist es ein Read-Type-Datapoint oder eine rein deklarative `EntityDescription`-Tabellen-Abbildung ohne handgeschriebene Command-/Set-Methode, **MUSS [MUST]** der Skill auf `ha-entity-description-mapper` verweisen und abbrechen
- **MUSS [MUST]** `ha/entity-platform-types` lesen, daraus aktiv-vs-deklarativ und die Familie bestimmen, und die passende Familien-Spec (`ha/entity-platforms-controls` / `-climate` / `-devices` / `-media` / `-voice` / `-inputs` / `-sensors`) in voller Länge lesen
- **MUSS [MUST]** prüfen, dass ein Coordinator existiert oder eine `runtime_data`/`config_entry`-Anbindung erreichbar ist, an die `async_setup_entry` die Entities hängt; fehlt sie, **SOLLTE [SHOULD]** der Skill auf `ha-coordinator-add` verweisen
- **MUSS NICHT [MUST NOT]** ein bestehendes `<platform>.py`-Modul überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/entity-platform-types` + Familien-Spec)

- **MUSS [MUST]** das Plattform-Modul `<platform>.py` mit der von der Familien-Spec dokumentierten Entity-Basisklasse erzeugen
- **MUSS [MUST]** `async_setup_entry(hass, entry, async_add_entities)` implementieren, das die Entities anlegt und über `async_add_entities(...)` registriert, am Coordinator bzw. an der `config_entry.runtime_data` anknüpfend (Coordinator-Mechanik in `ha/entity-architecture` referenziert)
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus dem plattform-eigenen `*EntityFeature`-Enum setzen (`ClimateEntityFeature`/`CoverEntityFeature`/`LightEntityFeature`/`FanEntityFeature`/`LockEntityFeature`/`MediaPlayerEntityFeature`/`VacuumEntityFeature`/`ValveEntityFeature`/`HumidifierEntityFeature`/`WaterHeaterEntityFeature`/`SirenEntityFeature`/`LawnMowerEntityFeature`/…), niemals als rohe Ganzzahl
- **MUSS [MUST]** für jedes gesetzte Feature-Flag genau die in der Familien-Spec dokumentierte async Command-Methode implementieren (z. B. `CoverEntityFeature.OPEN` → `async_open_cover`, `ClimateEntityFeature.TARGET_TEMPERATURE` → `async_set_temperature`, `LockEntityFeature.OPEN` → `async_open`, `FanEntityFeature.SET_SPEED` → `async_set_percentage`, `MediaPlayerEntityFeature.PLAY` → `async_media_play`)
- **MUSS NICHT [MUST NOT]** ein Feature-Flag „auf Vorrat" setzen, dessen Command-Methode (noch) nicht implementiert ist — ein beworbenes, nicht bedienbares Feature bricht UI und Voice-Anbindung
- **MUSS [MUST]** die je Domäne als **Required** markierten State-/Attribut-Properties bereitstellen (z. B. `hvac_mode`/`hvac_modes` für `climate`, `is_closed` für `cover`, `color_mode`/`supported_color_modes` für `light`, `activity` für `vacuum`/`lawn_mower`, `alarm_state` für `alarm_control_panel`) und ausschließlich die eingebauten Zustands-/Mode-Enums verwenden (z. B. nur eingebaute `HVACMode`-Member; `VacuumActivity`/`LawnMowerActivity`)
- **MUSS [MUST]** die `device_class` aus dem geschlossenen plattform-eigenen Enum setzen, wo ein passendes Member existiert (`CoverDeviceClass`, `ValveDeviceClass`, `HumidifierDeviceClass`, `MediaPlayerDeviceClass`, …) — nie als frei gewählter String
- **KANN [MAY]** eine `EntityDescription` erzeugen, wenn die Familie das `EntityDescription`-Pattern für die Plattform nutzt, und `supported_features`/`device_class` dort statt über `_attr_*` setzen (Setz-Mechanik siehe `ha/entity-architecture`)
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen, das generische Entity-Pattern nicht duplizieren (an `ha/entity-architecture` delegieren) und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `<platform>.py` existiert; die Entity leitet von der dokumentierten Basisklasse ab; `async_setup_entry` registriert Entities via `async_add_entities`; `supported_features` ist eine `*EntityFeature`-Bitmaske (keine rohe Ganzzahl); jedes gesetzte Flag hat seine async Command-Methode; alle **Required**-Properties sind implementiert; Zustands-/Mode-Enums sind eingebaut; gesetzte `device_class` stammt aus dem plattform-eigenen Enum
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien von `ha/entity-platform-types` und der gewählten Familien-Spec liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Gold** für korrekte Device-Class-Abdeckung je Plattform, `entity-device-class`)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Plattform-Entity pro Lauf scaffolden
- **MUSS NICHT [MUST NOT]** eine rein deklarative `EntityDescription`-Tabellen-Entity ohne handgeschriebene Command-/Set-Methode über dieses Skill scaffolden — dafür `ha-entity-description-mapper`
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet Plattform/Domäne und Familie ab (oder erfragt sie) und lässt die Ziel-Domäne + Familie vor der Generierung bestätigen
- [ ] `<platform>.py` existiert; die Entity leitet von der dokumentierten Plattform-Basisklasse ab
- [ ] `async_setup_entry` legt die Entities an und registriert sie via `async_add_entities`, am Coordinator/`runtime_data` anknüpfend
- [ ] `supported_features` ist eine bitweise-`|`-Kombination aus dem plattform-eigenen `*EntityFeature`-Enum, nie eine rohe Ganzzahl
- [ ] Für jedes gesetzte Feature-Flag existiert die korrespondierende async Command-Methode; kein „auf Vorrat" gesetztes Flag
- [ ] Alle je Domäne als **Required** markierten State-/Attribut-Properties sind implementiert; Zustands-/Mode-Enums sind eingebaut
- [ ] Gesetzte `device_class` stammt aus dem plattform-eigenen geschlossenen Enum; rein deklarative `EntityDescription`-Tabellen-Entities sind an `ha-entity-description-mapper` verwiesen
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **Gold** (`entity-device-class`)

## Offene Fragen

- **Familien-Spec-Auswahl-Automatik**: Soll der Skill die Familie strikt aus dem Domänen-Namen ableiten, oder bei Mehrdeutigkeit (z. B. `valve` vs. `cover`) immer rückfragen? Aktuell: ableiten und bestätigen lassen.
- **`EntityDescription` bei aktiven Plattformen**: Einige aktive Plattformen nutzen das `EntityDescription`-Pattern, andere nicht. Soll der Skill je Familie fest vorgeben, ob eine Description erzeugt wird, oder es pro Lauf entscheiden?
- **Coordinator-Pflicht**: Muss ein Coordinator zwingend existieren, oder darf der Skill auch eine direkte `config_entry.runtime_data`-Anbindung ohne Coordinator scaffolden? Aktuell: Coordinator bevorzugt, Verweis auf `ha-coordinator-add` bei Fehlen.
- **Infrarot/Funk-Sonderfall**: `ha/entity-platforms-devices` behandelt IR/Funk als Abstraktionsschicht ohne `supported_features`-Enum. Soll dieses Skill diese Sonderfälle abdecken oder an eine Folge-Spec verweisen?
