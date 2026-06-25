# Skill: `ha-helper-scaffold`

Status: draft

## Kontext

Home Assistant kennt eine Familie zustandsbehafteter Helfer-Entities, die rein in YAML (oder per UI) konfiguriert werden: `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer` und `schedule`. Sie halten manuell oder per Automation gesetzten Zustand und sind die Bausteine, mit denen Automationen Modus-Schalter, Schwellen, Zeitfenster, Countdowns und Zähler ausdrücken. Der `ha-automation/`-Korpus beschreibt pro Helfer die korrekte Nutzung, aber bisher gibt es keinen Skill, der sie scaffoldet. In der Praxis greifen Nutzer zum falschen Helfer (ein `input_boolean` für einen Einmal-Druck statt `input_button`, ein `input_number` für eine gemessene Größe statt eines Sensors), lassen Pflichtfelder weg (`min`/`max` bei `input_number`, `options` bei `input_select`, `has_date`/`has_time` bei `input_datetime`) oder vergessen `restore: true` beim `timer`.

Dieser Skill scaffoldet **einen** Zustands-Helfer aus einer beschriebenen Absicht als spec-konformen YAML-Block, wählt den richtigen Helfer-Typ (und lenkt auf den richtigen um, wenn die Absicht einen anderen verlangt) und liefert einen Konformitäts-Bericht.

## Scope

