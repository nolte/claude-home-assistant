# HA-Automation: Bayesian-Sensor nutzen

Status: draft

## Kontext

Die `bayesian`-Integration ist ein **Binary-Sensor-Helfer**, der mehrere unsichere Signale per Bayes-Schluss zu einer einzigen Wahrscheinlichkeit verrechnet und daraus einen `on`/`off`-Zustand ableitet. Typischer Anwendungsfall: „Ist der Raum belegt?" — geschätzt aus Bewegung, Stromverbrauch des Fernsehers, Türzustand und Tageszeit, von denen keines allein eindeutig ist. Der Sensor pflegt eine Ausgangswahrscheinlichkeit (`prior`) und aktualisiert sie für jede konfigurierte Beobachtung (`observation`) anhand zweier bedingter Wahrscheinlichkeiten, `prob_given_true` und `prob_given_false`.

Anders als die Regel-Engine hat die Bayesian-Integration eine **Integrations-Karte** im Katalog. Ihre reale Einordnung ist laut Doku **Binary Sensor / Utility** (Helfer-Kategorie) — kein verbindbares Gerät, sondern eine deklarative Sensor-Definition. Konfiguriert wird sie als `binary_sensor`-Plattform in YAML oder über den UI-Helfer; der UI-Pfad rechnet Wahrscheinlichkeiten als Prozente (0–100), YAML als Brüche (0–1).

Diese Spec überführt die offizielle Integrations-Doku in eine verbindliche Konvention für die vom Plugin erzeugten Bayesian-Sensoren. Sie verweist auf die Wurzel-Spec `ha-automation/automation` (Konsum der erzeugten `binary_sensor`-Entität in Triggern/Bedingungen) und auf `ha-automation/template` als deterministische Alternative.

