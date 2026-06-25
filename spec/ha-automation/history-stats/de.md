# HA-Automation: history_stats nutzen

Status: draft

## Kontext

`history_stats` ist eine **Helfer-/Sensor-Integration** (HA-Kategorien laut Doku: *Helper*, *Sensor*, *Utility*): Sie erzeugt einen abgeleiteten Sensor, der auswertet, **wie lange** oder **wie oft** ein anderes Entity über ein **vergangenes Zeitfenster** in einem bestimmten Zustand war. Sie liefert damit eine rückblickende Kennzahl (z. B. „wie lange war das Licht heute an") — keinen Echtzeit-Zustand und keine numerische Aggregation von Messwerten.

Auf Konfigurationsebene wird `history_stats` als Sensor-Plattform unter dem Top-Level-Schlüssel `sensor` mit `platform: history_stats` (YAML) angelegt; eine UI-Helfer-Einrichtung bietet die Integration ebenfalls. Pflicht sind `entity_id` und `state`; `type` wählt die Ausgabeform (`time`/`ratio`/`count`, Default `time`). Das Zeitfenster wird über `start`, `end` und `duration` definiert, von denen **genau zwei der drei** angegeben werden müssen — den dritten Wert berechnet HA. Weil die Auswertung auf Verlaufsdaten beruht, hängt `history_stats` an den Integrationen **`recorder`** und **`history`**.

Verifizierte Quelle: [`/integrations/history_stats/`](https://www.home-assistant.io/integrations/history_stats/) (Konfigurationsschlüssel `entity_id`/`state`/`type`/`start`/`end`/`duration`/`name`/`unique_id`/`state_class`/`min_state_duration`; `type`-Werte `time`/`ratio`/`count`; Zwei-von-drei-Regel für `start`/`end`/`duration`; Templating in `start`/`end` mit `now()`/`today_at()`/`timedelta()`; Abhängigkeit von `history`/`recorder` und `purge_keep_days`). Namens-Mechanik referenziert über `ha/naming-conventions`.

## Wann verwenden

Verwende `history_stats`, wenn du **wie lange** oder **wie oft** ein Entity über ein **vergangenes Zeitfenster** in einem bestimmten Zustand war als rückblickende Kennzahl brauchst. Typische Anwendungsfälle:

- **Dauer „heute an"** — wie viele Stunden Licht, Pumpe oder Heizung heute liefen (`type: time`, Fenster über `today_at()`)
- **Anteil/Auslastung** — prozentualer Anteil eines Zustands über das Fenster, etwa „WLAN-Gerät heute online" (`type: ratio`)
- **Häufigkeit** — wie oft die Tür geöffnet oder ein Gerät eingeschaltet wurde (`type: count`)
- **Schwellen-Automation auf Vergangenheit** — auslösen, wenn die Pumpe heute > 2 h lief (`numeric_state` auf den `history_stats`-Sensor)
- **Mehrere Zustände als ein Treffer** — zusammengehörige Zustände als String-Liste unter `state` bündeln und als ein Ereignis zählen

Ein `history_stats`-Sensor ist das richtige Werkzeug, sobald die Kennzahl **rückblickend über ein Fenster** gebildet wird. Für den aktuellen Echtzeit-Zustand, Mehr-Sensor-Aggregation oder Werte-Langzeitstatistik ist er es nicht (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines `history_stats`-Sensors (Pflicht-`entity_id`/`state`, `type`, Zwei-von-drei-Zeitfenster) verbindlich festschreiben
- Den korrekten Einsatz als rückblickende Dauer-/Häufigkeits-Kennzahl über ein definiertes Fenster fixieren
- Die Zwei-von-drei-Regel für `start`/`end`/`duration` und das DST-sichere Templating (`today_at()`) erzwingen
- Die dokumentierte Abhängigkeit von `recorder`/`history` und die `purge_keep_days`-Grenze in prüfbare Regeln gießen
- Klar abgrenzen, wann ein `history_stats`-Sensor **nicht** das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Modell der Automation selbst — `ha-automation/automation`
- Numerische Aggregation mehrerer Sensoren zu einem Zeitpunkt — `ha-automation/min-max`
- Langzeit-Statistik (Mittel/Min/Max) eines einzelnen numerischen Sensors über die Zeit — `ha-automation/statistics`
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur die fensterbildenden Muster (`now()`/`today_at()`/`timedelta()`)
- Die Namens-Dimension (`name`, snake_case-`object_id`, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen `history_stats`-Sensor als Sensor-Plattform (`platform: history_stats` unter dem Top-Level-Schlüssel `sensor`) oder über die UI-Helfer-Einrichtung anlegen und die **Pflichtschlüssel** `entity_id` und `state` setzen
- **MUSS [MUST]** unter `state` den/die zu zählenden Zustandswert(e) als String oder **Liste von Strings** angeben (die Doku erlaubt einen einzelnen Wert oder mehrere); die Werte müssen die realen Zustände des referenzierten Entities treffen
- **MUSS [MUST]** **genau zwei** der drei Schlüssel `start`, `end`, `duration` angeben — den dritten Wert berechnet HA; alle drei oder nur einen anzugeben ist laut Doku ungültig
- **MUSS [MUST]** `type` bewusst wählen: `time` (Dauer in Stunden, Default), `ratio` (Anteil in Prozent), `count` (Anzahl der Treffer) — die Ausgabeeinheit hängt direkt vom `type` ab
- **SOLLTE [SHOULD]** in `start`/`end`-Templates DST-sicher mit `today_at()` (statt manueller Datums-/Zeit-Arithmetik) und `timedelta()` arbeiten, wie es die Doku ausdrücklich empfiehlt, um Fehler bei Sommer-/Winterzeit-Umstellung zu vermeiden
- **SOLLTE [SHOULD]** ein `unique_id` setzen, damit der Sensor in der UI anpassbar wird, und die `object_id` als snake_case-Slug sowie den `name` englisch und ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)
- **KANN [MAY]** `min_state_duration` setzen, um Zustandswechsel unterhalb einer Mindestdauer herauszufiltern, sowie `state_class` (Default `measurement`) anpassen, wenn der Sensor in Langzeit-Statistiken auftauchen soll

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Sensorwert numerisch lesen: in `numeric_state`-Triggern/-Bedingungen per `above`/`below`, in Templates per `states('sensor.x') | float` — der Wert ist je nach `type` Stunden, Prozent oder eine Anzahl
- **MUSS [MUST]** beachten, dass `history_stats` nur das **aktuelle** Fenster auswertet und sich gleitend aktualisiert (laut Doku: bei Änderung des Quell-Entities und einmal pro Minute) — der Wert ist kein eingefrorener Tagesabschluss, sondern ein laufender Stand des Fensters
- **SOLLTE [SHOULD]** den Sensor als Eingang für Schwellen-Automationen nutzen (z. B. „Pumpe lief heute > 2 h → Hinweis") statt die Verlaufsauswertung in einem Template per `states.*`-History nachzubauen
- **KANN [MAY]** mehrere `state`-Werte kombinieren, um zusammengehörige Zustände als einen Treffer zu behandeln (laut Doku zählt ein Übergang zwischen gelisteten Zuständen bei `count` als ein zusammenhängendes Ereignis)

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `history_stats` verwenden, um den **aktuellen Echtzeit-Zustand** eines Entities abzufragen oder darauf zu reagieren — dafür ist ein direkter `state`-/`numeric_state`-Trigger oder ein **Template-/Schwellen-Sensor** (`ha-automation/template`, Threshold) das richtige Werkzeug, weil `history_stats` eine rückblickende Aggregation über ein Fenster ist und nicht den Momentanwert liefert
- **MUSS NICHT [MUST NOT]** `history_stats` zur **numerischen Aggregation der Messwerte mehrerer Sensoren zu einem Zeitpunkt** (Min/Max/Mittel/Summe) zweckentfremden — dafür ist `min_max` (`ha-automation/min-max`) zuständig, weil `history_stats` Zustands-**dauern/-häufigkeiten** eines einzelnen Entities misst, nicht die Werte mehrerer Quellen kombiniert
- **SOLLTE NICHT [SHOULD NOT]** `history_stats` für **Langzeit-Statistik** (Mittel/Min/Max/Median eines numerischen Sensors über die Zeit) einsetzen — dafür ist `statistics` (`ha-automation/statistics`) gedacht, weil `history_stats` an **Zustände** (an/aus/„home") gebunden ist und keine fortlaufende Werte-Statistik bildet
- **SOLLTE NICHT [SHOULD NOT]** ein `duration`/`start`/`end`-Fenster wählen, das **über die Recorder-Aufbewahrung hinausreicht** (`purge_keep_days`) — laut Doku decken die Verlaufsdaten dann nicht das volle Fenster ab und die Statistik wird unvollständig; das Fenster muss innerhalb der gespeicherten Historie liegen
- **SOLLTE NICHT [SHOULD NOT]** **alle drei** Zeitschlüssel oder nur **einen** angeben — die Doku verlangt genau zwei von drei; jede andere Kombination ist ungültig oder mehrdeutig

## Akzeptanzkriterien

- [ ] Jeder `history_stats`-Sensor setzt die Pflichtschlüssel `entity_id` und `state`
- [ ] `state` trifft reale Zustandswerte des Entities (String oder Liste)
- [ ] Genau zwei der drei Schlüssel `start`/`end`/`duration` sind angegeben
- [ ] `type` ist bewusst gesetzt (`time`/`ratio`/`count`) und die Lese-Logik passt zur resultierenden Einheit
- [ ] `start`/`end`-Templates nutzen `today_at()`/`timedelta()` (DST-sicher) statt manueller Datums-Arithmetik
- [ ] Das Zeitfenster liegt innerhalb der Recorder-Aufbewahrung (`purge_keep_days`)
- [ ] Der Sensor wird als rückblickende Dauer-/Häufigkeits-Kennzahl genutzt, nicht als Echtzeit-Zustand
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `history_stats`, wo Template/Threshold (Echtzeit), `min_max` (Mehr-Sensor-Aggregation) oder `statistics` (Werte-Langzeitstatistik) das richtige Werkzeug ist
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
