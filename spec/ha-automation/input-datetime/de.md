# HA-Automation: input_datetime nutzen

Status: draft

## Kontext

`input_datetime` ist eine **Helfer-Integration**: Sie stellt eine vom Benutzer setzbare Datums- und/oder Uhrzeit-Entität bereit, die über die Oberfläche oder als YAML angelegt wird. Typische Einsatzfälle sind eine vom Bewohner einstellbare Weckzeit, ein Startzeitpunkt oder ein Datum, auf das Automationen reagieren — nicht eine berechnete oder gemessene Zeit.

Die reale HA-Einordnung ist **Helper** (`ha_category: Helper`), nicht ein verbindbares Gerät/Dienst und kein Sensor. Quality-Scale ist hier **nicht zutreffend** — das ist ein Konzept der Integrations-*Entwicklung*, nicht der Nutzung.

Eine `input_datetime`-Entität braucht mindestens eine der beiden Achsen: laut Doku „At least one of `has_time` or `has_date` must be defined." Beide zusammen ergeben einen vollständigen Zeitstempel; nur `has_date` ergibt ein reines Datum, nur `has_time` eine reine Uhrzeit.

Verifizierte Quelle: [`/integrations/input_datetime/`](https://www.home-assistant.io/integrations/input_datetime/).

## Wann verwenden

Verwende `input_datetime` für ein **vom Benutzer setzbares Datum und/oder eine Uhrzeit**, die HA persistent hält und auf die Automationen reagieren — keine berechnete oder gemessene Zeit. Typische Anwendungsfälle:

- **Einstellbare Weckzeit** — eine reine Uhrzeit (`has_time: true`), die der Bewohner setzt und ein `time`-Trigger direkt referenziert (`at: input_datetime.<id>`)
- **Startzeitpunkt/Datum** — ein reines Datum (`has_date: true`) oder ein vollständiger Zeitstempel (beide Achsen), an dem eine Automation handeln soll
- **Benutzer-editierbarer Zeit-Trigger** — die Uhrzeit über die Entität ändern, ohne die Automation anzufassen, sodass der Bewohner den Auslösezeitpunkt selbst steuert
- **Programmatisches Setzen** — den Wert per `input_datetime.set_datetime` (`date`/`time`/`datetime`/`timestamp`) aus einer Automation schreiben
- **Dashboard-Steuerelement** — die Entität einbinden, damit der Bewohner Datum/Uhrzeit direkt setzt, und das `timestamp`-Attribut in Templates lesen

Ein `input_datetime` ist das richtige Werkzeug, sobald ein **fester, benutzer-editierbarer Zeitpunkt** gebraucht wird. Geht es um einen wiederkehrenden Wochenplan, einen Countdown oder einen abgeleiteten Zeitstempel, greift ein anderer Baustein (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration (`has_date`, `has_time`, `name`, `icon`, `initial`) verbindlich festschreiben
- Den dokumentierten Service `input_datetime.set_datetime` und seine Parameter-Varianten (`date`, `time`, `datetime`, `timestamp`) als einzigen Schreibweg fixieren
- Das Lesen von Zustand und Attributen (insbesondere `timestamp`) aus Automationen, Skripten, Templates und Dashboards verlässlich machen
- Das dokumentierte Restore-Verhalten (`initial` vs. Wiederherstellung des letzten Werts) bewusst nutzen
- Klar abgrenzen, wann **kein** `input_datetime` das richtige Werkzeug ist (Zeitplan, Timer, abgeleitete Zeit)

## Nicht-Ziele

- Die Namens-Dimension (`object_id`, snake_case, englischer Anzeigename, ≤50 Zeichen, ASCII) — `ha/naming-conventions`, hier nur referenziert
- Die Trigger-/Bedingungs-/Aktions-Mechanik der Automation selbst — `ha-automation/automation`
- Template-Syntax im Allgemeinen (`strftime`, `as_timestamp`, `as_datetime`) — `/docs/configuration/templating/`, hier nur das integrationsspezifische Lesen
- Wiederkehrende Wochenpläne — `ha-automation/schedule`; Countdown/Restzeit — `ha-automation/timer`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** mindestens eine der Achsen `has_date: true` oder `has_time: true` setzen — die Doku verlangt: „At least one of `has_time` or `has_date` must be defined."
- **MUSS [MUST]** die Achsen-Wahl am Anwendungsfall ausrichten: reines Datum (`has_date: true`), reine Uhrzeit (`has_time: true`) oder vollständiger Zeitstempel (beide `true`) — nicht mehr Achsen setzen, als gelesen werden
- **SOLLTE [SHOULD]** `initial` nur dann setzen, wenn ein deterministischer Startwert nach jedem HA-Start gewollt ist; sonst weglassen, damit der zuletzt gesetzte Wert restauriert wird (siehe Restore-Verhalten)
- **MUSS [MUST]** die `object_id` als snake_case-Slug und den Anzeigenamen englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`) — diese Spec wiederholt die Namens-Regeln nicht
- **KANN [MAY]** `name` und `icon` zur Darstellung im Frontend setzen

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Wert ausschließlich über den dokumentierten Service `input_datetime.set_datetime` schreiben und dabei genau eine passende Parameter-Variante wählen: `date` (`"2020-08-24"`), `time` (`"05:30:00"`), `datetime` (`"2020-08-25 05:30:00"`) oder `timestamp` (UNIX-Zeitstempel)
- **MUSS [MUST]** die gesetzte Parameter-Variante zur Konfiguration passen lassen: `date`/`datetime` nur bei `has_date: true`, `time`/`datetime` nur bei `has_time: true`
- **SOLLTE [SHOULD]** in Triggern auf den Zeitpunkt direkt referenzieren — der `time`-Trigger akzeptiert eine `input_datetime`-Entität (`at: input_datetime.<id>`), sodass die Uhrzeit benutzer-editierbar bleibt, ohne die Automation zu ändern
- **SOLLTE [SHOULD]** in Templates das Attribut `timestamp` (nur bei `has_time: true` vorhanden) als kanonische numerische Zeitquelle lesen und mit `as_datetime`/`strftime` formatieren, statt den String-State zu parsen
- **KANN [MAY]** das Attribut `has_date`/`has_time` lesen, um die vorhandenen Achsen abzufragen; bei reinem Datum steht zusätzlich die Tagesinformation (`year`/`month`/`day`) zur Verfügung
- **MUSS [MUST]** beim Lesen aus Automationen/Templates die Zustände `unknown`/`unavailable` abfangen (z. B. unmittelbar nach Start, bevor restauriert wurde), bevor auf `timestamp` zugegriffen wird
- **KANN [MAY]** die Entität als Dashboard-Steuerelement einbinden, damit der Bewohner Datum/Uhrzeit direkt setzt

### Restore-Verhalten

- **MUSS [MUST]** das dokumentierte Restore-Verhalten berücksichtigen: „If you set a valid value for `initial`, this integration will start with the state set to that value. Otherwise, it will restore the state it had before Home Assistant stopping."
- **SOLLTE NICHT [SHOULD NOT]** `initial` setzen, wenn der vom Bewohner zuletzt eingestellte Wert einen Neustart überdauern soll — `initial` überschreibt den restaurierten Wert bei jedem Start

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `input_datetime` als wiederkehrenden Wochenplan (z. B. „werktags 7–9 Uhr an/aus") missbrauchen — dafür ist der **`schedule`-Helfer** (`ha-automation/schedule`) gedacht, der periodische An-/Aus-Fenster deklarativ abbildet, statt sie aus einem Einzelzeitpunkt nachzubauen
- **MUSS NICHT [MUST NOT]** `input_datetime` als Countdown oder Restzeit-Anzeige verwenden — dafür ist ein **`timer`** (`ha-automation/timer`) das richtige Konstrukt, der eine ablaufende Dauer kapselt und ein `timer.finished`-Event liefert; ein Datums-/Zeit-Helfer hält einen festen Zeitpunkt, keine laufende Restdauer
- **SOLLTE NICHT [SHOULD NOT]** `input_datetime` verwenden, um einen **berechneten oder abgeleiteten** Zeitstempel zu speichern (z. B. „letzte Türöffnung", „nächster Sonnenaufgang") — das ist benutzer-editierbar und verliert die Quelle; stattdessen einen **Template-/Trigger-basierten Sensor** (`ha-automation/template`) mit `device_class: timestamp` definieren, der den Zeitpunkt deklarativ ableitet
- **SOLLTE NICHT [SHOULD NOT]** den String-`state` in Templates parsen, wenn `has_time: true` ist — das dokumentierte `timestamp`-Attribut liefert denselben Wert numerisch und zeitzonensicher
- **MUSS NICHT [MUST NOT]** mehr Achsen aktivieren, als gelesen werden (z. B. `has_date` für eine reine Weckzeit) — überflüssige Achsen erzeugen Attribute und UI-Felder ohne Zweck und verschleiern die Absicht

## Akzeptanzkriterien

- [ ] Jede `input_datetime`-Entität definiert mindestens `has_date: true` oder `has_time: true`, und die Achsen-Wahl passt zum Anwendungsfall
- [ ] Der Wert wird ausschließlich über `input_datetime.set_datetime` mit einer zur Konfiguration passenden Parameter-Variante gesetzt
- [ ] Zeit-Trigger referenzieren die Entität direkt (`at: input_datetime.<id>`), wo benutzer-editierbare Uhrzeit gefragt ist
- [ ] Templates lesen bei `has_time: true` das `timestamp`-Attribut statt den String-State und fangen `unknown`/`unavailable` ab
- [ ] `initial` ist nur gesetzt, wenn ein deterministischer Startwert gewollt ist; sonst greift das Restore-Verhalten
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `input_datetime` für Wochenpläne (→ `schedule`), Countdowns (→ `timer`) oder abgeleitete Zeitstempel (→ Template-Sensor)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
