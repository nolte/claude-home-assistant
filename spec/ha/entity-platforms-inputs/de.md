# HA-Integration: Entity-Plattformen (Input-Helfer)

Status: draft

## Kontext

Neben den read-only und aktor-orientierten Plattformen (`sensor`, `binary_sensor`, `light`, `cover`, `climate`, …) stellt Home Assistant eine Familie **eingabe-orientierter** Plattformen bereit, über die eine Integration dem Nutzer einen frei setzbaren Wert anbietet: `number`, `select`, `text`, `date`, `time` und `datetime`. Diese Plattformen spiegeln die bekannten `input_*`-Helfer (`input_number`, `input_select`, `input_text`, `input_datetime`), sind aber **integrations-backed** — der Wert wird vom Gerät oder Dienst gehalten und über eine Set-Methode an die Integration zurückgeschrieben, statt von Home Assistant lokal verwaltet zu werden.

Diese Spec ist der **konkrete Katalog** dieser Input-Plattformen: pro Plattform die Capability, die richtige Wahl-Heuristik, die Basisklasse, die Wert-Attribute und die Pflicht-Set-Methode, ausschließlich aus den jeweiligen Plattform-Docs auf `developers.home-assistant` abgeleitet. Das generische Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, Entity-Kategorien, Coordinator-Anbindung) ist in `ha/entity-architecture` festgeschrieben; die plattform-übergreifenden Typisierungs-Konzepte (`device_class`, Units, `state_class`, `supported_features`) in `ha/entity-platform-types`. Beide werden **hier nur per Slug referenziert, nicht wiederholt**.

Anders als Sensor-Plattformen sind diese Plattformen **bidirektional**: jede deklariert genau eine Set-Methode (`async_set_native_value`, `async_select_option`, `async_set_value`), die der Nutzer oder eine Automation auslöst. Der Skill-Output muss diese Methode zwingend implementieren, sonst ist die Entity nicht bedienbar.

## Ziele

- Die Plattformwahl an den Werttyp binden, den der Nutzer eingibt — numerisch → `number`, feste Optionsliste → `select`, Freitext → `text`, Datum → `date`, Uhrzeit → `time`, Zeitstempel → `datetime`
- Pro Plattform die korrekte Basisklasse (`NumberEntity`, `SelectEntity`, `TextEntity`, `DateEntity`, `TimeEntity`, `DateTimeEntity`) und die dokumentierten Wert-Attribute setzen
- Für jede Input-Entity die in der Plattform-Doku als **Required** markierte Property (`native_value`, `options`) und die zugehörige Set-Methode bereitstellen
- `number`-Entitäten über `device_class` aus `NumberDeviceClass` typisieren und die passende `native_unit_of_measurement` liefern, wo ein Member existiert
- Den integrations-backed Charakter sichtbar machen — der Wert wird über die Set-Methode an das Gerät/den Dienst geschrieben, nicht lokal von HA verwaltet

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- Plattform-übergreifende Typisierungs-Konzepte (`device_class`-Mechanik allgemein, Unit-Konvertierung, `state_class`, `supported_features`-Bitmasken) — vollständig in `ha/entity-platform-types`; diese Spec referenziert sie nur
- HA-Translation-Format selbst (`strings.json`-Aufbau, `entity.<platform>.<key>.name`, Options-/State-Übersetzungen) — eigene Spec `ha/translations`
- `RestoreNumber`/`RestoreEntity`-Persistenz von `native_value` über Restart — die `number`-Doku verweist auf `RestoreNumber`; eine eigene Folge-Spec, sobald konkret nötig
- Die YAML-`input_*`-Helfer selbst (nutzer-konfigurierbare Helfer ohne Integration) — diese Spec adressiert ausschließlich die integrations-backed Plattform-Entitäten

## Anforderungen

### `number`

- **MUSS [MUST]** eine frei vom Nutzer setzbare numerische Größe als `number` mit Basisklasse `NumberEntity` abbilden — die Doku definiert `number` als „entity that allows the user to input an arbitrary value"
- **MUSS [MUST]** den aktuellen Wert über `native_value` (float, **Required**) in der `native_unit_of_measurement` zurückgeben
- **MUSS [MUST]** den Wertebereich über `native_min_value` und `native_max_value` (inklusive Grenzen) deklarieren und die Auflösung über `native_step` angeben — wird `native_step` nicht gesetzt, leitet HA den Default dynamisch aus dem Bereich ab
- **SOLLTE [SHOULD]** bei einer physikalischen Größe die `device_class` aus dem geschlossenen `NumberDeviceClass`-Enum setzen und dann die für diese Klasse zulässige `native_unit_of_measurement` liefern (z. B. `TEMPERATURE` → °C/°F/K, `POWER` → mW/W/kW/…) — die Mechanik selbst beschreibt `ha/entity-platform-types`
- **SOLLTE [SHOULD]** `mode` auf dem Default `auto` belassen und nur bei begründetem Bedarf auf `box` oder `slider` zwingen — so empfiehlt es die Doku
- **MUSS [MUST]** genau eine Set-Methode implementieren — `async_set_native_value(value: float)` (oder die synchrone `set_native_value`) — sonst ist der `number` nicht setzbar

### `select`

