# HA-Integration: Entity-Architektur

Status: draft

## Kontext

Eine Entity in einer Custom Integration wird über drei zusammenwirkende Mechanismen identifiziert und benannt: eine **`unique_id`** (stabile Identifikation für das Entity-Registry, niemals UI-sichtbar), eine **`translation_key`-basierte Anzeigename** (übersetzbarer Anzeigename, wirkt zusammen mit `_attr_has_entity_name`), und die **automatisch von HA generierte `entity_id`** (technische ID in `domain.<slug>`-Form, abgeleitet aus Device-Name und Entity-Name zur Laufzeit). Das manuelle Setzen von `self.entity_id` ist ein Anti-Pattern, weil es die HA-eigene Slug-Logik umgeht und eine sprach-/installations­abhängige ID festschreibt.

Parallel dazu hat HA das **`EntityDescription`-Pattern** etabliert: statt für jeden Datapoint eine eigene Entity-Klasse zu schreiben, deklariert die Integration eine Tupel-Liste mit `<Plattform>EntityDescription`-Instanzen, und eine generische Entity-Klasse iteriert sie. Das macht die Integration deklarativ statt imperativ: neue Entitäten kommen als Eintrag in die Tupel-Liste, nicht als neue Klasse.

`nolte/kamerplanter-ha` validiert das Triple — `unique_id`-Format, `translation_key`-basierte Namen, `EntityDescription`-Pattern — über fünf Plattformen (sensor, binary_sensor, button, calendar, todo) hinweg konsistent. Diese Spec überführt die Konvention in eine generische Verpflichtung. Die Device-Hierarchie selbst (DeviceInfo, `via_device`) lebt in der parallelen Spec `ha/device-registry`.

Quality-Scale-Marker:
- **Bronze**: stabile, nicht-zufällige `unique_id` pro Entity.
- **Silver**: `_attr_has_entity_name = True` plus `translation_key`-basierte Namen statt Hard-Coded-Strings; `EntityDescription`-Pattern statt einer Klasse pro Datapoint.

## Ziele

- Eine `unique_id` pro Entity festschreiben, die Re-Discovery, Server-Restart und HA-Restart übersteht
- `_attr_has_entity_name = True` als Default — HA komponiert dann den Display-Namen aus Device-Name + Entity-Name, der Entity-Name kommt aus `translation_key`
- Manuelle `self.entity_id`-Zuweisung verbieten — HA generiert die `entity_id` aus dem (englischen) Display-Namen automatisch
- Das `EntityDescription`-Pattern als Standard­form für Plattform-Setup festlegen, sodass das Hinzufügen einer neuen Entity-Variante eine Datenzeile statt eine neue Klasse ist
- Pflicht-Entity-Category-Markierungen (`CONFIG`, `DIAGNOSTIC`) sichtbar machen, damit die HA-UI Entitäten korrekt einsortiert
- Generierten Code Bronze-/Silver-konform aus dem Skill-Output starten lassen

## Nicht-Ziele

- DeviceInfo-Konstruktion und `via_device`-Hierarchie — eigene Spec `ha/device-registry`
- `RestoreEntity`-Pattern (Persistenz von State über Restart hinweg) — eigene Folge-Spec, sobald konkret nötig
- Custom-State-Class-Definition (`SensorStateClass.MEASUREMENT` vs. `TOTAL_INCREASING` vs. …) — gehört in plattform­spezifische Folge-Specs (`ha/sensor-platform`, …); diese Spec adressiert nur die plattform-übergreifende Entity-Architektur
- Lovelace-spezifische Anzeige-Logik (Card-Layout, Custom-Cards) — eigene Spec `ha/lovelace-card-patterns`
- HA-Translation-Format selbst (`strings.json`-Aufbau, Sync zu `translations/<lang>.json`) — eigene Spec `ha/translations`

## Anforderungen

### Base-Entity-Klasse

- **MUSS [MUST]** in `entity.py` eine plattform-übergreifende Base-Entity-Klasse definieren, die von `homeassistant.helpers.update_coordinator.CoordinatorEntity` (oder `TimestampedDataUpdateCoordinator`-Variante, falls genutzt) erbt
- **MUSS [MUST]** in der Base-Klasse `_attr_has_entity_name = True` als Klassen-Attribut setzen — alle abgeleiteten Entitäten erben das
- **MUSS [MUST]** in der Base-Klasse einen typisierten Constructor anbieten, der mindestens `coordinator`, `entry_id` und ein `device_info: DeviceInfo` entgegennimmt und `self._attr_device_info = device_info` setzt (siehe `ha/device-registry`)
- **SOLLTE [SHOULD]** in der Base-Klasse den `entry_id` als Instanz-Attribut speichern (`self._entry_id = entry_id`) — wird für `unique_id`-Konstruktion und Diagnostics gebraucht
- **MUSS NICHT [MUST NOT]** Plattform-spezifische Logik in der Base-Klasse unterbringen — die Base-Klasse bleibt agnostisch zu Sensor / Binary Sensor / Button / …

