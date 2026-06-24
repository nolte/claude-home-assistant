# HA-Integration: Entity-Plattformen (Controls)

Status: draft

## Kontext

Eine Custom Integration bildet steuerbare Aktoren über die Control-Plattformen von Home Assistant ab: `switch`, `button`, `scene`, `siren`, `valve`, `lock` und `remote`. Jede dieser Plattformen steht für eine konkrete Steuer-Capability — etwas an-/ausschalten, eine zustandslose Aktion auslösen, einen Zielzustand reproduzieren, eine Sirene auslösen, ein Ventil bewegen, ein Schloss ver-/entriegeln oder Kommandos an ein Gerät senden. Diese Spec ist der **konkrete Katalog** dieser Control-/Aktor-Plattformen: für jede Plattform die abgebildete Capability, die Basis-Entity-Klasse, das plattform-eigene `device_class`-Enum (falls vorhanden), die `supported_features`-Flags und die zu implementierenden Methoden.

Das **generische Entity-Pattern** — Base-Klasse, `_attr_has_entity_name`, `unique_id`, das `EntityDescription`-Pattern, Entity-Kategorien und die Coordinator-Anbindung — ist in `ha/entity-architecture` festgeschrieben und wird **hier nicht wiederholt**. Das **querschnittliche Typisierungs-Konzept** — `device_class`/`state_class`/`supported_features` als Muster, die Regel „nur tatsächlich implementierte Features bewerben", die Bitmasken-Kombination per `|` — liegt in `ha/entity-platform-types`. Diese Spec referenziert beide per Slug und konkretisiert sie für die sieben Control-Plattformen.

Die durchgängige Kopplung lautet: ein `supported_features`-Flag **darf nur gesetzt werden, wenn die zugehörige Methode implementiert ist** — die Plattform-Docs koppeln Flag und Methode eins-zu-eins (z. B. `LockEntityFeature.OPEN` ↔ `async_open`, `ValveEntityFeature.SET_POSITION` ↔ `async_set_valve_position`).

## Ziele

- Für jede steuerbare Aktor-Capability die semantisch passende Control-Plattform aus `switch`/`button`/`scene`/`siren`/`valve`/`lock`/`remote` wählen
- Je Plattform die korrekte Basis-Entity-Klasse ableiten (`SwitchEntity`, `ButtonEntity`, `Scene`, `SirenEntity`, `ValveEntity`, `LockEntity`, `RemoteEntity`)
- Die plattform-eigene `device_class` aus dem geschlossenen Enum setzen, wo ein Enum existiert (`SwitchDeviceClass`, `ButtonDeviceClass`, `ValveDeviceClass`)
- `supported_features` aus dem plattform-eigenen Feature-Enum (`SirenEntityFeature`, `ValveEntityFeature`, `LockEntityFeature`, `RemoteEntityFeature`) so setzen, dass jedes Flag seine implementierte Methode hat
- Die je Plattform erforderlichen Methoden bereitstellen (`async_turn_on/off`, `async_press`, `async_activate`, `async_lock/unlock/open`, `async_open_valve/close_valve/set_valve_position`, `async_send_command`)

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- Das querschnittliche Typisierungs-Konzept (`device_class`/`state_class`/`supported_features` als Muster, Bitmasken-Mechanik, Feature-↔-Methoden-Regel) — vollständig in `ha/entity-platform-types`; diese Spec konkretisiert es nur für die Control-Plattformen
- HA-Translation-Format (`strings.json`, `entity.<platform>.<key>.name`, Tone-/Activity-Namen) — eigene Spec `ha/translations`
- Icon-Auswahl und Icon-Translations (`icons.json`, `default`/`state`) — eigene Spec `ha/icons`
- Read-only-/Mess-Plattformen (`sensor`, `binary_sensor`) und die übrigen Aktor-Plattformen außerhalb der hier behandelten sieben (`light`, `cover`, `climate`, `fan`, `number`, `select`, `humidifier`, …) — die generischen Regeln gelten analog, sind aber nicht Gegenstand dieses Katalogs

