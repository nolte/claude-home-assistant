# HA-Integration: Entity-Plattformen (Geräte-Domänen)

Status: draft

## Kontext

Neben den einfachen Mess- und Schalt-Plattformen kennt Home Assistant eine Reihe **komplexer Geräte-Domänen**, die ein ganzes Gerät mit Zustandsmaschine, Aktionsbefehlen und teils CRUD-Datensätzen abbilden: Alarmanlage, Saugroboter, Mähroboter, Kalender, To-do-Liste sowie die Infrarot- und Funk-Abstraktionen. Jede dieser Domänen leitet von einer eigenen Plattform-Basisklasse ab und erwartet eine charakteristische Kombination aus Zustands-Enum, `supported_features`-Bitmaske und feature-gekoppelten `async_`-Methoden.

Das generische Entity-Pattern — Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, das `EntityDescription`-Pattern, Entity-Kategorien und die Coordinator-Anbindung — ist in `ha/entity-architecture` festgeschrieben und wird **hier nicht wiederholt**. Die generische Typisierungs-Mechanik — `device_class` aus geschlossenen Enums, `supported_features` als Bitmaske, die Eins-zu-eins-Kopplung von Flag und Methode — ist in `ha/entity-platform-types` festgeschrieben und wird **hier nur referenziert**. Diese Spec ist der **konkrete Katalog** für die genannten Geräte-Domänen: pro Plattform die richtige Basisklasse, das Zustands-Enum, die erlaubten Feature-Flags und die Pflichtmethoden, jeweils geerdet in der Plattform-Doku von `developers.home-assistant`.

Diese Domänen sind durchweg aktor- und befehlsgetrieben: ihr State ist eine Aktivitäts-Enum (`VacuumActivity`, `LawnMowerActivity`, `AlarmControlPanelState`) oder ein abgeleiteter Zustand (Kalender: aktives Event; To-do: Anzahl offener Items), und jedes beworbene Feature verspricht eine implementierte `async_`-Methode. Infrarot und Funk sind ein Sonderfall: sie definieren Emitter-/Receiver-/Transmitter-Entitäten als **Abstraktionsschicht** zwischen Hardware-Integrationen und Consumer-Integrationen.

## Ziele

- Für jede der sieben Geräte-Domänen die korrekte Plattform-Basisklasse benennen (`AlarmControlPanelEntity`, `StateVacuumEntity`, `LawnMowerEntity`, `CalendarEntity`, `TodoListEntity`, Infrarot-Emitter/Receiver, `RadioFrequencyTransmitterEntity`)
- Den State jeder Domäne aus dem dokumentierten Zustands-Enum bzw. der dokumentierten State-Ableitung liefern
- `supported_features` je Domäne ausschließlich aus dem domänen-eigenen Feature-Enum setzen und jedes Flag an seine implementierte `async_`-Methode koppeln
- Die als **Required** markierten Properties je Domäne bereitstellen (`alarm_state`, `activity`, `event`, `todo_items`)
- Infrarot- und Funk-Entitäten als Hardware-Abstraktionsschicht korrekt anlegen und ihre Consumer-/Helper-Trennung respektieren
- Generierten Code so starten lassen, dass Flag, Methode und State je Geräte-Domäne konsistent sind

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- Generische Typisierungs-Mechanik (`device_class`-Enums, `supported_features`-Bitmasken, Feature-↔-Methoden-Kopplung im Allgemeinen) — vollständig in `ha/entity-platform-types`; diese Spec wendet sie nur pro Domäne an
- Einfache Mess-/Schalt-Plattformen (`sensor`, `binary_sensor`, `switch`, `light`, `cover`, …) — in `ha/entity-platform-types` exemplarisch behandelt
- HA-Translation-Format (`strings.json`, State- und Feature-Übersetzungen) — eigene Spec `ha/translations`
- Icon-Auswahl und Icon-Translations (`icons.json`) — eigene Spec `ha/icons`
- Geräte-Domänen außerhalb der hier behandelten sieben (z. B. `media_player`, `climate`, `water_heater`) — die generischen Regeln gelten analog

