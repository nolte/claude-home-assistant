# HA-Integration: Entity-Plattform-Typen

Status: draft

## Kontext

Eine Custom Integration deklariert ihre Entitäten über typisierte Plattform-Basisklassen: `SensorEntity`, `BinarySensorEntity`, `ClimateEntity`, `LightEntity`, `CoverEntity` und die übrigen aus der HA-Plattform-Liste. Die generische Entity-Architektur — Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, das `EntityDescription`-Pattern, Entity-Kategorien und die Coordinator-Anbindung — ist bereits in `ha/entity-architecture` festgeschrieben und wird **hier nicht wiederholt**. Diese Spec adressiert ausschließlich die **plattform-spezifische Typisierung**: welche Plattform eine Capability korrekt abbildet, und welche Felder diese Plattform aus einem **geschlossenen Enum** erwartet, damit UI, Sprachsteuerung, Einheiten-Konvertierung und Long-Term-Statistics funktionieren.

Drei Mechanismen tragen diese Typisierung. **`device_class`** klassifiziert eine Entity aus einem plattform-eigenen Enum (`SensorDeviceClass`, `BinarySensorDeviceClass`, `CoverDeviceClass`, …); HA leitet daraus Default-Namen, Icons, erlaubte Einheiten und die Voice-/Cloud-Anbindung ab. **`state_class`** plus `native_unit_of_measurement`, `native_value` und `suggested_display_precision` machen einen numerischen Sensor zur Long-Term-Statistics-Quelle. **`supported_features`** ist eine Bitmaske aus einem plattform-eigenen Feature-Enum (`ClimateEntityFeature`, `LightEntityFeature`, `CoverEntityFeature`); jedes gesetzte Flag verspricht eine implementierte Methode. Light-Color-Modes (`supported_color_modes` / `color_mode`) sind das kanonische Beispiel für eine Menge **wechselseitig ausschließender** Capability-Optionen.

`developers.home-assistant` macht diese Typisierung zur Quality-Scale-Pflicht: die Regel `entity-device-class` (Gold) verlangt, dass Entitäten Device-Classes setzen, wo immer möglich, weil sie Einheiten-Umschaltung, Voice-Control, Cloud-Export (Google Assistant, Alexa) und UI-Darstellung steuern. Diese Spec überführt die Plattform-Doku in eine generische Verpflichtung für den Skill-Output.

Quality-Scale-Marker:
- **Gold**: korrekt gesetzte `device_class` je Plattform, wo immer ein passendes Enum-Member existiert (`entity-device-class`).

## Ziele

