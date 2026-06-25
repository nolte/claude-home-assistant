# HA-Automation: Utility Meter nutzen

Status: draft

## Kontext

Die `utility_meter`-Integration ist ein **Verbrauchszähler mit Abrechnungszyklen**: Sie nimmt einen kontinuierlich steigenden Gesamtzähler (z. B. einen Energie-, Wasser- oder Gas-Sensor) als `source` und leitet daraus einen Sensor ab, der den Verbrauch **innerhalb eines Zyklus** ausweist und am Zyklusende automatisch auf null zurückgesetzt wird. So entstehen aus einem stetig wachsenden Zählerstand abrechenbare Größen wie „Energieverbrauch dieser Woche" oder „Wasserverbrauch diesen Monat".

`utility_meter` ist **keine** Automation-Domäne. Ihre reale HA-Kategorie ist **Helper/Utility** (Integrations-Karte unter `/integrations/utility_meter/`); sie wird per YAML unter dem Top-Level-Schlüssel `utility_meter:` oder als UI-Helfer angelegt. Diese Spec überführt die offizielle Nutzungs-Doku in eine verbindliche Konvention dafür, wie das Plugin Utility-Meter-Helfer konfiguriert und in Automationen referenziert.

Optional unterstützt die Integration **Tarife** (`tariffs`): Statt eines einzelnen Sensors entstehen dann pro Tarif ein eigener Sensor und zusätzlich eine **Select-Entität**, über die der aktuell aktive Tarif umgeschaltet wird — nur der aktive Tarif zählt weiter, die übrigen pausieren.

Verifizierte Quelle: `/integrations/utility_meter/` (Konfigurationsvariablen `source`, `name`, `unique_id`, `cycle`, `offset`, `cron`, `delta_values`, `net_consumption`, `tariffs`, `periodically_resetting`, `always_available`; Aktionen `utility_meter.calibrate`, `utility_meter.reset`; die Tarif-Umschaltung per `select.select_option` auf die generierte Select-Entität).

## Wann verwenden

Verwende `utility_meter`, wenn du aus einem **kontinuierlich steigenden Gesamtzähler** einen Verbrauch je Abrechnungszyklus ableiten willst, der am Zyklusende automatisch auf null zurückspringt. Der Helfer schneidet einen stetig wachsenden Zählerstand in abrechenbare Perioden. Typische Anwendungsfälle:

- **Tages-/Monats-/Jahresverbrauch** — aus einem Gesamt-Energie-/Wasser-/Gas-Zähler den Verbrauch je `cycle` (`daily`, `monthly`, `yearly` …) als eigenen, am Periodenende rücksetzbaren Sensor bilden
- **Tarif-/Zeitzonen-Abrechnung** — über `tariffs` pro Tarif (z. B. Hoch-/Niedertarif) einen Sensor plus Select-Entität erzeugen und den aktiven Tarif zeitbasiert per `select.select_option` umschalten
- **Einspeisung/Netto-Zähler** — mit `net_consumption: true` einen Zähler führen, der sowohl positiv (Bezug) als auch negativ (Einspeisung) laufen darf
- **Versetzte Abrechnungsperioden** — über `offset` (oder `cron`) den Reset nicht am Periodenanfang, sondern z. B. zum Abrechnungsstichtag des Versorgers ausrichten
- **Quelle mit Differenzwerten oder Selbst-Reset** — über `delta_values`/`periodically_resetting` Quellen korrekt verarbeiten, die Differenzen statt Absolutwerte liefern oder selbst auf 0 zurückspringen (z. B. Smart Plug beim Boot)
- **Energy-Dashboard-Quelle** — den zyklisch zurückgesetzten Verbrauchssensor als Verbrauchsquelle ins Energy-Dashboard einspeisen