## Anforderungen

### Alarm-Control-Panel

- **MUSS [MUST]** eine Alarmanlagen-Entity von `AlarmControlPanelEntity` ableiten — diese Plattform bildet die Steuerung einer Alarmanlage ab
- **MUSS [MUST]** den State über die als **Required** markierte Property `alarm_state` als Member von `AlarmControlPanelState` liefern (`DISARMED`, `ARMED_HOME`, `ARMED_AWAY`, `ARMED_NIGHT`, `ARMED_VACATION`, `ARMED_CUSTOM_BYPASS`, `PENDING`, `ARMING`, `DISARMING`, `TRIGGERED`)
- **MUSS [MUST]** `supported_features` aus `AlarmControlPanelEntityFeature` (`ARM_HOME`, `ARM_AWAY`, `ARM_NIGHT`, `ARM_VACATION`, `ARM_CUSTOM_BYPASS`, `TRIGGER`) als bitweise-`|`-Kombination setzen und für jedes Flag die zugehörige Methode implementieren (`ARM_HOME` → `async_alarm_arm_home`, `ARM_AWAY` → `async_alarm_arm_away`, `ARM_NIGHT` → `async_alarm_arm_night`, `ARM_VACATION` → `async_alarm_arm_vacation`, `ARM_CUSTOM_BYPASS` → `async_alarm_arm_custom_bypass`, `TRIGGER` → `async_alarm_trigger`)
- **MUSS [MUST]** `async_alarm_disarm` (oder die synchrone Variante) bereitstellen, um das Entschärfen abzubilden — die Doku listet Disarm als eigene Methode unabhängig von einem Feature-Flag
- **SOLLTE [SHOULD]** `code_format` aus `CodeFormat` (`None`, `NUMBER`, `TEXT`) setzen, wenn die Anlage einen Code erfordert, und `code_arm_required` passend zur Geräte-Realität führen — beide Properties steuern die Code-Eingabe im Frontend
- **MUSS NICHT [MUST NOT]** `ARMED_CUSTOM_BYPASS` verwenden, um einen getrennten, defekten oder schwachen Sensor zu signalisieren — die Doku verlangt dafür dedizierte Sensor-Entitäten

### Vacuum (Saugroboter)

- **MUSS [MUST]** eine Saugroboter-Entity von `StateVacuumEntity` ableiten
- **MUSS [MUST]** den State über die als **Required** markierte Property `activity` als Member von `VacuumActivity` liefern (`CLEANING`, `DOCKED`, `IDLE`, `PAUSED`, `RETURNING`, `ERROR`)
- **MUSS [MUST]** auf jeder von `StateVacuumEntity` abgeleiteten Entity das Flag `VacuumEntityFeature.STATE` setzen — die Doku schreibt das ausdrücklich für alle abgeleiteten Plattformen vor
- **MUSS [MUST]** `supported_features` aus `VacuumEntityFeature` als bitweise-`|`-Kombination setzen und jedes gesetzte Flag an seine Methode koppeln (`START` → `async_start`, `PAUSE` → `async_pause`, `STOP` → `async_stop`, `RETURN_HOME` → `async_return_to_base`, `FAN_SPEED` → `async_set_fan_speed`, `CLEAN_SPOT` → `async_clean_spot`, `LOCATE` → `async_locate`, `SEND_COMMAND` → `async_send_command`)
- **MUSS [MUST]** bei gesetztem `VacuumEntityFeature.FAN_SPEED` die Property `fan_speed_list` (verfügbare Geschwindigkeiten) und `fan_speed` (aktuelle Geschwindigkeit) bereitstellen — sonst wirft `fan_speed_list` `NotImplementedError`
- **MUSS [MUST]** bei gesetztem `VacuumEntityFeature.CLEAN_AREA` die Methoden `async_get_segments` und `clean_segments`/`async_clean_segments` implementieren — die Doku markiert beide als für `CLEAN_AREA` erforderlich

