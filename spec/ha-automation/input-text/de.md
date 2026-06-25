# HA-Automation: input_text nutzen

Status: draft

## Kontext

`input_text` ist eine **Helfer-Integration**: Sie stellt ein vom Benutzer setzbares Freitext-Feld bereit, das über die Oberfläche oder als YAML angelegt wird. Typische Einsatzfälle sind eine kurze, vom Bewohner editierbare Notiz, ein Anzeige-/Statusstring oder ein kleiner, von Automationen gesetzter Wert (z. B. eine zuletzt gescannte Kennung).

Die reale HA-Einordnung ist **Helper** (`ha_category: Helper`), nicht ein verbindbares Gerät/Dienst und kein abgeleiteter Sensor. Quality-Scale ist hier **nicht zutreffend** — das ist ein Konzept der Integrations-*Entwicklung*, nicht der Nutzung.

Der Zustand ist der Textwert selbst. Die Doku legt für das Feld Grenzen fest: `min` (Default `0`) und `max` (Default `100`) begrenzen die Länge, `pattern` erlaubt eine clientseitige Regex-Validierung, und `mode` (`text` oder `password`) steuert die Eingabedarstellung. Generell gilt die HA-Zustandsgrenze: „255 is the maximum number of characters allowed in an entity state".

Verifizierte Quelle: [`/integrations/input_text/`](https://www.home-assistant.io/integrations/input_text/).

## Wann verwenden

Verwende `input_text` für einen **kurzen, vom Benutzer setzbaren Freitext-Wert** (≤255 Zeichen), den HA persistent hält und Automationen lesen — kein großer Speicher, kein Secret, kein abgeleiteter Wert. Typische Anwendungsfälle:

- **Editierbare Notiz** — eine kurze, vom Bewohner gesetzte Notiz oder ein Anzeige-/Statusstring auf einem Dashboard
- **Von Automationen gesetzter Wert** — ein kleiner String, den eine Automation per `input_text.set_value` setzt (z. B. eine zuletzt gescannte Kennung)
- **Reaktion auf Wertänderung** — per `state`-Trigger auf eine Änderung reagieren und den Zustand in Bedingungen/Templates direkt als String vergleichen (`states('input_text.<id>')`)
- **Validierte/maskierte Eingabe** — `min`/`max` und (clientseitig) `pattern` zur Längen-/Format-Eingrenzung nutzen, `mode: password` zur Anzeige-Maskierung
- **Dashboard-Texteingabe** — die Entität als Texteingabe einbinden, damit der Bewohner den Wert direkt setzt

Ein `input_text` ist das richtige Werkzeug, sobald ein **kurzer, benutzer-setzbarer Freitext** gebraucht wird. Geht es um großen/strukturierten Speicher, Secrets, einen abgeleiteten Wert oder einen getypten Wert (Zahl/Boolean/Auswahl), greift ein anderer Baustein (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration (`name`, `min`, `max`, `initial`, `icon`, `pattern`, `mode`) verbindlich festschreiben
- Den dokumentierten Service `input_text.set_value` (mit `value`) als einzigen Schreibweg fixieren
- Das Lesen des Textzustands aus Automationen, Skripten, Templates und Dashboards verlässlich machen
- Das dokumentierte Restore-Verhalten (`initial` vs. Wiederherstellung des letzten Werts) bewusst nutzen
- Klar abgrenzen, wann **kein** `input_text` das richtige Werkzeug ist (großer Speicher, Secrets, abgeleitete Werte)

## Nicht-Ziele

- Die Namens-Dimension (`object_id`, snake_case, englischer Anzeigename, ≤50 Zeichen, ASCII) — `ha/naming-conventions`, hier nur referenziert
- Die Trigger-/Bedingungs-/Aktions-Mechanik der Automation selbst — `ha-automation/automation`
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur das integrationsspezifische Lesen
- Template-getriebene Textzustände — `ha-automation/template`

## Anforderungen

### Konfiguration

- **SOLLTE [SHOULD]** `min` und `max` bewusst am Anwendungsfall setzen (Defaults `min: 0`, `max: 100`) und `max` nie über die HA-Zustandsgrenze treiben — die Doku: „255 is the maximum number of characters allowed in an entity state"
- **KANN [MAY]** `pattern` als clientseitige Regex-Validierung setzen; die Doku bezeichnet sie als „Regex pattern for client-side validation" — sie ist eine UI-Hilfe, kein serverseitiger Zwang, also nicht als Sicherheits-/Integritätsgrenze verstehen
- **SOLLTE [SHOULD]** `mode: password` setzen, wenn der Wert in der UI maskiert dargestellt werden soll — das verbirgt nur die Anzeige; der Zustand bleibt im Klartext gespeichert und ist kein Geheimnis-Speicher (siehe Abgrenzung)
- **SOLLTE [SHOULD]** `initial` nur dann setzen, wenn ein deterministischer Startwert nach jedem HA-Start gewollt ist; sonst weglassen, damit der zuletzt gesetzte Wert restauriert wird
- **MUSS [MUST]** die `object_id` als snake_case-Slug und den Anzeigenamen englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`) — diese Spec wiederholt die Namens-Regeln nicht
- **KANN [MAY]** `name` und `icon` zur Darstellung im Frontend setzen

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Wert ausschließlich über den dokumentierten Service `input_text.set_value` (Parameter `value`) schreiben — „Sets the value of an input text"
- **MUSS [MUST]** sicherstellen, dass ein geschriebener `value` innerhalb von `min`/`max` und (falls gesetzt) `pattern` liegt, da serverseitig sonst die Übernahme scheitert bzw. die Validierung greift
- **SOLLTE [SHOULD]** auf Wertänderungen per `state`-Trigger auf die Entität reagieren und den Zustand in Bedingungen/Templates direkt als String vergleichen (`states('input_text.<id>')`)
- **KANN [MAY]** die Attribute `min`, `max`, `pattern`, `mode` lesen, um die Grenzen oder den Modus dynamisch abzufragen
- **MUSS [MUST]** beim Lesen aus Automationen/Templates die Zustände `unknown`/`unavailable` sowie den leeren String abfangen (z. B. unmittelbar nach Start, bevor restauriert wurde), bevor der Wert verarbeitet wird
- **KANN [MAY]** die Entität als Dashboard-Texteingabe einbinden, damit der Bewohner den Wert direkt setzt

### Restore-Verhalten

- **MUSS [MUST]** das dokumentierte Restore-Verhalten berücksichtigen: „If you set a valid value for `initial` this integration will start with state set to that value. Otherwise, it will restore the state it had before Home Assistant stopping."
- **SOLLTE NICHT [SHOULD NOT]** `initial` setzen, wenn der vom Bewohner zuletzt eingegebene Wert einen Neustart überdauern soll — `initial` überschreibt den restaurierten Wert bei jedem Start

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `input_text` als allgemeinen Datenspeicher oder große Zustands-Ablage missbrauchen — die HA-Zustandsgrenze von 255 Zeichen macht es dafür ungeeignet; für strukturierte oder größere Daten gehört der Wert in ein eigenes Speichermedium (Datei, externe DB, Add-on), nicht in einen Zustand
- **MUSS NICHT [MUST NOT]** `input_text` für **Secrets** (API-Schlüssel, Passwörter, Tokens) verwenden — der Zustand wird im Klartext gehalten, in Historie/Logbuch sichtbar und über die API abrufbar; `mode: password` maskiert nur die Anzeige. Geheimnisse gehören in `secrets.yaml` bzw. die jeweils vorgesehene Konfigurations-/Credentials-Mechanik
- **SOLLTE NICHT [SHOULD NOT]** `input_text` verwenden, um einen **berechneten/abgeleiteten** Stringwert zu speichern (z. B. eine formatierte Statuszeile aus mehreren Sensoren) — das ist benutzer-editierbar und läuft der Quelle hinterher; stattdessen einen **Template-Sensor** (`ha-automation/template`) definieren, der den String deklarativ ableitet
- **SOLLTE NICHT [SHOULD NOT]** `input_text` als Ersatz für getypte Helfer einsetzen, wenn der Wert in Wahrheit eine Zahl, ein Boolean oder eine geschlossene Auswahl ist — dann ist ein **`input_number`**, **`input_boolean`** bzw. **`input_select`** (`ha-automation/input-number`, `…/input-boolean`, `…/input-select`) richtig, das Validierung und passende Vergleiche mitbringt
- **MUSS NICHT [MUST NOT]** sich auf `pattern` als verlässliche Integritäts-/Sicherheitsschranke verlassen — die Doku bezeichnet sie ausdrücklich als „client-side validation"; ein per Service gesetzter Wert kann sie umgehen, daher die Validierung in der schreibenden Automation absichern

## Akzeptanzkriterien

- [ ] `min`/`max` sind bewusst gesetzt und überschreiten nie die HA-Zustandsgrenze von 255 Zeichen
- [ ] Der Wert wird ausschließlich über `input_text.set_value` gesetzt und liegt innerhalb `min`/`max`/`pattern`
- [ ] Automationen reagieren per `state`-Trigger; Templates fangen `unknown`/`unavailable` und den leeren String ab
- [ ] `mode: password` wird nur zur Anzeige-Maskierung genutzt, nie als Geheimnis-Speicher
- [ ] `initial` ist nur gesetzt, wenn ein deterministischer Startwert gewollt ist; sonst greift das Restore-Verhalten
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `input_text` als großer Speicher, für Secrets, für abgeleitete Werte (→ Template-Sensor) oder als Ersatz für getypte Helfer
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
