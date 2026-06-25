# HA-Automation: input_select nutzen

Status: draft

## Kontext

`input_select` ist eine **Helfer-Integration**: Sie stellt eine vom Benutzer wählbare Auswahlliste (Dropdown) bereit, deren aktueller Zustand eine der vordefinierten Optionen ist. Typische Einsatzfälle sind ein Modus-/Preset-Wähler (z. B. „Heim/Abwesend/Urlaub", „Tag/Nacht/Party"), den der Bewohner manuell oder eine Automation umschaltet und auf den andere Automationen reagieren.

Die reale HA-Einordnung ist **Helper** (`ha_category: Helper`), nicht ein verbindbares Gerät/Dienst und kein berechneter Zustand. Quality-Scale ist hier **nicht zutreffend** — das ist ein Konzept der Integrations-*Entwicklung*, nicht der Nutzung.

Eine `input_select`-Entität braucht laut Doku eine `options`-Liste („List of options to choose from"); der Zustand ist stets eine dieser Optionen, und `initial` legt den Startwert fest (sonst das erste Listenelement).

Verifizierte Quelle: [`/integrations/input_select/`](https://www.home-assistant.io/integrations/input_select/).

## Wann verwenden

Verwende `input_select` für eine **vom Benutzer wählbare Auswahl aus einem geschlossenen Satz benannter Optionen**, deren aktueller Zustand stets eine dieser Optionen ist und auf die Automationen reagieren. Typische Anwendungsfälle:

- **Modus-/Preset-Wähler** — ein Haus-Modus wie „Heim/Abwesend/Urlaub" oder eine Szene wie „Tag/Nacht/Party", den der Bewohner manuell umschaltet
- **Verzweigung im Aktionsteil** — per `state`-Trigger auf einen Optionswechsel reagieren und im Aktionsteil per `choose`/`if` auf den Zustand verzweigen
- **Programmatisches Setzen** — eine Option per `input_select.select_option` (mit einem in `options` enthaltenen Wert) oder per `select_next`/`select_previous`/`select_first`/`select_last` setzen
- **Dynamische Optionsliste** — die Liste zur Laufzeit über `input_select.set_options` aus einer dynamischen Quelle ersetzen
- **Dashboard-Dropdown** — die Entität als Dropdown einbinden, damit der Bewohner die Option direkt wählt

Ein `input_select` ist das richtige Werkzeug, sobald eine **benutzer-wählbare Auswahl aus benannten, geschlossenen Optionen** gebraucht wird. Geht es um einen abgeleiteten Enum, einen echten Gerätezustand, einen An/Aus-Zustand oder eine numerische Größe, greift ein anderer Baustein (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration (`options`, `name`, `icon`, `initial`) verbindlich festschreiben
- Die dokumentierten Services (`select_option`, `select_next`, `select_previous`, `select_first`, `select_last`, `set_options`) als einzige Schreibwege fixieren
- Das Lesen des Zustands und der `options`-Liste aus Automationen, Skripten, Templates und Dashboards verlässlich machen
- Das dokumentierte Restore-Verhalten (`initial` vs. Wiederherstellung des letzten Werts) bewusst nutzen
- Klar abgrenzen, wann **kein** `input_select` das richtige Werkzeug ist (abgeleiteter Enum, echter Gerätezustand)

## Nicht-Ziele

- Die Namens-Dimension (`object_id`, snake_case, englischer Anzeigename, ≤50 Zeichen, ASCII) — `ha/naming-conventions`, hier nur referenziert; gilt auch für die Options-Strings
- Die Trigger-/Bedingungs-/Aktions-Mechanik der Automation selbst — `ha-automation/automation`
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur das integrationsspezifische Lesen
- Template-getriebene Enum-Zustände — `ha-automation/template`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** eine nicht-leere `options`-Liste definieren — laut Doku „List of options to choose from"; der Zustand ist stets eine dieser Optionen
- **SOLLTE [SHOULD]** die `options` als stabilen, geschlossenen Wertebereich behandeln und einen `initial`-Wert nur dann setzen, wenn ein deterministischer Startwert nach jedem HA-Start gewollt ist; sonst weglassen (Default ist das erste Element bzw. der restaurierte Wert)
- **MUSS [MUST]** die `object_id` als snake_case-Slug und den Anzeigenamen englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`); auch die Options-Strings folgen den dortigen Sprach-/Stabilitäts-Regeln und tragen keine volatilen Daten
- **SOLLTE NICHT [SHOULD NOT]** Optionen verwenden, die später per Übersetzung oder Anzeige umbenannt werden müssen — ein Options-String ist zugleich der Zustandswert, auf den Automationen matchen
- **KANN [MAY]** `name` und `icon` zur Darstellung im Frontend setzen

### Nutzung in Automationen & Templates

- **MUSS [MUST]** eine Option ausschließlich über die dokumentierten Services setzen: `input_select.select_option` (mit `option`), `select_next`/`select_previous` (mit optionalem `cycle`), `select_first`/`select_last` — keinen Zustand „von außen" schreiben
- **MUSS [MUST]** bei `input_select.select_option` nur einen `option`-Wert übergeben, der in der konfigurierten `options`-Liste enthalten ist
- **SOLLTE [SHOULD]** auf Wechsel per `state`-Trigger auf die Entität reagieren (`to:`/`from:` auf einen Options-String) und im Aktionsteil per `choose`/`if` auf den Zustand verzweigen
- **SOLLTE [SHOULD]** in Bedingungen und Templates den Zustand direkt mit einem Options-String vergleichen (`states('input_select.<id>')`) statt Teilstrings oder Reihenfolge anzunehmen
- **KANN [MAY]** das Attribut `options` lesen, um die verfügbaren Werte dynamisch (z. B. in einem Template oder einer Dashboard-Logik) zu ermitteln
- **KANN [MAY]** die Optionsliste zur Laufzeit über `input_select.set_options` ersetzen, wenn sie aus einer dynamischen Quelle stammt — dabei beachten, dass der aktuelle Zustand ungültig werden kann, wenn er nicht mehr enthalten ist
- **MUSS [MUST]** beim Lesen aus Automationen/Templates die Zustände `unknown`/`unavailable` abfangen (z. B. unmittelbar nach Start, bevor restauriert wurde), bevor auf den Optionswert verzweigt wird
- **KANN [MAY]** die Entität als Dashboard-Dropdown einbinden, damit der Bewohner die Option direkt wählt

### Restore-Verhalten

- **MUSS [MUST]** das dokumentierte Restore-Verhalten berücksichtigen: „If you set a valid value for `initial` this integration will start with the state set to that value. Otherwise, it will restore the state it had before Home Assistant stopping."
- **SOLLTE NICHT [SHOULD NOT]** `initial` setzen, wenn die vom Bewohner zuletzt gewählte Option einen Neustart überdauern soll — `initial` überschreibt den restaurierten Wert bei jedem Start

### Abgrenzung: Wann NICHT verwenden

- **SOLLTE NICHT [SHOULD NOT]** `input_select` verwenden, um einen **berechneten/abgeleiteten Enum-Zustand** zu halten (z. B. „Haus-Modus" aus mehreren Sensoren) — das ist benutzer-editierbar und kann von der Logik abweichen; stattdessen einen **Template-Sensor** (`ha-automation/template`) definieren, der den Enum-Zustand deklarativ aus seinen Eingängen ableitet
- **SOLLTE NICHT [SHOULD NOT]** `input_select` als Ersatz für einen **echten Gerätezustand** einsetzen (z. B. den Lüftermodus eines Klimageräts spiegeln) — der Helfer und das Gerät können auseinanderlaufen; stattdessen direkt die `select`-/`climate`-Entität des Geräts ansprechen und lesen
- **MUSS NICHT [MUST NOT]** einen einfachen An/Aus- oder Ja/Nein-Zustand als zweielementige `input_select` modellieren — dafür ist ein **`input_boolean`** (`ha-automation/input-boolean`) gedacht, der Toggle-Semantik und passende UI/Service-Verben mitbringt
- **SOLLTE NICHT [SHOULD NOT]** eine numerische, vom Benutzer einstellbare Größe (z. B. Zielhelligkeit) als Optionsliste abbilden — dafür ist ein **`input_number`** (`ha-automation/input-number`) gedacht, der Min/Max/Schritt und numerische Vergleiche liefert
- **SOLLTE NICHT [SHOULD NOT]** auf die **Reihenfolge** der Optionen über `select_next`/`select_previous` als verlässliche Semantik bauen, wenn der Anwendungsfall eine konkrete Option meint — `select_option` mit explizitem `option` ist robust gegen spätere Listenänderungen

## Akzeptanzkriterien

- [ ] Jede `input_select`-Entität definiert eine nicht-leere `options`-Liste; der Zustand ist stets eine dieser Optionen
- [ ] Optionen werden ausschließlich über die dokumentierten Services gesetzt; `select_option` erhält nur einen in `options` enthaltenen Wert
- [ ] Automationen reagieren per `state`-Trigger und vergleichen den Zustand direkt mit einem Options-String
- [ ] `set_options` zur Laufzeit berücksichtigt, dass der aktuelle Zustand ungültig werden kann; `unknown`/`unavailable` wird beim Lesen abgefangen
- [ ] `initial` ist nur gesetzt, wenn ein deterministischer Startwert gewollt ist; sonst greift das Restore-Verhalten
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: kein `input_select` für abgeleitete Enums (→ Template-Sensor), Gerätezustände (→ Geräte-Entität), Booleans (→ `input_boolean`) oder numerische Größen (→ `input_number`)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