### Lawn-Mower (Mähroboter)

- **MUSS [MUST]** eine Mähroboter-Entity von `LawnMowerEntity` ableiten
- **MUSS [MUST]** den State über die Property `activity` als Member von `LawnMowerActivity` liefern (`MOWING`, `DOCKED`, `PAUSED`, `RETURNING`, `ERROR`)
- **MUSS [MUST]** `supported_features` aus `LawnMowerEntityFeature` (`START_MOWING`, `PAUSE`, `DOCK`) als bitweise-`|`-Kombination setzen und jedes Flag an seine Methode koppeln (`START_MOWING` → `async_start_mowing`, `PAUSE` → `async_pause`, `DOCK` → `async_dock`)
- **MUSS NICHT [MUST NOT]** ein Mähroboter-Feature-Flag setzen, dessen `async_`-Methode nicht implementiert ist — die Doku koppelt jedes der drei Flags genau an eine Methode

### Calendar (Kalender)

- **MUSS [MUST]** eine Kalender-Entity von `CalendarEntity` ableiten — diese Plattform bildet eine Menge von Events mit Start-/End-Zeitpunkt ab
- **MUSS [MUST]** die als **Required** markierte Property `event` mit dem aktuellen oder nächsten anstehenden `CalendarEvent` (oder `None`) liefern; daraus leitet HA den binär-sensor-ähnlichen State (aktives Event ja/nein) ab
- **MUSS [MUST]** `async_get_events(hass, start_date, end_date)` implementieren und die Events geordnet sowie mit aufgelösten (geflatteten) wiederkehrenden Events im HA-Zeitzonen-Kontext zurückgeben
- **MUSS [MUST]** Zeiten in der HA-Zeitzone interpretieren (z. B. über `homeassistant.util.dt.now`) und Ganztages-Events als `datetime.date` (nicht als Datum mit Uhrzeit) führen
- **MUSS [MUST]** für jedes gesetzte `CalendarEntityFeature`-Flag die zugehörige Mutations-Methode implementieren (`CREATE_EVENT` → `async_create_event`, `DELETE_EVENT` → `async_delete_event`, `UPDATE_EVENT` → `async_update_event`)
- **MUSS [MUST]** bei Unterstützung von Mutationen die rfc5545-Felder und wiederkehrenden Events behandeln (Serie über `uid`; einzelne Instanz über `uid` + `recurrence_id`; Bereich zusätzlich über `recurrence_range = THISANDFUTURE`)
- **SOLLTE [SHOULD]** nach CRUD-Operationen außerhalb einer State-Änderung `CalendarEntity.async_update_event_listeners` aufrufen, um Subscriber zu benachrichtigen — der State wird bei Create/Update/Delete nicht automatisch aktualisiert

### To-do-Liste

- **MUSS [MUST]** eine To-do-Listen-Entity von `TodoListEntity` ableiten
- **MUSS [MUST]** die als **Required** markierte Property `todo_items` (geordnete `list[TodoItem]`) bereitstellen; der State ist die Anzahl unvollständiger Items
- **MUSS [MUST]** jedes `TodoItem` mit den für State und Updates erforderlichen Feldern führen (`uid`, `summary`, `status` aus `TodoItemStatus` `NEEDS_ACTION`/`COMPLETE`)
- **MUSS [MUST]** für jedes gesetzte `TodoListEntityFeature`-Flag die zugehörige Methode implementieren (`CREATE_TODO_ITEM` → `async_create_todo_item`, `DELETE_TODO_ITEM` → `async_delete_todo_items`, `UPDATE_TODO_ITEM` → `async_update_todo_item`, `MOVE_TODO_ITEM` → `async_move_todo_item`)
- **MUSS [MUST]** bei gesetztem `DELETE_TODO_ITEM` das Löschen mehrerer Items unterstützen — `async_delete_todo_items` nimmt eine `list[str]` von `uids`
- **SOLLTE [SHOULD]** die `due`-Feature-Flags (`SET_DUE_DATE_ON_ITEM` für `datetime.date`, `SET_DUE_DATETIME_ON_ITEM` für `datetime.datetime`) und `SET_DESCRIPTION_ON_ITEM` nur setzen, wenn das jeweilige Feld beim Erstellen/Aktualisieren tatsächlich gesetzt werden kann
- **MUSS [MUST]** beim Verschieben (`MOVE_TODO_ITEM`) das Item mit dem angegebenen `uid` hinter das durch `previous_uid` bezeichnete Item einsortieren (`previous_uid = None` bedeutet erste Position)