## Anforderungen

### `switch`

- **MUSS [MUST]** eine Entity, die etwas an- oder ausschaltet (z. B. ein Relais), von `SwitchEntity` ableiten — so die Switch-Doku
- **MUSS [MUST]** `async_turn_on` und `async_turn_off` (oder ihre synchronen Varianten `turn_on`/`turn_off`) implementieren und den Zustand über `is_on` melden
- **SOLLTE [SHOULD]** `async_toggle`/`toggle` nur überschreiben, wenn ein gerätespezifisches Toggle nötig ist; ohne Implementierung leitet HA `toggle` aus `is_on` ab — so die Switch-Doku
- **SOLLTE [SHOULD]** die `device_class` aus `SwitchDeviceClass` setzen (`SwitchDeviceClass.OUTLET` für eine Steckdose, `SwitchDeviceClass.SWITCH` für einen generischen Schalter), wo passend — sie kann auf Google-Device-Typen abbilden
- **MUSS NICHT [MUST NOT]** `switch` für einen Zustand verwenden, der nur gemeldet, aber nicht von HA aus geschaltet werden kann — dafür ist `binary_sensor` korrekt; und nicht für eine zustandslose Aktion — dafür ist `button` oder ein Custom-Event korrekt (so grenzt die Switch-Doku ab)

### `button`

- **MUSS [MUST]** eine Entity, die eine Aktion zu Gerät oder Dienst auslöst, aber aus HA-Sicht **zustandslos** bleibt, von `ButtonEntity` ableiten — so die Button-Doku (z. B. Firmware-Upgrade, Neustart, Reset eines Zählers)
- **MUSS [MUST]** `async_press` (oder die synchrone Variante `press`) implementieren — das ist die einzige plattform-spezifische Methode; die Plattform liefert keine eigenen State-Properties
- **SOLLTE [SHOULD]** die `device_class` aus `ButtonDeviceClass` setzen (`IDENTIFY`, `RESTART`), wo passend — sie kann auf Google-Device-Typen abbilden
- **MUSS NICHT [MUST NOT]** `ButtonDeviceClass.UPDATE` verwenden, wo eine `update`-Entity korrekt wäre — die Button-Doku rät ausdrücklich davon ab
- **MUSS NICHT [MUST NOT]** `button` für etwas mit echtem An-/Aus-Zustand verwenden (dafür `switch`) oder zur Integration eines realen, physischen Tasters (dafür Custom-Events) — so grenzt die Button-Doku ab

### `scene`

- **MUSS [MUST]** eine Entity, die einen gewünschten Zustand für eine Gruppe von Entitäten reproduziert und aus HA-Sicht **zustandslos** bleibt, von `Scene` ableiten — so die Scene-Doku
- **MUSS [MUST]** `async_activate` (oder die synchrone Variante `activate`) implementieren — sie wird beim Drücken des `activate`-Buttons bzw. beim Aufruf von `scene.turn_on` aufgerufen
- **SOLLTE [SHOULD]** für Szenen, die auch **außerhalb** von HA (z. B. per physischem Taster) aktiviert werden können, stattdessen von `BaseScene` ableiten, `_async_activate()` überschreiben und bei externer Aktivierung `_async_record_activation()` aufrufen — so die Scene-Doku
- **MUSS NICHT [MUST NOT]** eine `device_class` auf einer Scene-Entity setzen — die Scene-Doku stellt fest, dass es keine gibt und das Attribut nicht gesetzt wird
- **MUSS NICHT [MUST NOT]** `scene` für etwas mit echtem An-/Aus-Zustand verwenden — dafür ist `switch` korrekt (so grenzt die Scene-Doku ab)

### `siren`

