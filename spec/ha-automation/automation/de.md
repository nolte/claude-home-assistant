# HA-Automation: Automation nutzen

Status: draft

## Kontext

Die `automation`-Domäne ist die Regel-Engine von Home Assistant: Sie lässt HA „automatisch auf Dinge reagieren, die passieren" — etwa das Licht bei Sonnenuntergang einschalten. Eine Automation besteht aus drei Konzepten: **Triggern** (was sie startet), **Bedingungen** (optionales Gate) und **Aktionen** (was läuft). Sie wird über den visuellen Editor oder als YAML verfasst; die offizielle Doku empfiehlt, mit Blueprints zu beginnen.

Anders als Helfer-Integrationen hat die Automation **keine Integrations-Karte** im Katalog — sie ist unter [`/docs/automation/`](https://www.home-assistant.io/docs/automation/) dokumentiert, nicht unter `/integrations/`. Ihre reale Einordnung ist eine **Kern-Konfigurationsdomäne**, kein verbindbares Gerät/Dienst. Diese Spec überführt die offizielle Nutzungs-Doku in eine verbindliche Konvention für die vom Plugin erzeugten Automationen und ist die Wurzel-Spec des `ha-automation`-Korpus: Sie definiert das Trigger/Bedingung/Aktion-Modell, auf das die Helfer- und Sensor-Specs verweisen.

Verifizierte Quellen: `/docs/automation/` (+ `basics`, `trigger`, `condition`, `action`, `modes`, `templating`, `yaml`), die Aktions-/Bedingungs-Kataloge unter `/docs/scripts/` (auf die die Automation-Doku verweist) sowie der Release-Blog 2024.10 für die Schlüssel-Umbenennung.

## Wann verwenden

Verwende `automation` immer dann, wenn Home Assistant **ereignisgetrieben auf eine Zustandsänderung oder ein Ereignis reagieren** soll, ohne dass jemand manuell auslöst. Eine Automation verbindet einen Auslöser mit einer Aktion und ist der Standard-Baustein für reaktives Verhalten. Typische Anwendungsfälle:

- **Reaktion auf Sensoren** — Licht bei Bewegung einschalten, Benachrichtigung bei offener Tür oder Wasserleck, Rollladen je nach Sonnenstand
- **Zeit-/Sonnenstand-gesteuert** — Aktionen zu einer Uhrzeit, bei Sonnenauf-/-untergang (mit Offset) oder nach einem Zeitplan auslösen
- **Anwesenheits-/Zonen-Logik** — Heizung, Licht oder Szenen abhängig von An-/Abwesenheit und Zonen-Ein-/-Austritt schalten
- **Schwellwert-Überwachung** — bei Über-/Unterschreiten eines Messwerts (`numeric_state`) handeln, optional mit Haltezeit
- **Ereignis-Bridge** — auf MQTT-Nachrichten, Webhooks, NFC-Tags, Kalender-Ereignisse oder benutzerdefinierte Events reagieren

Eine Automation ist das richtige Werkzeug, sobald ein **Trigger** den Ablauf starten soll. Geht es um eine manuell oder mehrfach aufrufbare Aktionsfolge ohne Auslöser, ist ein Skript richtig; für rein abgeleitete Werte ein Template-/Helfer-Sensor (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Anatomie einer Automation (Top-Level-Schlüssel, Plural-Syntax) verbindlich festschreiben
- Das Trigger-/Bedingungs-/Aktions-Modell und die Ausführungsmodi als Grundlage für hochwertige Automationen fixieren
- Den bewussten, dokumentierten Umgang mit `mode`/`max` erzwingen, statt Defaults blind zu übernehmen
- Die dokumentierten Fallstricke (Race-Condition Trigger↔Bedingung, `for` übersteht keinen Neustart, stilles Verwerfen von Läufen) in prüfbare Regeln gießen
- Klar abgrenzen, wann **keine** Automation das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Die vollständigen Aktions-/Bedingungs-Kataloge im Detail — diese liegen in `ha-automation/script` (Skript-Syntax), auf die HA selbst verweist
- Blueprint-Schema, Selektoren und der Templating-Bridge — `ha/blueprint-patterns`
- Geräte-zentrierte Trigger/Bedingungen/Aktionen (Backend-Vertrag) — `ha/device-automations`
- Die Namens-Dimension (`alias`, `id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur die Automation-spezifischen Variablen

## Anforderungen

### Konfiguration und Struktur

- **MUSS [MUST]** eine YAML-Automation über die Top-Level-Schlüssel `id`, `alias`, `triggers`, `actions` und — sofern ein Gate nötig ist — `conditions` strukturieren; `description`, `mode`, `max`, `max_exceeded`, `variables`, `trigger_variables`, `initial_state`, `trace` sind optionale Ergänzungen
- **MUSS [MUST]** die **Plural-Schlüssel** `triggers`/`conditions`/`actions` und in Listenelementen `trigger:`/`condition:` verwenden (seit 2024.10 die aktuelle Syntax); die alte Singular-/`platform:`-Form ist nicht-breaking, aber neue Artefakte verwenden sie nicht
- **MUSS [MUST]** für jede generierte Automation eine stabile `id` als snake_case-Slug vergeben (nicht den volatilen UI-Zeitstempel) und den `alias` englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** `mode` bewusst wählen und nicht blind den Default `single` übernehmen; die Wahl im `description`-Feld oder einem Kommentar begründen, wenn sie nicht offensichtlich ist
- **MUSS [MUST]** bei `mode: parallel`/`queued` ein passendes `max` setzen, wenn die erwartete Last den Default (`10`; `1` bei `single`) überschreiten kann
- **SOLLTE NICHT [SHOULD NOT]** `max_exceeded: silent` setzen, ohne den Grund zu dokumentieren — es verdeckt, dass Läufe verworfen werden

### Trigger, Bedingungen, Aktionen und Ausführungsmodi

- **MUSS [MUST]** mindestens einen Trigger aus dem dokumentierten Katalog verwenden (`state`, `numeric_state`, `time`, `time_pattern`, `template`, `event`, `mqtt`, `sun`, `zone`, `geo_location`, `calendar`, `tag`, `webhook`, `homeassistant`, `persistent_notification`, `conversation`, Geräte-Trigger); mehrere Trigger sind ODER-verknüpft
- **SOLLTE [SHOULD]** ereignisgetriebene Trigger (`state`, `event`, `mqtt`) gegenüber pollenden `time_pattern`-Schleifen bevorzugen, wenn der Zustandswechsel ein Event auslöst
- **MUSS [MUST]** beachten, dass die `for`-Option eines Triggers **keinen Neustart und kein Reload** übersteht (dokumentierte Einschränkung) — zeitkritische Halte-Logik darf sich nicht allein darauf verlassen
- **MUSS [MUST]** Bedingungen (UND-verknüpft per Default; `and`/`or`/`not` zum Gruppieren) nur als Gate nutzen und die **Race-Condition** zwischen Trigger und Bedingung berücksichtigen: Bedingungen sehen nur den aktuellen Zustand, nicht das bereits eingetretene Ereignis
- **SOLLTE [SHOULD]** Trigger über `id` benennen und im Aktionsteil per `trigger`-Bedingung oder `choose`/`if` darauf verzweigen, statt mehrere fast gleiche Automationen zu pflegen
- **KANN [MAY]** im Aktionsteil die volle Skript-Syntax nutzen (`action`-Aufrufe, `delay`, `wait_template`, `wait_for_trigger`, `choose`, `if/then/else`, `repeat`, `parallel`, `stop`, `variables`, `response_variable`) — Detailvertrag in `ha-automation/script`
- **KANN [MAY]** in Templates die Variablen `this` (eigenes Zustandsobjekt), `trigger` (auslösendes Objekt, u. a. `trigger.platform`/`.id`/`.entity_id`/`.to_state`/`.from_state`) und `trigger_variables` verwenden

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** eine Automation für eine wiederverwendbare Aktionssequenz verwenden, die mehrfach oder manuell aufgerufen werden soll — dafür ist ein **Skript** (`ha-automation/script`) das richtige Konstrukt, weil es einen aufrufbaren Service exponiert und in mehreren Automationen referenzierbar ist
- **SOLLTE NICHT [SHOULD NOT]** eine Automation dazu verwenden, einen abgeleiteten/berechneten Wert in einen `input_number`/`input_text` zu schreiben, um ihn „als Sensor" zu speichern — das ist anfällig und verliert die Messquelle; stattdessen einen **Template-/Derivative-/Statistics-Sensor** (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`) definieren, der den Wert deklarativ ableitet
- **SOLLTE NICHT [SHOULD NOT]** wiederkehrende Logik per Copy-Paste über viele Automationen streuen, wenn sie parametrisierbar ist — dafür ist ein **Blueprint** (`ha/blueprint-patterns`) gedacht, der die Logik einmal kapselt und mehrfach instanziiert
- **SOLLTE NICHT [SHOULD NOT]** eine `time_pattern`-Pollingschleife einsetzen, wo ein Event-/State-Trigger denselben Zweck erfüllt — Polling erzeugt unnötige Last und reagiert verzögert
- **MUSS NICHT [MUST NOT]** Bedingungen als Ersatz für präzise Trigger missbrauchen (z. B. breiter Trigger + nachgelagerte Bedingung), wenn ein gezielter Trigger die Race-Condition von vornherein vermeidet
- **SOLLTE NICHT [SHOULD NOT]** geräte-zentrierte Trigger/Bedingungen/Aktionen aus dem UI-Editor in generiertem YAML bevorzugen, wenn ein entitäts-/zustandsbasierter Trigger portabler und installations­unabhängig ist (Hintergrund: `ha/device-automations`)

## Akzeptanzkriterien

- [ ] Jede generierte Automation nutzt die Plural-Syntax (`triggers`/`conditions`/`actions`, `trigger:`/`condition:` in Listen)
- [ ] Jede Automation trägt eine stabile snake_case-`id` und einen englischen `alias` ≤50 Zeichen
- [ ] `mode` ist bewusst gesetzt; bei `parallel`/`queued` ist ein passendes `max` vergeben
- [ ] `max_exceeded: silent` kommt nur mit dokumentierter Begründung vor
- [ ] Mindestens ein Trigger stammt aus dem dokumentierten Katalog; Event-Trigger werden gegenüber Polling bevorzugt
- [ ] Keine zeitkritische Logik verlässt sich allein auf die `for`-Option (Neustart-/Reload-Verlust berücksichtigt)
- [ ] Bedingungen sind als Gate eingesetzt und die Trigger↔Bedingung-Race-Condition ist berücksichtigt
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: keine Automation, wo Skript, Template-/Derivative-Sensor oder Blueprint das richtige Werkzeug ist
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Unavailable-/unknown-Handling**: Eine querschnittliche Regel zum Abfangen von `unavailable`/`unknown`-Zuständen in Trigger-/Bedingungs-Templates ist auf den acht Automation-Doc-Seiten nicht als eigene Warnung verankert (sie lebt in der Templating-/Blueprint-Doku). Soll diese Spec eine eigene, dort verankerte Guard-Regel aufnehmen oder auf eine künftige `ha-automation/template`-Regel verweisen?
