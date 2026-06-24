# HA-Integration: Entity-Plattformen (Klima-Familie)

Status: draft

## Kontext

Die generische Typisierungs-Mechanik — `device_class`, `supported_features` als Bitmaske aus einem plattform-eigenen Feature-Enum, und die Eins-zu-eins-Kopplung zwischen gesetztem Flag und implementierter Methode — ist in `ha/entity-platform-types` festgeschrieben; das generische Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, Coordinator-Anbindung) in `ha/entity-architecture`. Beide werden hier **nur referenziert, nicht wiederholt**. Die `climate`-Plattform selbst ist bereits in `ha/entity-platform-types` als Beispiel behandelt und ist **nicht** Gegenstand dieser Spec.

Diese Spec ist der **konkrete Plattform-Katalog für die klima-nahen Komfort-Plattformen**: `fan`, `humidifier` und `water-heater`. Diese Geräte gruppieren sich mit `climate` um Raumklima und Komfort, haben aber jeweils eine eigene Basisklasse (`FanEntity`, `HumidifierEntity`, `WaterHeaterEntity`), ein eigenes Feature-Enum und einen eigenen Satz Pflicht-Properties und -Methoden. Für jede dieser drei Plattformen legt diese Spec fest, wann sie zu wählen ist, welche `device_class` (sofern vorhanden), welche `supported_features`-Flags und welche Properties/Methoden der Skill-Output liefern muss, damit nur tatsächlich implementierte Capabilities beworben werden.

Übergreifende Verweise: HA-Translation-Format (`strings.json`, State-Übersetzungen für Modes/Operation-States) regelt `ha/translations`; Icon-Auswahl regelt `ha/icons`.

## Ziele

- Die Plattformwahl innerhalb der Klima-Familie an die abzubildende Capability binden — Luftbewegung → `fan`, Feuchte-Regelung → `humidifier`, Warmwasser-Bereitung → `water-heater`
- Für jede der drei Plattformen die korrekte Basisklasse (`FanEntity`, `HumidifierEntity`, `WaterHeaterEntity`) und — wo vorhanden — die `device_class` aus dem geschlossenen Enum setzen
- `supported_features`-Bitmasken aus dem plattform-eigenen Feature-Enum (`FanEntityFeature`, `HumidifierEntityFeature`, `WaterHeaterEntityFeature`) so setzen, dass nur Flags mit implementierter Methode beworben werden
- Die je Flag oder je Plattform als „Required" markierten Properties und Methoden vollständig bereitstellen
- Den generierten Code je Plattform konsistent zwischen Feature-Flag und Implementierung halten

## Nicht-Ziele

