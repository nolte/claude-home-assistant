# HA-Automation: Script nutzen

Status: draft

## Kontext

Die `script`-Domäne kapselt eine **benannte Sequenz von Aktionen**, die Home Assistant ausführt, wenn das Skript explizit aufgerufen wird. Ein Skript hat — anders als eine Automation — **keinen Trigger**: Die offizielle Doku stellt klar, dass Automationen automatisch auslösen, während Skripte „nur dann ausgeführt werden, wenn sie explizit aufgerufen werden" und „keine Trigger besitzen". Damit ist das Skript der wiederverwendbare, aufrufbare Aktionsblock des `ha-automation`-Korpus, auf den die Automation-Spec im Aktionsteil verweist.

Ein Skript wird über den visuellen Editor oder als YAML verfasst. Pflicht ist der Schlüssel `sequence` (die Aktionsliste); optional sind `alias`, `icon`, `description`, `variables`, `fields`, `mode`, `max` und `max_exceeded`. Jedes Skript erscheint als Entität `script.<object_id>` mit dem Zustand `on`/`off` und wird zugleich als eigener aufrufbarer Service `script.<object_id>` exponiert. Über den Aktionsteil steht die **volle Skript-Syntax** zur Verfügung (Aktions-Aufrufe, `delay`, `wait_template`, `wait_for_trigger`, `choose`, `if/then/else`, `repeat`, `parallel`, `stop`, `variables`).

Reale Einordnung: Das Skript ist eine **Kern-Konfigurationsdomäne** (kein verbindbares Gerät/Dienst) und besitzt zwar eine Integrations-Karte unter `/integrations/script/`, dokumentiert seine Aktions-Syntax aber zentral unter `/docs/scripts/` — derselben Seite, auf die die Automation-Aktionen verweisen.

