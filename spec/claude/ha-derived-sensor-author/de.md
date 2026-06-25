# Skill: `ha-derived-sensor-author`

Status: draft

## Kontext

Home Assistant bringt eine Reihe vorgefertigter Integrationen mit, die aus bestehenden Entities einen abgeleiteten oder statistischen Sensor berechnen — `bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration` (Riemann-Summe), `utility_meter` und `group`. Sie sind die richtige Antwort, wenn ein Nutzer eine Rate, eine Glättung, eine Aggregation, eine Schwelle, einen Trend, eine Verbrauchsperiode oder eine Wahrscheinlichkeit braucht — statt diese Mathematik frei Hand in ein `template` zu schreiben (das die zeitliche Historie nicht kennt) oder in eine Automation zu gießen (die in `input_*` zwischenspeichert). Der `ha-automation/`-Korpus beschreibt jede dieser Integrationen, aber bisher operationalisiert sie kein Skill. Typische Fehler: `prob_given_true`/`prob_given_false` auf 0/1 setzen (bricht Bayes), `state_class: total_increasing` an der Quelle eines `derivative` vergessen, ein zu großes ganzzahliges `window_size` beim `filter` (DB-Last beim Start), eine fluktuierende Quelle in einen `utility_meter` stecken, oder `min_max`-Quellen mit unterschiedlicher Einheit (→ `ERR`).

Dieser Skill autoriert **einen** abgeleiteten/statistischen Sensor aus einer beschriebenen Absicht als spec-konformes YAML, wählt die richtige Integration (und grenzt sie gegen die verwandten ab) und liefert einen Konformitäts-Bericht.

## Scope

Generierung genau eines abgeleiteten Sensors pro Lauf aus: `bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration`, `utility_meter`, `group`. Der Skill bestimmt die Integration (oder fragt nach), liest die zuständige `ha-automation/<topic>`-Spec und schreibt den Block als `sensor:`/`binary_sensor:`-Plattform-Eintrag, als Top-Level-`utility_meter:` oder als modernen domänen-spezifischen `group` in `configuration.yaml` (oder ein `packages/`-File).

## Ziele

- Aus einer Prosa-Absicht die richtige abgeleitete/statistische Integration wählen und als spec-konformen YAML-Block schreiben
- Den mathematik-tragenden Parameter pro Integration korrekt setzen (`observations`/`prob_given_*`, `unit_time`/`time_window`, `filters`/`window_size`, `state_characteristic`, `lower`/`upper`/`hysteresis`, `min_gradient`/`sample_duration`, `start`/`end`/`duration`, `method`, `cycle`/`tariffs`, `type`)
- Die Integrationen scharf gegeneinander abgrenzen (Rate vs. Glättung vs. Integral; Momentan-Aggregat vs. Zeit-Aggregat vs. Historie; Schwelle vs. Trend)
- Den produzierten Sensor korrekt typisieren (`sensor` vs. `binary_sensor`, `device_class`/`state_class`) und gegen Quell-`unavailable`/`unknown` robust machen
- Auf Abhängigkeiten hinweisen (Recorder-Retention für `statistics`/`history_stats`; `integration` als typische Quelle eines `utility_meter`)

## Nicht-Ziele

- Die generische `template:`-Integration (frei formulierte Jinja-Sensoren) — das ist `ha-automation-author`
- Zustands-Helfer (`input_*`, `counter`, `timer`, `schedule`) — das ist `ha-helper-scaffold`
- Automationen/Scripts/Scenes — `ha-automation-author`
- Echte Sensoren aus einer eigenen Integration — `ha-integration-scaffold`
- Blueprints — `ha-blueprint-scaffold`
- Deployment in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a sensor for the rate of change / energy from power / moving average / threshold / trend of …"
  - „make a utility_meter / statistics sensor / bayesian binary_sensor / min_max sensor for …"
  - „erstelle einen Sensor für die Änderungsrate / den Verbrauch / den gleitenden Mittelwert / die Schwelle von …"

### Eingaben

