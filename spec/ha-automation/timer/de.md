# HA-Automation: Timer nutzen

Status: draft

## Kontext

Die `timer`-Integration ist ein Helfer, der einen **abwärtszählenden Countdown** als Entität bereitstellt. Ein Timer wird über eine Aktion gestartet, läuft eine konfigurierte Dauer herunter und feuert beim Ablauf ein Event — das macht ihn zum natürlichen Werkzeug für „X passiert, dann nach N Minuten Y" ohne blockierendes `delay` im Aktionsteil einer Automation.

Die reale HA-Einordnung ist **Helfer** (Helper) — ein per UI oder YAML angelegtes Hilfsobjekt, kein verbindbares Gerät. Ein Timer trägt einen Zustand (`idle`/`active`/`paused`) und Attribute (`duration`, `remaining`, `finishes_at`, `restore`, `editable`), wird per `timer.*`-Aktionen gesteuert und feuert eigene Events, auf die Automationen triggern. Anders als ein `delay` oder die `for`-Option eines Triggers ist ein Timer eine **persistente, beobachtbare Entität**: mehrere Automationen können ihn lesen, steuern und auf seine Events reagieren.

Verifizierte Quelle: [`/integrations/timer/`](https://www.home-assistant.io/integrations/timer/) (Konfigurationsvariablen, Aktionen, Trigger, Bedingungen, Zustände, Neustart-Einschränkung). Das Trigger/Bedingung/Aktion-Grundmodell stammt aus `ha-automation/automation`.

## Wann verwenden

Verwende `timer` für eine **relative, beobachtbare Countdown-Dauer**, die von einer Automation gestartet wird und beim Ablauf ein Event feuert. Ein Timer lohnt sich, sobald die Wartezeit von außen lesbar, steuerbar oder neustart-fest sein muss. Typische Anwendungsfälle:

- **Auto-Abschaltung nach Inaktivität** — Licht nach N Minuten ohne Bewegung ausschalten, mit `timer.start` bei jeder Bewegung neugestartet und Reaktion auf `timer.finished`
- **Neustart-feste Verzögerung** — eine Verzögerung, die einen HA-Neustart übersteht (`restore: true`), wo ein `delay` oder die `for`-Option verloren ginge
- **Von mehreren Automationen geteilter Countdown** — ein Timer, den mehrere Automationen lesen, starten und über `timer.pause`/`timer.cancel`/`timer.change` steuern
- **Unterbrechbare Wartezeit** — ein laufender Countdown, der per `timer.cancel` (ohne `timer.finished`-Event) oder `timer.change` zur Laufzeit verlängert/verkürzt werden kann
- **Restzeit-Anzeige** — die Attribute `remaining` und `finishes_at` in einem Template lesen, um die verbleibende Zeit darzustellen

Ein Timer ist das richtige Werkzeug, sobald die Dauer **beobachtbar, steuerbar oder neustart-fest** sein muss. Geht es nur um eine schlichte Halte-Bedingung, eine absolute Uhrzeit, einen wiederkehrenden Plan oder einen Ereigniszähler, ist ein anderer Baustein richtig (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines Timers (`name`, `duration`, `icon`, `restore`) verbindlich festschreiben
- Den Steuerungsvertrag über die Aktionen `timer.start`/`pause`/`cancel`/`finish`/`change` (inkl. `duration`-Feld) fixieren
- Den Lese-Vertrag über Zustand (`idle`/`active`/`paused`) und Attribute (`remaining`, `finishes_at`, `restore`) festschreiben
- Die Event-Trigger (`timer.started`, `timer.finished`, `timer.cancelled`, `timer.paused`, `timer.restarted`) als bevorzugten Reaktionsweg verankern
- Klar abgrenzen, wann ein Timer **nicht** das richtige Werkzeug ist (gegen `for`, gegen `time`-Trigger, gegen `schedule`)

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Grundmodell von Automationen — `ha-automation/automation`
- Die Skript-Syntax im Aktionsteil (`delay`, `wait_template`, `choose`) — `ha-automation/script`
- Die Namens-Dimension (`name`/Entity-ID, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Wiederkehrende Wochenpläne — `ha-automation/schedule`
- Diskrete Ereigniszähler — `ha-automation/counter`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen YAML-Timer unter der Domäne `timer:` mit einem snake_case-Schlüssel (der Alias, der die Entity-ID bestimmt) anlegen; Mechanik der ID/`name`-Vergabe: `ha/naming-conventions`
- **SOLLTE [SHOULD]** eine `duration` als Default-Dauer setzen (Sekunden oder `"00:00:00"`-Form); fehlt sie, ist der Default `0` und der Timer muss bei jedem Start eine explizite `duration` mitliefern
- **MUSS [MUST]** `restore: true` setzen, wenn der Timer einen HA-Neustart überstehen soll — ohne `restore` (Default `false`) gehen aktive und pausierte Timer beim Neustart verloren
- **SOLLTE [SHOULD]** einen `name` (Friendly Name) und optional `icon` für die UI-Darstellung vergeben; der `name` bleibt englisch und ≤50 Zeichen (`ha/naming-conventions`)
- **KANN [MAY]** mehrere Timer unter `timer:` als Geschwister-Einträge definieren

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Timer über die dokumentierten Aktionen steuern: `timer.start` (startet/neustartet, optional mit abweichender `duration`), `timer.pause`, `timer.cancel` (ohne `finished`-Event), `timer.finish` (vorzeitiges, regulär feuerndes Beenden), `timer.change` (addiert/subtrahiert `duration` auf einem laufenden Timer)
- **SOLLTE [SHOULD]** auf die Event-Trigger `timer.finished`/`timer.started`/`timer.restarted`/`timer.paused`/`timer.cancelled` triggern, statt den Zustand zu pollen; der auslösende Timer steht im Event-Daten-`entity_id`
- **MUSS [MUST]** beachten, dass `timer.cancel` **kein** `timer.finished`-Event feuert — Abbruch- und Ablauf-Logik dürfen nicht denselben Trigger erwarten
- **KANN [MAY]** im Aktionsteil/Template den Zustand (`active`/`idle`/`paused`) sowie die Attribute `remaining` (Restzeit) und `finishes_at` (absoluter Endzeitpunkt) lesen, etwa für eine Anzeige der verbleibenden Zeit
- **KANN [MAY]** die Bedingungen `timer.is_active`/`timer.is_idle`/`timer.is_paused` als Gate verwenden
- **MUSS [MUST]** berücksichtigen, dass ein Timer, der **während HA aus war** abläuft, das `timer.finished`-Event nach dem Start **nicht** nachholt (dokumentierte Einschränkung) — auf Ablauf angewiesene, kritische Logik braucht eine zusätzliche Zustandsprüfung beim Start

### Abgrenzung: Wann NICHT verwenden

- **SOLLTE NICHT [SHOULD NOT]** einen Timer einsetzen, wo eine reine, an Ort und Stelle wirkende Halte-Bedingung genügt — für „Zustand X hält N Minuten an, dann handle" ist die `for`-Option eines `state`-Triggers einfacher; ein Timer lohnt sich, **weil** er einen HA-Neustart übersteht (`restore: true`) und beobachtbar/steuerbar ist, was `for` nicht bietet (Hintergrund-Modell: `ha-automation/automation`)
- **MUSS NICHT [MUST NOT]** einen Timer für eine **feste Uhrzeit am Wandkalender** missbrauchen (z. B. „um 22:00 Uhr") — ein Timer zählt eine relative Dauer herunter, keine absolute Zeit; stattdessen einen `time`-Trigger bzw. ein `input_datetime` verwenden
- **MUSS NICHT [MUST NOT]** einen Timer als **wiederkehrenden Planer** verwenden (täglich/wöchentlich wiederholt) — ein Timer ist ein einmaliger Countdown; für wiederkehrende Wochenfenster ist `ha-automation/schedule` das richtige Konstrukt
- **SOLLTE NICHT [SHOULD NOT]** einen Timer als **Zähler diskreter Ereignisse** zweckentfremden — dafür ist `ha-automation/counter` gedacht; ein Timer modelliert verstreichende Zeit, keine Ereignis-Anzahl
- **SOLLTE NICHT [SHOULD NOT]** ein blockierendes `delay` im Aktionsteil durch einen Timer ersetzen, wenn die Wartezeit kurz ist und keine andere Automation den Ablauf beobachten oder unterbrechen muss — der Timer lohnt sich erst, wenn Beobachtbarkeit, Neustart-Festigkeit oder externe Steuerung (`pause`/`cancel`/`change`) gebraucht werden

## Akzeptanzkriterien

- [ ] Jeder Timer ist unter `timer:` mit snake_case-Alias angelegt; `name` bleibt englisch und ≤50 Zeichen (`ha/naming-conventions` referenziert)
- [ ] `restore: true` ist gesetzt, wenn der Timer einen Neustart überstehen soll
- [ ] Steuerung erfolgt ausschließlich über `timer.start`/`pause`/`cancel`/`finish`/`change`
- [ ] Reaktionen nutzen die Event-Trigger (`timer.finished` etc.), nicht Zustands-Polling
- [ ] Abbruch- vs. Ablauf-Logik unterscheidet `timer.cancel` (kein `finished`-Event) von regulärem Ablauf
- [ ] Auf Ablauf angewiesene, kritische Logik berücksichtigt, dass ein während HA-Aus abgelaufener Timer kein nachträgliches `finished`-Event feuert
- [ ] Kein Timer wird statt `for`, `time`-Trigger/`input_datetime`, `schedule` oder `counter` eingesetzt, wo diese das richtige Werkzeug sind
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