### `_attr_has_entity_name` und `translation_key`

- **MUSS [MUST]** auf jeder Entity `_attr_has_entity_name = True` setzen (typischerweise geerbt aus der Base-Klasse, siehe oben)
- **MUSS [MUST]** auf jeder Entity einen `translation_key` setzen — entweder als `_attr_translation_key = "<key>"` oder über die `EntityDescription.translation_key`-Property
- **MUSS [MUST]** der `translation_key` in `strings.json` unter `entity.<platform>.<key>.name` einen Eintrag haben (siehe `ha/translations`)
- **MUSS NICHT [MUST NOT]** `_attr_name` als Hard-Coded-String setzen — Hard-Coded-Namen verhindern Übersetzungen und produzieren in jeder UI-Sprache denselben Text
- **KANN [MAY]** für die **Haupt-Device-Entity** `_attr_name = None` setzen, sodass die Entity nur den Device-Namen trägt (typisch für die Kern-Entity, die ein Device repräsentiert)

### `unique_id`

- **MUSS [MUST]** auf jeder Entity einen `unique_id` setzen — entweder als `_attr_unique_id = "..."` im Constructor oder über die `EntityDescription.key`-Komposition
- **MUSS [MUST]** den `unique_id` so konstruieren, dass er den Entry-Scope, den Resource-Typ, den Resource-Slug und einen Suffix enthält:
  - Format: `{entry_id}_{resource_type}_{resource_slug}_{suffix}`
  - Beispiele: `{entry_id}_server_refresh_all`, `{entry_id}_<resource>_<slug>_<descriptor>`
- **MUSS [MUST]** den `unique_id` über die Lebenszeit eines Entries stabil halten — eine Entity, die heute `_phase` heißt und morgen `_growth_phase`, ist eine andere Entity aus Sicht des Entity-Registries und führt zu Datenverlust
- **MUSS NICHT [MUST NOT]** eine Zufalls-`uuid` als `unique_id` verwenden — Zufallsgenerierung bricht über Restart hinweg
- **MUSS NICHT [MUST NOT]** den `unique_id` aus der `entity_id` ableiten — die `entity_id` ist sprach- und installations­abhängig

### Verbotene `entity_id`-Zuweisung

- **MUSS NICHT [MUST NOT]** `self.entity_id = "..."` manuell setzen — HA generiert die `entity_id` aus dem Device-Namen und dem Entity-Namen automatisch beim Registry-Eintritt
- **SOLLTE [SHOULD]** sicherstellen, dass der Display-Name in `strings.json` (Englisch als Source of Truth) so gewählt ist, dass die generierte `entity_id` lesbar ist — die `entity_id` basiert auf dem **System-Sprach-Display-Namen** zur Erstregistrierung; eine englische Quell-Sprache produziert stabile, sprach­unabhängige IDs (siehe `ha/translations` für die Sprach-Konvention)
- **KANN [MAY]** in Sonderfällen `_attr_suggested_object_id` setzen, wenn der HA-generierte Slug objektiv schlecht ist; das ist eine Suggestion, die HA bei Konflikten überschreibt

### `EntityDescription`-Pattern

- **MUSS [MUST]** für jede Plattform mit mehr als zwei Datapoints `EntityDescription`-Tupel-Listen verwenden statt einer Klasse pro Datapoint
- **MUSS [MUST]** die Tupel-Liste als Top-Level-Konstante definieren: `<DOMAIN>_<PLATFORM>_<ROLE>_DESCRIPTIONS: tuple[<Platform>EntityDescription, ...] = (...)`
- **MUSS [MUST]** in jeder `EntityDescription` mindestens `key` und `translation_key` setzen — weitere Felder (`device_class`, `state_class`, `native_unit_of_measurement`, `entity_category`, `icon` als Fallback) je nach Plattform
- **MUSS [MUST]** in der generischen Entity-Klasse `entity_description: <Platform>EntityDescription` als Class-Annotation setzen und `self.entity_description = description` im Constructor zuweisen
- **SOLLTE [SHOULD]** die Datapoint-Extraktion (`_handle_coordinator_update` oder `native_value`-Property) generisch über `entity_description.key` aufgelöst implementieren statt mit `if/elif`-Ketten pro Key
- **KANN [MAY]** für sehr eng gekoppelte Spezial-Entities (z. B. ein einzelner Refresh-Button) eine einzelne dedizierte Klasse statt `EntityDescription` führen