Generierung genau eines Helfer-Blocks pro Lauf aus der Zustands-Helfer-Familie: `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, `schedule`. Der Skill bestimmt den Helfer-Typ (oder fragt nach), liest die zuständige `ha-automation/<topic>`-Spec und schreibt den Block unter den passenden Top-Level-Schlüssel in `configuration.yaml` (oder ein `packages/`-File).

## Ziele

- Aus einer Prosa-Absicht den richtigen Zustands-Helfer wählen und als spec-konformen YAML-Block scaffolden
- Pro Helfer alle Pflichtfelder setzen (`min`/`max`, `options`, `has_date`/`has_time`, `duration`, Wochenfenster) und sinnvolle Defaults für optionale Felder
- Die Helfer scharf gegeneinander abgrenzen: gemessene vs. gesetzte Werte, Einmal-Druck vs. persistenter Zustand, Countdown vs. Wochenplan
- `object_id`/Alias nach `ha/naming-conventions` benennen (snake_case, englische Anzeigenamen ≤ 50 Zeichen)
- Die Zustands-/Event-/Service-Oberfläche jedes Helfers im Output benennen, damit Automationen wissen, wie sie ihn lesen und mutieren

## Nicht-Ziele

- Automationen, Scripts, Scenes, Template-Entities oder Command-Integrationen — das ist `ha-automation-author`
- Abgeleitete/statistische Helfer-Sensoren (`bayesian`, `derivative`, … `utility_meter`, `group`) — das ist `ha-template-sensor-author`
- Echte Sensoren/Aktoren aus einer Integration — gemessene Werte gehören in eine Integration, nicht in einen Input-Helfer
- Blueprints — `ha-blueprint-scaffold`
- Deployment in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add an input_number / input_select / input_boolean helper for …"
  - „create a timer / counter / schedule for …"
  - „I need a helper to hold / toggle / count / schedule …"
  - „lege einen Helfer für … an", „erstelle einen Timer / Zähler / Wochenplan für …"

### Eingaben

- **MUSS [MUST]** erfassen: `intent` (Prosa, was der Helfer halten/tun soll)
- **KANN [MAY]** erfassen: `helper_type` (`input_boolean` / `input_button` / `input_datetime` / `input_number` / `input_select` / `input_text` / `counter` / `timer` / `schedule`); fehlt er, leitet der Skill ihn aus der Absicht ab und bestätigt ihn
- **KANN [MAY]** erfassen: `object_id`, `target_dir`, `target_file` (Default `configuration.yaml`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** `intent` als nichtleer prüfen
- **MUSS [MUST]** den Helfer-Typ auflösen und gegen die Abgrenzungs-Regeln prüfen: zielt die Absicht auf einen gemessenen Wert (→ Sensor/Integration), einen abgeleiteten Wert (→ Template-/Statistik-Sensor) oder ein Verhalten, das ein anderer Helfer besser trägt, **MUSS [MUST]** der Skill umlenken statt den falschen Helfer zu scaffolden
- **MUSS [MUST]** die zuständige `ha-automation/<topic>`-Spec lesen
- **MUSS NICHT [MUST NOT]** einen bestehenden Helfer mit gleicher `object_id` überschreiben

### Scaffold-Regeln (pro Helfer, aus der jeweiligen Spec)

- **MUSS [MUST]** für `input_number` `min` und `max` setzen, `mode` (`slider`/`box`) und `step` bewusst wählen
- **MUSS [MUST]** für `input_select` eine nichtleere `options`-Liste setzen
- **MUSS [MUST]** für `input_datetime` mindestens eines von `has_date`/`has_time` setzen
- **MUSS [MUST]** für `input_text` `max` ≤ 255 halten (HA-State-Limit) und für Secrets nicht missbrauchen (Klartext in State/History/API)
- **MUSS [MUST]** für `timer` `restore: true` setzen, wenn der Timer einen Neustart überleben soll, und im Bericht auf das Verhalten bei während-Downtime-abgelaufenen Timern hinweisen
- **MUSS [MUST]** für `schedule` pro genutztem Wochentag eine `from`/`to`-Fenster-Liste setzen
- **MUSS [MUST]** für `counter` `initial`/`step`/`minimum`/`maximum`/`restore` bewusst belegen (Integer-only)
- **MUSS [MUST]** `initial` nur setzen, wenn ein fixer Startwert gewünscht ist; sonst die Restore-Semantik dokumentieren (ein gesetztes `initial` überschreibt die Wiederherstellung bei jedem Start)
- **MUSS [MUST]** alle Bezeichner nach `ha/naming-conventions` benennen
- **MUSS [MUST]** HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Bericht

- **MUSS [MUST]** den geschriebenen Block, den Datei-Pfad und jeden Default nennen
- **MUSS [MUST]** die Lese-/Mutations-Oberfläche des Helfers angeben: relevanter Zustand/Attribute, Trigger-Events (z. B. `timer.finished`, `counter.maximum_reached`, `schedule.turned_on`) und mutierende Services (z. B. `input_number.set_value`, `counter.increment`)
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien der zuständigen Spec liefern

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als einen Helfer pro Lauf scaffolden
- **MUSS NICHT [MUST NOT]** einen Input-Helfer für einen gemessenen oder abgeleiteten Wert vorschlagen
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet den Helfer-Typ ab (oder erfragt ihn) und bestätigt ihn
- [ ] Skill liest die zuständige `ha-automation/<topic>`-Spec vor dem Scaffold
- [ ] Jeder Helfer trägt seine Pflichtfelder (`min`/`max`, `options`, `has_date`/`has_time`, `duration`/Fenster)
- [ ] `timer` mit Neustart-Anforderung trägt `restore: true`
- [ ] Eine auf einen gemessenen/abgeleiteten Wert zielende Absicht wird auf Sensor/Template/Statistik umgelenkt
- [ ] Bericht nennt Zustand, Trigger-Events und mutierende Services des Helfers
- [ ] Skill liefert einen CONFORMANT / NEEDS-WORK-Bericht mit Datei-Pfad und Defaults

## Offene Fragen

- **UI- vs. YAML-Helfer**: HA erlaubt dieselben Helfer auch per UI (Settings → Devices & Services → Helpers). Soll der Skill nur YAML scaffolden oder auch den UI-Weg dokumentieren? Aktuell YAML-only.
- **Bündelung mit Konsument**: Soll der Skill den Helfer optional zusammen mit der Automation, die ihn nutzt, in ein `packages/<name>.yaml` schreiben? Aktuell ein Helfer pro Lauf, Bündelung über `ha-automation-author`.
- **`restore`-Default**: `timer` defaultet auf `restore: false`, `counter` auf `true`. Soll der Skill `timer.restore: true` aktiv vorschlagen, wenn die Absicht Persistenz nahelegt? Aktuell ja (MUSS bei Neustart-Anforderung).