- **MUSS [MUST]** eine Entity, deren Hauptzweck die Steuerung von Sirenen-Geräten ist (z. B. Türklingel oder Gong), von `SirenEntity` ableiten — so die Siren-Doku
- **MUSS [MUST]** `async_turn_on` implementieren und `SirenEntityFeature.TURN_ON` setzen; `async_turn_off` implementieren und `SirenEntityFeature.TURN_OFF` setzen, sofern das Gerät ausschaltbar ist — die Siren-Doku koppelt jeden Service-Call an sein Feature-Flag
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `SirenEntityFeature` setzen — die zulässigen Flags sind `TURN_ON`, `TURN_OFF`, `TONES`, `DURATION`, `VOLUME_SET`
- **MUSS [MUST]** bei gesetztem `SirenEntityFeature.TONES` die `available_tones` (Liste oder Dict) bereitstellen — die Siren-Doku verlangt diese Property genau für dieses Feature
- **MUSS NICHT [MUST NOT]** `SirenEntityFeature.DURATION` oder `SirenEntityFeature.VOLUME_SET` setzen, wenn das Gerät den entsprechenden `turn_on`-Parameter (`duration`, `volume_level`) nicht bedient — die Basis-Plattform filtert nicht beworbene Parameter aus dem Call

### `valve`

- **MUSS [MUST]** eine Entity, die ein Ventil steuert (z. B. Wasser- oder Gas-Ventil), von `ValveEntity` ableiten — so die Valve-Doku
- **MUSS [MUST]** `reports_position` setzen (Pflicht-Property); bei `reports_position = True` zusätzlich `current_valve_position` (0 = geschlossen, 100 = voll offen) bereitstellen, andernfalls den Zustand über `is_closed`/`is_closing`/`is_opening` melden
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `ValveEntityFeature` (`OPEN`, `CLOSE`, `SET_POSITION`, `STOP`) setzen und genau die Methode implementieren, deren Flag gesetzt ist — `OPEN` ↔ `async_open_valve`, `CLOSE` ↔ `async_close_valve`, `SET_POSITION` ↔ `async_set_valve_position`, `STOP` ↔ `async_stop_valve`
- **MUSS [MUST]** für positionierbare Ventile `async_open_valve`/`async_close_valve` **unimplementiert** lassen und ausschließlich `async_set_valve_position` bereitstellen — so die Valve-Doku ausdrücklich
- **SOLLTE [SHOULD]** die `device_class` aus `ValveDeviceClass` setzen (`ValveDeviceClass.WATER`, `ValveDeviceClass.GAS`), wo passend

### `lock`

- **MUSS [MUST]** eine Entity, die ver- und entriegelt werden kann, von `LockEntity` ableiten — so die Lock-Doku
- **MUSS [MUST]** `async_lock` und `async_unlock` (oder die synchronen Varianten `lock`/`unlock`) implementieren und den Zustand über `is_locked`/`is_locking`/`is_unlocking` (sowie optional `is_jammed`, `is_opening`, `is_open`) melden
- **MUSS [MUST]** `async_open` (Entriegeln/Öffnen der Falle) **nur** implementieren, wenn `LockEntityFeature.OPEN` gesetzt ist — das ist das einzige Flag des `LockEntityFeature`-Enums
- **SOLLTE [SHOULD]** `code_format` (Regex) setzen, wenn das Schloss einen Benutzer-Code zum Ver-/Entriegeln verlangt, und `changed_by` melden, wenn die Quelle der letzten Änderung bekannt ist
- **MUSS NICHT [MUST NOT]** `LockEntityFeature.OPEN` setzen, wenn das Gerät die Falle nicht öffnen kann oder `async_open` nicht implementiert ist — sonst bewirbt die Entity ein nicht bedienbares Feature

### `remote`

