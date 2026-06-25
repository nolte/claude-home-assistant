# HA-Automation: Counter nutzen

Status: draft

## Kontext

Die `counter`-Integration ist ein Helfer, der einen **ganzzahligen Zähler** als Entität bereitstellt. Sein Zustand ist eine ganze Zahl, die per Aktion erhöht, verringert, zurückgesetzt oder direkt gesetzt wird — das macht ihn zum natürlichen Werkzeug für das Mitzählen **diskreter Ereignisse** (Türöffnungen, Tassen Kaffee, ausgelöste Alarme) über die Zeit.

Die reale HA-Einordnung ist **Helfer** (Helper) — ein per UI oder YAML angelegtes Hilfsobjekt, kein verbindbares Gerät und keine Messquelle. Der Zustand ist der aktuelle Zählerwert; die Attribute (`initial`, `step`, `minimum`, `maximum`, `editable`) beschreiben das Zählverhalten. Gesteuert wird er über `counter.*`-Aktionen; er feuert eigene Events, auf die Automationen triggern können.

Verifizierte Quelle: [`/integrations/counter/`](https://www.home-assistant.io/integrations/counter/) (Konfigurationsvariablen, Aktionen, Trigger, Bedingung, Attribute). Das Trigger/Bedingung/Aktion-Grundmodell stammt aus `ha-automation/automation`.

## Wann verwenden

Verwende `counter` für das **Mitzählen diskreter Ereignisse als ganzzahligen Zustand**, der per Aktion erhöht, verringert, zurückgesetzt oder gesetzt wird. Ein Counter lohnt sich, sobald eine Ereignis-Anzahl persistent gehalten und beobachtet werden soll. Typische Anwendungsfälle:

- **Ereignis-Zählung** — Türöffnungen, Tassen Kaffee oder ausgelöste Alarme über die Zeit hochzählen (`counter.increment` bei jedem Vorkommen)
- **Schwellwert-Aktion** — bei Erreichen einer Obergrenze handeln, indem auf `counter.maximum_reached` (bzw. `counter.minimum_reached`) getriggert wird
- **Periodisch zurückgesetzter Tageszähler** — einen Wert je Tag/Schicht mitführen und per `counter.reset` auf `initial` zurücksetzen
- **Direktes Setzen eines Standes** — einen bekannten Stand per `counter.set_value` auf einen konkreten Wert bringen (z. B. aus einer externen Quelle)
- **Begrenzter Schrittzähler** — mit `minimum`/`maximum` und `step` einen beschränkten, schrittweise veränderten Wert führen und per `counter.is_value` als Gate prüfen

Ein Counter ist das richtige Werkzeug, sobald eine **diskrete, ganzzahlige Anzahl** gezählt und gehalten werden soll. Geht es um gemessene/kontinuierliche Werte, Arithmetik auf Sensordaten, verstreichende Zeit oder Bruchteile, ist ein anderer Baustein richtig (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines Counters (`name`, `initial`, `step`, `minimum`, `maximum`, `restore`, `icon`) verbindlich festschreiben
- Den Steuerungsvertrag über die Aktionen `counter.increment`/`decrement`/`reset`/`set_value` fixieren
- Den Lese-Vertrag über den ganzzahligen Zustand und die Attribute (`step`, `minimum`, `maximum`, `initial`) festschreiben
- Die Event-Trigger (`counter.incremented`, `counter.decremented`, `counter.reset`, `counter.maximum_reached`, `counter.minimum_reached`) als bevorzugten Reaktionsweg verankern
- Klar abgrenzen, wann ein Counter **nicht** das richtige Werkzeug ist (gegen Sensor, gegen Template/Utility-Meter)

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Grundmodell von Automationen — `ha-automation/automation`
- Die Namens-Dimension (`name`/Entity-ID, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Mess-/Verbrauchszählung aus Sensordaten — `ha-automation/utility-meter`
- Abgeleitete/berechnete Werte aus Sensoren — `ha-automation/template`
- Verstreichende Zeit / Countdowns — `ha-automation/timer`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen YAML-Counter unter der Domäne `counter:` mit einem snake_case-Schlüssel (der Alias, der die Entity-ID bestimmt) anlegen; Mechanik der ID/`name`-Vergabe: `ha/naming-conventions`
- **SOLLTE [SHOULD]** `initial` (Startwert, Default `0`, 0 oder positive Ganzzahl) und `step` (Schrittweite, Default `1`) explizit setzen, wenn sie von den Defaults abweichen
- **KANN [MAY]** `minimum` und/oder `maximum` setzen, um den Wertebereich zu begrenzen — beim Erreichen feuern `counter.minimum_reached`/`counter.maximum_reached`
- **SOLLTE [SHOULD]** `restore` bewusst behandeln: Default ist `true` (letzter Wert wird über einen Neustart hinweg wiederhergestellt); auf `false` setzen, wenn der Counter bei jedem Start auf `initial` beginnen soll
- **SOLLTE [SHOULD]** einen `name` (Friendly Name) und optional `icon` für die UI vergeben; der `name` bleibt englisch und ≤50 Zeichen (`ha/naming-conventions`)

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Counter über die dokumentierten Aktionen steuern: `counter.increment` (um `step` erhöhen), `counter.decrement` (um `step` verringern), `counter.reset` (auf `initial` zurücksetzen), `counter.set_value` (auf einen konkreten `value` setzen)
- **SOLLTE [SHOULD]** auf die Event-Trigger `counter.incremented`/`counter.decremented`/`counter.reset`/`counter.maximum_reached`/`counter.minimum_reached` triggern, statt den Zustand zu pollen
- **KANN [MAY]** den Zähler-Zustand und die Attribute `step`/`minimum`/`maximum`/`initial` in Templates und Bedingungen lesen; die Bedingung `counter.is_value` testet den Wert als Gate
- **MUSS [MUST]** den Zustand bei numerischer Auswertung als Zahl behandeln (z. B. via `numeric_state`-Trigger oder `int`-Filter im Template), nicht als rohen String vergleichen

### Abgrenzung: Wann NICHT verwenden

- **SOLLTE NICHT [SHOULD NOT]** einen Counter für **gemessene oder kontinuierliche Werte** (Temperatur, Leistung, Füllstand) verwenden — ein Counter hält nur ganzzahlige, manuell oder per Automation veränderte Schritte und hat keine Messquelle; für gemessene/abgeleitete Werte ist ein **Sensor** (`ha-automation/template` für abgeleitete, eine native Sensor-Entität für gemessene) das richtige Konstrukt
- **SOLLTE NICHT [SHOULD NOT]** Counter-Aktionen für **Arithmetik auf Sensordaten** missbrauchen (z. B. Summen/Differenzen aus Sensorwerten in einen Counter schreiben) — das verliert die Quelle und ist fehleranfällig; stattdessen einen **Template-Sensor** (`ha-automation/template`) oder, bei Verbrauchs-/Zykluszählung über Zeit, einen **Utility-Meter** (`ha-automation/utility-meter`) deklarativ definieren
- **MUSS NICHT [MUST NOT]** einen Counter als **Zeitmesser/Countdown** verwenden (z. B. Sekunden hochzählen) — verstreichende Zeit modelliert `ha-automation/timer`, nicht ein Ereigniszähler
- **SOLLTE NICHT [SHOULD NOT]** nicht-ganzzahlige Mengen (Bruchteile, Nachkommastellen) in einem Counter abbilden — der Counter ist ganzzahlig; für Fließkomma-Größen ist ein `input_number` oder ein Template-Sensor passend

## Akzeptanzkriterien

- [ ] Jeder Counter ist unter `counter:` mit snake_case-Alias angelegt; `name` bleibt englisch und ≤50 Zeichen (`ha/naming-conventions` referenziert)
- [ ] `initial`/`step` sind gesetzt, wo sie von den Defaults abweichen; `minimum`/`maximum` begrenzen den Bereich, wo nötig
- [ ] `restore` ist bewusst behandelt (Default `true`)
- [ ] Steuerung erfolgt ausschließlich über `counter.increment`/`decrement`/`reset`/`set_value`
- [ ] Reaktionen nutzen die Event-Trigger (`counter.incremented` etc.), nicht Zustands-Polling
- [ ] Numerische Auswertung behandelt den Zustand als Zahl
- [ ] Kein Counter wird für gemessene/kontinuierliche Werte, Arithmetik auf Sensordaten, Zeitmessung oder Bruchteile eingesetzt, wo Sensor, Template/Utility-Meter oder Timer das richtige Werkzeug sind
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