Verifizierte Quelle: [`/integrations/bayesian/`](https://www.home-assistant.io/integrations/bayesian/).

## Wann verwenden

Verwende `bayesian` immer dann, wenn ein `on`/`off`-Zustand aus **mehreren unsicheren, voneinander unabhängigen Signalen** geschätzt werden soll, von denen keines allein eindeutig ist. Typische Anwendungsfälle:

- **Wahrscheinliche Anwesenheit/Belegung** — „Raum belegt?" aus Bewegung, TV-Stromverbrauch, Türzustand und Tageszeit kombinieren (`state`/`numeric_state`-Beobachtungen)
- **Schlaf-/Abwesenheits-Inferenz** — Schlafzustand oder „Haus leer" aus mehreren schwachen Indizien (Licht aus, keine Bewegung, Uhrzeit) ableiten
- **Numerische Indizien einbeziehen** — Stromverbrauch oder Helligkeit über `above`/`below` als `numeric_state`-Beobachtung in die Wahrscheinlichkeit einfließen lassen
- **Template-Beobachtung** — eine zusammengesetzte Bedingung als `value_template`-Beobachtung (`True`/`False`) einspeisen
- **Abgestufte Logik über `probability`** — das `probability`-Attribut (Posterior) lesen, um unterhalb der harten `probability_threshold`-Schwelle differenziert zu reagieren

Ein Bayesian-Sensor ist das richtige Werkzeug, sobald **mehrere schwache, unsichere Signale** zu einer Wahrscheinlichkeit verrechnet werden. Für deterministische Logik, Glättung oder ein einzelnes starkes Signal ist er es nicht (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Anatomie eines Bayesian-Sensors (`prior`, `probability_threshold`, `observations`) verbindlich festschreiben
- Die drei Beobachtungstypen (`state`, `numeric_state`, `template`) und das Multi-State-Muster mit ihren Pflicht-Wahrscheinlichkeiten fixieren
- Ehrliche, dokumentierte Wahrscheinlichkeitsschätzungen erzwingen statt rückwärts auf ein Wunschergebnis getunter Werte
- Die dokumentierten Fallstricke (Werte `0`/`1` vermeiden, Multi-State-Summen, Schwellwert vs. Prior) in prüfbare Regeln gießen
- Klar abgrenzen, wann **kein** Bayesian-Sensor das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Die Trigger-/Bedingungs-/Aktions-Syntax, die die erzeugte `binary_sensor`-Entität konsumiert — `ha-automation/automation`
- Allgemeine Template-Syntax in `value_template` — `/docs/configuration/templating/`, hier nur der Bayesian-spezifische Beobachtungsvertrag
- Die Namens-Dimension (`name`, `unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Glättung/Entrauschen eines verrauschten Sensorstreams — `ha-automation/filter`
- Quality-Scale-Marker — nicht zutreffend (Nutzungs-Spec, kein Integrations-Entwicklungs-Konzept)

## Anforderungen

### Konfiguration

- **MUSS [MUST]** den Sensor als `binary_sensor`-Plattform mit `platform: bayesian` definieren und einen `prior` (Float 0–1, Pflicht) sowie eine nicht-leere `observations`-Liste (Pflicht) angeben
- **MUSS [MUST]** für jede generierte Entität eine `name` (englisch, ≤50 Zeichen) und eine stabile `unique_id` als snake_case-Slug vergeben, damit die Entität UI-anpassbar bleibt (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** `probability_threshold` (Default `0.5`) bewusst setzen; ist die Schwelle höher als der `prior`, ist der Default-Zustand `off` (dokumentierte Eigenschaft)
- **MUSS [MUST]** jede Beobachtung mit `prob_given_true` und `prob_given_false` (beide Float 0–1, Pflicht) versehen — der Wahrscheinlichkeit, dass die Beobachtung zutrifft, wenn das Ereignis wahr bzw. falsch ist
- **MUSS NICHT [MUST NOT]** für `prob_given_true`/`prob_given_false` die Werte `0` oder `1` verwenden — die Doku warnt, dass diese die Odds verfälschen und selten zutreffen, da Sensoren ausfallen; bei extremen Schätzungen `0.99`/`0.001` verwenden, wobei die Zahl der `9`er/`0`er das Gewicht bestimmt
- **MUSS [MUST]** bei `platform: state` `entity_id` und `to_state` (Ziel-Zustandswert) angeben
- **MUSS [MUST]** bei `platform: numeric_state` `entity_id` und mindestens eines von `above`/`below` angeben (Bereichsgrenzen)
- **MUSS [MUST]** bei `platform: template` ein `value_template` angeben, das zu `True`/`False` auswertet
- **MUSS [MUST]** bei einer Entität mit mehr als zwei relevanten Zuständen/Bereichen **alle möglichen Werte** als separate Beobachtungen abdecken; dabei müssen die `prob_given_true` aller Werte zu `1` summieren, ebenso die `prob_given_false` (dokumentierte Multi-State-Regel)
- **KANN [MAY]** `device_class` setzen, um Icon/Darstellung der `binary_sensor`-Entität zu beeinflussen

### Nutzung in Automationen & Templates

- **MUSS [MUST]** die erzeugte `binary_sensor`-Entität in Automationen nur über ihren `on`/`off`-Zustand triggern/gaten (`state`-/`numeric_state`-Trigger und -Bedingungen) — Detailvertrag in `ha-automation/automation`
- **KANN [MAY]** das `probability`-Attribut der Entität (die berechnete Posterior-Wahrscheinlichkeit) in Templates/Bedingungen lesen, etwa um abgestufte Logik unterhalb der harten Schwelle zu bauen
- **KANN [MAY]** das `observations`-Attribut zur Fehlersuche heranziehen, um nachzuvollziehen, welche Beobachtungen aktuell zur Wahrscheinlichkeit beitragen
- **SOLLTE [SHOULD]** den Schwellwert `probability_threshold` anheben, statt Beobachtungs-Wahrscheinlichkeiten zu verbiegen, wenn der Sensor zu leicht auslöst (dokumentierte Empfehlung)

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** einen Bayesian-Sensor für eine **deterministische UND/ODER-Verknüpfung** mehrerer eindeutiger Signale verwenden (z. B. „Tür offen UND Alarm scharf") — dafür ist ein **Template-Binary-Sensor** (`ha-automation/template`) das richtige Konstrukt, weil die Logik exakt, nachvollziehbar und ohne Wahrscheinlichkeits-Tuning ist; Bayes ist nur dann gerechtfertigt, wenn die Einzelsignale **unsicher** sind
- **MUSS NICHT [MUST NOT]** `prob_given_true`/`prob_given_false` rückwärts so wählen, dass ein gewünschtes Ergebnis erzwungen wird — die Doku warnt ausdrücklich davor; die Werte müssen **ehrliche** Schätzungen der bedingten Wahrscheinlichkeiten sein, sonst ist das Modell wertlos
- **SOLLTE NICHT [SHOULD NOT]** einen Bayesian-Sensor einsetzen, wenn **ein einzelnes** zuverlässiges Signal genügt — die Bayes-Maschinerie fügt nur dann Wert hinzu, wenn mehrere schwache, voneinander unabhängige Signale kombiniert werden; bei einem starken Signal genügt ein direkter `state`-Trigger oder Template-Sensor
- **SOLLTE NICHT [SHOULD NOT]** einen verrauschten **numerischen Stream glätten** wollen, indem man ihn in Bayes-Beobachtungen presst — Glättung/Entrauschen leistet die `filter`-Integration (`ha-automation/filter`); Bayes liefert eine binäre Inferenz, keine geglättete Messreihe
- **SOLLTE NICHT [SHOULD NOT]** stark **korrelierte** Signale als unabhängige Beobachtungen einspeisen (z. B. zwei Bewegungsmelder, die fast immer gemeinsam auslösen) — Bayes behandelt Beobachtungen als bedingt unabhängig, doppelt gezählte Korrelation überschätzt die Wahrscheinlichkeit

## Akzeptanzkriterien

- [ ] Der Sensor ist als `binary_sensor`-Plattform `bayesian` mit `prior` (0–1) und nicht-leerer `observations`-Liste definiert
- [ ] Jede Entität trägt eine englische `name` ≤50 Zeichen und eine stabile snake_case-`unique_id`
- [ ] `probability_threshold` ist bewusst gesetzt (Default `0.5` nur, wo gewollt)
- [ ] Jede Beobachtung hat `prob_given_true` und `prob_given_false`; keiner der Werte ist `0` oder `1`
- [ ] Beobachtungstyp-spezifische Pflichtfelder sind gesetzt (`state`: `entity_id`+`to_state`; `numeric_state`: `entity_id`+`above`/`below`; `template`: `value_template`)
- [ ] Bei Multi-State-Entitäten sind alle Werte abgedeckt und die `prob_given_true`/`prob_given_false` summieren je zu `1`
- [ ] Die Wahrscheinlichkeiten sind ehrliche Schätzungen, nicht rückwärts auf ein Wunschergebnis getunt
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein Bayes für deterministische Logik (Template), Glättung (filter) oder ein einzelnes starkes Signal
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Unabhängigkeitsannahme**: Bayes setzt bedingte Unabhängigkeit der Beobachtungen voraus, die Doku verankert dazu keine eigene Warnung. Soll diese Spec eine harte Regel gegen offensichtlich korrelierte Beobachtungen aufnehmen oder bei der SOLLTE-NICHT-Empfehlung bleiben?
