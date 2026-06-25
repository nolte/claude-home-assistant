# HA-Automation: Group nutzen

Status: draft

## Kontext

Die `group`-Integration fasst mehrere Entitäten zu einer einzigen Gruppen-Entität zusammen, deren Zustand aus den Mitgliedern berechnet wird. Sie dient zwei Zwecken: die gemeinsame Steuerung mehrerer Entitäten (z. B. „alle Lichter aus") und das Ableiten eines zusammengefassten Zustands (z. B. „ist irgendein Fenster offen?"). Laut offizieller Doku wird die Integration von rund 31 % der aktiven HA-Installationen genutzt.

Ihre reale Einordnung ist **Helper / Organization** — sie ist eine interne, vollständig konfigurierbare Helfer-Integration, **keine** Automation. Diese Spec überführt die offizielle Nutzungs-Doku in eine Konvention dafür, welche Gruppenart das Plugin generiert und wie deren kombinierter Zustand verbindlich berechnet wird, damit nachgelagerte Trigger und Templates auf einen vorhersagbaren Zustand setzen können.

Die Integration kennt zwei Generationen: das **alte `group:`-YAML** (generische Entitäts-Gruppen unter dem Top-Level-Schlüssel `group:` in `configuration.yaml`) und die **modernen Pro-Domänen-Gruppen** (light, switch, cover, fan, lock, media_player, binary_sensor, sensor, button, event, notify — per UI-Helfer oder YAML pro Domäne angelegt). Beide werden hier abgedeckt; für neue Artefakte ist die moderne Form vorgeschrieben.