Verifizierte Quellen: [`/integrations/script/`](https://www.home-assistant.io/integrations/script/) (Konfigurationsschlüssel, `fields`, Modi, Aufruf mit Variablen, `script.turn_on`) und [`/docs/scripts/`](https://www.home-assistant.io/docs/scripts/) (Sequenz-Syntax, Wait-Aktionen, `choose`/`if`/`repeat`/`parallel`/`stop`, `response_variable`, `continue_on_error`, Skript-Variablen `repeat`/`wait`/`trigger`).

## Wann verwenden

Verwende `script` immer dann, wenn eine **wiederverwendbare, explizit aufrufbare Aktionssequenz** gebraucht wird — ein benannter Block ohne eigenen Trigger, der als Service `script.<object_id>` aus Automationen, Skripten und Dashboards aufgerufen wird. Typische Anwendungsfälle:

- **Geteilte Aktionssequenz** — eine mehrstufige Abfolge (`delay`, `wait_template`, `choose`, `repeat`) einmal definieren und aus mehreren Automationen per `action: script.<object_id>` aufrufen, statt sie zu duplizieren
- **Parametrisierte Aktion** — über `fields` mit Selektoren ein öffentliches Aufruf-Schema anbieten (ein Skript, viele Aufrufer mit unterschiedlichen Werten), z. B. „benachrichtige Gerät X mit Text Y"
- **Manueller Auslöser** — eine Aktionsfolge, die per Knopfdruck im Dashboard, per Sprachbefehl oder per `script.turn_on` bewusst gestartet wird, nicht ereignisgetrieben
- **Funktion mit Rückgabewert** — einen Wert deklarativ über `response_variable`/`stop` an den Aufrufer zurückgeben, statt das Ergebnis über einen Umweg-Helfer zu transportieren
- **Feuer-und-vergiss-Ablauf** — einen langlaufenden Ablauf über `script.turn_on` asynchron starten, ohne dass der Aufrufer auf den Abschluss wartet

Ein Skript ist das richtige Werkzeug, sobald die Logik **aufgerufen** statt **ausgelöst** werden soll. Geht es um ereignisreaktives Verhalten mit Trigger, ist eine Automation richtig; für einen rein abgeleiteten Wert ein Template-Sensor (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Anatomie eines Skripts (Pflicht-`sequence`, optionale Schlüssel) verbindlich festschreiben
- Den Vertrag „parametrisiere über `fields` mit Selektoren statt über fest verdrahtete Werte" durchsetzen
- Den bewussten Umgang mit `mode`/`max` und den Aufruf-Semantiken (direkt vs. `script.turn_on`) fixieren
- Den Rückgabe-Pfad über `response_variable`/`stop` als deklarativen Weg verankern
- Klar abgrenzen, wann **kein** Skript das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Ausführungsmodell der Regel-Engine — `ha-automation/automation`
- Der vollständige Aktions-/Bedingungs-Katalog im Detail (Datenform jeder einzelnen Aktion) — die HA-Seite `/docs/scripts/`, hier nur als Vertrag referenziert
- Blueprint-Schema und `!input`-Bridge für Skript-Blueprints — `ha/blueprint-patterns`
- Die Namens-Dimension (`object_id`, `alias`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur die skript-spezifischen Variablen

## Anforderungen

### Konfiguration und Struktur

- **MUSS [MUST]** jedes Skript über den Pflicht-Schlüssel `sequence` (Liste von Aktionen) definieren; `alias`, `icon`, `description`, `variables`, `fields`, `mode`, `max`, `max_exceeded` sind optionale Ergänzungen
- **MUSS [MUST]** als `object_id` (Schlüssel unter `script:` bzw. UI-Name) einen snake_case-Slug ohne Großbuchstaben und ohne Bindestriche vergeben — die Doku verbietet Großbuchstaben und `-` ausdrücklich; den `alias` englisch und ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** `description` setzen, damit das Skript im **Actions**-Tab nachvollziehbar dokumentiert ist
- **SOLLTE [SHOULD]** `mode` bewusst wählen und nicht blind den Default `single` übernehmen; die Wahl begründen, wenn sie nicht offensichtlich ist (`single` = neuen Lauf verweigern + warnen, `restart` = laufenden Lauf abbrechen und neu starten, `queued` = nach Abschluss aller Läufe starten, `parallel` = unabhängig parallel starten)
- **MUSS [MUST]** bei `mode: parallel`/`queued` ein passendes `max` setzen, wenn die erwartete Last den Default (`10`) überschreiten kann
- **SOLLTE NICHT [SHOULD NOT]** `max_exceeded` auf `silent` setzen, ohne den Grund zu dokumentieren — der Default `warning` macht verworfene Läufe sichtbar

### Parametrisierung über `fields`

- **SOLLTE [SHOULD]** wiederverwendbare Eingaben über den `fields`-Block deklarieren statt feste Werte in die `sequence` zu verdrahten; jedes Feld trägt mindestens `name`/`description` und — wo sinnvoll — `required`, `example`, `default` und einen `selector`
- **SOLLTE [SHOULD]** jedem Feld einen passenden `selector` geben, damit der UI-Editor eine typgerechte Eingabe rendert (laut Doku steuert `selector`, „wie die Eingabe im Frontend dargestellt wird")
- **MUSS [MUST]** den Unterschied zwischen `fields` und `variables` respektieren: `fields` ist das **öffentliche, dokumentierte Aufruf-Schema** für Aufrufer (UI-Metadaten), `variables` definiert **interne** Template-Variablen innerhalb des Skripts — die beiden nicht vermischen
- **KANN [MAY]** über `variables` interne Zwischenwerte ableiten, die in nachfolgenden Aktionen per `{{ … }}` referenziert werden

### Aufruf, Rückgabe und Skript-Variablen

- **MUSS [MUST]** die beiden Aufruf-Semantiken bewusst unterscheiden: der **direkte** Aufruf `action: script.<object_id>` **wartet** auf den Abschluss (und bricht bei Fehlern ab), während `action: script.turn_on` mit `target.entity_id` das Skript **asynchron** startet und sofort weiterläuft
- **MUSS [MUST]** Variablen beim Aufruf konsistent übergeben: beim direkten Aufruf als `data:`-Schlüssel (die `fields`), bei `script.turn_on` als verschachtelter `data.variables`-Map
- **SOLLTE [SHOULD]** Rückgabewerte deklarativ über `response_variable` bzw. `stop` mit `response_variable` liefern, statt das Ergebnis über einen Umweg-Helfer (`input_*`) zu transportieren
- **KANN [MAY]** im Aktionsteil die volle Skript-Syntax nutzen (`action`-Aufrufe, `delay`, `wait_template`, `wait_for_trigger`, `choose`, `if/then/else`, `repeat` mit `count`/`while`/`until`/`for_each`, `parallel`, `stop`, `event`, `variables`); `continue_on_error` (Default `false`) und `continue_on_timeout` (Default `true`) steuern das Fehler-/Timeout-Verhalten
- **KANN [MAY]** die dokumentierten Skript-Variablen verwenden: `repeat` (`index`/`first`/`last`/`item`) in Schleifen, `wait` (`completed`/`remaining`/`trigger`) nach Wait-Aktionen sowie `trigger` — Letzteres ist **nur verfügbar, wenn das Skript innerhalb einer Automation läuft**, nicht beim manuellen Aufruf

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** ein Skript dort einsetzen, wo HA **auf ein Ereignis reagieren** soll — ein Skript hat keinen Trigger und muss aufgerufen werden; sobald die Logik durch Zustand/Zeit/Event ausgelöst werden soll, ist die **Automation** (`ha-automation/automation`) das richtige Konstrukt
- **SOLLTE NICHT [SHOULD NOT]** dieselbe Skript-Logik mehrfach mit fest verdrahteten, leicht abweichenden Werten kopieren — wenn die Sequenz parametrisierbar ist, gehören die Unterschiede in **`fields` mit Selektoren** (ein Skript, viele Aufrufer), statt in n nahezu identische Skripte
- **SOLLTE NICHT [SHOULD NOT]** ein Skript zum Berechnen/Speichern eines abgeleiteten Wertes („als Sensor") missbrauchen, indem es das Ergebnis in einen `input_number`/`input_text` schreibt — das verliert die Messquelle und ist anfällig; einen **Template-/Derivative-/Statistics-Sensor** (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`) definieren, der den Wert deklarativ ableitet
- **SOLLTE NICHT [SHOULD NOT]** identische Skript-Logik per Copy-Paste über viele Installationen oder den Community-Austausch streuen, wenn sie generisch parametrisierbar ist — dafür ist ein **Skript-Blueprint** (`ha/blueprint-patterns`) gedacht, der die Logik einmal kapselt und mit `!input`-Eingaben instanziiert
- **SOLLTE NICHT [SHOULD NOT]** den blockierenden direkten Aufruf `script.<object_id>` für ein langlaufendes Feuer-und-Vergiss-Skript verwenden, wenn der Aufrufer nicht auf den Abschluss warten soll — dann `script.turn_on` nutzen (umgekehrt: nicht `script.turn_on` einsetzen, wenn das Ergebnis bzw. ein `response_variable` benötigt wird, denn der asynchrone Start liefert keinen Rückgabewert an den Aufrufer)

## Akzeptanzkriterien

- [ ] Jedes Skript hat einen Pflicht-`sequence`-Block und eine snake_case-`object_id` ohne Großbuchstaben/Bindestriche
- [ ] Der `alias` ist englisch und ≤50 Zeichen; die Namens-Mechanik wird referenziert, nicht wiederholt
- [ ] `mode` ist bewusst gesetzt; bei `parallel`/`queued` ist ein passendes `max` vergeben; `max_exceeded: silent` nur mit Begründung
- [ ] Wiederverwendbare Eingaben sind als `fields` mit Selektoren deklariert, nicht fest verdrahtet
- [ ] `fields` (öffentliches Aufruf-Schema) und `variables` (interne Template-Variablen) sind nicht vermischt
- [ ] Die Aufruf-Semantik ist bewusst gewählt: direkter Aufruf (wartet) vs. `script.turn_on` (asynchron); Variablen werden formgerecht übergeben
- [ ] Rückgabewerte laufen über `response_variable`/`stop`, nicht über Umweg-Helfer
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: keine ereignisreaktive Logik im Skript (Automation), kein abgeleiteter Sensor-Ersatz, kein Copy-Paste wo `fields`/Blueprint greift

## Offene Fragen

- **Entitäts-Attribute**: Die Integrations-Karte `/integrations/script/` zählt die Laufzeit-Attribute der Skript-Entität (`current`, `last_triggered`, `mode`, `max`) nicht explizit auf der gelesenen Seite auf. Soll diese Spec eine eigene, an einer konkreten Doku-Stelle verankerte Regel zum Lesen von `last_triggered`/`current` aufnehmen, oder bleibt das außerhalb des Nutzungs-Scopes?
