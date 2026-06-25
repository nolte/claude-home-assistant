# HA-Automation: Derivative nutzen

Status: draft

## Kontext

Die `derivative`-Integration erzeugt einen Sensor, der die **Ableitung** (Änderungsrate) eines anderen numerischen Sensors schätzt — die Doku formuliert: „estimates the derivative of the values provided by another sensor (the **source sensor**)". Typische Anwendungen sind Leistung aus Energie, Geschwindigkeit aus Position oder allgemein „wie schnell ändert sich dieser Messwert pro Zeiteinheit". Der erzeugte Sensor trägt eine Einheit der Form `x/y`, wobei `x` die Einheit des Quell-Sensors und `y` der Wert von `unit_time` ist.

Die reale HA-Einordnung ist **Helper / Utility** (Doku-Kategorien: *Helper, Sensor, Utility, Energy*) — **keine** Automation. Es gibt eine Integrations-Karte unter [`/integrations/derivative/`](https://www.home-assistant.io/integrations/derivative/). Der Helper wird entweder über die UI angelegt (Settings → Devices & Services → Helpers → Create Helper → *Derivative*) oder als YAML unter der `sensor:`-Plattform mit `platform: derivative`. Diese Spec liegt bewusst im `ha-automation`-Korpus, weil der Wert eines Derivative-Sensors fast immer in Automationen, Templates und Dashboards konsumiert wird; sie regelt die **Nutzung**, nicht die Entwicklung einer Custom Integration.

Verifizierte Quelle: [`/integrations/derivative/`](https://www.home-assistant.io/integrations/derivative/) (Konfigurationsoptionen, `time_window`-Verhalten, `total_increasing`-Hinweis für nicht-negative Ableitungen).

## Wann verwenden

Verwende `derivative`, wenn du aus einem numerischen Sensor dessen **Änderungsrate pro Zeiteinheit** als eigenen Sensor brauchst. Der Helfer bildet die Ableitung `Quell-Einheit/unit_time` und ist das richtige Werkzeug, sobald „wie schnell ändert sich dieser Messwert" die Frage ist. Typische Anwendungsfälle:

- **Leistung aus Energie** — aus einem Energiezähler (`Wh`/`kWh`) mit `unit_time: h` die Momentanleistung (`Wh/h ≈ W`) ableiten
- **Geschwindigkeit aus Position/Strecke** — aus einem Wegstrecken- oder Positions-Sensor die Geschwindigkeit (Strecke pro Zeit) gewinnen
- **Verbrauchs-/Durchflussrate** — aus einem nicht-negativen Zähler (Router-Bandbreite, Regenmesser) die Rate ableiten, mit `state_class: total_increasing` für korrektes Reset-Handling
- **Temperatur-/Füllstands-Gradient** — die Anstiegs-/Abfallrate (z. B. °C pro Stunde, Tankfüllung pro Minute) als Zahlenwert für Trigger und Anzeige berechnen
- **Geglättete Rate für Trigger** — über `time_window` > 0 (zeitgewichteter SMA) eine entprellte Änderungsrate für `numeric_state`-Trigger erzeugen, statt auf der rohen Punkt-zu-Punkt-Ableitung zu flattern

Ein Derivative-Sensor ist richtig, sobald die **zeitliche Ableitung** eines kontinuierlichen Werts gebraucht wird. Für das Zeit-Integral (Energie aus Leistung), reine Glättung, statistische Kennzahlen oder beliebige berechnete Werte greifen andere Helfer (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Konfigurationsoptionen des Derivative-Helpers (`source`, `unit_time`, `unit_prefix`, `round`, `time_window`, `max_sub_interval`) als verbindliche Nutzungs-Konvention festschreiben
- Die bewusste Wahl von `unit_time`/`unit_prefix` so erzwingen, dass die resultierende Einheit physikalisch sinnvoll und sprechend ist
- Die korrekte Nutzung von `time_window` als zeitgewichteten gleitenden Mittelwert (Simple Moving Average) für diskrete/verrauschte Quellen verankern
- Den `total_increasing`-Vertrag für nicht-negative Ableitungen (Zähler, Regenmesser) als prüfbare Regel fixieren
- Klar abgrenzen, wann **kein** Derivative-Sensor das richtige Werkzeug ist (Glättung, generische Templates, Integration statt Ableitung)

## Nicht-Ziele

- Die Umkehrung — Zeit-Integral (Energie aus Leistung) — gehört in `ha-automation/integration-riemann`
- Allgemeine Glättung/Filterung verrauschter Signale als Selbstzweck — `ha-automation/filter`
- Statistische Aggregation über ein Zeitfenster (min/max/mean) — `ha-automation/statistics`
- Beliebige berechnete Werte ohne Bezug zur Änderungsrate — `ha-automation/template`
- Die Namens-Dimension (`name`/`unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Konsum-Vertrag von Automationen/Triggern im Allgemeinen — `ha-automation/automation`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen `source` setzen, der die `entity_id` eines Sensors mit **numerischen** Messwerten liefert („The entity ID of the sensor providing numeric readings")
- **MUSS [MUST]** `unit_time` bewusst aus dem dokumentierten SI-Satz wählen (`s`, `min`, `h`, `d`; Default `h`) — die resultierende Einheit ist `Quell-Einheit/unit_time`, daher bestimmt diese Wahl die physikalische Bedeutung (z. B. Energie `Wh` → `unit_time: h` ergibt Leistung `Wh/h ≈ W`)
- **SOLLTE [SHOULD]** `unit_prefix` nur setzen, wenn der Zahlenbereich es erfordert (dokumentierte Präfixe `n`, `µ`, `m`, `k`, `M`, `G`, `T`; Default `None`), und die Wahl an einer sinnvollen Größenordnung des Ergebnisses ausrichten
- **KANN [MAY]** `unit` explizit setzen, um die automatisch generierte Einheit zu überschreiben — nur wenn die Auto-Einheit physikalisch irreführend wäre
- **SOLLTE [SHOULD]** `round` (Default `3`) an der sinnvollen Anzeigegenauigkeit ausrichten, damit der Sensor keine Schein-Präzision suggeriert
- **MUSS [MUST]** `time_window` (Default `0`) **bewusst** wählen: `0` bildet die rohe Punkt-zu-Punkt-Ableitung, ein Wert > 0 mittelt über das Fenster per „Simple Moving Average algorithm weighted by time" — für diskrete oder kurzzeitig verrauschte Quellen ist ein Fenster > 0 angezeigt
- **KANN [MAY]** `max_sub_interval` setzen, um die Ableitung auch dann neu zu berechnen, wenn der `source` über diese Dauer kein Update liefert (Default `0` = nur bei Quell-Update)
- **MUSS [MUST]** bei nicht-negativen Ableitungen (Zähler, die nach Stromausfall auf 0 zurückspringen — Router-Bandbreite, Regenmesser) sicherstellen, dass der `source` die `state_class: total_increasing` trägt, „as this is necessary for the integration to handle resets correctly without registering significant changes in the derivative sensor"
- **MUSS [MUST]** den `name`/`unique_id` gemäß `ha/naming-conventions` vergeben (snake_case-Id, englischer Anzeigename ≤50 Zeichen) — Mechanik dort, hier nicht wiederholt

### Nutzung in Automationen & Templates

- **KANN [MAY]** den Derivative-Sensor wie jeden Sensor in `numeric_state`-Triggern/-Bedingungen verwenden (z. B. „Leistung überschreitet 2000 W"), in Templates über `states('sensor.…')` lesen und auf Dashboards (z. B. als Verlaufs-/History-Graph der Änderungsrate) darstellen
- **SOLLTE [SHOULD]** beim Lesen in Templates `unavailable`/`unknown` abfangen, bevor der Wert numerisch verglichen wird — ein frisch angelegter oder neu gestarteter Derivative-Sensor liefert kurzzeitig keinen Zahlenwert
- **SOLLTE [SHOULD]** in `numeric_state`-Triggern auf den geglätteten Sensor (`time_window` > 0) triggern statt auf die rohe Ableitung, wenn der Quellwert verrauscht ist, um Flattern (häufiges Feuern um eine Schwelle) zu vermeiden
- **SOLLTE NICHT [SHOULD NOT]** den Roh-Sensor (`time_window: 0`) ohne weitere Entprellung als alleinigen Trigger für teure/sichtbare Aktionen nutzen, wenn die Quelle sprunghaft ist

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** einen Derivative-Sensor als generischen **Glättungs-/Entrausch-Filter** zweckentfremden — er berechnet eine Ableitung, nicht einen gefilterten Originalwert; für reine Rauschunterdrückung eines Signals ist die **`filter`**-Integration (`ha-automation/filter`) das richtige Werkzeug, weil sie den Originalwert (ggf. mit Low-Pass/Outlier-Filter) erhält, statt ihn abzuleiten
- **MUSS NICHT [MUST NOT]** einen Derivative-Sensor verwenden, wo das **Zeit-Integral** gebraucht wird (Energie `kWh` aus Leistung `W`) — das ist die Umkehroperation; dafür ist die **`integration`**-Integration (Riemann-Summe, `ha-automation/integration-riemann`) zuständig, weil sie über die Zeit akkumuliert statt zu differenzieren
- **SOLLTE NICHT [SHOULD NOT]** einen Derivative-Sensor für einen **beliebigen berechneten Wert** ohne Bezug zur Änderungsrate einsetzen (z. B. Summe/Differenz zweier Sensoren) — dafür ist ein **Template-Sensor** (`ha-automation/template`) das passende, ausdrucksstärkere Konstrukt
- **SOLLTE NICHT [SHOULD NOT]** `time_window` blind groß wählen, um „glattere Zahlen" zu erhalten — ein zu großes Fenster verschleppt echte, schnelle Änderungen (das gemittelte Ergebnis hinkt der Realität hinterher); das Fenster ist an der erwarteten Dynamik des Signals auszurichten
- **SOLLTE NICHT [SHOULD NOT]** statistische Kennzahlen über ein Fenster (Mittelwert, Min/Max, Trend) aus einem Derivative-Sensor ableiten wollen — dafür ist die **`statistics`**-Integration (`ha-automation/statistics`) gedacht; der Derivative-Sensor liefert ausschließlich die Änderungsrate

## Akzeptanzkriterien

- [ ] `source` zeigt auf einen numerischen Sensor; bei nicht-negativen Ableitungen trägt die Quelle `state_class: total_increasing`
- [ ] `unit_time` ist bewusst gewählt und die resultierende Einheit (`Quell-Einheit/unit_time`) ist physikalisch sinnvoll
- [ ] `unit_prefix`/`unit`/`round` sind nur gesetzt, wenn sie die Lesbarkeit oder Korrektheit verbessern
- [ ] `time_window` ist bewusst gesetzt (0 = roh; > 0 = zeitgewichteter SMA für diskrete/verrauschte Quellen) und nicht überdimensioniert
- [ ] Trigger/Templates fangen `unavailable`/`unknown` ab und triggern bei verrauschter Quelle auf den geglätteten Sensor
- [ ] Kein Derivative-Sensor wird als reiner Glättungsfilter (statt `filter`), als Zeit-Integral (statt `integration`), als generischer Template-Sensor oder als Statistik-Quelle (statt `statistics`) missbraucht
- [ ] `name`/`unique_id` folgen `ha/naming-conventions` (Mechanik nicht wiederholt)

## Offene Fragen

- **`state_class` des Ergebnisses**: Die Doku spezifiziert die `state_class` des Derivative-Sensors nicht explizit und nennt keine Energy-Dashboard-Eignung. Soll die Spec hier auf eine querschnittliche Sensor-Spec verweisen, statt einen Wert zu behaupten?
