# Skill: `ha-entity-description-mapper`

Status: draft

## Kontext

Eine Plattform-Datei (`sensor.py`, `binary_sensor.py`, …) wächst typischerweise mit der Zahl ihrer Datapoints — neue Backend-Felder, neue Status-Werte, neue Metriken. Ohne deklarative Form kommen pro neuer Datapoint zehn Code-Zeilen hinzu (eigene Klasse, eigener `unique_id`, eigene `native_value`-Property). Das `EntityDescription`-Pattern aus `ha/entity-architecture` schneidet diesen Aufwand auf eine Tupel-Eintrag pro Datapoint.

Dieser Skill nimmt eine Datapoint-Beschreibung (z. B. eine CSV mit `name`, `device_class`, `state_class`, `unit`, `icon`) oder eine API-Antwort-Schema-JSON entgegen und produziert die `EntityDescription`-Tupel-Liste plus die generische Entity-Klasse plus die korrespondierenden `strings.json`-/`icons.json`-Einträge.

## Scope

Der Skill ergänzt eine **bestehende** Plattform-Datei (typisch `sensor.py`) um Datapoints. Er erzeugt keine neue Plattform-Datei (das macht `ha-integration-scaffold` beim ersten Lauf bzw. ein dediziertes `ha-platform-add` falls geplant). Er löscht keine bestehenden Datapoints und überschreibt keine vorhandenen `EntityDescription`-Einträge — bei Konflikt bricht er ab und meldet den Datapoint-Schlüssel als Treffer.

## Ziele

- Datapoint-zu-Code-Generierung deterministisch und konsistent zwischen Plattform-Code, `strings.json`, `translations/<lang>.json` und `icons.json` machen
- Cross-File-Konsistenz erzwingen: derselbe `translation_key` über alle vier Stellen
- HA-Quality-Scale-Markierung pro Datapoint sichtbar (Bronze/Silver/Gold) — der Skill schreibt sie in den Code-Kommentar neben jeden `EntityDescription`-Eintrag, sofern eine Quality-Scale-Konvention definiert ist
- Sanity-Validierung: `device_class` plus `unit` gegen HA-bekannte Klassen prüfen, `state_class` gegen `MEASUREMENT`/`TOTAL_INCREASING`/`TOTAL`

## Nicht-Ziele

- API-Antwort-Parser-Generierung — der Skill produziert die `EntityDescription`s und die Skelett-`_handle_coordinator_update`-Logik, aber nicht den konkreten Pfad-Lookup im Coordinator-Daten-Dict (das ist Konsumenten-Aufgabe)
- Multi-Plattform-Generierung in einem Aufruf — pro Aufruf eine Plattform-Datei
- Migration vom Klassen-pro-Datapoint-Stil auf `EntityDescription` — eigene Folge-Spec, falls überhaupt nötig
- Lovelace-Card-Anpassung — andere Skill-Achse (`ha-lovelace-card-scaffold`)

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add sensors from this datapoint list to the integration"
  - „generate EntityDescriptions from this CSV"
  - „add binary_sensors for the alert types"
  - „erweitere die Sensor-Plattform um folgende Datapoints"
- **MUSS NICHT [MUST NOT]** aktivieren bei:
  - Greenfield-Scaffold (`ha-integration-scaffold`)
  - Plattform-Datei nicht vorhanden (User soll erst Scaffold ausführen)
  - Custom-State-Class-Definition (User-Edit)

### Eingaben

- **MUSS [MUST]** erfassen:
  - `target_dir` — Repo-Root
  - `platform` — `sensor`, `binary_sensor`, `button`, `number`, `select`, `switch`, `calendar`, `todo`
  - `datapoints` — Liste von Datapoint-Dicts mit den Feldern `key`, `translation_key`, `device_class` (optional), `state_class` (optional), `native_unit_of_measurement` (optional), `entity_category` (optional), `default_icon` (`mdi:...`), `state_icons` (Dict, optional, nur Sensoren mit Enum-State)
- **SOLLTE [SHOULD]** Datapoint-Format-Hinweise geben: CSV-Eingabe wird als Tabelle interpretiert; JSON-Eingabe als Liste-of-Dicts; freier Text als „bitte als Tabelle einreichen" abgewiesen

### Validierung