Verifizierte Quelle: [`/integrations/group/`](https://www.home-assistant.io/integrations/group/).

## Wann verwenden

Verwende `group` immer dann, wenn mehrere Entitäten derselben Domäne zu **einer Entität mit kombiniertem Zustand** zusammengefasst werden sollen — entweder zur gemeinsamen Steuerung oder als aggregierte Trigger-/Bedingungs-Grundlage. Typische Anwendungsfälle:

- **Gemeinsame Steuerung** — mehrere Lichter, Schalter oder Cover über die Gruppen-`entity_id` in einem Aufruf schalten (`homeassistant.turn_on`/`turn_off` fächert auf die Mitglieder auf), z. B. „alle Lichter aus"
- **„Irgendein Mitglied an?"** — über den ODER-Default abfragen, ob mindestens ein Fenster offen / ein Licht an ist, und den Gruppenzustand als Trigger/Bedingung nutzen
- **„Alle Mitglieder erfüllen?"** — über `all: true` UND-Semantik erzwingen (für `binary_sensor`/`light`/`switch`), z. B. „sind alle Türen verriegelt?", inklusive `unknown`/`unavailable`-Durchschlag
- **Numerische Aggregation** — eine Sensor-Gruppe mit `type` (`min`, `max`, `mean`, `median`, `sum`, `range` …) über gleichartige Sensoren bilden, mit bewusstem `ignore_non_numeric`-Verhalten
- **Domänen-Aggregation als Trigger** — die domänenspezifische Zustandsberechnung (Cover `open`, Lock-Prioritätsreihenfolge, Fan `on`) als vorhersagbare Grundlage für nachgelagerte Automationen nutzen

Eine Gruppe ist das richtige Werkzeug, sobald ein **konsumierter kombinierter Zustand** oder die **gemeinsame Steuerung** gebraucht wird. Zur reinen Raum-/Kategorie-Zuordnung sind Areas/Labels gedacht, für frei berechnete Werte ein Template-Sensor (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die Wahl zwischen altem `group:`-YAML und moderner Pro-Domänen-Gruppe verbindlich auf die moderne Form festlegen
- Die dokumentierte Zustandsberechnung (ODER per Default; UND via `all: true`) als prüfbare Konvention fixieren, damit Trigger den Gruppenzustand korrekt interpretieren
- Den `all`-Schalter bewusst und begründet setzen, statt den ODER-Default blind zu übernehmen
- Für Sensor-Gruppen den `type` (Aggregationsfunktion) und das `unknown`-Verhalten bei nicht-numerischen Mitgliedern (`ignore_non_numeric`) verbindlich machen
- Klar abgrenzen, wann **keine** Gruppe das richtige Werkzeug ist (Area/Label, min_max/statistics, Template-Sensor)

## Nicht-Ziele

- Die vollständige Trigger-/Bedingungs-/Aktions-Syntax, die eine Gruppe konsumiert — `ha-automation/automation`
- Numerische Aggregation jenseits der wenigen `type`-Funktionen (gleitende Mittel, Ableitung, Langzeit-Statistik) — `ha-automation/statistics`, `ha-automation/derivative`, `ha-automation/min-max`
- Deklarativ berechnete, frei formulierte Zustände/Attribute — `ha-automation/template`
- Die Namens-Dimension (`name`, `unique_id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Areas und Labels als reine Organisations-/Zuordnungsmechanik des Registers — sie haben keine eigene Spec-Karte und werden hier nur zur Abgrenzung genannt

## Anforderungen

### Konfiguration

- **MUSS [MUST]** für neue Artefakte eine **moderne Pro-Domänen-Gruppe** (light, switch, cover, fan, lock, media_player, binary_sensor, sensor, button, event, notify) verwenden und das alte generische `group:`-YAML nicht für Neuanlagen nutzen
- **MUSS [MUST]** in jeder Gruppe `entities` als Liste der Mitglieder angeben; `name` ist optional, `unique_id` ist optional, ermöglicht aber die UI-Anpassung — beide nach der Mechanik in `ha/naming-conventions`
- **MUSS [MUST]** Mitglieder einer Pro-Domänen-Gruppe aus **derselben Domäne** wählen (eine Light-Gruppe enthält Lichter, eine Sensor-Gruppe Sensoren), da die Zustands-/Attribut-Aggregation domänenspezifisch ist
- **SOLLTE [SHOULD]** den `all`-Schalter (verfügbar für `binary_sensor`-, `light`- und `switch`-Gruppen) bewusst setzen: Default ist `false` (ODER — `on`, wenn mindestens ein Mitglied `on` ist); `all: true` erzwingt UND-Semantik
- **MUSS [MUST]** für eine **Sensor-Gruppe** den `type` aus dem dokumentierten Katalog wählen: `min`, `max`, `last`, `first_available`, `mean`, `median`, `range`, `product`, `stdev` oder `sum`
- **SOLLTE [SHOULD]** bei Sensor-Gruppen `ignore_non_numeric` bewusst setzen: Default `false` lässt den Gruppenzustand `unknown` werden, sobald ein Mitglied keinen numerischen Zustand hat; `true` rechnet nur mit den verfügbaren numerischen Mitgliedern
- **KANN [MAY]** bei Sensor-Gruppen `unit_of_measurement` und `state_class` setzen und bei `binary_sensor`-Gruppen eine `device_class` vergeben
- **SOLLTE [SHOULD]** das alte `group:`-YAML nur dort weiterführen, wo bestehende Konfiguration es bereits nutzt, und dann `entities`, optional `name`, `icon` und `all` korrekt verwenden — `all: true` bedeutet hier, dass die Gruppe nur `on` ist, wenn **alle** Mitglieder `on` sind

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den dokumentierten kombinierten Zustand der modernen Gruppe als Trigger-/Bedingungs-Grundlage verstehen: ohne `all` ist die Gruppe `on`, wenn **mindestens ein** Mitglied `on` ist; mit `all: true` ist sie `unknown`, sobald ein Mitglied `unknown`/`unavailable` ist, `off`, sobald ein Mitglied `off` ist, sonst `on`
- **MUSS [MUST]** die domänenspezifische Aggregation berücksichtigen, wenn der Gruppenzustand als Trigger dient — etwa Cover/Valve: `open`, wenn ein Mitglied `opening`/`open` ist; Fan: `on`, wenn ein Mitglied `on` ist; Lock mit Prioritätsreihenfolge `jammed > opening > locking > open > unlocking > locked`
- **MUSS [MUST]** bei `all: true`-Gruppen die `unknown`/`unavailable`-Durchschlagsregel beim Trigger-/Bedingungs-Entwurf einkalkulieren, statt nur auf `on`/`off` zu prüfen
- **SOLLTE [SHOULD]** das Gruppen-Attribut `entity_id` (Liste aller `entity_id` der Gruppe) in Templates über `expand()` auflösen, wenn über die Mitglieder iteriert werden soll, statt die Mitgliederliste zu duplizieren
- **KANN [MAY]** eine Gruppe gemeinsam steuern, indem `homeassistant.turn_on`/`homeassistant.turn_off` auf die Gruppen-`entity_id` angewandt wird; die Aktion fächert auf die Mitglieder auf
- **SOLLTE NICHT [SHOULD NOT]** die alten-Stil-Dienste `group.set`/`group.remove`/`group.reload` für moderne Pro-Domänen-Gruppen verwenden — `group.set` und `group.remove` operieren laut Doku auf **old-style groups**; moderne Gruppen werden über UI-Helfer oder YAML pro Domäne verwaltet

### Abgrenzung: Wann NICHT verwenden

- **SOLLTE NICHT [SHOULD NOT]** eine Gruppe als reines Organisations-/Zuordnungsmittel anlegen, wenn es nur darum geht, Entitäten einem Raum oder einer Kategorie zuzuordnen — dafür sind **Areas** und **Labels** des Registers gedacht; eine Gruppe rechtfertigt sich erst durch einen **konsumierten kombinierten Zustand** oder die **gemeinsame Steuerung**
- **SOLLTE NICHT [SHOULD NOT]** das alte generische `group:`-YAML für Neuanlagen verwenden — die **modernen Pro-Domänen-Gruppen** liefern korrekte domänenspezifische Aggregation (Cover/Lock/Media-Player), den `all`-Schalter und sauberes `unavailable`-Verhalten, die die generische Gruppe nicht bietet
- **SOLLTE NICHT [SHOULD NOT]** eine Sensor-Gruppe für numerische Aggregation einsetzen, die über die fixen `type`-Funktionen hinausgeht (z. B. gewichtete Mittel, gleitendes Fenster über Zeit, Ableitung) — dafür sind **min_max**, **statistics** oder **derivative** (`ha-automation/min-max`, `ha-automation/statistics`, `ha-automation/derivative`) gedacht; die Sensor-Gruppe bietet nur die wenigen dokumentierten Aggregate
- **MUSS NICHT [MUST NOT]** eine Sensor-Gruppe als Ersatz für einen Template-Sensor missbrauchen, wenn der Wert aus mehreren Quellen frei berechnet oder mit Bedingungslogik gebildet werden muss — eine Sensor-Gruppe kann nur **eine** der festgelegten Aggregationsfunktionen über gleichartige Mitglieder anwenden; freie Formeln gehören in einen **Template-Sensor** (`ha-automation/template`)
- **SOLLTE NICHT [SHOULD NOT]** in einer Pro-Domänen-Gruppe Mitglieder fremder Domänen mischen (Licht + Schalter + Sensor in einer Gruppe), um „alles" zu erfassen — die Aggregation ist domänenspezifisch und das Ergebnis dann undefiniert; pro Domäne eine Gruppe anlegen oder per Template kombinieren
- **SOLLTE NICHT [SHOULD NOT]** sich auf den ODER-Default verlassen, wo die Absicht „alle Mitglieder erfüllen die Bedingung" ist — ohne `all: true` meldet die Gruppe schon bei einem einzigen `on`-Mitglied `on`, was eine „alles aus"-Prüfung still verfälscht

## Akzeptanzkriterien

- [ ] Neue Gruppen sind moderne Pro-Domänen-Gruppen; das alte `group:`-YAML wird nicht für Neuanlagen verwendet
- [ ] Jede Gruppe deklariert `entities`; `name`/`unique_id` folgen `ha/naming-conventions`
- [ ] Mitglieder stammen aus derselben Domäne wie die Gruppe
- [ ] Der `all`-Schalter ist bewusst gesetzt (ODER-Default vs. UND via `all: true`), passend zur Trigger-Absicht
- [ ] Sensor-Gruppen tragen einen dokumentierten `type`; `ignore_non_numeric` ist bewusst gesetzt
- [ ] Trigger/Bedingungen berücksichtigen die dokumentierte Zustandsberechnung inkl. `unknown`/`unavailable`-Durchschlag bei `all: true`
- [ ] Über Mitglieder wird per `expand()` auf das `entity_id`-Attribut iteriert statt per Duplikat-Liste
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: keine Gruppe, wo Area/Label, min_max/statistics/derivative oder ein Template-Sensor das richtige Werkzeug ist
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Sensor-Gruppe vs. statistics-Sensor bei `range`**: Die Sensor-Gruppe bietet `range` (Spanne über die aktuellen Mitglieder), `statistics` liefert zeitbasierte Spannen. Die Trennlinie „gleichzeitige Mitglieder vs. Zeitfenster" ist hier benannt, aber nicht mit einer eigenen Regel verankert — soll diese Spec eine explizite `range`-Abgrenzungsregel führen oder genügt der Verweis auf `ha-automation/statistics`?