- **MUSS [MUST]** erfassen: `intent` (Prosa, welcher abgeleitete Wert berechnet werden soll)
- **KANN [MAY]** erfassen: `integration` (`bayesian` / `derivative` / `filter` / `min_max` / `statistics` / `threshold` / `trend` / `history_stats` / `integration` / `utility_meter` / `group`); fehlt sie, leitet der Skill sie aus der Absicht ab und bestätigt sie
- **KANN [MAY]** erfassen: `source` (Quell-Entity/-Entities), `name`/`unique_id`, `target_dir`, `target_file` (Default `configuration.yaml`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** `intent` als nichtleer prüfen
- **MUSS [MUST]** die Integration auflösen und gegen die Abgrenzungs-Regeln prüfen: verlangt die Absicht eine freie Formel (→ `template` via `ha-automation-author`), einen gespeicherten Zustand (→ `ha-helper-scaffold`) oder eine verwandte aber andere Integration (Rate statt Glättung etc.), **MUSS [MUST]** der Skill umlenken
- **MUSS [MUST]** die zuständige `ha-automation/<topic>`-Spec lesen
- **MUSS [MUST]** prüfen, dass eine Quell-Entity benannt ist (außer `bayesian`, das über `observations` arbeitet); ohne Quelle abbrechen und nachfragen
- **MUSS NICHT [MUST NOT]** einen bestehenden Sensor mit gleicher `unique_id` überschreiben

### Generierungs-Regeln (pro Integration, aus der jeweiligen Spec)

- **MUSS [MUST]** für `bayesian` `prior` und eine vollständige `observations`-Liste setzen, `prob_given_true`/`prob_given_false` niemals auf 0 oder 1, und bei Multi-State-Beobachtungen die Wahrscheinlichkeiten je auf 1.0 summieren
- **MUSS [MUST]** für `derivative` und `integration` `unit_time` bewusst wählen; bei `derivative` an nicht-negativen Quellen `state_class: total_increasing` an der Quelle voraussetzen; bei `integration` `method` zur Quell-Charakteristik passend wählen
- **MUSS [MUST]** für `filter` die `filters`-Stufen in bewusster Reihenfolge setzen und `window_size` bewusst wählen (Zeitformat vs. Integer; kein unnötig großer Integer-Wert → Start-DB-Last)
- **MUSS [MUST]** für `min_max` gleiche Einheit aller Quellen sicherstellen und `type` aus dem Katalog wählen
- **MUSS [MUST]** für `statistics` ein `state_characteristic` passend zum Quelltyp (numerisch vs. binär) wählen und ein Fenster über `sampling_size` und/oder `max_age` definieren
- **MUSS [MUST]** für `threshold` mindestens `lower` oder `upper` setzen (bei beiden `lower < upper`) und bei verrauschten Quellen `hysteresis` setzen
- **MUSS [MUST]** für `trend` `min_gradient` in Einheit **pro Sekunde** ausdrücken und `sample_duration`/`max_samples` an die Update-Frequenz anpassen
- **MUSS [MUST]** für `history_stats` genau zwei von `start`/`end`/`duration` setzen, ein zur Quelle passendes `state` und DST-sichere Templates (`today_at()`, `timedelta()`); das Fenster innerhalb der Recorder-Retention halten
- **MUSS [MUST]** für `utility_meter` eine monoton steigende Quelle voraussetzen, `cycle` (oder `cron`, nicht beides) wählen und `delta_values`/`periodically_resetting`/`net_consumption` zur Quell-Realität setzen; Tarifwechsel über `select.select_option`
- **MUSS [MUST]** für `group` moderne domänen-spezifische Gruppen statt des alten `group:`-YAML nutzen, Mitglieder einer Domäne, `all` (OR vs. AND) bewusst setzen und bei Sensor-Gruppen `type`/`ignore_non_numeric` belegen
- **MUSS [MUST]** den produzierten Sensor korrekt typisieren und gegen Quell-`unavailable`/`unknown` robust machen
- **MUSS [MUST]** alle Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** das Artefakt offline validieren (YAML-Lint; Plausibilität von Einheit/`unit_time`/Fenster; Quell-Typ-Kompatibilität) und Verstöße benennen
- **MUSS [MUST]** auf Laufzeit-Abhängigkeiten hinweisen (Recorder-Retention, `integration`→`utility_meter`-Verkettung, unreife Fenster über `source_value_valid`/`age_coverage_ratio`)
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien der zuständigen Spec liefern, plus Datei-Pfad und Defaults

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als einen Sensor pro Lauf erzeugen
- **MUSS NICHT [MUST NOT]** eine freie Jinja-Formel als abgeleiteten Sensor ausgeben, wenn eine dedizierte Integration passt (oder umgekehrt eine dedizierte Integration, wo nur `template` passt)
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet die Integration ab (oder erfragt sie) und bestätigt sie
- [ ] Skill liest die zuständige `ha-automation/<topic>`-Spec vor der Generierung
- [ ] Der mathematik-tragende Parameter ist pro Integration korrekt gesetzt (siehe Generierungs-Regeln)
- [ ] Der produzierte Sensor ist korrekt typisiert (`sensor`/`binary_sensor`, `device_class`/`state_class`) und gegen Quell-`unavailable`/`unknown` robust
- [ ] Eine auf eine freie Formel oder einen gespeicherten Zustand zielende Absicht wird umgelenkt
- [ ] Bericht nennt Laufzeit-Abhängigkeiten (Recorder-Retention, `integration`→`utility_meter`)
- [ ] Skill liefert einen CONFORMANT / NEEDS-WORK-Bericht mit Datei-Pfad und Defaults

## Offene Fragen

- **Verkettung `integration` → `utility_meter`**: Soll der Skill bei „täglicher Stromverbrauch aus Leistung" beide Sensoren in einem Lauf erzeugen (Riemann-Integral + Utility-Meter-Zyklus) oder strikt einen pro Lauf? Aktuell einer pro Lauf, mit Hinweis auf die Verkettung.
- **`group`-Sonderfall**: `group` ist weniger „Sensor" als domänen-Aggregat. Bleibt es in diesem Skill oder gehört es eher zu einem Entity-Gruppen-Skill? Aktuell hier, weil Sensor-Gruppen die abgeleitete-Aggregat-Semantik teilen.
- **Validierungs-Tiefe**: Wann lohnt ein echtes `ha core check` gegen eine temporäre Config statt statischer Plausibilitäts-Prüfung?
