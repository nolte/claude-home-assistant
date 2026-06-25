# HA-Automation: min_max nutzen

Status: draft

## Kontext

`min_max` ist eine **Helfer-/Sensor-Integration** (HA-Kategorien laut Doku: *Helper*, *Sensor*, *Utility*): Sie fasst die **aktuellen Werte mehrerer Quell-Sensoren zu einem Zeitpunkt** zu einem einzelnen abgeleiteten Sensor zusammen — als Minimum, Maximum, jüngster Wert, Mittel, Median, Spannweite oder Summe über die überwachten Entities. Es ist eine **Quer**-Aggregation über mehrere Quellen im Moment, keine **Zeit**-Statistik eines einzelnen Sensors über die Vergangenheit.

Auf Konfigurationsebene wird `min_max` über die UI (Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen) oder als YAML unter dem Sensor-Plattform-Schlüssel `min_max` angelegt. Pflicht ist `entity_ids` (mindestens zwei Entities). `type` wählt die Rechenart (Default `max`), `round_digits` rundet die Mittel-/Median-/Summen-Ausgabe. **Alle Quell-Entities müssen dieselbe Maßeinheit verwenden** — die Einheit des ersten Eintrags wird die Einheit des Sensors; bei abweichenden Einheiten geht der Sensor laut Doku in einen Fehlerzustand (`UNKNOWN`/`ERR`).

