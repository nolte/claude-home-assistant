# HA-Automation: input_number nutzen

Status: draft

## Kontext

`input_number` ist eine **Helfer-Integration** (HA-Kategorie *Helper*): Sie stellt einen **vom Benutzer einstellbaren Zahlenwert** bereit, der als Schieberegler oder Eingabefeld in der Oberfläche erscheint. Der Zustand ist die aktuelle Zahl; sie ist ein Sollwert/Setpoint (z. B. Ziel-Temperatur, Helligkeits-Schwelle, Verzögerungsdauer), den ein Mensch wählt und Automationen lesen — nicht eine Messgröße.

Auf Konfigurationsebene wird ein `input_number` über die UI (Einstellungen → Geräte & Dienste → Helfer) oder als YAML unter dem Top-Level-Schlüssel `input_number` angelegt. Die Schlüssel `min` und `max` sind erforderlich; `name`, `initial`, `step`, `icon`, `unit_of_measurement` und `mode` (Werte `box` oder `slider`, Default `slider`) sind optional. Die Integration hat eine echte Integrations-Karte; ihre reale Einordnung ist **Helper**, nicht Sensor.

Verifizierte Quelle: [`/integrations/input_number/`](https://www.home-assistant.io/integrations/input_number/) (Konfigurationsschlüssel `name`/`min`/`max`/`initial`/`step`/`icon`/`unit_of_measurement`/`mode`; `mode`-Werte `box`/`slider`; Dienste `set_value`/`increment`/`decrement`/`reload`; Attribute `min`/`max`/`step`/`mode`/`unit_of_measurement`; Restore-Verhalten). Namens-Mechanik referenziert über `ha/naming-conventions`.

## Wann verwenden

Verwende `input_number` für einen **vom Benutzer einstellbaren Zahlenwert** mit festen `min`/`max`-Grenzen, den ein Mensch wählt und Automationen lesen — keine gemessene oder abgeleitete Größe. Typische Anwendungsfälle:

- **Einstellbarer Sollwert** — eine vom Bewohner gewählte Ziel-Temperatur, die eine Automation als Setpoint an `climate`/`light` weitergibt
- **Justierbare Schwelle** — eine Helligkeits- oder Schwellwert-Grenze, die per `numeric_state` (`above`/`below`) eine Automation auslöst
- **Verzögerungs-/Dauer-Parameter** — ein einstellbarer Wert, der als `delay` oder Aktions-Parameter in eine Automation einfließt
- **Programmatisches Setzen/Schrittwechsel** — den Wert per `input_number.set_value` oder schrittweise per `increment`/`decrement` (um genau `step`) verändern
- **Dashboard-Regler** — als Schieberegler (`mode: slider`) oder Eingabefeld (`mode: box`) über eine `entities`-Zeile oder `input_number`-Karte bedienbar machen

Ein `input_number` ist das richtige Werkzeug, sobald ein **benutzer-einstellbarer, begrenzter Zahlenwert** gebraucht wird. Geht es um einen gemessenen/abgeleiteten Wert oder eine Auswahl aus festen Optionen, greift ein anderer Baustein (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines `input_number` (Pflicht-`min`/`max`, `step`, `mode`, Restore-Semantik) verbindlich festschreiben
- Den korrekten Einsatz als vom Benutzer einstellbarer Sollwert/Setpoint fixieren
- Die exponierten Dienste (`set_value`/`increment`/`decrement`) und das Lesen von Zustand und Attributen aus Trigger/Bedingung/Template festlegen
- Klar abgrenzen, wann ein `input_number` **nicht** das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Modell der Automation selbst — `ha-automation/automation`
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur die Lese-Muster
- Die Namens-Dimension (`name`, snake_case-`object_id`, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Gemessene oder abgeleitete Zahlenwerte — `sensor`/Template-/Derivative-/Statistics-Sensor (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`)

## Anforderungen

### Konfiguration

- **MUSS [MUST]** ein `input_number` über den Top-Level-Schlüssel `input_number` strukturieren und pro Eintrag die **erforderlichen** Schlüssel `min` und `max` setzen; `name`, `initial`, `step`, `icon`, `unit_of_measurement`, `mode` sind optional
- **MUSS [MUST]** die `object_id` als snake_case-Slug und den `name` englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** `step` passend zur Größe wählen (Default `1`, Minimum `0.001` laut Doku) und `unit_of_measurement` setzen, wenn der Wert eine physikalische Größe darstellt, damit Oberfläche und Templates die Einheit kennen
- **SOLLTE [SHOULD]** `mode` bewusst wählen — `slider` (Default) für bequeme Grob-Einstellung, `box` für präzise Direkteingabe
- **SOLLTE [SHOULD]** den Schlüssel `initial` bewusst behandeln: Ist `initial` gesetzt, startet HA mit diesem Wert; sonst wird der Zustand vor dem Stopp wiederhergestellt (laut Doku)
- **SOLLTE NICHT [SHOULD NOT]** `initial` setzen, wenn der vom Benutzer zuletzt gewählte Wert einen Neustart überdauern soll — ein hart gesetztes `initial` überschreibt das Restore-Verhalten bei jedem Start

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Wert numerisch lesen: in Bedingungen/Triggern per `numeric_state` (mit `above`/`below`), in Templates per `states('input_number.x') | float` — der `states(...)`-Rückgabewert ist ein String und muss in eine Zahl gecastet werden
- **KANN [MAY]** die dokumentierten Attribute `min`, `max`, `step`, `mode` und `unit_of_measurement` per `state_attr('input_number.x', 'min')` usw. lesen, z. B. um Grenzen in der Logik zu spiegeln
- **MUSS [MUST]** zum programmatischen Setzen den dokumentierten Dienst `input_number.set_value` (mit `value`) verwenden und zum schrittweisen Ändern `input_number.increment`/`input_number.decrement` (verschieben um genau `step`); `input_number.reload` lädt die YAML-Helfer neu
- **KANN [MAY]** den Wert als Parameter in Aktionen einsetzen (z. B. `delay`, `target`-Daten, Sollwert für `climate`/`light`) — als vom Benutzer einstellbarer Stellhebel
- **KANN [MAY]** das Element auf einem Dashboard über eine `entities`-Zeile oder eine `input_number`-Karte einbinden

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** ein `input_number` als **Mess-Sensor** verwenden (z. B. um eine Temperatur oder einen Verbrauch „darzustellen") — es ist vom Benutzer editierbar und hat keine Messquelle; für gemessene Werte gehört ein **`sensor`** her, für abgeleitete ein **Template-Sensor** (`ha-automation/template`)
- **SOLLTE NICHT [SHOULD NOT]** ein `input_number` nutzen, um einen **berechneten/abgeleiteten** Zahlenwert zu „speichern", den eine Automation per `set_value` nachführt, damit er „wie ein Sensor" aussieht — das ist anfällig (Race-Conditions, kein Verlauf, Drift nach Neustart) und verliert die Quelle; stattdessen einen **Template-/Derivative-/Statistics-Sensor** (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`) definieren, der den Wert deklarativ ableitet
- **SOLLTE NICHT [SHOULD NOT]** ein `input_number` als Auswahl aus wenigen festen Optionen zweckentfremden (z. B. 1/2/3 für drei Modi) — dafür ist ein **`input_select`** das passende Helfer-Konstrukt, weil es benannte Optionen statt eines Zahlenbereichs erzwingt
- **SOLLTE NICHT [SHOULD NOT]** ein `input_number` ohne sinnvolle `min`/`max`-Grenzen einsetzen, um „beliebige" Zahlen zu speichern — die Pflichtgrenzen sind Teil der Semantik; ein unbegrenzter berechneter Wert gehört in einen Template-Sensor, nicht in einen einstellbaren Regler

## Akzeptanzkriterien

- [ ] Jeder Helfer wird über den Top-Level-Schlüssel `input_number` mit erforderlichem `min`/`max`, snake_case-`object_id` und englischem `name` ≤50 Zeichen angelegt
- [ ] `step`, `mode` und `unit_of_measurement` sind bewusst gesetzt; `initial` nur bei gewünschtem festem Startwert
- [ ] Der Wert wird numerisch gelesen (`numeric_state` bzw. `| float`); Attribute `min`/`max`/`step`/`mode`/`unit_of_measurement` werden über `state_attr(...)` gelesen
- [ ] Setzen erfolgt über `input_number.set_value`/`increment`/`decrement` mit `target.entity_id`
- [ ] Kein `input_number` trägt einen gemessenen oder abgeleiteten Wert (dafür `sensor`/Template-/Derivative-/Statistics-Sensor)
- [ ] Kein `input_number` ersetzt eine `input_select`-Optionsauswahl
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