- Generische Typisierungs-Mechanik (`device_class`-Enum-Schließung, `supported_features`-Bitmasken-Regel, Feature-↔-Implementierungs-Kopplung) — vollständig in `ha/entity-platform-types`; diese Spec wendet sie nur konkret an
- Die `climate`-Plattform selbst — bereits als Beispiel in `ha/entity-platform-types` behandelt
- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`
- HA-Translation-Format für Mode-/Operation-State-Strings (`strings.json`, State-Übersetzungen) — eigene Spec `ha/translations`
- Icon-Auswahl und Icon-Translations (`icons.json`) — eigene Spec `ha/icons`

## Anforderungen

### `fan`

- **MUSS [MUST]** eine Fan-Entity von `FanEntity` ableiten, wenn das Gerät Vektoren eines Ventilators steuert (Geschwindigkeit, Richtung, Oszillation) — so die Fan-Doku
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `FanEntityFeature` setzen (`SET_SPEED`, `PRESET_MODE`, `OSCILLATE`, `DIRECTION`, `TURN_ON`, `TURN_OFF`) und niemals als rohe Ganzzahl
- **MUSS [MUST]** `async_set_percentage` (oder `set_percentage`) implementieren, genau dann wenn `FanEntityFeature.SET_SPEED` gesetzt ist, und `percentage` als Wert zwischen 0 (aus) und 100 zurückgeben
- **MUSS [MUST]** `async_set_preset_mode` (oder `set_preset_mode`) implementieren und `preset_modes` bereitstellen, genau dann wenn `FanEntityFeature.PRESET_MODE` gesetzt ist; `preset_mode` ist ein Wert aus `preset_modes` oder `None`, wenn kein Preset aktiv ist
- **MUSS [MUST]** `async_oscillate` (oder `oscillate`) implementieren, genau dann wenn `FanEntityFeature.OSCILLATE` gesetzt ist, und `oscillating` zurückgeben
- **MUSS [MUST]** `async_set_direction` (oder `set_direction`) implementieren, genau dann wenn `FanEntityFeature.DIRECTION` gesetzt ist, und `current_direction` zurückgeben
- **MUSS [MUST]** `async_turn_on`/`async_turn_off` implementieren, genau dann wenn `FanEntityFeature.TURN_ON` bzw. `FanEntityFeature.TURN_OFF` gesetzt ist
- **MUSS NICHT [MUST NOT]** benannte (manuelle) Geschwindigkeits-Stufen in `preset_modes` aufnehmen — die Fan-Doku verlangt, dass `preset_modes` keine Speeds enthält und benannte Speeds als Prozentwerte abgebildet werden
- **SOLLTE [SHOULD]** für ein Gerät mit benannter oder numerischer Speed-Liste die HA-Utilities (`ordered_list_item_to_percentage`, `ranged_value_to_percentage`) zur Prozent-Umrechnung nutzen und `speed_count` entsprechend zurückgeben
- **SOLLTE [SHOULD]** das veraltete `speed`-Argument in neuen Integrationen nicht implementieren und ausschließlich `percentage` und `preset_mode` verwenden — so die Fan-Doku

### `humidifier`

- **MUSS [MUST]** eine Humidifier-Entity von `HumidifierEntity` ableiten, wenn der Hauptzweck des Geräts die Feuchte-Regelung ist (Be- oder Entfeuchter) — so die Humidifier-Doku
- **MUSS [MUST]** die `device_class` aus dem geschlossenen Enum `HumidifierDeviceClass` setzen (`HUMIDIFIER` oder `DEHUMIDIFIER`), wo der Gerätetyp das hergibt
- **MUSS [MUST]** `async_set_humidity` (oder `set_humidity`) implementieren und `target_humidity` zurückgeben; erlaubt das aktuelle Mode keine Sollwert-Anpassung, wechselt das Gerät bei diesem Aufruf automatisch in einen Mode, der das ermöglicht — so die Humidifier-Doku
- **MUSS [MUST]** `async_turn_on`/`async_turn_off` (oder die synchronen Varianten) implementieren und `is_on` bereitstellen
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `HumidifierEntityFeature` setzen — derzeit ist `MODES` das einzige Flag
- **MUSS [MUST]** `async_set_mode` (oder `set_mode`) implementieren sowie `mode` und `available_modes` bereitstellen, genau dann wenn `HumidifierEntityFeature.MODES` gesetzt ist
- **SOLLTE [SHOULD]** für `available_modes` bevorzugt die eingebauten Mode-Konstanten (`MODE_NORMAL`, `MODE_ECO`, `MODE_AWAY`, `MODE_BOOST`, `MODE_COMFORT`, `MODE_HOME`, `MODE_SLEEP`, `MODE_AUTO`, `MODE_BABY`) verwenden, da diese Übersetzungen mitbringen; eigene Modes sind erlaubt, wenn sie das Gerät besser abbilden
- **SOLLTE [SHOULD]** `action` als informative Property aus `HumidifierAction` (`HUMIDIFYING`, `DRYING`, `IDLE`, `OFF`) zurückgeben, wenn der Betriebsstatus bekannt ist
- **MUSS NICHT [MUST NOT]** `action = OFF` als Ersatz für die `is_on`-Property behandeln — die Humidifier-Doku stellt klar, dass `action` `is_on` nicht ersetzt

### `water-heater`

- **MUSS [MUST]** eine Water-Heater-Entity von `WaterHeaterEntity` ableiten, wenn das Gerät die Warmwasser-Bereitung steuert
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `WaterHeaterEntityFeature` setzen (`TARGET_TEMPERATURE`, `OPERATION_MODE`, `AWAY_MODE`, `ON_OFF`) und niemals als rohe Ganzzahl
- **MUSS [MUST]** `async_set_temperature` (oder `set_temperature`) implementieren, genau dann wenn `WaterHeaterEntityFeature.TARGET_TEMPERATURE` gesetzt ist, und die Temperatur-Properties in der über `temperature_unit` deklarierten Einheit zurückgeben
- **MUSS [MUST]** `async_set_operation_mode` (oder `set_operation_mode`) implementieren sowie `current_operation` und `operation_list` bereitstellen, genau dann wenn `WaterHeaterEntityFeature.OPERATION_MODE` gesetzt ist; `current_operation` muss in `operation_list` enthalten sein
- **MUSS [MUST]** `temperature_unit` auf einen Wert aus `UnitOfTemperature` (`CELSIUS`, `FAHRENHEIT` oder `KELVIN`) setzen — die Doku markiert das Feld sonst als `NotImplementedError`
- **MUSS [MUST]** `async_turn_on`/`async_turn_off` implementieren, genau dann wenn `WaterHeaterEntityFeature.ON_OFF` gesetzt ist, und `async_turn_away_mode_on`/`async_turn_away_mode_off` sowie `is_away_mode_on`, genau dann wenn `WaterHeaterEntityFeature.AWAY_MODE` gesetzt ist
- **MUSS NICHT [MUST NOT]** eigene Operation-Modes außerhalb der von der Basis-Komponente vorgegebenen States verwenden (`STATE_ECO`, `STATE_ELECTRIC`, `STATE_PERFORMANCE`, `STATE_HIGH_DEMAND`, `STATE_HEAT_PUMP`, `STATE_GAS`, `STATE_OFF`) — die Doku schreibt vor, dass Implementierungen davon nicht abweichen dürfen
- **SOLLTE [SHOULD]** alle Temperatur-Properties (`current_temperature`, `target_temperature`, `target_temperature_high`/`_low`, `min_temp`, `max_temp`) konsistent in der über `temperature_unit` deklarierten Einheit halten — so die Doku

## Akzeptanzkriterien

- [ ] Jede Capability der Klima-Familie ist auf der semantisch passenden Plattform abgebildet (Luftbewegung → `fan`, Feuchte → `humidifier`, Warmwasser → `water-heater`)
- [ ] Jede der drei Plattformen leitet von ihrer korrekten Basisklasse ab (`FanEntity`, `HumidifierEntity`, `WaterHeaterEntity`)
- [ ] `humidifier`-Entitäten setzen `device_class` aus `HumidifierDeviceClass`, wo der Gerätetyp es hergibt
- [ ] `supported_features` ist je Plattform als bitweise-`|`-Kombination aus dem plattform-eigenen Feature-Enum gesetzt, nie als rohe Ganzzahl
- [ ] Für jedes gesetzte `fan`-Flag existiert die korrespondierende Methode (`SET_SPEED` → `async_set_percentage` + `percentage`; `PRESET_MODE` → `async_set_preset_mode` + `preset_modes`; `OSCILLATE` → `async_oscillate`; `DIRECTION` → `async_set_direction`)
- [ ] `fan`-`preset_modes` enthält keine benannten Speeds; benannte Speeds sind als Prozentwerte abgebildet
- [ ] `humidifier` mit `HumidifierEntityFeature.MODES` stellt `async_set_mode`, `mode` und `available_modes` bereit; `action` ersetzt `is_on` nicht
- [ ] `water-heater` mit `OPERATION_MODE` stellt `async_set_operation_mode`, `current_operation` (in `operation_list`) bereit; mit `TARGET_TEMPERATURE` stellt es `async_set_temperature` bereit
- [ ] `water-heater`-Operation-Modes verwenden ausschließlich die von der Basis-Komponente vorgegebenen States; `temperature_unit` ist aus `UnitOfTemperature` gesetzt
- [ ] Kein Plattform-Flag ist „auf Vorrat" gesetzt, dessen Methode fehlt

## Offene Fragen

- **`fan`-Speed-Repräsentation**: Soll der Skill bei einem Gerät mit benannten Stufen automatisch die HA-Utility-Umrechnung (`ordered_list_item_to_percentage`) generieren, oder bleibt das eine manuelle Entscheidung des Autors?
- **`humidifier`-Custom-Modes**: Die Doku erlaubt eigene Mode-Strings neben den eingebauten. Soll diese Spec eine Translation-Key-Konvention für Custom-Modes vorschreiben (Schnittstelle zu `ha/translations`)?
- **`water-heater`-State-Übersetzungen**: Die Operation-States (`STATE_ECO`, …) sind geschlossen, aber nutzer-sichtbar. Gehört die Festlegung ihrer Übersetzung in diese Spec oder vollständig in `ha/translations`?
- **Weitere Klima-Familie-Plattformen**: Sollen angrenzende Plattformen (z. B. `climate`-Presets im Detail) hier ergänzt werden, oder bleibt die Klima-Familie auf `fan`, `humidifier`, `water-heater` plus den `climate`-Verweis in `ha/entity-platform-types` beschränkt?
