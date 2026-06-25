# HA-Automation: Filter-Sensor nutzen

Status: draft

## Kontext

Die `filter`-Integration ist ein **Sensor-Helfer**, der einen verrauschten numerischen Quell-Sensor nimmt und einen neuen, geglätteten Sensor erzeugt. Sie hängt eine oder mehrere Filterstufen an den Stream eines bestehenden `sensor`-Entitys und gibt den verarbeiteten Wert als eigene Entität aus. Typischer Anwendungsfall: einen zappelnden Temperatur-, Leistungs- oder Helligkeitssensor entrauschen, bevor er Automationen triggert, oder Ausreißer-Spitzen aus einem Funk-Sensor entfernen.

Anders als die Regel-Engine hat die Filter-Integration eine **Integrations-Karte** im Katalog. Ihre reale Einordnung ist laut Doku **Helper / Sensor / Utility** — kein verbindbares Gerät, sondern eine deklarative Sensor-Transformation. Konfiguriert wird sie als `sensor`-Plattform in YAML; der UI-Pfad unterstützt nur **eine** Filterstufe, mehrstufige Ketten erfordern YAML.

Filter sind **zustandsbehaftet** und führen **Verzögerung** ein: Jede Stufe betrachtet ein Fenster vergangener Zustände, sodass das geglättete Signal dem Roh-Signal nachläuft. Die Fenstergröße ist daher eine bewusste Abwägung zwischen Glättung und Latenz.

Diese Spec überführt die offizielle Integrations-Doku in eine verbindliche Konvention für die vom Plugin erzeugten Filter-Sensoren. Sie verweist auf `ha-automation/automation` (Konsum der erzeugten `sensor`-Entität) sowie auf `ha-automation/derivative` und `ha-automation/statistics` als Abgrenzungs-Alternativen.