- **MUSS [MUST]** eine Entity, die Kommandos sendet (physisches Sendegerät oder virtuelles HA-Gerät, das ein anderes Gerät steuert), von `RemoteEntity` ableiten — so die Remote-Doku
- **MUSS [MUST]** `async_turn_on` und `async_turn_off` (oder die synchronen Varianten) implementieren und den Zustand über `is_on` melden
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `RemoteEntityFeature` (`LEARN_COMMAND`, `DELETE_COMMAND`, `ACTIVITY`) setzen
- **MUSS [MUST]** `async_learn_command` **nur** bei gesetztem `RemoteEntityFeature.LEARN_COMMAND` und `async_delete_command` **nur** bei gesetztem `RemoteEntityFeature.DELETE_COMMAND` implementieren — so die Remote-Doku
- **SOLLTE [SHOULD]** bei gesetztem `RemoteEntityFeature.ACTIVITY` `current_activity` und `activity_list` melden und `async_send_command` zum Senden von Kommandos bereitstellen

## Akzeptanzkriterien

- [ ] Jede Aktor-Capability ist auf der semantisch passenden Control-Plattform abgebildet und leitet von der korrekten Basis-Klasse ab (`SwitchEntity`/`ButtonEntity`/`Scene`/`SirenEntity`/`ValveEntity`/`LockEntity`/`RemoteEntity`)
- [ ] `switch`-Entitäten implementieren `async_turn_on`/`async_turn_off`, melden `is_on` und setzen `SwitchDeviceClass` wo passend
- [ ] `button`-Entitäten implementieren `async_press`, bleiben zustandslos und verwenden nicht `ButtonDeviceClass.UPDATE`, wo eine `update`-Entity korrekt wäre
- [ ] `scene`-Entitäten implementieren `async_activate` (bzw. `BaseScene`/`_async_activate` bei externer Aktivierung) und setzen keine `device_class`
- [ ] `siren`-Entitäten setzen `supported_features` aus `SirenEntityFeature` und stellen `available_tones` bereit, wenn `TONES` gesetzt ist
- [ ] `valve`-Entitäten setzen `reports_position`, kombinieren `ValveEntityFeature`-Flags nur mit der jeweils implementierten Methode und lassen `open_valve`/`close_valve` bei positionierbaren Ventilen unimplementiert
- [ ] `lock`-Entitäten implementieren `async_lock`/`async_unlock` und setzen `LockEntityFeature.OPEN` nur, wenn `async_open` implementiert ist
- [ ] `remote`-Entitäten setzen `RemoteEntityFeature`-Flags nur mit der jeweils implementierten Methode (`LEARN_COMMAND` ↔ `async_learn_command`, `DELETE_COMMAND` ↔ `async_delete_command`)
- [ ] Kein `supported_features`-Flag ist gesetzt, ohne dass seine korrespondierende Methode implementiert ist
- [ ] Jede gesetzte `device_class` stammt aus dem plattform-eigenen geschlossenen Enum, nie aus einem frei gewählten String

## Offene Fragen

- **Quality-Scale-Abdeckung**: Diese Spec führt für die Control-Plattformen kein eigenes Quality-Scale-Marker-Set, da `entity-device-class` bereits in `ha/entity-platform-types` verankert ist. Soll der Katalog je Plattform zusätzlich auf Bronze-/Silver-Regeln (z. B. `has-entity-name`) verweisen oder bleibt das bei `ha/entity-architecture`?
- **`siren`-Tone-Dictionary-Übersetzung**: `available_tones` kann ein Dict (Anzeige-Wert → Geräte-Schlüssel) sein. Gehört eine Translation-Key-Konvention für die Anzeige-Werte in diese Spec oder vollständig nach `ha/translations`?
- **`remote`-Activity-Modell**: Die Remote-Doku beschreibt `current_activity`/`activity_list` knapp. Soll die Spec eine Konvention für die Translation der Activity-Namen vorschreiben (Schnittstelle zu `ha/translations`)?
- **`valve`-vs-`cover`-Abgrenzung**: Ventil und Cover teilen das Positions-/Open-Close-Modell. Soll eine explizite Entscheidungsregel (Ventil = Durchfluss, Cover = Öffnung/Abdeckung) in diese Spec oder nach `ha/entity-platform-types`?