### Infrarot (Emitter / Receiver)

- **MUSS [MUST]** eine IR-Emitter-Entity von `InfraredEmitterEntity` und eine IR-Receiver-Entity von `InfraredReceiverEntity` ableiten — die Infrarot-Domäne trennt Sende- und Empfangs-Hardware in zwei Entitätsarten
- **MUSS [MUST]** in einer Emitter-Integration `async_send_command(self, command)` implementieren, das die tatsächliche IR-Übertragung übernimmt und bei Fehlschlag `HomeAssistantError` wirft
- **MUSS [MUST]** in einer Receiver-Integration empfangene Signale über die Basisklassen-Methode `_handle_received_signal` (mit `InfraredReceivedSignal`) melden und die State-Aktualisierung dem Basis-Mechanismus überlassen
- **MUSS NICHT [MUST NOT]** die `device_class` der Infrarot-Entität selbst setzen — die Basisklassen setzen `InfraredDeviceClass.emitter` bzw. `InfraredDeviceClass.receiver` automatisch
- **MUSS NICHT [MUST NOT]** den State der Infrarot-Entität in der Integration verändern — er repräsentiert den Zeitstempel des letzten gesendeten/empfangenen Signals und wird von der Basisklasse gepflegt
- **MUSS NICHT [MUST NOT]** aus einer Consumer-Integration `InfraredEmitterEntity.async_send_command` direkt aufrufen — stattdessen den Helper `infrared.async_send_command` (oder die Consumer-Basisklasse `InfraredEmitterConsumerEntity`) nutzen, der State und Context propagiert
- **SOLLTE [SHOULD]** in einer Consumer-Integration die bereitgestellten Basisklassen (`InfraredEmitterConsumerEntity`, `InfraredReceiverConsumerEntity`) bzw. die Helper (`async_get_emitters`, `async_get_receivers`, `async_subscribe_receiver`) verwenden, statt direkte Referenzen auf Entity-Instanzen zu halten

### Funk (Radio-Frequency-Transmitter)

- **MUSS [MUST]** eine Funk-Sender-Entity von `RadioFrequencyTransmitterEntity` ableiten — die Funk-Domäne bildet einen virtuellen RF-Transmitter als Abstraktionsschicht über der Hardware ab
- **MUSS [MUST]** in einer Transmitter-Integration die Property `supported_frequency_ranges` als Liste von `(min_hz, max_hz)`-Tupeln deklarieren, damit Consumer einen kompatiblen Transmitter wählen können
- **MUSS [MUST]** `async_send_command(self, command)` implementieren, das die tatsächliche RF-Übertragung übernimmt und bei Fehlschlag `HomeAssistantError` wirft
- **MUSS NICHT [MUST NOT]** den State der Funk-Entität in der Integration verändern — er repräsentiert den Zeitstempel des letzten gesendeten RF-Befehls und wird von der Basisklasse gepflegt
- **MUSS NICHT [MUST NOT]** aus einer Consumer-Integration `RadioFrequencyTransmitterEntity.async_send_command` direkt aufrufen — stattdessen den Helper `radio_frequency.async_send_command` nutzen, der State und Context verwaltet
- **SOLLTE [SHOULD]** in einer Consumer-Integration über `radio_frequency.async_get_transmitters(hass, frequency, modulation)` einen passenden Transmitter ermitteln; aktuell unterstützt die Doku ausschließlich `ModulationType.OOK`

## Akzeptanzkriterien

