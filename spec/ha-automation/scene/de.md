# HA-Automation: Scene nutzen

Status: draft

## Kontext

Die `scene`-Integration bündelt einen Satz von Entitäten in einem benannten **Ziel-Zustand**: „A scene captures the states you want certain entities to be in." Beim Aktivieren setzt HA alle in der Szene aufgeführten Entitäten auf die definierten States und Attribute — etwa „Romantisch" = Deckenlicht gedimmt, TV-Hintergrundlicht an. Eine Szene beschreibt also ausschließlich einen statischen Soll-Zustand, keine Abfolge und keine Logik.

Ihre **reale Kategorie** ist laut Integrations-Karte **„Organization"**, nicht Automation — die Szene ist ein Organisations-Baustein, der in Automationen, Skripten und Dashboards *referenziert* wird. Diese Spec ordnet sie dem `ha-automation`-Korpus zu, weil sie aus Sicht der Automations-Autorin ein Aktions-Ziel ist (`scene.turn_on`), nicht weil HA sie unter Automation einsortiert. Das wird hier ehrlich offengelegt.

Eine Szene-Entität ist **zustandslos** im üblichen Sinn: Ihr State ist „the timestamp of when it was last called, either via the Home Assistant UI or via an action." Mögliche Werte sind dieser Zeitstempel sowie `unavailable`/`unknown`. Es gibt bewusst **kein** `scene.turn_off`.