### Entity-Kategorien

- **SOLLTE [SHOULD]** Entitäten, die **Konfiguration ändern** (Refresh-Button, Modus-Selector, Schwellwert-Number), als `EntityCategory.CONFIG` markieren — die HA-UI listet sie dann unter "Configuration" statt unter "Sensors"
- **SOLLTE [SHOULD]** Entitäten, die **diagnostische Read-Only-Information** liefern (Sensor-Offline-Status, Last-Update-Timestamp, Firmware-Version), als `EntityCategory.DIAGNOSTIC` markieren
- **KANN [MAY]** Entitäten ohne `entity_category` lassen — sie landen dann in der Standard-Sektion (Sensoren, Aktoren, …) ohne Sondereinordnung

### Coordinator-Anbindung

- **MUSS [MUST]** Entitäten an genau einen Coordinator binden (über die Base-Klasse, die `CoordinatorEntity` erbt)
- **MUSS [MUST]** in der Plattform-`async_setup_entry` den Coordinator über `entry.runtime_data.coordinators["<role>"]` lesen (siehe `ha/runtime-data-pattern` und `ha/coordinator-patterns`)
- **SOLLTE [SHOULD]** Entitäten, die Daten aus mehreren Coordinators kombinieren, an den **Hauptcoordinator** binden und die Daten anderer Coordinators on-demand über `runtime_data` lesen — Multi-Coordinator-Subscription ist HA-seitig nicht direkt unterstützt
- **MUSS NICHT [MUST NOT]** in `_handle_coordinator_update` blocking I/O ausführen; der Callback läuft im Event-Loop und muss synchron mit den Coordinator-Daten arbeiten

## Akzeptanzkriterien

- [ ] `entity.py` enthält eine plattform-übergreifende Base-Entity-Klasse mit `_attr_has_entity_name = True` und `_attr_device_info`-Setzung
- [ ] Jede Plattform-Entity erbt von der Base-Klasse
- [ ] Jede Entity hat einen `translation_key` (entweder `_attr_translation_key` oder über `EntityDescription`)
- [ ] Jede Entity hat einen `unique_id` im Format `{entry_id}_{resource_type}_{resource_slug}_{suffix}`
- [ ] Kein Code im `custom_components/<domain>/`-Ordner setzt `self.entity_id = "..."`
- [ ] Plattformen mit > 2 Datapoints verwenden `EntityDescription`-Tupel-Listen
- [ ] Entitäten, die Konfiguration ändern, sind als `EntityCategory.CONFIG` markiert
- [ ] Entitäten, die diagnostische Read-Only-Info liefern, sind als `EntityCategory.DIAGNOSTIC` markiert
- [ ] `_handle_coordinator_update` enthält keine blocking I/O
- [ ] Quality-Scale-Marker: **Bronze** für stabile `unique_id`, zusätzlich **Silver** für `_attr_has_entity_name = True` + `translation_key` + `EntityDescription`-Pattern

## Offene Fragen

- **Plattform-Schwelle für `EntityDescription`-Pflicht**: „mehr als zwei Datapoints" ist eine Heuristik. Sollte die Schwelle bei 1 (immer) oder bei 5 (großzügiger) liegen? `kamerplanter-ha` verwendet das Pattern faktisch ab dem ersten Datapoint pro Plattform.
- **Suggested-Object-ID-Verbot**: `_attr_suggested_object_id` ist heute als KANN formuliert. Soll es ein vollständiges Verbot werden, weil es das Slug-Verhalten unvorhersehbar macht?
- **Translation-Keys für Sub-States**: `kamerplanter-ha` definiert pro Sensor-Translation-Key auch `state.<value>`-Mappings (z. B. Phase-Werte). Gehört diese Konvention in diese Spec oder in `ha/translations`?
- **Multi-Coordinator-Subscriptions**: HA hat experimentelle APIs für Multi-Coordinator-Listening. Soll die Spec sie zulassen, sobald sie stabil sind, oder bleibt die Single-Coordinator-Bindung Pflicht?
- **`RestoreEntity`-Schwelle**: Wann verlangt die Spec den `RestoreEntity`-Mixin (Persistenz über HA-Restart)? Aktuell als Nicht-Ziel; eine Folge-Spec entsteht, sobald die erste konkrete Entity-Klasse das braucht.