- **MUSS [MUST]** eine Auswahl aus einer **begrenzten, von der Integration vorgegebenen Optionsliste** als `select` mit Basisklasse `SelectEntity` abbilden
- **MUSS [MUST]** die verfügbaren Optionen über `options` (list of str, **Required**) und die aktuell gewählte Option über `current_option` (str) bereitstellen
- **MUSS [MUST]** genau eine Set-Methode implementieren — `async_select_option(option: str)` (oder die synchrone `select_option`)
- **MUSS NICHT [MUST NOT]** `select` verwenden, wo eine besser passende Plattform existiert — die Doku schreibt: „This entity should only be used in cases there is no better fitting option available" (z. B. Licht-Effekte gehören in die `light`-Entity, nicht in einen `select`)
- **SOLLTE [SHOULD]** die Options-Strings nicht roh als UI-Text führen, sondern über das HA-Translation-Format lokalisierbar machen — Schnittstelle zu `ha/translations`

### `text`

- **MUSS [MUST]** eine frei vom Nutzer eingebbare Zeichenkette als `text` mit Basisklasse `TextEntity` abbilden
- **MUSS [MUST]** den aktuellen Wert über `native_value` (str, **Required**) zurückgeben
- **SOLLTE [SHOULD]** die zulässige Länge über `native_min` und `native_max` (inklusive Zeichenzahl) eingrenzen und, wo das Format feststeht, über `pattern` (Regex) validieren
- **SOLLTE [SHOULD]** `mode` auf `password` setzen, wenn der Wert ein Geheimnis ist, sonst auf dem Default `text` belassen — die Doku kennt genau diese beiden Modi
- **MUSS [MUST]** genau eine Set-Methode implementieren — `async_set_value(value: str)` (oder die synchrone `set_value`)

### `date`

- **MUSS [MUST]** ein vom Nutzer eingebbares Datum als `date` mit Basisklasse `DateEntity` abbilden
- **MUSS [MUST]** den Wert über `native_value` als `datetime.date | None` (**Required**) zurückgeben
- **MUSS [MUST]** genau eine Set-Methode implementieren — `async_set_value(value: date)` (oder die synchrone `set_value`)
- **MUSS NICHT [MUST NOT]** `date` verwenden, wenn zusätzlich eine Uhrzeit Teil des Werts ist — dafür ist `datetime` vorgesehen

### `time`

- **MUSS [MUST]** eine vom Nutzer eingebbare Uhrzeit als `time` mit Basisklasse `TimeEntity` abbilden
- **MUSS [MUST]** den Wert über `native_value` als `time` (**Required**) zurückgeben
- **MUSS [MUST]** genau eine Set-Methode implementieren — `async_set_value(value: time)` (oder die synchrone `set_value`)
- **MUSS NICHT [MUST NOT]** `time` verwenden, wenn zusätzlich ein Datum Teil des Werts ist — dafür ist `datetime` vorgesehen

### `datetime`

- **MUSS [MUST]** einen vom Nutzer eingebbaren Zeitstempel als `datetime` mit Basisklasse `DateTimeEntity` abbilden
- **MUSS [MUST]** den Wert über `native_value` als `datetime.datetime | None` (**Required**) zurückgeben und dabei **Timezone-Info einschließen** — die Doku verlangt: „Must include timezone info"
- **MUSS [MUST]** genau eine Set-Methode implementieren — `async_set_value(value: datetime)` (oder die synchrone `set_value`); der von HA übergebene Eingabewert ist **immer in UTC**, wie die Doku ausdrücklich festhält
- **MUSS NICHT [MUST NOT]** `datetime` für einen reinen Datums- oder reinen Uhrzeit-Wert verwenden — dafür sind `date` bzw. `time` vorgesehen

## Akzeptanzkriterien

- [ ] Jede Nutzereingabe ist auf der werttyp-passenden Plattform abgebildet (numerisch → `number`, feste Optionsliste → `select`, Freitext → `text`, Datum → `date`, Uhrzeit → `time`, Zeitstempel → `datetime`)
- [ ] Jede Input-Entity leitet von der korrekten Basisklasse ab (`NumberEntity`, `SelectEntity`, `TextEntity`, `DateEntity`, `TimeEntity`, `DateTimeEntity`)
- [ ] Jede Input-Entity stellt die als **Required** markierte Property bereit (`native_value` bzw. `options`)
- [ ] Jede Input-Entity implementiert genau eine Set-Methode (`async_set_native_value`, `async_select_option`, `async_set_value`)
- [ ] Jeder `number` deklariert `native_min_value`/`native_max_value` und liefert `native_value` in der `native_unit_of_measurement`; eine gesetzte `NumberDeviceClass` hat eine zur Klasse passende Unit
- [ ] Jeder `select` setzt `options` und `current_option`; `select` ist nicht dort verwendet, wo eine passendere Plattform existiert
- [ ] Jeder `text` mit Geheimnis-Wert nutzt `mode = password`; wo das Format feststeht, ist `pattern` gesetzt
- [ ] Jede `datetime`-Entity liefert ein timezone-aware `native_value`; `date`/`time`/`datetime` sind nicht gegeneinander vertauscht

## Offene Fragen

- **Persistenz über Restart**: Die `number`-Doku verweist auf `RestoreNumber` statt `RestoreEntity`. Gehört eine Restore-Konvention für `number` (und sinngemäß für die übrigen Input-Plattformen) in diese Spec oder in eine eigene Folge-Spec?
- **Options-Translation für `select`**: Sollen die `options`-Strings verpflichtend über `ha/translations` lokalisiert werden, oder bleibt das eine Empfehlung?
- **`device_class` für Nicht-`number`-Inputs**: Nur `number` führt ein `device_class`-Enum. Soll die Spec das explizit festhalten, damit der Skill für `select`/`text`/`date`/`time`/`datetime` keine `device_class` zu setzen versucht?
- **`mode`-Heuristik für `text`**: Wann ist ein Wert „geheim" genug für `mode = password`? Soll die Spec eine Heuristik vorgeben oder die Entscheidung dem Autor überlassen?
