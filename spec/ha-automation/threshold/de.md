# HA-Automation: Threshold nutzen

Status: draft

## Kontext

Die `threshold`-Integration erzeugt einen **`binary_sensor`**, der einen analogen Sensorwert gegen eine oder zwei Schwellen vergleicht und das Ergebnis als `on`/`off` ausgibt. Sie verwandelt damit eine kontinuierliche Messgröße (Temperatur, Feuchte, Leistung, Helligkeit …) in einen booleschen Zustand, der in Automationen, Bedingungen und Dashboards wiederverwendet werden kann. Eine optionale **Hysterese** verhindert das Flattern (rapides Hin- und Herschalten) rund um die Schwelle.

Ihre reale HA-Einordnung ist **Helper** (zugleich „Binary sensor" und „Utility" laut Integrations-Karte) — kein verbindbares Gerät und keine eigene Automations-Domäne. Sie wird per UI-Helfer (Einstellungen → Geräte & Dienste → Helfer → „Helfer erstellen") oder als YAML unter der `binary_sensor`-Plattform `threshold` eingerichtet.

Drei Modi ergeben sich aus den gesetzten Schlüsseln: nur `lower` (Untergrenze), nur `upper` (Obergrenze) oder beide (`lower` **und** `upper` → Bereichs-/„in_range"-Modus). Der erzeugte Sensor exponiert neben seinem `on`/`off`-Zustand das Attribut `position` (`above`, `below`, `in_range`, `unknown`) sowie `type`, `lower`, `upper`, `hysteresis` und `sensor_value`.

Verifizierte Quellen: `/integrations/threshold/` (Konfigurationsvariablen, Modus-Tabelle „Rising/Falling sensor values", Hysterese-Semantik) sowie die Core-Komponente `homeassistant/components/threshold/binary_sensor.py` für die exakten Attribut-Namen und `position`-Werte.

## Wann verwenden

Verwende `threshold`, wenn du einen **analogen Sensorwert in einen wiederverwendbaren booleschen `binary_sensor`** überführen willst, der `on`/`off` ausgibt, sobald er eine oder zwei Schwellen über-/unterschreitet. Typische Anwendungsfälle:

- **Ober-/Untergrenzen-Alarm** — über nur `upper` (z. B. Temperatur über 28 °C → `on`) oder nur `lower` (z. B. Luftfeuchte unter 30 %) einen Grenzwert als Boolean abbilden
- **Bereichs-/„in_range"-Überwachung** — mit `lower` **und** `upper` einen Komfort-/Sollbereich abbilden (innerhalb → `on`, außerhalb → `off`), z. B. Temperatur 20–24 °C
- **Flatter-freier Schaltpunkt** — über `hysteresis` einen verrauschten oder nahe der Schwelle pendelnden Wert (Leistung, Helligkeit) stabil schalten lassen
- **Mehrfach genutzter Schwellen-Boolean** — eine Schwellendefinition zentral als Entität anlegen, statt denselben `numeric_state`-Vergleich über mehrere Automationen, Bedingungen und Dashboard-Karten zu duplizieren
- **Drei-Wege-Lage per `position`** — das Attribut `position` (`above`/`below`/`in_range`/`unknown`) für eine Dreiwege-Verzweigung lesen, statt den Rohwert erneut gegen die Schwelle zu rechnen

Ein `threshold`-Helfer ist richtig, sobald ein analoger Wert als **wiederverwendbarer Über-/Unterschreitungs-Boolean** gebraucht wird. Für exakte Gleichheit/kategoriale Logik, Einmal-Verwendung ohne eigene Entität oder die Bewertung einer Änderungsrate greifen andere Bausteine (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Den `threshold`-Helfer als kanonischen Weg festschreiben, einen analogen Wert in einen wiederverwendbaren booleschen `binary_sensor` zu überführen
- Die drei Modi (`lower`, `upper`, beide) und ihre `on`/`off`-Semantik verbindlich machen
- Den bewussten Einsatz von `hysteresis` gegen Flattern erzwingen
- Die Nutzung des `position`-Attributs gegenüber erneuter Schwellenwert-Rechnerei in Templates priorisieren
- Klar abgrenzen, wann **kein** `threshold` das richtige Werkzeug ist (exakte Gleichheit, Einmal-Trigger ohne Wiederverwendung, Rohwerte ohne Glättung)

## Nicht-Ziele

- Die allgemeine Automations-Anatomie (Trigger/Bedingung/Aktion, Modi) — `ha-automation/automation`
- Rein berechnete oder kombinierte boolesche Logik (UND/ODER mehrerer Entitäten, exakte String-Gleichheit) — `ha-automation/template`
- Raten-/Ableitungswerte (z. B. °C pro Stunde als Zahl) — `ha-automation/derivative`; Trendrichtung als Boolean — `ha-automation/trend`
- Statistische Aggregate (Mittelwert, Min/Max über ein Fenster) als Glättungsquelle — `ha-automation/statistics`
- Die Namens-Dimension (`name`/`unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration

- **MUSS [MUST]** genau eine zu überwachende Quelle über `entity_id` angeben; laut Doku werden nur Sensoren unterstützt
- **MUSS [MUST]** mindestens einen Schwellen-Schlüssel setzen: `lower`, `upper` oder beide — ohne Schwelle hat der Sensor keine Vergleichsbasis
- **MUSS [MUST]** den Modus bewusst wählen: nur `lower` (Sensor unterhalb der Untergrenze → `on`), nur `upper` (Sensor oberhalb der Obergrenze → `on`) oder `lower` **und** `upper` (innerhalb des Bereichs → `on`, außerhalb → `off`; `position: in_range`)
- **SOLLTE [SHOULD]** `hysteresis` (Default `0.0`) explizit setzen, wenn der Quellwert verrauscht ist oder nahe der Schwelle pendeln kann; die Hysterese ist „die Distanz, die der beobachtete Wert von der Schwelle haben muss, bevor sich der Zustand ändert" und verhindert so Flattern
- **MUSS [MUST]** `lower < upper` halten, wenn beide gesetzt sind, damit ein gültiger Bereich entsteht
- **KANN [MAY]** `device_class` setzen, um Icon und `on`/`off`-Beschriftung im Frontend passend zu wählen (z. B. `cold`, `heat`, `problem`)
- **SOLLTE [SHOULD]** `name` und — bei YAML — `unique_id` vergeben, damit der Sensor stabil referenzierbar und im UI anpassbar ist; Mechanik in `ha/naming-conventions`

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den erzeugten `binary_sensor.<name>` als ganz normale boolesche Entität behandeln: als `state`-Trigger (`to: "on"`/`"off"`), als `state`-Bedingung und in Templates via `is_state(...)`
- **SOLLTE [SHOULD]** das Attribut `position` lesen (`above`, `below`, `in_range`, `unknown`) statt den Rohwert erneut gegen dieselbe Schwelle zu rechnen, wenn die Drei-Wege-Lage gebraucht wird
- **KANN [MAY]** die Attribute `lower`, `upper`, `hysteresis`, `type` und `sensor_value` zur Diagnose oder zur Anzeige im Dashboard auslesen
- **SOLLTE [SHOULD]** den `binary_sensor` bevorzugen, sobald derselbe Schwellen-Boolean an **mehreren** Stellen (mehrere Automationen, Bedingungen, Dashboard-Karten) gebraucht wird — eine Schwellendefinition statt n-facher `numeric_state`-Duplikate
- **MUSS [MUST]** `unavailable`/`unknown` der Quell-Entität berücksichtigen: der Schwellen-Sensor kann selbst `unknown`/`position: unknown` werden, wenn die Quelle keinen numerischen Wert liefert — nachgelagerte Automationen müssen diesen Fall abfangen

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `threshold` für **exakte Gleichheit** oder diskrete Zustände verwenden (z. B. „genau 21 °C", „Modus == eco", String-Vergleich) — `threshold` kennt nur „ober-/unterhalb einer Grenze"; für exakte/kategoriale Logik gehört ein **Template-Binary-Sensor** (`ha-automation/template`) her, der die Bedingung deklarativ ausdrückt
- **SOLLTE NICHT [SHOULD NOT]** einen `threshold`-Helfer anlegen, wenn der Schwellenwert **nur an einer einzigen Stelle** gebraucht wird und keine wiederverwendbare Entität entstehen soll — dann ist ein `numeric_state`-Trigger direkt in der Automation (`ha-automation/automation`) schlanker; der Helfer lohnt sich, sobald der Boolean **wiederverwendet** wird
- **SOLLTE NICHT [SHOULD NOT]** `threshold` auf ein **stark verrauschtes** Rohsignal ohne Glättung **und** ohne `hysteresis` anwenden — der Sensor flattert dann; entweder `hysteresis` setzen oder zuerst über `ha-automation/statistics` (z. B. gleitender Mittelwert) glätten und den geglätteten Wert als `entity_id` verwenden
- **MUSS NICHT [MUST NOT]** `threshold` benutzen, um eine **Änderungsrate** zu bewerten („steigt schneller als X") — das ist kein Schwellenvergleich eines Momentanwerts; für die Richtung gehört `ha-automation/trend`, für den Zahlenwert der Rate `ha-automation/derivative` her
- **SOLLTE NICHT [SHOULD NOT]** mehrere `threshold`-Sensoren stapeln, um eine UND/ODER-Verknüpfung mehrerer Bedingungen zu bauen, wenn ein einzelner **Template-Binary-Sensor** (`ha-automation/template`) die zusammengesetzte Logik klarer und mit einer Entität ausdrückt

## Akzeptanzkriterien

- [ ] Genau eine `entity_id` (Sensor) ist als Quelle gesetzt
- [ ] Mindestens eine Schwelle (`lower`, `upper` oder beide) ist gesetzt; bei beiden gilt `lower < upper`
- [ ] Der Modus (lower/upper/Bereich) und die daraus folgende `on`/`off`-Semantik sind bewusst gewählt
- [ ] `hysteresis` ist explizit gesetzt, wenn das Quellsignal verrauscht ist oder nahe der Schwelle pendeln kann
- [ ] Der `binary_sensor` wird als boolesche Entität in Triggern/Bedingungen/Templates verwendet; bei Drei-Wege-Lage wird `position` gelesen statt nachzurechnen
- [ ] `unavailable`/`unknown` der Quelle ist nachgelagert abgefangen
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `threshold` für exakte Gleichheit (→ Template), keinen Helfer ohne Wiederverwendung (→ `numeric_state`), kein ungeglättetes Rauschen ohne `hysteresis`, keine Ratenbewertung (→ `trend`/`derivative`)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Attribut-Stabilität**: Die exakten `position`-Werte (`above`/`below`/`in_range`/`unknown`) und die Attribut-Namen stammen aus der Core-Komponente, nicht aus der Integrations-Doku-Seite selbst. Soll die Spec sie als verbindlich führen oder nur als „beobachtbar, aber nicht dokumentiert garantiert" kennzeichnen, bis sie auf `/integrations/threshold/` erscheinen?