Verifizierte Quellen: [`/integrations/scene/`](https://www.home-assistant.io/integrations/scene/) (YAML-Schema, Dienste `scene.turn_on`/`apply`/`create`/`delete`/`reload`, `snapshot_entities`, State = Zeitstempel der letzten Aktivierung, Kategorie „Organization", Trigger `scene.activated`) und [`/docs/scene/`](https://www.home-assistant.io/docs/scene/) (Szene-Definition, `transition`, `scene.apply` inline).

## Wann verwenden

Verwende `scene` immer dann, wenn ein **benannter statischer Ziel-Zustand** für einen Satz von Entitäten festgelegt und per `scene.turn_on` aktiviert werden soll — ohne Abfolge, Logik oder berechnete Werte. Typische Anwendungsfälle:

- **Stimmungs-/Modus-Voreinstellung** — „Romantisch", „Filmabend", „Aufwachen" als festen Soll-Zustand mehrerer Lichter (gedimmt, Farbe, an/aus) definieren und auf Knopfdruck oder aus einer Automation aktivieren
- **Mehrere Entitäten gleichzeitig setzen** — eine Sammlung von Lichtern, Schaltern und Medien in einem Schritt auf definierte States und Attribute (`brightness`, `color_mode`, `xy_color`) bringen
- **Weicher Lichtwechsel** — bei `scene.turn_on` eine `transition` (Sekunden) für fähige Licht-Entitäten angeben, damit der Zustand sanft statt hart gesetzt wird
- **Einmaliger Inline-Zustand** — mit `scene.apply` einen Soll-Zustand direkt anwenden, ohne ihn vorher als Szene zu definieren (für nicht wiederverwendete Zustände)
- **Save/Restore** — vor einem Eingriff per `scene.create` mit `snapshot_entities` schnappschießen und danach per `scene.turn_on` auf den Schnappschuss zurücksetzen (kurzlebig, übersteht keinen Reload)

Eine Szene ist das richtige Werkzeug, sobald es um einen **absoluten, statischen Soll-Zustand** geht. Sobald Reihenfolge, Zeit oder Logik ins Spiel kommt, ist ein Skript richtig; zum Bündeln mehrerer Entitäten unter einem gemeinsamen Zustand eine Gruppe (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Das YAML-Schema einer Szene (`scene:`-Liste mit `name`, `entities`, optional `icon`) verbindlich festschreiben
- Die zwei Formen der Entitäts-State-Angabe (direkter State vs. State + Attribute) fixieren
- Den korrekten Einsatz von `scene.turn_on` (inkl. `transition`), `scene.apply` (inline States) und `scene.create` (Snapshot-Szenen, `snapshot_entities`) regeln
- Die dokumentierten Eigenschaften (kein `scene.turn_off`, `transition` nur bei Lichtern, `scene.create` übersteht keinen Reload, State = Zeitstempel) in prüfbare Regeln gießen
- Klar abgrenzen, wann **keine** Szene das richtige Werkzeug ist (Skript, Gruppe, Toggle, dynamische Werte)

## Nicht-Ziele

- Aktions-/Ablauf-Syntax (Sequenz, `delay`, `choose`, `repeat`) — `ha-automation/script`
- Das Trigger/Bedingung/Aktion-Modell, das Szenen aufruft — `ha-automation/automation`
- Gruppen-Semantik (eine Entität aus mehreren) — `ha-automation/group`
- Berechnete/abgeleitete Zustandswerte — `ha-automation/template`
- Die Namens-Dimension (`name`/`id`, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration

- **MUSS [MUST]** eine statische Szene über den Top-Level-Schlüssel `scene:` als **Liste** definieren; jeder Eintrag trägt `name` und `entities`, optional `icon`
- **MUSS [MUST]** unter `entities` jede Entität auf ihren Soll-State abbilden — entweder als **direkter State** (`light.tv_back_light: "on"`) oder als **State + Attribute** über den verschachtelten `state:`-Schlüssel plus Attribut-Schlüssel (`brightness`, `color_mode`, `xy_color` usw.)
- **MUSS [MUST]** Attribut-Schlüssel nur unter der verschachtelten Form verwenden; ein direkter Skalar-Wert setzt ausschließlich den State, keine Attribute
- **SOLLTE [SHOULD]** den `name` englisch und ≤50 Zeichen halten und keinen volatilen UI-Zeitstempel als Identität verwenden (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** nach Änderungen an der YAML-Konfiguration `scene.reload` aufrufen, statt HA neu zu starten
- **MUSS [MUST]** sich bewusst sein, dass die Szene **nur die aufgeführten Entitäten** setzt; nicht gelistete Entitäten bleiben unangetastet (eine Szene ist additiv, nicht exklusiv)

### Nutzung in Automationen & Templates

- **MUSS [MUST]** eine vordefinierte Szene über die Aktion `scene.turn_on` mit `target: { entity_id: scene.<id> }` aktivieren; es existiert **kein** `scene.turn_off` — eine Szene wird nicht „ausgeschaltet"
- **KANN [MAY]** bei `scene.turn_on` eine `transition` (Sekunden) angeben; laut Doku unterstützen `transition` **nur Lichter**, und auch nur, wenn die Lampe es kann
- **KANN [MAY]** mit `scene.apply` einen Soll-Zustand **inline** anwenden, ohne ihn vorher als Szene zu definieren (`data.entities` im selben Format wie die Konfiguration, optional `transition`) — sinnvoll für einmalige, nicht wiederverwendete Zustände
- **KANN [MAY]** mit `scene.create` zur Laufzeit eine Szene erzeugen; `scene_id` ist Pflicht (lowercase, Unterstriche), und es MUSS mindestens eines von `entities` (explizite Soll-States) oder `snapshot_entities` (aktueller State der genannten Entitäten zum Erzeugungszeitpunkt) angegeben werden — beide sind kombinierbar
- **MUSS [MUST]** beachten, dass per `scene.create` erzeugte Szenen **nicht persistent** sind: „This scene will be discarded after reloading the configuration" — sie überstehen weder Neustart noch `scene.reload`; gleicher `scene_id` überschreibt eine vorhandene erzeugte Szene
- **KANN [MAY]** das klassische Save/Restore-Muster nutzen: vor einem Eingriff per `scene.create` mit `snapshot_entities` schnappschießen und nach dem Eingriff per `scene.turn_on` auf den Schnappschuss zurücksetzen; per `scene.delete` lässt sich eine erzeugte Szene wieder entfernen
- **KANN [MAY]** auf den Szene-State lesend zugreifen — er ist der **Zeitstempel der letzten Aktivierung**, nicht „on/off"; und auf den Trigger `scene.activated` reagieren, wenn eine Aktion beim Aktivieren einer Szene laufen soll

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** eine Szene für eine **Abfolge** mit Schritten, Wartezeiten oder Verzweigung verwenden — eine Szene setzt nur einen statischen Ziel-Zustand und kennt weder `delay`/`wait_template` noch `choose`/`repeat`; sobald Reihenfolge, Zeit oder Logik ins Spiel kommt, ist ein **Skript** (`ha-automation/script`) das richtige Konstrukt
- **MUSS NICHT [MUST NOT]** eine Szene zum **Umschalten/Toggeln** missbrauchen — eine Szene setzt einen **absoluten** Soll-Zustand und kennt kein Gegenstück (es gibt kein `scene.turn_off`); für „an↔aus je nach aktuellem Zustand" gehört `homeassistant.toggle`/`light.toggle` bzw. eine `choose`-Verzweigung in eine Automation/ein Skript
- **SOLLTE NICHT [SHOULD NOT]** eine Szene für **dynamische oder berechnete** Werte einsetzen (z. B. „Helligkeit = Außenhelligkeit × Faktor") — die `entities`-States sind statisch und werden zur Definitionszeit festgelegt; abgeleitete Zielwerte gehören in ein **Template**/Skript (`ha-automation/template`, `ha-automation/script`), das den Wert zur Laufzeit berechnet
- **SOLLTE NICHT [SHOULD NOT]** eine Szene als **Gruppe** zweckentfremden, um mehrere Entitäten unter einem Namen zusammenzufassen — eine Szene *setzt* States, sie *aggregiert* keinen gemeinsamen State und liefert keine gemeinsame Steuer-Entität; zum Bündeln gehört eine **Gruppe** (`ha-automation/group`)
- **SOLLTE NICHT [SHOULD NOT]** sich darauf verlassen, dass eine per `scene.create` erzeugte Snapshot-Szene einen Neustart oder `scene.reload` übersteht — für persistente Szenen die YAML-/UI-Definition nutzen; `scene.create` ist nur für kurzlebiges Save/Restore innerhalb eines Laufs gedacht
- **SOLLTE NICHT [SHOULD NOT]** `transition` bei `scene.turn_on` für Nicht-Licht-Entitäten erwarten — laut Doku unterstützen nur Lichter (und nur fähige) den weichen Übergang; bei anderen Domänen wird der State hart gesetzt

## Akzeptanzkriterien

- [ ] Jede statische Szene ist unter `scene:` als Listeneintrag mit `name` und `entities` definiert
- [ ] Entitäts-States nutzen entweder die direkte Form oder die verschachtelte `state:`+Attribut-Form; Attribute stehen nie an einem Skalar-Wert
- [ ] Aktiviert wird ausschließlich über `scene.turn_on` (kein `scene.turn_off` angenommen)
- [ ] `transition` wird nur für Licht-Entitäten gesetzt
- [ ] `scene.create` nutzt `scene_id` plus mindestens `entities` oder `snapshot_entities`; die Nicht-Persistenz ist berücksichtigt
- [ ] Snapshot-/Restore-Muster verlässt sich nicht auf einen Reload-überlebenden Schnappschuss
- [ ] Der Szene-State wird als Zeitstempel der letzten Aktivierung (nicht on/off) gelesen
- [ ] Die „Wann NICHT verwenden"-Abgrenzung ist eingehalten: keine Szene für Abläufe (→ Skript), Toggle, dynamische Werte oder als Gruppe
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