- **MUSS [MUST]** für jedes Datapoint-Dict prüfen:
  - `key` ist lowercase-snake_case ASCII
  - `translation_key` ist lowercase-snake_case ASCII (kann gleich `key` sein)
  - `device_class` (sofern gesetzt) ist eine HA-bekannte Klasse für die jeweilige Plattform — z. B. `SensorDeviceClass.TEMPERATURE` für `sensor`
  - `state_class` (sofern gesetzt) ist `MEASUREMENT`, `TOTAL_INCREASING`, oder `TOTAL`
  - `native_unit_of_measurement` (sofern gesetzt) ist konsistent mit `device_class` (z. B. `°C`/`K` für `TEMPERATURE`)
- **MUSS [MUST]** Validierungs-Verstöße als ausführliche Liste melden und den Lauf abbrechen, statt halb generierte Datapoints zu schreiben

### Generator-Choreographie

- **MUSS [MUST]** in `<platform>.py` die `EntityDescription`-Tupel-Liste anhängen — Konstanten-Name typisch `<DOMAIN>_<PLATFORM>_DESCRIPTIONS` (PascalCase mit `_DESCRIPTIONS`-Suffix)
- **MUSS [MUST]** sicherstellen, dass eine generische Entity-Klasse existiert, die die Tupel-Liste konsumiert; falls noch nicht vorhanden, anhängen
- **MUSS [MUST]** in `strings.json` und allen `translations/<lang>.json` `entity.<platform>.<translation_key>.name` für jeden Datapoint ergänzen — Englisch in `strings.json`, Übersetzungen als TODO-Markierung in nicht-EN-Sprachen, sofern der User sie nicht mit­liefert
- **MUSS [MUST]** in `icons.json` `entity.<platform>.<translation_key>.default` (plus `state.<value>` falls Datapoint-Spec State-Icons enthält) ergänzen
- **SOLLTE [SHOULD]** im Plattform-Code einen Kommentar mit der HA-Quality-Scale-Stufe pro Datapoint setzen, sofern die Spec sie definiert (typisch Bronze für Datapoints ohne `device_class`, Silver für Datapoints mit korrektem `device_class`+`state_class`)

### Verbote

- **MUSS NICHT [MUST NOT]** existierende `EntityDescription`-Einträge mit gleichem `key` überschreiben — Konflikt führt zum Abbruch mit Hinweis
- **MUSS NICHT [MUST NOT]** Übersetzungen für nicht-EN-Sprachen erfinden — Nicht-EN-Übersetzungen werden als `<TODO: translate '<EN-Wert>'>` markiert, sofern der User sie nicht mit­liefert
- **MUSS NICHT [MUST NOT]** den `_handle_coordinator_update`-Pfad konkretisieren (welches Backend-Feld zu welchem Datapoint gemappt wird) — das ist Konsumenten-Aufgabe; der Skill liefert nur die generische Klasse mit `entity_description.key`-Lookup-Skelett

## Akzeptanzkriterien

- [ ] Die `EntityDescription`-Tupel-Liste in `<platform>.py` enthält alle gewünschten Datapoints
- [ ] `strings.json` enthält jeden Datapoint unter `entity.<platform>.<translation_key>.name`
- [ ] Jede `translations/<lang>.json` enthält jeden Datapoint mit Übersetzung oder `<TODO: …>`-Marker
- [ ] `icons.json` enthält jeden Datapoint unter `entity.<platform>.<translation_key>.default`; falls State-Icons gegeben, auch der `state:`-Block
- [ ] `ruff check custom_components/<domain>/<platform>.py` läuft fehlerfrei
- [ ] Validierungs-Verstöße werden als Liste gemeldet und blockieren den Lauf
- [ ] Existierende Datapoints bleiben unverändert

## Offene Fragen

- **`_handle_coordinator_update`-Konkretisierung**: Soll der Skill den Datapoint-zu-Backend-Feld-Lookup als Skelett liefern (z. B. `data.get(<key>)`), oder bleibt das User-Aufgabe?
- **Auto-Übersetzung**: Soll der Skill Maschinen-Übersetzungen liefern (z. B. via DeepL-API), oder bleibt es bei `<TODO>`-Markern?
- **State-Class-Heuristik**: Bei numerischen Datapoints — soll der Skill `MEASUREMENT` als Default vorschlagen, oder muss der User es immer angeben?
- **HA-Quality-Scale-Stufen-Format**: Wie genau wird die Stufe im Code-Kommentar markiert? Stil-Frage; aktuell offen.
