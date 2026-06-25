# HA-Automation: Integration (Riemann-Summe) nutzen

Status: draft

## Kontext

Die `integration`-Integration erzeugt einen Sensor, der das **Zeit-Integral** eines anderen numerischen Sensors über eine Riemann-Summe schätzt — die klassische Anwendung ist Energie (`kWh`) aus Leistung (`W`). Sie ist die Umkehroperation zu `derivative`: Statt zu differenzieren, akkumuliert sie über die Zeit. Liefert die Quelle Leistung in Watt mit `device_class: power`, setzt der Sensor automatisch die `device_class: energy` und ergibt z. B. `sensor.energy_spent` „which will have your energy in kWh, as a `device_class` of `energy`". Die resultierende Einheit kombiniert Quell-Einheit, Präfix und Zeiteinheit (z. B. `W` + Präfix `k` + Zeit `h` = `kWh`).

Achtung Mehrdeutigkeit: Der **reale Domänen-Schlüssel ist `integration`** (nicht `integration-riemann`) — dieser Slug ist nur zur Vermeidung der Verwechslung mit der allgemeinen „Integration" (Add-on/Custom-Component) gewählt. In der UI heißt der Helper **Integral** (Settings → Devices & Services → Helpers → Create Helper → *Integral*). Im YAML steht er unter der `sensor:`-Plattform mit `platform: integration`.

