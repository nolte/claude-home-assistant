# HA-Automation: Schedule nutzen

Status: draft

## Kontext

Die `schedule`-Integration ist ein Helfer, der einen **wiederkehrenden Wochenplan** als binäre Entität bereitstellt. Pro Wochentag werden Zeitfenster (`from`/`to`) definiert; die Entität steht auf `on`, solange ein Fenster aktiv ist, sonst auf `off`. Das macht sie zum natürlichen Werkzeug für „immer montags–freitags 07:00–09:00 gilt X" — ein deklarativer, wöchentlich wiederkehrender Ein/Aus-Zustand.

Die reale HA-Einordnung ist **Helfer** (Helper). Anders als Timer und Counter ist Schedule **rein konfigurations-/UI-definiert**: Es gibt **keine mutierende `schedule.*`-Aktion**, um die Zeitfenster zur Laufzeit zu ändern — nur `schedule.reload` (lädt die YAML neu) und `schedule.get_schedule` (liest die konfigurierten Bereiche). Der Plan wird im UI-Editor oder in YAML gepflegt. Die Entität trägt den Zustand `on`/`off` und das Attribut `next_event` (Zeitpunkt des nächsten Zustandswechsels); pro Fenster definierte `data`-Werte erscheinen als Attribute, solange das Fenster aktiv ist.

