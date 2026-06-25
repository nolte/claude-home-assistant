# Skill: `ha-automation-author`

Status: draft

## Kontext

Der `ha-automation/`-Spec-Korpus beschreibt, wie die YAML-basierten Automations-Bausteine von Home Assistant *genutzt* werden — `automation`, `script`, `scene`, die `template`-Integration (generische Jinja-Entities), die Command-Escape-Hatches `rest_command` / `shell_command` / `python_script` sowie der Anti-Pattern-Leitfaden `legacy-trigger-helpers`. Bisher gibt es keinen Skill, der diese Specs operationalisiert: Nutzer schreiben Automationen frei Hand und stolpern über die immer gleichen Fehler — falscher `mode`, fehlende stabile `id`/`unique_id`, ungeschützte Templates an `unavailable`-Quellen, Shell-Injection in `shell_command`, `import` im Sandbox-`python_script`, oder sie greifen zu Legacy-Helfern, die nicht UI-editierbar und nicht teilbar sind.

Dieser Skill autoriert **ein** Automations-Artefakt aus einer beschriebenen Absicht als spec-konformes YAML (bzw. `.py` für `python_script`), validiert es offline und liefert einen Konformitäts-Bericht. Er ist die Nicht-Blueprint-Schwester des `ha-blueprint-author`-Agents: Blueprints parametrisieren eine Automation zum Teilen; dieser Skill schreibt die konkrete, instanzierte Automation für die eigene HA-Instanz.

## Scope

Generierung genau eines Artefakts pro Lauf aus dem Logik-/Command-Teil von `ha-automation/`: eine `automation`, ein `script`, eine `scene`, eine `template`-Integrations-Entity (Jinja-`sensor`/`binary_sensor`/Aktor), oder ein `rest_command` / `shell_command` / `python_script`. Der Skill bestimmt den Artefakt-Typ (oder fragt nach), liest die zuständige `ha-automation/<topic>`-Spec, schreibt das Artefakt an die richtige Stelle (`automations.yaml`, `scripts.yaml`, `scenes.yaml`, ein `packages/`-File, `configuration.yaml`, oder `python_scripts/<name>.py`) und validiert.

## Ziele

- Aus einer Prosa-Absicht ein einzelnes, spec-konformes Automations-Artefakt erzeugen, das jede MUSS-Regel der zuständigen `ha-automation/<topic>`-Spec erfüllt
- Den Artefakt-Typ bewusst wählen (Automation vs. Script vs. Scene vs. Template-Entity vs. Command) und die Wahl im Output begründen — die Specs grenzen diese Typen scharf gegeneinander ab
- Die typischen Anti-Patterns aktiv verhindern: blind `mode: single`, fehlende `id`/`unique_id`, ungeschützte Templates, Shell-Injection, `import` im `python_script`, Legacy-Trigger-Helfer
- Templates gegen `unavailable`/`unknown` absichern (`has_value()`, `is_number()`, `float(default)`, `availability`)
- Das Artefakt offline validieren und einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien der Spec liefern

## Nicht-Ziele

- Parametrisierte, teilbare Blueprints — das ist `ha-blueprint-scaffold` / `ha-blueprint-author`
- Zustands-Helfer (`input_*`, `counter`, `timer`, `schedule`) — das ist `ha-helper-scaffold`
- Abgeleitete/statistische Helfer-Sensoren (`bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration`, `utility_meter`, `group`) — das ist `ha-derived-sensor-author`
- Python-Custom-Integrationen — das ist `ha-integration-scaffold`
- Deployment in eine laufende HA-Instanz — Generierung only; Deploy ist `ha-integration-deploy` / manuell
- Migration einer bestehenden Automation in einen Blueprint — `ha-blueprint-scaffold`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „write an automation that …", „create a script for …", „add a scene for …"
  - „make a template sensor that …" (generische Jinja-Entity, kein Statistik-Helfer)
  - „add a rest_command / shell_command / python_script for …"
  - „schreibe eine Automation, die …", „erstelle ein Script für …", „lege eine Szene für … an"

### Eingaben