- Die Plattformwahl an die abzubildende Capability binden — Mess-/Read-Only-Wert → `sensor`, Zwei-Zustands-Wert → `binary_sensor`, schaltbarer Aktor → `switch`/`light`, Öffnung → `cover` usw.
- `device_class` als Pflichtfeld je Plattform aus dem geschlossenen Enum setzen, damit UI, Einheiten und Voice korrekt funktionieren (`entity-device-class`, Gold)
- Numerische Sensoren mit `state_class` + `native_unit_of_measurement` + `native_value` (+ `suggested_display_precision`) Long-Term-Statistics-fähig machen
- `supported_features`-Bitmasken so setzen, dass nur tatsächlich implementierte Features beworben werden — jedes Flag hat seine `async_`-Methode
- Light-Color-Modes (`supported_color_modes` / `color_mode`) als wechselseitig ausschließende Capability-Menge korrekt deklarieren
- Generierten Code Gold-konform bezüglich Device-Class-Abdeckung aus dem Skill-Output starten lassen

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, verbotene `entity_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- HA-Translation-Format selbst (`strings.json`-Aufbau, `entity.<platform>.<key>.name`, State-Übersetzungen) — eigene Spec `ha/translations`
- Icon-Auswahl und Icon-Translations (`icons.json`, `default`/`state`) — eigene Spec `ha/icons`; diese Spec setzt nur die `device_class`, aus der HA Default-Icons ableitet
- `RestoreSensor`/`RestoreEntity`-Persistenz von `native_value` über Restart — eigene Folge-Spec, sobald konkret nötig
- Plattformen außerhalb der hier behandelten Beispiele (`fan`, `number`, `select`, `valve`, `humidifier`, …) im Detail — die generischen Regeln gelten analog, eine erschöpfende Pro-Plattform-Tabelle ist nicht Ziel

## Anforderungen

### Plattformwahl

- **MUSS [MUST]** für jede abzubildende Capability genau eine Plattform aus dem HA-Plattform-Katalog wählen, deren Semantik die Capability trägt — ein read-only Messwert ist `sensor`, ein Zwei-Zustands-Wert ist `binary_sensor`
- **MUSS [MUST]** für einen Wert, der genau zwei Zustände hat, `binary_sensor` (mit `is_on`) statt eines `sensor` mit Text-State verwenden — `binary_sensor` ist auf zwei Zustände definiert
- **MUSS [MUST]** für ein steuerbares Licht `light` (mit `color_mode`/`supported_color_modes`) und nicht `switch` verwenden, sobald Helligkeit oder Farbe steuerbar sind — `switch` kann nur an/aus
- **SOLLTE [SHOULD]** für eine Öffnung oder Abdeckung (Garagentor, Rollladen, Markise) `cover` verwenden; die `cover`-Doku verweist explizit darauf, andere Gerätetypen (z. B. eine reine Sollwert-Stellgröße) stattdessen als `number` abzubilden
- **SOLLTE [SHOULD]** für einen numerischen Sollwert ohne Öffnungs-Semantik `number` statt `cover` verwenden — die `cover`-Doku grenzt das ausdrücklich ab
- **MUSS NICHT [MUST NOT]** mehrere wechselnde Werte in `extra_state_attributes` eines einzelnen Sensors zusammenfassen, wo separate Entitäten korrekt wären — die Sensor-Doku verlangt für zusätzliche, sich ändernde Werte eine eigene `sensor`-Entity

### `device_class` (geschlossene Enums)

- **MUSS [MUST]** auf jeder Entity, für die ein passendes Enum-Member existiert, die `device_class` aus dem **plattform-eigenen geschlossenen Enum** setzen (`SensorDeviceClass`, `BinarySensorDeviceClass`, `CoverDeviceClass`, …) — Quality-Regel `entity-device-class`, Gold
- **MUSS [MUST]** ausschließlich Enum-Member verwenden, niemals einen frei gewählten String — `device_class` ist je Plattform auf das dokumentierte Enum geschlossen
- **MUSS [MUST]** bei gesetzter Sensor-`device_class` eine zur Klasse passende `native_unit_of_measurement` zurückgeben — die Sensor-Doku bindet jede Klasse an erlaubte Einheiten (z. B. `TEMPERATURE` → °C/°F/K, `POWER` → mW/W/kW/…)
- **MUSS [MUST]** für `SensorDeviceClass.ENUM` die `options`-Liste setzen und darf diese Klasse nicht mit `state_class` oder `native_unit_of_measurement` kombinieren — so dokumentiert die Sensor-Doku
- **SOLLTE [SHOULD]** die `device_class` über die `EntityDescription` (`device_class=...`) statt als `_attr_device_class` setzen, wenn die Plattform das `EntityDescription`-Pattern nutzt (Setz-Mechanik siehe `ha/entity-architecture`)
- **MUSS NICHT [MUST NOT]** `BinarySensorDeviceClass.UPDATE` verwenden, wo eine `update`-Entity korrekt wäre — die Binary-Sensor-Doku rät ausdrücklich davon ab

### Sensor: `state_class`, Units & Präzision

- **MUSS [MUST]** für jeden numerischen `sensor`, der in Long-Term-Statistics einfließen soll, `state_class` auf genau einen der Werte `SensorStateClass.MEASUREMENT`, `SensorStateClass.TOTAL` oder `SensorStateClass.TOTAL_INCREASING` setzen
- **MUSS [MUST]** `SensorStateClass.MEASUREMENT` für einen Messwert der Gegenwart wählen (aktuelle Temperatur, Leistung, Restkapazität) und nicht für aufakkumulierte Werte — so die Sensor-Doku
- **MUSS [MUST]** `SensorStateClass.TOTAL_INCREASING` für einen monoton steigenden Zähler, der periodisch auf 0 zurücksetzt (Tages-Gasverbrauch, Lifetime-Energie), und `SensorStateClass.TOTAL` für einen Wert, der steigen und fallen kann, verwenden
- **MUSS [MUST]** den Wert über `native_value` in der `native_unit_of_measurement` zurückgeben (nicht über ein generisches `state`/`unit_of_measurement`-Override) — HA übernimmt die Nutzer-seitige Einheiten-Konvertierung
- **SOLLTE [SHOULD]** `suggested_display_precision` setzen, wenn die rohe `native_value` mehr Nachkommastellen liefert, als sinnvoll angezeigt werden — das Feld steuert nur die Anzeige, nicht den gespeicherten Wert
- **SOLLTE [SHOULD]** `state_class = MEASUREMENT` nicht mit den Device-Classes setzen, die die Sensor-Doku für Min/Max/Mean ausschließt (`DATE`, `ENUM`, `ENERGY`, `GAS`, `MONETARY`, `TIMESTAMP`, `VOLUME`, `WATER`)
- **MUSS NICHT [MUST NOT]** eine eigene, von den HA-Konstanten abweichende Unit-Schreibweise setzen (z. B. `KWh` statt `kWh`) — die Sensor-Doku warnt, dass HA das als Unit-Wechsel interpretiert und die Statistik aussetzt

### `supported_features`-Bitmasken

- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus dem **plattform-eigenen Feature-Enum** (`ClimateEntityFeature`, `LightEntityFeature`, `CoverEntityFeature`, …) setzen, niemals als rohe Ganzzahl
- **MUSS [MUST]** ausschließlich Flags setzen, deren zugehörige Methode tatsächlich implementiert ist — die `cover`-Doku verlangt z. B. `async_open_cover` nur und genau dann, wenn `CoverEntityFeature.OPEN` gesetzt ist (analog `CLOSE`, `SET_POSITION`, `STOP`, Tilt-Varianten)
- **MUSS [MUST]** bei gesetztem `ClimateEntityFeature`-Flag die von der Climate-Doku als „Required by …" markierten Properties bereitstellen (z. B. `FAN_MODE` → `fan_mode` + `fan_modes`, `TARGET_TEMPERATURE_RANGE` → `target_temperature_high`/`_low`)
- **MUSS [MUST]** für `climate`-Entitäten ausschließlich die eingebauten `HVACMode`-Member in `hvac_modes` verwenden — die Doku verbietet eigene Modes und verweist für zusätzliche Bedürfnisse auf Presets
- **MUSS NICHT [MUST NOT]** ein Feature-Flag „auf Vorrat" setzen, dessen Methode (noch) nicht implementiert ist — ein beworbenes, aber nicht bedienbares Feature bricht UI und Voice-Anbindung
- **SOLLTE [SHOULD]** die Feature-Maske über die `EntityDescription` oder ein `_attr_supported_features`-Klassenattribut setzen, je nachdem ob die Plattform das `EntityDescription`-Pattern nutzt (siehe `ha/entity-architecture`)

### Color-Modes (Light) als Beispiel

- **MUSS [MUST]** auf jeder `light`-Entity sowohl `supported_color_modes` (eine `set[ColorMode]`) als auch `color_mode` setzen — die Light-Doku wirft sonst beim State-Schreiben einen Fehler
- **MUSS [MUST]** `color_mode` auf einen Wert aus `supported_color_modes` setzen (Ausnahme: laufender Effekt, der einen restriktiveren Mode setzen darf)
- **MUSS [MUST]** `ColorMode.ONOFF` und `ColorMode.BRIGHTNESS` jeweils als **einzigen** Mode führen, wenn unterstützt — die Light-Doku schreibt vor, dass diese beiden Modes nicht mit anderen kombiniert werden
- **MUSS NICHT [MUST NOT]** `ColorMode.WHITE` ohne mindestens einen Farb-Mode (`HS`, `RGB`, `RGBW`, `RGBWW` oder `XY`) und nicht zusammen mit `ColorMode.COLOR_TEMP` setzen — so die Light-Doku
- **SOLLTE [SHOULD]** `LightEntityFeature.EFFECT`/`FLASH`/`TRANSITION` nur setzen, wenn das Gerät die jeweilige Fähigkeit tatsächlich bedient — dieselbe Feature-↔-Implementierungs-Regel wie oben

### Konsistenz Feature-Flag ↔ Implementierung

- **MUSS [MUST]** für jedes gesetzte `supported_features`-Flag sicherstellen, dass die korrespondierende `async_`-Methode (oder ihre synchrone Variante) in der Entity-Klasse existiert — die Plattform-Docs koppeln Flag und Methode eins-zu-eins
- **MUSS [MUST]** für jede von einem Flag oder einer `device_class` als „Required" markierte Property eine Implementierung bereitstellen (z. B. `native_value` für `sensor`, `is_closed` für `cover`, `hvac_mode`/`hvac_modes` für `climate`)
- **SOLLTE [SHOULD]** `device_class`, `supported_features` und andere Capability-Attribute zur Laufzeit nur ändern, wenn unbedingt nötig, und dann in maßvollem Intervall — die Entity-Doku warnt, dass solche Änderungen z. B. Voice-Assistant-Integrationen zur Resynchronisierung zwingen
- **MUSS NICHT [MUST NOT]** eine Plattform-Capability widersprüchlich deklarieren (Flag gesetzt, Property/Methode fehlt; `device_class` gesetzt, Unit unpassend) — solche Inkonsistenzen führen zu Laufzeitfehlern oder stiller UI-Fehldarstellung

## Akzeptanzkriterien

- [ ] Jede Capability ist auf der semantisch passenden Plattform abgebildet (Messwert → `sensor`, Zwei-Zustands → `binary_sensor`, dimm-/farbfähiges Licht → `light`, Öffnung → `cover`)
- [ ] Jede Entity mit passendem Enum-Member setzt `device_class` aus dem geschlossenen Plattform-Enum (Gold-Regel `entity-device-class`)
- [ ] Keine `device_class` ist als frei gewählter String gesetzt; jede gesetzte Sensor-`device_class` hat eine passende `native_unit_of_measurement`
- [ ] Jeder statistik-relevante numerische `sensor` setzt `state_class` auf `MEASUREMENT`, `TOTAL` oder `TOTAL_INCREASING` und liefert `native_value` in `native_unit_of_measurement`
- [ ] `suggested_display_precision` ist gesetzt, wo die rohe `native_value` zu viele Nachkommastellen liefert
- [ ] Keine Unit weicht in der Schreibweise von der HA-Konstante ab (z. B. kein `KWh` statt `kWh`)
- [ ] `supported_features` ist als bitweise-`|`-Kombination aus dem plattform-eigenen Feature-Enum gesetzt, nie als rohe Ganzzahl
- [ ] Für jedes gesetzte Feature-Flag existiert die korrespondierende `async_`-Methode; keine „auf Vorrat" gesetzten Flags
- [ ] Jede `light`-Entity setzt `supported_color_modes` und `color_mode`; `ONOFF`/`BRIGHTNESS` stehen jeweils allein, `WHITE` nie ohne Farb-Mode und nie mit `COLOR_TEMP`
- [ ] `climate`-Entitäten verwenden ausschließlich eingebaute `HVACMode`-Member; alle „Required by feature"-Properties sind implementiert
- [ ] Quality-Scale-Marker: **Gold** für korrekte Device-Class-Abdeckung je Plattform

## Offene Fragen

- **Pro-Plattform-Tabellen-Tiefe**: Diese Spec behandelt `sensor`, `binary_sensor`, `climate`, `light`, `cover` exemplarisch. Sollen `fan`, `number`, `select`, `valve`, `humidifier` jeweils eigene Folge-Specs bekommen, oder bleibt es bei der generischen Regel plus Verweis auf die HA-Docs?
- **Device-Class-Abdeckungs-Schwelle**: Die Gold-Regel sagt „wo immer möglich". Soll der Skill bei einer Entity ohne passendes Enum-Member explizit dokumentieren, warum keine `device_class` gesetzt ist, oder genügt das Weglassen?
- **`state_class`-vs-Device-Class-Konflikte automatisch prüfen**: Die Sensor-Doku schließt für `MEASUREMENT`-Statistik bestimmte Device-Classes aus. Soll der Skill diese Kombination aktiv verbieten oder nur warnen?
- **Color-Mode-Migration**: Wenn ein Gerät später Farbe nachrüstet, ändert sich `supported_color_modes`. Gehört eine Migrations-/Versionierungs-Konvention dafür in diese Spec oder in `ha/entity-architecture`?
- **Custom-Presets/Fan-Modes**: Climate erlaubt eigene Preset- und Fan-Mode-Strings (nicht aber eigene `HVACMode`). Soll die Spec eine Konvention für deren Translation-Keys vorschreiben (Schnittstelle zu `ha/translations`)?