Ein Utility Meter ist richtig, sobald ein steigender Gesamtzähler in **rücksetzbare Verbrauchszyklen** geschnitten werden soll. Zum Bilden des Roh-Integrals aus einer Leistungsgröße, für frei inkrementierbare Zähler oder statistische Kennzahlen greifen andere Bausteine (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Pflicht- und Optionsschlüssel eines Utility-Meter-Helfers (`source`, `cycle`, `offset`, `tariffs`, `net_consumption`, `delta_values`, `periodically_resetting`) verbindlich festschreiben
- Die korrekte Beschaffenheit der `source` (kontinuierlich steigender Gesamtzähler) als Vorbedingung erzwingen
- Die Tarif-Mechanik (Tarif-Sensoren + Select-Entität, Umschaltung per `select.select_option`) als dokumentierten Weg festlegen
- Den bewussten Einsatz von `delta_values`/`periodically_resetting`/`net_consumption` gegen ihre jeweilige Messsituation absichern
- Klar abgrenzen, wann **kein** Utility Meter das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Erzeugung des Roh-Integrals aus einer Leistungsgröße (W → kWh) — dafür ist die Riemann-Integration zuständig (`ha-automation/integration-riemann`)
- Die Automation-Engine selbst (Trigger/Bedingung/Aktion, Modi) — `ha-automation/automation`
- Die Energy-Dashboard-Konfiguration im UI (Einrichtung der Verbrauchsquellen) — außerhalb dieser Spec; hier nur die Eignung des Sensors als Quelle
- Die Namens-Dimension (Schlüssel/`name`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Cron-Detailsyntax für `cron:` — die crontab-Erweiterung der HA-Doku, hier nur als Alternative zu `cycle`/`offset` benannt

## Anforderungen

### Konfiguration

- **MUSS [MUST]** eine `source` angeben, deren State ein **kontinuierlich steigender Gesamtzähler** ist (Energie, Wasser, Gas, Wärme); die Doku bezeichnet die Quelle als „the entity ID of the sensor providing utility readings"
- **MUSS [MUST]** den Zurücksetz-Zyklus über `cycle` aus dem dokumentierten Wertebereich wählen: `quarter-hourly`, `hourly`, `daily`, `weekly`, `monthly`, `bimonthly`, `quarterly`, `yearly` (`bimonthly` setzt einmal in zwei Monaten zurück)
- **MUSS [MUST]** für jeden generierten Helfer einen stabilen snake_case-Schlüssel und einen englischen `name` ≤50 Zeichen vergeben sowie für die UI-Anpassbarkeit eine `unique_id` setzen (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** `offset` nur setzen, wenn der Zyklus nicht am Periodenanfang beginnen soll (die Doku: „Cycle reset occur at the beginning of the period"); Formate `'HH:MM:SS'`, `'HH:MM'` oder eine Zeitraum-Dictionary
- **KANN [MAY]** statt `cycle`/`offset` ein `cron` verwenden, wenn ein erweiterter Zurücksetz-Zeitplan nötig ist — `cron` ist laut Doku „mutually exclusive of `cycle` and `offset`" und darf nicht zusammen mit ihnen gesetzt werden
- **MUSS [MUST]** `delta_values: true` setzen, **genau dann wenn** die Quelle Differenzwerte seit der letzten Messung liefert statt Absolutwerte („Set this to True if the source values are delta values since the last reading instead of absolute values") — falsche Wahl verfälscht jeden Zählerstand
- **MUSS [MUST]** `periodically_resetting` bewusst belassen oder abschalten: Default `true` erwartet eine Quelle, die selbst auf 0 zurückspringen kann (z. B. ein Smart Plug, der beim Boot resettet); für eine Quelle, die das nie tut, ist dies zu prüfen, da es die Verbrauchsberechnung über Quell-Resets hinweg steuert
- **KANN [MAY]** `net_consumption: true` setzen, wenn die Quelle ein Netto-Zähler ist und der Zähler sowohl positiv als auch negativ laufen darf („This will allow your counter to go both positive and negative") — etwa bei Einspeisung
- **KANN [MAY]** `always_available: true` setzen, damit der Sensor mit dem letzten Wert verfügbar bleibt, auch wenn die Quelle `unavailable`/`unknown` wird
- **KANN [MAY]** eine `tariffs`-Liste angeben; dann erzeugt die Integration **pro Tarif einen Sensor** und zusätzlich eine **Select-Entität**, die den aktuellen Tarif führt

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den vom Helfer erzeugten Verbrauchssensor (`sensor.<key>` bzw. `sensor.<key>_<tariff>`) als Lesegröße behandeln; den Zählerstand nicht aus Automationen heraus „nachpflegen", sondern aus der `source` ableiten lassen
- **MUSS [MUST]** den Tarifwechsel über `select.select_option` auf die generierte Select-Entität (z. B. `select.daily_energy`) ausführen — das ist der von der Doku gezeigte Weg, etwa per zeitbasierter Automation (`trigger: time` … `action: select.select_option`)
- **SOLLTE NICHT [SHOULD NOT]** sich auf undokumentierte Tarif-Aktionsnamen verlassen: die Integrations-Karte führt als Aktionen nur `utility_meter.calibrate` (setzt den Zähler auf einen Wert) und `utility_meter.reset` (setzt alle Zähler auf null) — der dokumentierte Tarifwechsel läuft über die Select-Entität
- **KANN [MAY]** `utility_meter.calibrate` nutzen, um nach einem Zählertausch oder Datenausfall einen bekannten Stand zu setzen, und `utility_meter.reset`, um einen Zyklus außerplanmäßig zu beginnen
- **KANN [MAY]** den Verbrauchssensor als Quelle des **Energy-Dashboards** verwenden; Eignung dafür ergibt sich aus der monotonen, zyklisch zurückgesetzten Natur des Sensors

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `utility_meter` verwenden, um aus einer **Leistungsgröße** (z. B. `W`) eine Energiegröße (`kWh`) zu bilden — `utility_meter` summiert kein Integral, sondern setzt einen bereits steigenden Gesamtzähler in Zyklen; das Roh-Integral liefert die Riemann-Integration (`ha-automation/integration-riemann`), deren Ausgabe dann die `source` sein kann
- **MUSS NICHT [MUST NOT]** `utility_meter` als generischen, manuell hoch-/runterzählenden Zähler einsetzen — dafür ist `counter` (`ha-automation/counter`) gedacht; `utility_meter` ist an eine externe, kontinuierlich steigende Messquelle gebunden und nicht frei inkrementierbar
- **SOLLTE NICHT [SHOULD NOT]** eine **nicht monoton steigende** Quelle (ein schwankender Momentanwert wie Temperatur, Leistung, Füllstand) als `source` anhängen — der Verbrauch ergibt sich aus dem Zuwachs eines Totals; eine schwankende Quelle erzeugt sinnlose oder negative Verbräuche. Für statistische Kennzahlen über solche Werte ist `ha-automation/statistics` zuständig
- **SOLLTE NICHT [SHOULD NOT]** `delta_values` und `periodically_resetting` „auf Verdacht" setzen — beide kodieren eine konkrete Annahme über die Quelle (Differenz- vs. Absolutwerte; Quelle springt selbst auf 0). Falsch gesetzt verfälschen sie den Verbrauch über jeden Reset hinweg; die Wahl muss zur realen Quelle passen
- **SOLLTE NICHT [SHOULD NOT]** mehrere fast gleiche Utility-Meter-Helfer für unterschiedliche Zyklen derselben Quelle von Hand vervielfältigen, wenn ein Tarif- oder Zyklus-Set dasselbe deklarativ ausdrückt — mehrere `cycle`-Helfer auf derselben `source` sind legitim, aber Logik gehört nicht in begleitende Automationen, die den Stand manuell setzen

## Akzeptanzkriterien

- [ ] Jeder Helfer hat eine `source`, die ein kontinuierlich steigender Gesamtzähler ist (kein Momentan-/Schwankungswert)
- [ ] `cycle` stammt aus dem dokumentierten Wertebereich; `cron` ist nicht zusammen mit `cycle`/`offset` gesetzt
- [ ] Jeder Helfer trägt einen stabilen snake_case-Schlüssel, einen englischen `name` ≤50 Zeichen und eine `unique_id`
- [ ] `delta_values`, `periodically_resetting` und `net_consumption` sind nur gesetzt, wenn die reale Quelle es erfordert, nicht pauschal
- [ ] Tarif-Helfer schalten den Tarif ausschließlich per `select.select_option` auf die generierte Select-Entität um
- [ ] Es werden nur die dokumentierten Aktionen `utility_meter.calibrate`/`utility_meter.reset` aufgerufen
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein Utility Meter, wo Riemann-Integration, `counter` oder `statistics` das richtige Werkzeug ist
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Tarif-Umschalt-Aktionen**: Frühere HA-Versionen exponierten `utility_meter.next_tariff` und `utility_meter.select_tariff`. Die aktuell verifizierte Integrations-Karte (`/integrations/utility_meter/`) zeigt die Tarif-Umschaltung ausschließlich über `select.select_option` und listet unter Aktionen nur `calibrate`/`reset`. Diese Spec hält sich an die dokumentierte Form. Soll eine Anmerkung zu den Alt-Aktionen aufgenommen werden, sobald deren Status (entfernt vs. nur undokumentiert) gegen die Quelle bestätigt ist?