Verifizierte Quelle: [`/integrations/schedule/`](https://www.home-assistant.io/integrations/schedule/) (Wochentags-Schlüssel, `from`/`to`/`data`, Zustände, `next_event`, `schedule.reload`/`get_schedule`, Trigger). Das Trigger/Bedingung/Aktion-Grundmodell stammt aus `ha-automation/automation`.

## Wann verwenden

Verwende `schedule` für einen **wiederkehrenden Wochenplan** aus festen `from`/`to`-Zeitfenstern, der sich als `on`/`off`-Zustand deklarativ ausdrücken lässt. Ein Schedule lohnt sich, sobald „immer an diesen Wochentagen zu diesen Zeiten gilt X" gefragt ist. Typische Anwendungsfälle:

- **Wöchentliches Aktiv-Fenster** — montags–freitags 07:00–09:00 als `on`-Fenster definieren und auf `schedule.turned_on`/`schedule.turned_off` reagieren
- **Zeit-Gate für Automationen** — den `on`/`off`-Zustand als Bedingung verwenden, um eine Automation nur innerhalb der Plan-Fenster handeln zu lassen
- **Tagesabhängige Nacht-/Ruhezeiten** — pro Wochentag abweichende Fenster (z. B. am Wochenende später) deklarativ pflegen
- **Pro-Fenster-Parameter** — über das `data`-Mapping je Fenster Werte als Attribute bereitstellen (z. B. eine Soll-Temperatur), die nur im aktiven Fenster sichtbar sind
- **Anzeige des nächsten Wechsels** — das Attribut `next_event` in einem Template lesen, um den nächsten Zustandswechsel darzustellen

Ein Schedule ist das richtige Werkzeug, sobald feste, **wöchentlich wiederkehrende Ein/Aus-Fenster** gebraucht werden. Geht es um einen einmaligen Termin, einen Countdown, zur Laufzeit veränderbare Grenzen oder komplexe Kalenderlogik, ist ein anderer Baustein richtig (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines Schedules (`name`, `icon`, die Wochentags-Schlüssel mit `from`/`to`, optional `data`) verbindlich festschreiben
- Den Lese-Vertrag über den `on`/`off`-Zustand und das `next_event`-Attribut festschreiben
- Klarstellen, dass Schedule **keine mutierende Aktion** hat — nur `reload`/`get_schedule`
- Die Event-Trigger (`schedule.turned_on`, `schedule.turned_off`) sowie Zustands-Trigger als Reaktionsweg verankern
- Klar abgrenzen, wann ein Schedule **nicht** das richtige Werkzeug ist (gegen einmalige Termine, gegen Countdowns, gegen Kalenderlogik)

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Grundmodell von Automationen — `ha-automation/automation`
- Die Namens-Dimension (`name`/Entity-ID, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Einmalige Datums-/Uhrzeit-Werte — `ha-automation/input-datetime`
- Verstreichende Zeit / Countdowns — `ha-automation/timer`
- Termin-/Kalenderbasierte Auslösung — die `calendar`-Integration

## Anforderungen

### Konfiguration

- **MUSS [MUST]** ein YAML-Schedule unter der Domäne `schedule:` mit einem snake_case-Schlüssel (der Alias, der die Entity-ID bestimmt) und einem `name` anlegen; Mechanik der ID/`name`-Vergabe: `ha/naming-conventions`
- **MUSS [MUST]** pro genutztem Wochentag (`monday`…`sunday`) eine Liste von Fenstern mit den Pflichtfeldern `from` (Startzeit, markiert `on`) und `to` (Endzeit, markiert wieder `off`) angeben
- **KANN [MAY]** pro Fenster ein `data`-Mapping setzen; dessen Schlüssel/Werte erscheinen als Entity-Attribute, solange das Fenster aktiv ist
- **SOLLTE [SHOULD]** optional `icon` für die UI vergeben; der `name` bleibt englisch und ≤50 Zeichen (`ha/naming-conventions`)

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Schedule als **Lesequelle** behandeln — er hat keine mutierende Aktion; zur Laufzeit stehen nur `schedule.reload` (YAML neu laden) und `schedule.get_schedule` (Bereiche auslesen) zur Verfügung
- **SOLLTE [SHOULD]** auf die Event-Trigger `schedule.turned_on`/`schedule.turned_off` oder einen `state`-Trigger auf `on`/`off` reagieren, statt den Zustand zu pollen
- **KANN [MAY]** den `on`/`off`-Zustand als Bedingung/Gate verwenden (z. B. „nur handeln, wenn der Schedule gerade `on` ist")
- **KANN [MAY]** das Attribut `next_event` (nächster Zustandswechsel) und pro Fenster gesetzte `data`-Attribute in Templates lesen, etwa für Anzeige oder Verzweigung

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** einen Schedule für einen **einmaligen Termin** an einem festen Datum/Uhrzeit verwenden — Schedule wiederholt sich wöchentlich und kennt kein Datum; für eine einmalige, vom User setzbare Zeit ist ein `input_datetime` plus Automation das richtige Konstrukt
- **MUSS NICHT [MUST NOT]** einen Schedule als **Countdown** missbrauchen — er modelliert wiederkehrende Wandkalender-Fenster, keine ablaufende Dauer; für „nach N Minuten" ist `ha-automation/timer` zuständig
- **SOLLTE NICHT [SHOULD NOT]** komplexe **Kalenderlogik** (Feiertage, Ausnahmen, einmalige Termine, externe Kalender, „jeden zweiten Dienstag") in Schedule abbilden — Schedule kann nur feste wöchentliche `from`/`to`-Fenster; für termin-/kalenderbasierte Auslösung ist die **`calendar`-Integration** das richtige Werkzeug
- **SOLLTE NICHT [SHOULD NOT]** Schedule für ein Fenster verwenden, das zur Laufzeit per Automation **verändert** werden soll — es gibt keine mutierende Aktion; veränderbare Grenzwerte gehören in `input_datetime`/`input_number`, die per `set_value` gesetzt werden können

## Akzeptanzkriterien

- [ ] Jedes Schedule ist unter `schedule:` mit snake_case-Alias und `name` angelegt; `name` bleibt englisch und ≤50 Zeichen (`ha/naming-conventions` referenziert)
- [ ] Jeder genutzte Wochentag listet Fenster mit `from`/`to`; optionales `data` ist nur als aktive Attribute genutzt
- [ ] Der Schedule wird als Lesequelle behandelt; keine mutierende `schedule.*`-Aktion wird erwartet (nur `reload`/`get_schedule`)
- [ ] Reaktionen nutzen `schedule.turned_on`/`turned_off` oder `state`-Trigger, nicht Zustands-Polling
- [ ] `next_event` und `data`-Attribute werden nur lesend genutzt
- [ ] Kein Schedule wird für einmalige Termine, Countdowns, veränderbare Grenzwerte oder komplexe Kalenderlogik eingesetzt, wo `input_datetime`, `timer` oder die `calendar`-Integration das richtige Werkzeug sind
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