Verifizierte Quelle: [`/integrations/min_max/`](https://www.home-assistant.io/integrations/min_max/) (Konfigurationsschlüssel `entity_ids`/`type`/`round_digits`/`name`/`unique_id`; `type`-Werte `min`/`max`/`last`/`mean`/`median`/`range`/`sum`; mindestens zwei Entities; gemeinsame Maßeinheit; Behandlung von `unknown`-Zuständen — ignoriert außer bei `sum`; UI- und YAML-Einrichtung). Namens-Mechanik referenziert über `ha/naming-conventions`.

## Wann verwenden

Verwende `min_max`, wenn du die **aktuellen Werte mehrerer gleichartiger Sensoren zu einem Zeitpunkt** zu einem einzelnen Wert zusammenfassen willst — alle Quellen mit derselben Maßeinheit. Typische Anwendungsfälle:

- **Extremwert über Räume** — wärmster/kältester Raum als `max`/`min` über mehrere Temperatur-Sensoren
- **Mittelwert mehrerer Quellen** — Durchschnittstemperatur oder -feuchte über alle Raum-Sensoren (`mean`/`median`, `round_digits`)
- **Summe gleichartiger Zähler** — Gesamtleistung mehrerer Steckdosen oder Gesamtniederschlag (`sum`)
- **Jüngster Messwert** — den zuletzt gemeldeten Wert über eine Sensor-Gruppe abbilden (`last`)
- **Schwellen-Automation auf das Aggregat** — auf den zusammengefassten Wert triggern (z. B. „wärmster Raum > 26 °C → lüften") statt die Rechnung je Automation zu wiederholen

Ein `min_max`-Sensor ist das richtige Werkzeug, sobald **mehrere numerische Quellen im Moment** kombiniert werden. Für Zeit-Statistik einer einzelnen Quelle, Zustands-Dauer/-Häufigkeit oder nicht-numerische Gruppen-Logik ist er es nicht (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines `min_max`-Sensors (Pflicht-`entity_ids`, `type`, `round_digits`) verbindlich festschreiben
- Den korrekten Einsatz als momentane Quer-Aggregation mehrerer gleichartiger Sensoren fixieren
- Die dokumentierte Einheiten-Konsistenz (gleiche Maßeinheit, Einheit des ersten Eintrags) erzwingen
- Die `type`-Wahl (`min`/`max`/`last`/`mean`/`median`/`range`/`sum`) und die `round_digits`-Wirkung präzise festlegen
- Klar abgrenzen, wann ein `min_max`-Sensor **nicht** das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Modell der Automation selbst — `ha-automation/automation`
- Zustands-Dauer/-Häufigkeit eines einzelnen Entities über ein Fenster — `ha-automation/history-stats`
- Langzeit-Statistik (Mittel/Min/Max über die Zeit) eines einzelnen numerischen Sensors — `ha-automation/statistics`
- Nicht-numerische Gruppen-Zustandsaggregation (z. B. „eines an") — `ha-automation/group`
- Die Namens-Dimension (`name`, snake_case-`object_id`, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen `min_max`-Sensor über die UI-Helfer-Einrichtung oder als YAML-Sensor-Plattform `min_max` anlegen und den **Pflichtschlüssel** `entity_ids` mit **mindestens zwei** Entities setzen
- **MUSS [MUST]** sicherstellen, dass **alle** unter `entity_ids` referenzierten Quellen **dieselbe Maßeinheit** liefern — die Einheit des ersten Eintrags wird die Einheit des Sensors; bei abweichenden Einheiten geht der Sensor laut Doku in einen Fehlerzustand (Wert `UNKNOWN`, Einheit `ERR`)
- **MUSS [MUST]** `type` bewusst aus dem dokumentierten Katalog wählen: `min`, `max` (Default), `last`, `mean`, `median`, `range`, `sum` — jeder Wert berechnet eine andere Aggregation über die Quellen
- **SOLLTE [SHOULD]** `round_digits` (Default `2`) passend zur Größe setzen, da es die Ausgabe von `mean`, `median` und `sum` rundet und übermäßige Scheingenauigkeit vermeidet
- **SOLLTE [SHOULD]** ein `unique_id` setzen, damit der Sensor in der UI anpassbar wird, und die `object_id` als snake_case-Slug sowie den `name` englisch und ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Sensorwert numerisch lesen: in `numeric_state`-Triggern/-Bedingungen per `above`/`below`, in Templates per `states('sensor.x') | float` — der Wert ist die gewählte Aggregation der Quellen zum aktuellen Zeitpunkt
- **MUSS [MUST]** beachten, dass `unknown`-Quellzustände laut Doku ignoriert werden — **außer bei `type: sum`**, wo der Sensor selbst `unknown` wird; Automationen müssen diesen Fall (und den Einheiten-Fehlerzustand) abfangen, statt blind zu rechnen
- **SOLLTE [SHOULD]** den Sensor als Eingang für Schwellen-Automationen nutzen (z. B. „wärmster Raum > 26 °C → lüften"), statt die Min-/Max-/Mittel-Berechnung in jeder Automation per Template zu wiederholen
- **KANN [MAY]** `type: last` nutzen, um den jüngsten gemeldeten Wert über die Quellen abzubilden, wenn nicht eine echte Aggregation, sondern der letzte Messwert gewünscht ist

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `min_max` als **Zeit-Statistik eines einzelnen Sensors** (Mittel/Min/Max über die Vergangenheit) zweckentfremden — dafür ist `statistics` (`ha-automation/statistics`) zuständig, das eine **einzelne** `entity_id` konsumiert; dieser Verweis gilt also für den Einzelquellen-Fall, weil `min_max` mehrere Quellen **zu einem Zeitpunkt** kombiniert und keinen Zeitverlauf einer einzelnen Quelle bildet
- **MUSS NICHT [MUST NOT]** `min_max` für **Zustands-Dauer/-Häufigkeit** (wie lange/wie oft ein Entity in einem Zustand war) verwenden — dafür ist `history_stats` (`ha-automation/history-stats`) gedacht, weil `min_max` numerische Momentanwerte aggregiert und keine Verlaufs-/Zustandsauswertung kennt
- **MUSS NICHT [MUST NOT]** `min_max` für **nicht-numerische Gruppen-Zustandsaggregation** (z. B. „eine von mehreren Türen offen", „mindestens ein Licht an") einsetzen — dafür ist eine **Gruppe** (`ha-automation/group`) das richtige Werkzeug, weil `min_max` ausschließlich auf numerischen Werten mit gemeinsamer Einheit rechnet. Bietet hingegen auch eine Sensor-`group` eine momentane numerische Mehrquellen-Aggregation (Mittel/Median/Spannweite/Summe), greift folgender Tie-Breaker: `min_max` (`ha-automation/min-max`) für einen eigenständigen Aggregat-Sensor, eine Sensor-`group` (`ha-automation/group`), wenn das Aggregat zugleich eine Gruppen-Entität sein bzw. neben der Gruppensteuerung leben soll
- **MUSS NICHT [MUST NOT]** Quellen mit **uneinheitlichen Maßeinheiten** kombinieren (z. B. °C und °F oder W und kWh) — der Sensor verfällt laut Doku in `UNKNOWN`/`ERR`; vor der Aggregation müssen die Quellen auf eine gemeinsame Einheit normalisiert werden (z. B. über Template-Sensoren)
- **SOLLTE NICHT [SHOULD NOT]** `round_digits` so grob setzen, dass schwellenrelevante Nachkommastellen verloren gehen, wenn der Sensor `above`/`below`-Vergleiche speist — die Rundung wirkt auf den ausgegebenen Wert und kann Schwellen-Logik verfälschen

## Akzeptanzkriterien

- [ ] Jeder `min_max`-Sensor setzt `entity_ids` mit mindestens zwei Entities
- [ ] Alle Quell-Entities liefern dieselbe Maßeinheit (kein `UNKNOWN`/`ERR`-Fehlerzustand)
- [ ] `type` ist bewusst aus `min`/`max`/`last`/`mean`/`median`/`range`/`sum` gewählt
- [ ] `round_digits` ist passend gesetzt und verfälscht keine schwellenrelevanten Nachkommastellen
- [ ] Die Lese-Logik fängt `unknown` (insb. bei `sum`) und den Einheiten-Fehlerzustand ab
- [ ] Der Sensor wird als momentane Quer-Aggregation mehrerer Quellen genutzt, nicht als Zeit-Statistik
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `min_max`, wo `statistics` (Zeit-Statistik), `history_stats` (Zustands-Dauer/-Häufigkeit) oder eine `group` (nicht-numerische Aggregation) das richtige Werkzeug ist
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