- **MUSS [MUST]** erfassen: `intent` (Prosa, was das Artefakt tun soll) — ohne Absicht kein Lauf
- **KANN [MAY]** erfassen: `artifact_type` (`automation` / `script` / `scene` / `template` / `rest_command` / `shell_command` / `python_script`); fehlt er, leitet der Skill ihn aus der Absicht ab und bestätigt ihn
- **KANN [MAY]** erfassen: `target_dir` (Repo-/Config-Root; Default Arbeitsverzeichnis) und `target_file` (Default je Typ: `automations.yaml` / `scripts.yaml` / `scenes.yaml` / `configuration.yaml` / `python_scripts/<name>.py`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** `intent` als nichtleer prüfen; sonst nachfragen statt generieren
- **MUSS [MUST]** den Artefakt-Typ auflösen und gegen die `legacy-trigger-helpers`-Spec prüfen: zielt die Absicht auf einen Legacy-Helfer (`flux`, `device_sun_light_trigger`, hand-gebaute `platform:`-Trigger-Helfer), **MUSS [MUST]** der Skill die moderne Alternative vorschlagen statt den Legacy-Weg zu generieren
- **MUSS [MUST]** die zuständige `ha-automation/<topic>`-Spec lesen, bevor er generiert
- **MUSS NICHT [MUST NOT]** eine bestehende Ziel-Entity überschreiben; bei Kollision auf `id`/`unique_id`/`object_id` mit zitiertem Bezeichner abbrechen

### Generierungs-Regeln (pro Typ, aus der jeweiligen Spec)

- **MUSS [MUST]** für `automation` und `script` den `mode` bewusst wählen (nicht blind `single`), bei `parallel`/`queued` ein passendes `max` setzen und ein `max_exceeded: silent` begründen; die moderne Plural-Syntax (`triggers`/`conditions`/`actions`) nutzen; jeder Automation eine stabile `id` und einen englischen `alias` (≤ 50 Zeichen) geben
- **MUSS [MUST]** für `script` öffentliche Parameter über `fields` mit Selektoren ausdrücken und interne Werte über `variables` trennen
- **MUSS [MUST]** für `scene` Attribute nur in der verschachtelten `state:`-Form setzen, niemals an einen skalaren Zustandswert hängen
- **MUSS [MUST]** für `template` die moderne `template:`-Block-Form nutzen (nie `platform: template`), jeder Entity eine stabile `unique_id` geben und jedes Template gegen `unavailable`/`unknown` absichern (`has_value()`, `is_number()`, `float(default)`, `availability`)
- **MUSS [MUST]** für `rest_command` `verify_ssl: false` nur mit dokumentierter Begründung setzen und Credentials über `username`/`password`/`authentication` statt in der URL führen
- **MUSS [MUST]** für `shell_command` untrusted Input niemals ungequotet interpolieren (Shell-Injection läuft als root), keine Pipes/Redirects im Template nutzen und den `returncode` über `response_variable` prüfen
- **MUSS [MUST]** für `python_script` ohne `import` auskommen, nur die bereitgestellten Objekte (`hass`, `data`, `logger`, `output`) nutzen und über `logger` statt `print` loggen
- **MUSS [MUST]** alle Bezeichner (`id`, `object_id`, `unique_id`, `alias`, Service-Namen) nach `ha/naming-conventions` benennen (snake_case-IDs, englische Anzeigenamen)
- **MUSS [MUST]** HA-Interna gegen die offizielle Doku verifizieren statt aus dem Gedächtnis (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** das Artefakt offline validieren (YAML-Lint; wo möglich `ha core check`; Template-Rendering mit `unavailable`/`unknown`-Quellen gedanklich durchspielen) und Verstöße benennen
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der jeden Punkt auf eine Akzeptanzkriterium der zuständigen `ha-automation/<topic>`-Spec zurückführt
- **MUSS [MUST]** den geschriebenen Datei-Pfad und jeden angenommenen Default im Output nennen

### Verbote

- **MUSS NICHT [MUST NOT]** mehrere Artefakte pro Lauf erzeugen (ein Artefakt, ein Typ, ein Lauf)
- **MUSS NICHT [MUST NOT]** einen Legacy-Trigger-Helfer generieren, wenn eine moderne Alternative existiert
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet den Artefakt-Typ ab (oder erfragt ihn) und bestätigt ihn vor der Generierung
- [ ] Skill liest die zuständige `ha-automation/<topic>`-Spec vor der Generierung
- [ ] `automation`/`script` tragen einen bewusst gewählten `mode` (mit `max` bei `parallel`/`queued`), eine stabile `id` und einen englischen `alias`
- [ ] `template`-Entities tragen eine `unique_id` und gegen `unavailable`/`unknown` abgesicherte Templates
- [ ] `shell_command`/`python_script` verletzen keine Sandbox-/Injection-Regel (kein ungequoteter Input, kein `import`)
- [ ] Eine auf einen Legacy-Helfer zielende Absicht wird auf die moderne Alternative umgelenkt
- [ ] Skill liefert einen CONFORMANT / NEEDS-WORK-Bericht mit Datei-Pfad und angenommenen Defaults

## Offene Fragen

- **Packages-Layout**: Soll der Skill standardmäßig in `automations.yaml`/`scripts.yaml` schreiben oder ein `packages/<name>.yaml` bevorzugen, das Automation + zugehörige Helfer bündelt? Aktuell Default je Typ, `packages/` auf Wunsch.
- **Validierungs-Tiefe**: Wann lohnt ein echtes `ha core check` gegen eine temporäre Config statt statischer YAML-/Template-Prüfung?
- **Agent-Auslagerung**: Soll der Draft-Validate-Iterate-Loop wie bei Blueprints in einen `ha-automation-author`-Agent ausgelagert werden, oder bleibt die Generierung inline im Skill?
- **`template`-Abgrenzung**: Die generische `template:`-Integration produziert auch Sensoren — die Grenze zu `ha-derived-sensor-author` (vorgefertigte Statistik-Helfer) ist konzeptionell, nicht syntaktisch. Reicht die Beschreibung zur sauberen Trennung?