Die reale HA-Einordnung ist **Helper / Utility** (Doku-Kategorien: *Helper, Sensor, Energy, Utility*) — **keine** Automation. Es gibt eine Integrations-Karte unter [`/integrations/integration/`](https://www.home-assistant.io/integrations/integration/). Diese Spec liegt im `ha-automation`-Korpus, weil der Sensor in Automationen, Dashboards und vor allem im **Energy-Dashboard** konsumiert wird; sie regelt die **Nutzung**, nicht die Entwicklung einer Custom Integration. Der Sensor „keeps its value across Home Assistant restarts".

Verifizierte Quelle: [`/integrations/integration/`](https://www.home-assistant.io/integrations/integration/) (Konfigurationsoptionen, `method`-Werte, `device_class`-Ableitung, `max_sub_interval`, Restart-Persistenz, Update-Trigger).

## Wann verwenden

Verwende `integration` (Integral/Riemann-Summe), wenn du eine **Momentan-Größe über die Zeit zu einer akkumulierten Größe** aufsummieren willst. Der Helfer ist die Umkehrung von `derivative`: Er integriert statt zu differenzieren und behält seinen Wert über Neustarts hinweg. Typische Anwendungsfälle:

- **Energie aus Leistung** — aus einer `device_class: power`-Quelle (Watt) automatisch `device_class: energy` (`kWh`) bilden, z. B. für einen Smart Plug ohne eigenen Energiezähler
- **Energy-Dashboard-Quelle** — den akkumulierten, neustart-festen Energie-Sensor als Verbrauchsquelle ins Energy-Dashboard einspeisen
- **Volumen aus Durchfluss** — aus einer Durchflussrate (z. B. l/min) das kumulierte Volumen (Liter) über die Zeit integrieren
- **Methode an die Quelle anpassen** — `trapezoidal` für häufig aktualisierende Quellen, `left`/`right` für rechteckige, lange stabile Treppenprofile (Genauigkeit über die `method` steuern)
- **Selten meldende Quelle akkumulieren** — über `max_sub_interval` zeitbasiert weiter integrieren, wenn die Quelle lange konstant bleibt und nur selten Updates sendet

Ein Integral-Sensor ist richtig, sobald das **Zeit-Integral** eines kontinuierlichen Messwerts gebraucht wird. Für Ereignis-Zähler, rücksetzbare Verbrauchszyklen oder die reine Ableitung greifen andere Helfer (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Konfigurationsoptionen des Integral-Helpers (`source`, `method`, `round`, `unit_prefix`, `unit_time`, `max_sub_interval`) als verbindliche Nutzungs-Konvention festschreiben
- Die **bewusste Wahl der `method`** (`left`/`right`/`trapezoidal`) gegen die Charakteristik der Quelle erzwingen, weil sie die Genauigkeit bestimmt
- Die automatische `device_class: energy`-Ableitung (Quelle `power` in Watt) und die Eignung fürs Energy-Dashboard verankern
- Den Nutzen von `max_sub_interval` für selten aktualisierende Quellen verankern (zeitbasierte Integration)
- Klar abgrenzen, wann **kein** Integral-Sensor das richtige Werkzeug ist (Event-Zähler, rücksetzbare Verbrauchszyklen, reine Ableitung)

## Nicht-Ziele

- Die Umkehrung — Ableitung/Änderungsrate (Leistung aus Energie) — gehört in `ha-automation/derivative`
- Rücksetzbare Verbrauchszyklen (täglich/monatlich, Tarifzyklen) — `ha-automation/utility-meter`
- Zählen diskreter Ereignisse — `ha-automation/counter`
- Die Energy-Dashboard-Konfiguration selbst (Geräte, Tarife, Netz/Erzeugung) — `ha/energy-dashboard`
- Die Namens-Dimension (`name`/`unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Konsum-Vertrag von Automationen/Triggern im Allgemeinen — `ha-automation/automation`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen `source` setzen, der die `entity_id` eines Sensors mit **numerischen** Messwerten liefert („The entity ID of the sensor providing numeric readings") — typisch eine Momentan-Größe (Leistung, Durchfluss)
- **MUSS [MUST]** die `method` (Default `trapezoidal`) bewusst gegen die Charakteristik der Quelle wählen:
  - `trapezoidal` — „the most accurate of the currently implemented methods, **if** the source updates often"
  - `left` — „**underestimates** the intrinsic source, but is extremely accurate at estimating rectangular functions which are very stable for long periods"
  - `right` — wie `left`, aber „**overestimates** the intrinsic source"
- **MUSS [MUST]** `unit_time` bewusst aus dem dokumentierten SI-Satz wählen (`s`, `min`, `h`, `d`; Default `h`) — sie bestimmt die Zeit-Achse der Integration und damit die Ergebnis-Einheit (Watt über `h` integriert ⇒ Wattstunden)
- **SOLLTE [SHOULD]** `unit_prefix` setzen, wo die Größenordnung es verlangt (dokumentierte Präfixe `k`, `M`, `G`, `T`; Default `None`) — z. B. `k`, damit aus `Wh` ein lesbares `kWh` wird
- **SOLLTE [SHOULD]** `round` (Default `3`) an der sinnvollen Anzeigegenauigkeit ausrichten
- **KANN [MAY]** `max_sub_interval` setzen, das „applies time-based integration if the source did not change for this duration" — angezeigt für Quellen, die lange konstant bleiben und selten Updates senden, damit der akkumulierte Wert nicht einfriert
- **MUSS [MUST]** akzeptieren, dass der Sensor „is updated whenever the source changes and, optionally, based on a predefined time interval" (via `max_sub_interval`) — die Update-Frequenz folgt der Quelle, nicht einem festen Takt
- **MUSS [MUST]** den `name`/`unique_id` gemäß `ha/naming-conventions` vergeben (snake_case-Id, englischer Anzeigename ≤50 Zeichen) — Mechanik dort, hier nicht wiederholt

### Nutzung in Automationen, Templates & Energy-Dashboard

- **SOLLTE [SHOULD]** den Integral-Sensor, wenn die Quelle `device_class: power` (Watt) trägt, fürs **Energy-Dashboard** nutzen — er erhält dann automatisch `device_class: energy` und liefert z. B. Energie in `kWh`; der akkumulierte Wert übersteht „across Home Assistant restarts", was Energie-Tracking überhaupt erst tragfähig macht
- **KANN [MAY]** den Sensor in `numeric_state`-Triggern/-Bedingungen (z. B. „heute verbrauchte Energie überschreitet X"), in Templates über `states('sensor.…')` und auf Dashboards (Verbrauchs-/Verlaufsgraph) verwenden
- **SOLLTE [SHOULD]** beim Lesen in Templates `unavailable`/`unknown` abfangen, bevor numerisch verglichen wird — ein frisch angelegter Integral-Sensor liefert kurzzeitig keinen Zahlenwert
- **SOLLTE NICHT [SHOULD NOT]** den monoton steigenden Integral-Sensor direkt als „Tages-/Monatsverbrauch" anzeigen, ohne einen rücksetzbaren Zyklus darüberzulegen (siehe Abgrenzung) — der Roh-Integral akkumuliert ohne Reset weiter

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** einen Integral-Sensor als **Ereignis-Zähler** verwenden (z. B. „wie oft wurde die Tür geöffnet") — er integriert einen kontinuierlichen Messwert über die Zeit, zählt aber keine diskreten Ereignisse; dafür ist ein **`counter`** (`ha-automation/counter`) das richtige Konstrukt
- **MUSS NICHT [MUST NOT]** einen Integral-Sensor für **rücksetzbare Verbrauchszyklen** (Tages-, Monats-, Tarif-Zyklus) verwenden — der Integral akkumuliert monoton und kennt keinen periodischen Reset; dafür ist der **`utility_meter`** (`ha-automation/utility-meter`) zuständig, der den Zähler zyklisch zurücksetzt und Tarif-Perioden kennt (üblicherweise speist man den Integral-Sensor *in* einen Utility-Meter)
- **MUSS NICHT [MUST NOT]** einen Integral-Sensor verwenden, wo eine **Ableitung/Änderungsrate** gebraucht wird (Leistung `W` aus Energie `Wh`) — das ist die Umkehroperation; dafür ist die **`derivative`**-Integration (`ha-automation/derivative`) zuständig
- **SOLLTE NICHT [SHOULD NOT]** die `method` blind auf dem Default `trapezoidal` belassen, wenn die Quelle ein **Treppen-/Halteprofil** mit seltenen Updates hat (z. B. ein Gerät, das nur bei Laständerung meldet) — hier sind `left`/`right` für rechteckige, lange stabile Funktionen genauer; die Default-Trapez-Regel ist nur „accurate … if the source updates often"
- **SOLLTE NICHT [SHOULD NOT]** `max_sub_interval` weglassen, wenn die Quelle lange konstant bleibt und selten sendet und dennoch fortlaufend akkumuliert werden soll — ohne `max_sub_interval` bewegt sich der Integral zwischen Quell-Updates nicht weiter

## Akzeptanzkriterien

- [ ] `source` zeigt auf einen numerischen (typisch momentanen) Sensor
- [ ] `method` ist bewusst gegen die Quell-Charakteristik gewählt (häufige Updates → `trapezoidal`; rechteckig/selten → `left`/`right`)
- [ ] `unit_time`/`unit_prefix`/`round` sind bewusst gesetzt; die Ergebnis-Einheit ist lesbar (z. B. `kWh`)
- [ ] `max_sub_interval` ist gesetzt, wenn die Quelle lange konstant ist und selten meldet
- [ ] Bei `power`-Quelle wird die automatische `device_class: energy`-Ableitung fürs Energy-Dashboard genutzt; Restart-Persistenz ist eingeplant
- [ ] Trigger/Templates fangen `unavailable`/`unknown` ab
- [ ] Kein Integral-Sensor wird als Ereignis-Zähler (statt `counter`), als rücksetzbarer Verbrauchszyklus (statt `utility_meter`) oder als Ableitung (statt `derivative`) missbraucht
- [ ] `name`/`unique_id` folgen `ha/naming-conventions` (Mechanik nicht wiederholt)

## Offene Fragen

- **`state_class` des Ergebnisses**: Die Doku nennt nicht explizit, ob der Integral-Sensor `state_class: total` oder `total_increasing` trägt (relevant für Langzeit-Statistik/Energy-Dashboard). Soll die Spec hierfür auf eine querschnittliche Sensor-Spec verweisen, statt einen Wert zu behaupten?
