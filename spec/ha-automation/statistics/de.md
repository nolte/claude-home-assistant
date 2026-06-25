# HA-Automation: Statistics-Sensor nutzen

Status: draft

## Kontext

Die `statistics`-Integration stellt einen **Statistik-Sensor** bereit: Er beobachtet eine Quell-Entität (`entity_id` — nur Sensoren und Binärsensoren) und berechnet aus deren jüngsten Messwerten **eine einzelne statistische Kennzahl** (`state_characteristic`) wie Mittelwert, Median, Minimum, Maximum, Änderung oder Standardabweichung über ein gleitendes Fenster der letzten Samples. Der Sensor ist damit ein **gleitendes Aggregat über aktuelle Werte**, nicht eine Langzeit-Historie.

`statistics` ist **keine** Automation-Domäne. Ihre reale HA-Kategorie ist **Helper/Utility** (Integrations-Karte unter `/integrations/statistics/`); der Sensor wird per YAML (Plattform-Sensor) oder als UI-Helfer angelegt. Diese Spec überführt die offizielle Nutzungs-Doku in eine verbindliche Konvention dafür, wie das Plugin Statistik-Sensoren konfiguriert und in Automationen liest.

Das Sample-Fenster wird über zwei Achsen begrenzt: `sampling_size` (maximale Anzahl gespeicherter Messwerte) und/oder `max_age` (maximales Alter gespeicherter Messwerte). Beide zusammen schneiden auf die jüngsten `sampling_size` Samples innerhalb des `max_age`-Fensters zu.

Verifizierte Quelle: `/integrations/statistics/` (Konfigurationsvariablen `entity_id`, `name`, `state_characteristic`, `sampling_size`, `max_age`, `keep_last_sample`, `percentile`, `precision`, `unique_id`; der vollständige Kennzahl-Katalog für numerische und binäre Quellen; die Sensor-Attribute `age_coverage_ratio`, `buffer_usage_ratio`, `source_value_valid`).

## Wann verwenden

Verwende `statistics`, wenn du aus einem Sensor oder Binärsensor **eine einzelne statistische Kennzahl über ein gleitendes Fenster der jüngsten Messwerte** brauchst — eine Verteilung über mehrere Samples, nicht einen einzelnen abgeleiteten Wert. Typische Anwendungsfälle:

- **Gleitender Mittelwert glätten** — über `state_characteristic: mean`/`average_linear` ein verrauschtes Signal (Temperatur, Leistung) glätten, etwa als saubere `entity_id`-Quelle für einen `threshold`-Helfer
- **Min/Max/Spanne im Fenster** — über `value_min`/`value_max`/`distance_absolute` die Extrema oder Schwankungsbreite der letzten Samples für Anzeige und Trigger ermitteln
- **Streuung/Rausch-Maß** — über `standard_deviation`/`variance`/`noisiness` beurteilen, wie stark ein Messwert schwankt
- **Änderung über das Fenster** — über `change`/`change_second`/`sum_differences` die Veränderung oder Zu-/Abnahme über die jüngsten Samples beziffern
- **Binärsensor aggregieren** — über `count_on`/`count`/`mean` zählen, wie oft ein Binärsensor im Fenster `on` war oder umgeschaltet hat
- **Fenster-Achsen bewusst spannen** — über `sampling_size` und/oder `max_age` (plus optional `keep_last_sample`) das Sample-Fenster nach Menge und/oder Alter definieren