Verifizierte Quelle: [`/integrations/filter/`](https://www.home-assistant.io/integrations/filter/).

## Wann verwenden

Verwende `filter`, wenn ein **verrauschter numerischer Quell-Sensor geglättet** und als neue, ruhigere Entität ausgegeben werden soll, bevor er Automationen triggert. Typische Anwendungsfälle:

- **Zappelnden Sensor entrauschen** — Temperatur, Leistung oder Helligkeit per `lowpass` oder `time_simple_moving_average` glätten
- **Ausreißer-Spitzen entfernen** — kurze Fehlmessungen eines Funk-/Batteriesensors per `outlier`-Stufe (`radius`) verwerfen
- **Unplausible Werte begrenzen** — Werte außerhalb fester Grenzen per `range` (`lower_bound`/`upper_bound`) abschneiden
- **Datenaufkommen reduzieren** — nur den ersten Wert pro Fenster durchlassen via `throttle`/`time_throttle` (Entprellung, keine Glättung)
- **Mehrstufige Verarbeitungskette** — mehrere Stufen in der `filters`-Liste verketten (z. B. `outlier` dann `lowpass`), Ausgabe jeder Stufe ist Eingabe der nächsten

Ein Filter-Sensor ist das richtige Werkzeug, sobald der **Wert selbst geglättet/bereinigt** werden soll. Für Änderungsrate, statistische Kennzahlen oder kategorische Zustände ist er es nicht (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Anatomie eines Filter-Sensors (`entity_id`, `filters`-Liste) verbindlich festschreiben
- Die sechs Filtertypen (`lowpass`, `outlier`, `throttle`, `time_throttle`, `time_simple_moving_average`, `range`) mit ihren typ-spezifischen Schlüsseln fixieren
- Den bewussten Umgang mit `window_size` (Glättung vs. Latenz) und `precision` erzwingen
- Die dokumentierten Fallstricke (DB-Last bei großem `window_size`, Reihenfolge in Ketten, UI-Limit) in prüfbare Regeln gießen
- Klar abgrenzen, wann **kein** Filter-Sensor das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Die Trigger-/Bedingungs-/Aktions-Syntax, die die erzeugte `sensor`-Entität konsumiert — `ha-automation/automation`
- Änderungsrate/Ableitung eines Sensors — `ha-automation/derivative`
- Statistische Kennzahlen (Mittelwert, Min/Max, Standardabweichung über ein Zeitfenster) — `ha-automation/statistics`
- Die Namens-Dimension (`name`, `unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Quality-Scale-Marker — nicht zutreffend (Nutzungs-Spec, kein Integrations-Entwicklungs-Konzept)

## Anforderungen

### Konfiguration

- **MUSS [MUST]** den Sensor als `sensor`-Plattform mit `platform: filter` definieren und eine `entity_id` (Pflicht; nur ein `sensor`-Quell-Entity) sowie eine nicht-leere `filters`-Liste (Pflicht) angeben
- **MUSS [MUST]** für jede generierte Entität eine `name` (englisch, ≤50 Zeichen) vergeben und eine `unique_id` setzen — letztere ist die Voraussetzung für UI-Anpassung der Entität (dokumentiert; Mechanik: `ha/naming-conventions`)
- **MUSS [MUST]** in jeder Stufe der `filters`-Liste den `filter`-Schlüssel mit einem der sechs Typen angeben: `lowpass`, `outlier`, `throttle`, `time_throttle`, `time_simple_moving_average`, `range`
- **SOLLTE [SHOULD]** `window_size` bewusst wählen (Default `1`): bei `time_throttle`/`time_simple_moving_average` als Zeit (`"hh:mm"`), sonst als Ganzzahl der zu betrachtenden vergangenen Zustände — größeres Fenster glättet stärker, erhöht aber die Latenz
- **KANN [MAY]** `precision` setzen (Default `2`), das den gefilterten Ausgabewert per Pythons `round()` auf die angegebenen Nachkommastellen rundet
- **MUSS [MUST]** die typ-spezifischen Schlüssel korrekt zuordnen: `time_constant` (Default `10`) nur bei `lowpass`; `radius` (Default `2.0`) nur bei `outlier`; `type` (Default `"last"`) nur bei `time_simple_moving_average`; `lower_bound`/`upper_bound` (Default `-∞`/`+∞`) nur bei `range`
- **MUSS [MUST]** beachten, dass `throttle` nur den ersten Zustand pro (ganzzahligem) Fenster durchlässt und `time_throttle` nur den ersten Zustand pro Zeitfenster — beide reduzieren das Datenaufkommen, glätten aber nicht

### Nutzung in Automationen & Templates

- **MUSS [MUST]** die erzeugte `sensor`-Entität (den geglätteten Wert) in Automationen und Templates anstelle des Roh-Sensors konsumieren, wo Glättung der Zweck war — Detailvertrag in `ha-automation/automation`
- **MUSS [MUST]** Filterstufen in der gewünschten Verarbeitungsreihenfolge anordnen — die Doku stellt klar: „Filter werden in der Reihenfolge angewandt, in der sie in der Konfiguration stehen"; die Ausgabe jeder Stufe ist die Eingabe der nächsten
- **SOLLTE [SHOULD]** die durch das Fenster eingeführte Latenz in zeitkritischen Triggern berücksichtigen — der geglättete Sensor läuft dem Roh-Signal nach

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** einen Filter-Sensor verwenden, um die **Änderungsrate** eines Werts zu berechnen (z. B. Verbrauch pro Stunde aus einem Zählerstand) — dafür ist die **Derivative**-Integration (`ha-automation/derivative`) gedacht; ein Filter glättet den Wert selbst, er differenziert ihn nicht
- **MUSS NICHT [MUST NOT]** einen Filter-Sensor verwenden, um **statistische Kennzahlen** (Mittelwert, Min/Max, Standardabweichung, Anzahl) über ein Zeitfenster zu gewinnen — dafür ist die **Statistics**-Integration (`ha-automation/statistics`) das richtige Werkzeug; der Filter gibt einen einzelnen geglätteten Strom aus, kein Set von Kennzahlen
- **SOLLTE NICHT [SHOULD NOT]** ein großes ganzzahliges `window_size` (>1, nicht-Zeit-Format) leichtfertig setzen — die Doku warnt, dass HA beim Start nahezu jeden gespeicherten Zustand des Quell-Sensors per DB-Query untersucht, was bei angepasstem `purge_keep_days` oder umfangreicher Historie die Responsivität verschlechtert; Zeit-Format oder kleines Fenster bevorzugen
- **SOLLTE NICHT [SHOULD NOT]** `throttle`/`time_throttle` einsetzen, wenn das Ziel **Glättung** ist — diese Filter lassen nur den ersten Wert pro Fenster durch (Datenreduktion/Entprellung), entrauschen das Signal aber nicht; für Glättung `lowpass` oder `time_simple_moving_average` verwenden
- **SOLLTE NICHT [SHOULD NOT]** einen Filter-Sensor auf einen nicht-numerischen oder kategorischen Zustand anwenden — die Filter operieren auf numerischen `sensor`-Werten; für Zustands-Logik einen Template-Sensor (`ha-automation/template`) nutzen

## Akzeptanzkriterien

- [ ] Der Sensor ist als `sensor`-Plattform `filter` mit `entity_id` (genau eine Quelle) und nicht-leerer `filters`-Liste definiert
- [ ] Jede Entität trägt eine englische `name` ≤50 Zeichen und eine `unique_id` (für UI-Anpassung)
- [ ] Jede Filterstufe nennt einen der sechs gültigen `filter`-Typen
- [ ] `window_size` ist bewusst gewählt (Zeit-Format bei `time_*`, sonst Ganzzahl); die Latenz ist berücksichtigt
- [ ] Typ-spezifische Schlüssel sind korrekt zugeordnet (`time_constant`/`lowpass`, `radius`/`outlier`, `type`/`time_simple_moving_average`, `lower_bound`/`upper_bound`/`range`)
- [ ] Filterstufen stehen in der beabsichtigten Verarbeitungsreihenfolge
- [ ] Kein leichtfertig großes ganzzahliges `window_size` (DB-Last-Warnung berücksichtigt)
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein Filter für Änderungsrate (derivative), Statistik (statistics) oder Drossel-statt-Glättung
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Default-Filterwahl**: Soll diese Spec einen Default-Filtertyp für „verrauschten Sensor glätten" verbindlich empfehlen (z. B. `outlier` gefolgt von `lowpass`), oder bleibt die Filterwahl eine Fall-zu-Fall-Entscheidung des Autors?
