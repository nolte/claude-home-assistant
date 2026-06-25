# HA-Automation: Trend nutzen

Status: draft

## Kontext

Die `trend`-Integration erzeugt einen **`binary_sensor`**, der erkennt, ob ein beobachteter Wert über ein Zeitfenster **steigt oder fällt**, und das Ergebnis als `on`/`off` ausgibt. Sie sammelt Stichproben der Quelle, legt eine Ausgleichsgerade durch diese Stichproben und vergleicht deren **Gradienten** (gemessen in „Sensor-Einheiten pro Sekunde") gegen `min_gradient`. Überschreitet der Gradient die Schwelle in der erwarteten Richtung, geht der Sensor `on`.

Ihre reale HA-Einordnung ist **Helper** (zugleich „Binary sensor" und „Utility" laut Integrations-Karte) — kein verbindbares Gerät und keine eigene Automations-Domäne. Sie wird per UI-Helfer (Einstellungen → Geräte & Dienste → Helfer → „Helfer erstellen") oder als YAML unter der `binary_sensor`-Plattform `trend` eingerichtet.

Standardmäßig erkennt der Sensor **steigende** Trends (`on` bei positivem Gradienten ≥ `min_gradient`); `invert: true` dreht das auf **fallende** Trends um. Der Sensor braucht laut Doku „mindestens zwei Updates der getrackten Entität, um einen Trend zu etablieren". Das Verhalten hängt empfindlich von `sample_duration`, `max_samples` und `min_gradient` ab — eine schlechte Abstimmung erzeugt entweder Rauschen oder verschluckt echte Trends. Der Sensor exponiert u. a. die Attribute `gradient`, `min_gradient`, `invert`, `sample_count` und `sample_duration`.

Verifizierte Quellen: `/integrations/trend/` (Konfigurationsvariablen, `min_gradient`-Beispiel „-2 °C/h = -0.00055", Gradient „in Sensor-Einheiten pro Sekunde", `max_samples`-Faustregel „7200/120 = 60") sowie die Core-Komponente `homeassistant/components/trend/binary_sensor.py` für die exakten Attribut-Namen und die `is_on`-Logik (Betrag des Gradienten über `min_gradient` **und** gleiches Vorzeichen, danach ggf. invertiert).

## Wann verwenden

Verwende `trend` immer dann, wenn die **Richtung** (steigend oder fallend) eines numerischen Werts als wiederverwendbarer boolescher `binary_sensor` gebraucht wird — nicht der exakte Wert, sondern die Aussage „bewegt sich nach oben/unten". Typische Anwendungsfälle:

- **Steigenden Trend erkennen** — Hinweis, wenn die Raumtemperatur oder Luftfeuchtigkeit über das Sample-Fenster anzieht (Default `invert: false`)
- **Fallenden Trend erkennen** — Warnung bei sinkendem Batterie-/Tank-/Akku-Pegel via `invert: true`
- **Steigung statt Momentanwert** — Lüftung/Heizung schon bei beginnendem Anstieg auslösen, bevor eine feste Grenze erreicht ist (`min_gradient`)
- **Wiederverwendbares Richtungssignal** — dieselbe „steigt/fällt"-Aussage einmal definieren und in mehreren Automationen, Bedingungen und Dashboard-Karten als `binary_sensor.<name>` referenzieren
- **Diagnose über `gradient`** — die aktuell gemessene Steigung (Einheiten/Sekunde) per Attribut auf einem Dashboard sichtbar machen

Ein `trend` ist das richtige Werkzeug, sobald nur die **Richtung** zählt. Für den exakten Ratenwert, einen Momentan-Schwellenvergleich oder ungeglättetes Rauschen ist er es nicht (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Den `trend`-Helfer als kanonischen Weg festschreiben, eine **Richtung** (steigend/fallend) eines Werts als wiederverwendbaren booleschen `binary_sensor` auszudrücken
- Die Rolle von `sample_duration`, `max_samples`, `min_samples` und `min_gradient` für eine belastbare Trend-Erkennung verbindlich machen
- Den bewussten Einsatz von `invert` (fallend statt steigend) erzwingen
- Die Notwendigkeit der Glättung/Abtast-Abstimmung bei verrauschten Signalen festschreiben
- Klar abgrenzen, wann **kein** `trend` das richtige Werkzeug ist (exakter Ratenwert, Momentan-Schwelle, ungeglättetes Rauschen)

## Nicht-Ziele

- Die allgemeine Automations-Anatomie (Trigger/Bedingung/Aktion, Modi) — `ha-automation/automation`
- Der **exakte Zahlenwert** einer Änderungsrate (z. B. °C pro Stunde) — `ha-automation/derivative`
- Der Vergleich eines **Momentanwerts** gegen eine feste Grenze als Boolean — `ha-automation/threshold`
- Statistische Aggregate/Glättung (Mittelwert, Min/Max über ein Fenster) als Eingangs-Glättung — `ha-automation/statistics`
- Die Namens-Dimension (`friendly_name`/`unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration

- **MUSS [MUST]** genau eine zu beobachtende Quelle über `entity_id` angeben; ohne `attribute` wird der **State** getrackt, mit `attribute` der genannte Attributwert
- **MUSS [MUST]** `min_gradient` bewusst setzen (Default `0.0`) und in der Einheit „Sensor-Einheiten **pro Sekunde**" denken — die Doku rechnet ihr Beispiel „-2 °C pro Stunde" als `-2 / 3600 = -0.00055` vor; ein zu kleiner Wert macht den Sensor überempfindlich, ein zu großer verschluckt echte Trends
- **MUSS [MUST]** `sample_duration` (Default `0`, Sekunden) und `max_samples` (Default `2`) auf die Update-Frequenz der Quelle abstimmen; die Doku gibt die Faustregel vor: für einen Trend über zwei Stunden bei einem 120-s-Update muss `max_samples` ≥ `7200/120 = 60` sein
- **KANN [MAY]** `min_samples` (Default `2`) erhöhen, damit der Gradient erst nach genügend gesammelten Stichproben berechnet wird und kurze Ausreißer keinen Trend vortäuschen
- **MUSS [MUST]** `invert: true` setzen, wenn ein **fallender** statt eines steigenden Trends erkannt werden soll (Default `false` = steigend)
- **KANN [MAY]** `device_class` setzen, um Icon und `on`/`off`-Beschriftung im Frontend passend zu wählen
- **SOLLTE [SHOULD]** `friendly_name` und — bei YAML — `unique_id` vergeben, damit der Sensor stabil referenzierbar und im UI anpassbar ist; Mechanik in `ha/naming-conventions`

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den erzeugten `binary_sensor.<name>` als ganz normale boolesche Entität behandeln: als `state`-Trigger (`to: "on"`/`"off"`), als `state`-Bedingung und in Templates via `is_state(...)`; `on` bedeutet „Trend in der konfigurierten Richtung erkannt"
- **KANN [MAY]** das Attribut `gradient` (aktuell gemessene Steigung in Einheiten/Sekunde) sowie `min_gradient`, `invert`, `sample_count` und `sample_duration` zur Diagnose oder Dashboard-Anzeige auslesen
- **SOLLTE [SHOULD]** den `binary_sensor` bevorzugen, sobald dieselbe Richtungs-Aussage an **mehreren** Stellen (mehrere Automationen, Bedingungen, Dashboard-Karten) gebraucht wird — eine Trend-Definition statt n-facher Template-Duplikate
- **MUSS [MUST]** `unavailable`/`unknown` der Quell-Entität berücksichtigen: liefert die Quelle keine numerischen Stichproben, kann der Trend-Sensor unbestimmt werden — nachgelagerte Automationen müssen diesen Fall abfangen
- **SOLLTE [SHOULD]** beachten, dass `on` nach Wegfall des Trends erst wieder `off` wird, wenn der Gradient unter `min_gradient` fällt — für eine Halte-Logik mit fester Mindestdauer ist die Automations-`for`-Option (`ha-automation/automation`) zuständig, nicht der Trend selbst

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `trend` verwenden, um einen **exakten Ratenwert** zu erhalten oder anzuzeigen (z. B. „aktuell +1,4 °C/h") — `trend` liefert nur den Boolean „Trend ja/nein"; für die Rate als verwendbaren Zahlenwert/Sensor gehört `ha-automation/derivative` her
- **MUSS NICHT [MUST NOT]** `trend` verwenden, um einen **Momentanwert** gegen eine feste Grenze zu prüfen (z. B. „Temperatur > 25 °C") — das ist ein Schwellenvergleich, kein Richtungssignal; dafür gehört `ha-automation/threshold` (oder ein `numeric_state`-Trigger) her
- **SOLLTE NICHT [SHOULD NOT]** `trend` auf ein **stark verrauschtes** Signal ohne ausreichendes `sample_duration`/`max_samples` und ohne Vorglättung anwenden — Rauschen erzeugt Schein-Trends und falsche `on`/`off`-Wechsel; zuerst über `ha-automation/statistics` (z. B. gleitenden Mittelwert) glätten und den geglätteten Wert als `entity_id` verwenden, oder `min_gradient` und das Sample-Fenster konservativer wählen
- **SOLLTE NICHT [SHOULD NOT]** `trend` mit dem Default `max_samples: 2` für ein **langfristiges** Trendfenster einsetzen — zwei Stichproben messen nur die letzte Änderung, nicht den Trend über die Zeit; `sample_duration`/`max_samples` müssen das gewünschte Fenster abdecken (Faustregel der Doku)
- **MUSS NICHT [MUST NOT]** mit `trend` eine **boolesche Kombinationslogik** mehrerer Entitäten ausdrücken (UND/ODER) — dafür gehört ein **Template-Binary-Sensor** (`ha-automation/template`) her, der die zusammengesetzte Bedingung deklarativ ausdrückt

## Akzeptanzkriterien

- [ ] Genau eine `entity_id` ist gesetzt; `attribute` ist nur gesetzt, wenn nicht der State getrackt werden soll
- [ ] `min_gradient` ist bewusst in Einheiten **pro Sekunde** gesetzt (Stunden-/Minuten-Raten sind umgerechnet)
- [ ] `sample_duration` und `max_samples` decken das gewünschte Trendfenster ab (Faustregel der Doku angewandt); der Default `max_samples: 2` wird nicht für Langzeit-Trends belassen
- [ ] `invert: true` ist gesetzt, wenn ein fallender Trend erkannt werden soll
- [ ] Der `binary_sensor` wird als boolesche Entität in Triggern/Bedingungen/Templates verwendet; `on` = „Trend in konfigurierter Richtung"
- [ ] `unavailable`/`unknown` der Quelle ist nachgelagert abgefangen
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `trend` für exakte Raten (→ `derivative`), keinen `trend` für Momentan-Schwellen (→ `threshold`), kein ungeglättetes Rauschen, kein Langzeit-Trend mit `max_samples: 2`, keine Kombinationslogik (→ `template`)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Attribut-Stabilität**: Die exakten Attribut-Namen (`gradient`, `min_gradient`, `invert`, `sample_count`, `sample_duration`) und die `is_on`-Logik (Betrag + Vorzeichen) stammen aus der Core-Komponente, nicht aus der Integrations-Doku-Seite selbst. Soll die Spec sie als verbindlich führen oder nur als „beobachtbar, aber nicht dokumentiert garantiert" kennzeichnen, bis sie auf `/integrations/trend/` erscheinen?