Ein Statistik-Sensor ist richtig, sobald eine **echte Verteilung über mehrere aktuelle Samples** ausgewertet wird. Für Langzeit-/Historien-Auswertungen, einen einzelnen Formel-Wert oder einen rücksetzbaren Verbrauchszähler greifen andere Bausteine (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Den Pflicht-Vertrag (`entity_id` + `state_characteristic`) und die Fenster-Achsen (`sampling_size`, `max_age`, `keep_last_sample`) verbindlich festschreiben
- Die bewusste Wahl von `state_characteristic` aus dem dokumentierten Katalog gegen den Verwendungszweck erzwingen
- Die Trennung „gleitende Statistik über aktuelle Samples" vs. „Langzeit-Historie" als Abgrenzungsregel verankern
- Den Umgang mit numerischen vs. binären Quellen (unterschiedliche zulässige Kennzahlen) festschreiben
- Klar abgrenzen, wann **kein** Statistik-Sensor das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Langzeit-/historische Auswertungen über lange Zeiträume (Stunden/Tage „an" o. ä.) — `history_stats` bzw. die Recorder-Langzeitstatistik, außerhalb dieser Spec
- Die Automation-Engine selbst (Trigger/Bedingung/Aktion, Modi) — `ha-automation/automation`
- Allgemeine abgeleitete Einzelwerte per Template — `ha-automation/template`
- Die Namens-Dimension (`name`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Die exakte mathematische Definition jeder einzelnen Kennzahl — die Integrations-Karte ist die Quelle; hier nur Auswahlregeln

## Anforderungen

### Konfiguration

- **MUSS [MUST]** eine `entity_id` angeben, die ein **Sensor oder Binärsensor** ist („Only sensors and binary sensors are supported")
- **MUSS [MUST]** eine `state_characteristic` aus dem dokumentierten Katalog setzen — der Schlüssel ist Pflicht („The characteristic that should be used as the state of the statistics sensor")
- **MUSS [MUST]** für eine **numerische Quelle** eine Kennzahl aus dem numerischen Katalog wählen: `average_linear`, `average_step`, `average_timeless`, `change`, `change_sample`, `change_second`, `count`, `datetime_newest`, `datetime_oldest`, `datetime_value_max`, `datetime_value_min`, `distance_95_percent_of_values`, `distance_99_percent_of_values`, `distance_absolute`, `mean`, `mean_circular`, `median`, `noisiness`, `percentile`, `standard_deviation`, `sum`, `sum_differences`, `sum_differences_nonnegative`, `total`, `value_max`, `value_min`, `variance`
- **MUSS [MUST]** für eine **binäre Quelle** eine Kennzahl aus dem binären Katalog wählen: `average_step`, `average_timeless`, `count`, `count_on`, `count_off`, `datetime_newest`, `datetime_oldest`, `mean`
- **MUSS [MUST]** das Sample-Fenster über `sampling_size` und/oder `max_age` definieren; mindestens eine der beiden Achsen ist sinnvoll zu setzen, da `sampling_size` ohne `max_age` keine Zeitgrenze und `max_age` ohne `sampling_size` keine Mengengrenze hat
- **SOLLTE [SHOULD]** `sampling_size` „reasonably high" wählen oder weglassen, wenn die Samples über `max_age` getrieben werden sollen (Doku-Empfehlung)
- **KANN [MAY]** `keep_last_sample: true` setzen, damit der jüngste Sample-Wert unabhängig von `max_age` erhalten bleibt (Default `false`) — relevant, wenn die Quelle länger als `max_age` nicht aktualisiert
- **MUSS [MUST]** `percentile` (1–99, Default `50`) nur in Verbindung mit der `percentile`-Kennzahl setzen; es ist „only relevant with the percentile characteristic"
- **SOLLTE [SHOULD]** `precision` (Default `2`) bewusst an die sinnvolle Nachkommastellenzahl der Kennzahl anpassen
- **MUSS [MUST]** für jeden Sensor einen englischen `name` ≤50 Zeichen und eine `unique_id` für die UI-Anpassbarkeit vergeben (Mechanik: `ha/naming-conventions`)

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Statistik-Sensor (`sensor.<name>`) als Lesegröße behandeln; der State trägt die berechnete Kennzahl, nicht den Quellwert
- **KANN [MAY]** die dokumentierten Attribute auswerten: `age_coverage_ratio` (0.0–1.0, wie gut das `max_age`-Fenster mit Messwerten abgedeckt ist), `buffer_usage_ratio` (0.0–1.0, wie weit der `sampling_size`-Puffer gefüllt ist), `source_value_valid` (ob die Quelle gültige Werte liefert)
- **SOLLTE [SHOULD]** in Triggern/Bedingungen `source_value_valid`/`age_coverage_ratio` berücksichtigen, bevor auf der Kennzahl entschieden wird, wenn ein noch nicht gefülltes Fenster zu falschen Schlüssen führen kann
- **KANN [MAY]** die Kennzahl als `numeric_state`-Trigger/-Bedingung nutzen (z. B. „Mittelwert über die letzten N Werte überschreitet Schwelle") — Trigger-Mechanik in `ha-automation/automation`

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** den Statistik-Sensor für **Langzeit-/historische Auswertungen** über lange Zeiträume verwenden (z. B. „Stunden, die ein Gerät heute an war") — dafür sind `history_stats` bzw. die Recorder-Langzeitstatistik gedacht; `statistics` arbeitet auf einem gleitenden Fenster der jüngsten Samples, nicht auf der vollständigen Historie
- **SOLLTE NICHT [SHOULD NOT]** einen Statistik-Sensor anlegen, wo ein **einzelner abgeleiteter Wert** per Formel genügt (z. B. Summe/Differenz/Umrechnung zweier Entitäten) — das ist Aufgabe eines Template-Sensors (`ha-automation/template`); `statistics` ist nur sinnvoll, wenn eine echte Verteilung über mehrere Samples ausgewertet wird
- **SOLLTE NICHT [SHOULD NOT]** `state_characteristic` und Fenstergröße „nach Gefühl" wählen — die Kennzahl (z. B. `mean` vs. `median` vs. `change`) und `sampling_size`/`max_age` bestimmen die Aussage des Sensors vollständig; eine unpassende Kombination liefert eine technisch gültige, fachlich falsche Zahl
- **SOLLTE NICHT [SHOULD NOT]** eine **binäre Quelle** mit einer rein numerischen Kennzahl (z. B. `median`, `standard_deviation`) koppeln oder umgekehrt — die Doku führt getrennte Kennzahl-Kataloge für Sensor- und Binärsensor-Quellen; nur deren Schnittmenge ist über beide Quelltypen gültig
- **MUSS NICHT [MUST NOT]** `statistics` als Ersatz für einen zyklisch zurückgesetzten **Verbrauchszähler** missbrauchen (z. B. „Verbrauch dieser Woche") — dafür ist `utility_meter` (`ha-automation/utility-meter`) zuständig, das einen steigenden Gesamtzähler in abrechenbare Zyklen schneidet

## Akzeptanzkriterien

- [ ] Jeder Sensor hat eine `entity_id` (Sensor oder Binärsensor) und eine gesetzte `state_characteristic`
- [ ] Die gewählte `state_characteristic` stammt aus dem zum Quelltyp (numerisch vs. binär) passenden Katalog
- [ ] Das Fenster ist über `sampling_size` und/oder `max_age` bewusst definiert; `keep_last_sample` nur bei Bedarf
- [ ] `percentile` ist nur zusammen mit der `percentile`-Kennzahl gesetzt; `precision` ist bewusst gewählt
- [ ] Jeder Sensor trägt einen englischen `name` ≤50 Zeichen und eine `unique_id`
- [ ] Automationen lesen die Kennzahl und berücksichtigen ggf. `source_value_valid`/`age_coverage_ratio`
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein Statistik-Sensor, wo `history_stats`, `template` oder `utility_meter` das richtige Werkzeug ist
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