- [ ] Jede Geräte-Domäne leitet von ihrer dokumentierten Basisklasse ab (`AlarmControlPanelEntity`, `StateVacuumEntity`, `LawnMowerEntity`, `CalendarEntity`, `TodoListEntity`, `InfraredEmitterEntity`/`InfraredReceiverEntity`, `RadioFrequencyTransmitterEntity`)
- [ ] Alarm-Entity liefert `alarm_state` aus `AlarmControlPanelState`; jedes gesetzte `AlarmControlPanelEntityFeature`-Flag hat seine Arm-/Trigger-Methode; `async_alarm_disarm` ist implementiert
- [ ] Vacuum-Entity liefert `activity` aus `VacuumActivity`, setzt `VacuumEntityFeature.STATE`, und jedes weitere Flag (`START`/`PAUSE`/`STOP`/`RETURN_HOME`/`FAN_SPEED`/…) hat seine Methode
- [ ] Lawn-Mower-Entity liefert `activity` aus `LawnMowerActivity`; `START_MOWING`/`PAUSE`/`DOCK` sind genau dann gesetzt, wenn `async_start_mowing`/`async_pause`/`async_dock` implementiert sind
- [ ] Calendar-Entity liefert `event`, implementiert `async_get_events` mit geordneten, geflatteten Events in HA-Zeitzone; jedes `CalendarEntityFeature`-Flag (`CREATE`/`DELETE`/`UPDATE_EVENT`) hat seine Mutations-Methode mit rfc5545-Recurrence-Handling
- [ ] To-do-Entity liefert `todo_items`; jedes `TodoListEntityFeature`-Flag hat seine Methode; `async_delete_todo_items` löscht mehrere Items; `MOVE_TODO_ITEM` respektiert `previous_uid`
- [ ] Infrarot-Emitter/Receiver implementieren `async_send_command` bzw. `_handle_received_signal`, setzen die `device_class` nicht selbst, verändern den Basis-State nicht, und Consumer nutzen Helper/Consumer-Basisklassen statt Direktaufrufe
- [ ] Funk-Transmitter deklariert `supported_frequency_ranges`, implementiert `async_send_command`, verändert den Basis-State nicht; Consumer nutzen `radio_frequency.async_send_command` und `async_get_transmitters`
- [ ] Für jedes gesetzte Feature-Flag über alle sieben Domänen existiert die korrespondierende `async_`-Methode; keine „auf Vorrat" gesetzten Flags

## Offene Fragen

- **Infrarot-Detailtiefe**: Die Infrarot-Doku zeigt Basisklassen, Helper und Consumer-Basisklassen, aber kein `supported_features`-Enum und keine Quality-Scale-Marker für diese Domäne. Sollen IR-Consumer-Entitäten (Button/Event) zusätzlich in `ha/entity-platforms-controls` referenziert werden, oder bleibt die IR-Abstraktion vollständig hier?
- **Funk-Modulations-Erweiterung**: Die Doku unterstützt aktuell nur `ModulationType.OOK` und kündigt weitere Typen an. Soll die Spec eine Konvention vorgeben, wie Transmitter zusätzliche Modulationen später deklarieren, oder erst nachziehen, wenn die Doku sie zeigt?
- **Custom-Fan-Speeds (Vacuum)**: `fan_speed_list` enthält freie Strings. Soll die Spec eine Translation-Key-Konvention für Fan-Speed-Namen vorschreiben (Schnittstelle zu `ha/translations`)?
- **Custom-Alarm-Codes**: `code_format` deckt `NUMBER`/`TEXT` ab. Reicht das für alle realen Anlagen, oder braucht es eine Konvention für gerätespezifische Validierungsregeln jenseits des Enums?
- **Kalender-/To-do-Statistik**: Beide Domänen leiten ihren State aus Datensätzen ab (aktives Event, Anzahl offener Items). Soll die Spec klären, ob/wie diese Zustände in Long-Term-Statistics einfließen, oder bleibt das `ha/entity-platform-types` vorbehalten?
