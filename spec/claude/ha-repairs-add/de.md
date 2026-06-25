# Skill: `ha-repairs-add`

Status: draft

## Kontext

`ha/repairs` definiert, wie eine HA-Integration über die **Issue-Registry** auf actionable Probleme hinweist (Deprecations, veraltete Backend-Versionen, Fehlkonfiguration): `async_create_issue(...)` zum Anlegen, ein `repairs.py`-Modul mit `async_create_fix_flow(...)` für **fixable** Issues, übersetzte Texte in `strings.json` unter `issues:`, und `async_delete_issue(...)` zum Aufräumen, sobald der Zustand behoben ist. Die Regel `repair-issues` ist eine **Gold**-Quality-Scale-Regel. Bislang gibt es keinen Skill, der das operationalisiert: Entwickler hartkodieren Issue-Texte, setzen `is_fixable=True` ohne zugehörigen Flow, vergessen den `async_delete_issue`-Pfad (veraltetes Issue bleibt stehen) oder missbrauchen Repairs für transiente Verbindungsfehler, die in das Coordinator-Fehlerhandling gehören.

Dieser Skill ergänzt **ein** Repair-Issue (fixable oder informativ) in einer **bestehenden** Integration: er erzeugt die `async_create_issue`-Aufrufstelle, bei fixable Issues das `repairs.py` mit `async_create_fix_flow` und einem `RepairsFlow`/`ConfirmRepairFlow`, die `issues:`-Einträge in `strings.json`, sowie den `async_delete_issue`-Lebenszyklus-Pfad — spec-konform zu `ha/repairs`. Er ist die Repairs-Schwester von `ha-quality-scale-audit`: jener bewertet, dieser baut die Gold-Regel.

## Scope

Ergänzung genau eines Repair-Issues pro Lauf in einer bestehenden `custom_components/<domain>/`-Integration: die `async_create_issue`-Aufrufstelle (am Ort der Zustandserkennung), `strings.json`-`issues:`-Eintrag (`title`/`description`), bei fixable Issues `repairs.py` (`async_create_fix_flow` + Flow), und der `async_delete_issue`-Pfad. Der Skill bestimmt fixable vs. informativ und die `severity`, liest `ha/repairs` und validiert.

## Ziele

- Aus einer beschriebenen Problem-Situation ein spec-konformes Repair-Issue ergänzen, das jede MUSS-Regel aus `ha/repairs` erfüllt
- Fixable vs. informativ bewusst entscheiden und die Konsequenz erzwingen: `is_fixable=True` nur mit zugehörigem `RepairsFlow`; informativ mit `learn_more_url`
- Alle User-sichtbaren Texte über `strings.json`/`issues:` übersetzbar machen — keine hartkodierten Strings
- Den Issue-Lebenszyklus an den Problem-Zustand binden: einen `async_delete_issue`-Pfad erzeugen, der das Issue nach Behebung entfernt
- Repairs scharf von transienten Fehlern abgrenzen und letztere auf das Coordinator-`UpdateFailed`-Handling umlenken

## Nicht-Ziele

- Greenfield-Scaffolding einer Integration — das ist `ha-integration-scaffold`
- System-Health (`system_health.py`) — eigener HA-Mechanismus
- Mehrstufige Repair-Flows mit komplexer User-Eingabe — dieser Skill deckt den `ConfirmRepairFlow`-/einfachen `async_step_init`-Standardfall ab
- Issues im Namen einer *anderen* Integration (`issue_domain`) — außerhalb des Standard-Patterns
- Quality-Scale-Bewertung der Gesamtintegration — das ist `ha-quality-scale-audit`
- Transientes Fehlerhandling (`UpdateFailed`, `entity-unavailable`) — das ist `ha-coordinator-add` / `ha/coordinator-patterns`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a repair issue for …", „create a fixable repair flow for …", „warn the user about a deprecation"
  - „surface an issue when the backend version is too old"
  - „füge ein Repair-Issue für … hinzu", „erstelle einen Repair-Flow für …", „weise den User auf eine Deprecation hin"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Problem-Situation (Prosa, woraufhin das Issue hinweist)
- **KANN [MAY]** erfassen: `issue_id` (Default aus der Situation abgeleitet, `snake_case`), `fixable` (sonst aus der Situation abgeleitet und bestätigt), `severity` (`error`/`warning`), `breaks_in_ha_version`, `learn_more_url`, `is_persistent`

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` daraus lesen
- **MUSS [MUST]** die Problem-Situation gegen die Transienz-Abgrenzung prüfen: ist sie ein transienter Verbindungs-/API-Fehler, **MUSS [MUST]** der Skill auf das Coordinator-`UpdateFailed`-Handling umlenken statt ein Issue anzulegen
- **MUSS [MUST]** die `ha/repairs`-Spec lesen, bevor er generiert
- **MUSS NICHT [MUST NOT]** ein bestehendes Issue mit gleicher `issue_id` überschreiben; bei Kollision mit zitierter `issue_id` abbrechen

### Generierungs-Regeln (aus `ha/repairs`)

- **MUSS [MUST]** das Issue über `homeassistant.helpers.issue_registry.async_create_issue(hass, domain, issue_id, ...)` anlegen und mindestens `domain`, `issue_id`, `is_fixable`, `severity` (`IssueSeverity`) und `translation_key` setzen; `issue_id` ist innerhalb der `domain` eindeutig
- **MUSS [MUST]** `severity` bewusst wählen: `ERROR` wenn aktuell etwas kaputt ist, `WARNING` wenn etwas in Zukunft bricht; `CRITICAL` nicht für Normalfälle
- **SOLLTE [SHOULD]** bei Deprecations `breaks_in_ha_version` setzen
- **MUSS [MUST]** für `is_fixable=True` ein `repairs.py` mit `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow` als Top-Level-Async-Funktion erzeugen, das anhand `issue_id` zum Flow routet; der Flow leitet von `RepairsFlow` ab (oder nutzt `ConfirmRepairFlow`), implementiert `async_step_init` und schließt mit `self.async_create_entry(title="", data={})` ab (entfernt das Issue automatisch)
- **MUSS [MUST]** für `is_fixable=False` `learn_more_url` auf die Anleitung zeigen lassen und **kein** `repairs.py` für dieses Issue verlangen
- **MUSS [MUST]** den `translation_key` in `strings.json` unter `issues:` mit `title` und `description` hinterlegen, alle `translation_placeholders` im Text auflösen und **keine** hartkodierten User-Strings im Python-Code lassen (Detail-Übersetzung folgt `ha/translations`)
- **MUSS [MUST]** einen `async_delete_issue(hass, domain, issue_id)`-Pfad erzeugen oder benennen, der das Issue entfernt, sobald der zugrunde liegende Zustand behoben ist
- **SOLLTE [SHOULD]** `is_persistent=True` setzen, wenn das Problem nur im Moment seines Auftretens erkennbar ist (z. B. fehlgeschlagenes Update) — die Anzeige überlebt dann einen HA-Neustart; sonst `is_persistent=False`, wenn der Zustand bei jedem Start neu prüfbar ist (z. B. veraltete Backend-Version)
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: jeder `async_create_issue` setzt die Pflichtfelder; kein `is_fixable=True` ohne `repairs.py`-Flow; jeder `translation_key` ist in `strings.json` aufgelöst; ein `async_delete_issue`-Pfad existiert; keine hartkodierten Strings
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/repairs` liefern, plus die geschriebenen/geänderten Datei-Pfade und den Quality-Scale-Marker (**Gold**)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als ein Issue pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** ein Repair-Issue für einen transienten Fehler oder eine reine „etwas ist kaputt"-Meldung ohne User-Aktion anlegen
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill entscheidet fixable vs. informativ und bestätigt es vor der Generierung
- [ ] Skill liest `ha/repairs` und prüft die Transienz-Abgrenzung im Pre-Flight
- [ ] `async_create_issue` setzt `domain`, `issue_id`, `is_fixable`, `severity`, `translation_key`
- [ ] `is_fixable=True` geht stets mit einem `repairs.py`/`async_create_fix_flow` einher
- [ ] `translation_key` ist in `strings.json` unter `issues:` mit `title`/`description` aufgelöst; keine hartkodierten User-Strings
- [ ] Ein `async_delete_issue`-Pfad entfernt das Issue nach Behebung
- [ ] Eine transiente Situation wird auf `UpdateFailed`/Coordinator umgelenkt statt als Issue angelegt
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **Gold**

## Offene Fragen

- **Platzierung der Aufrufstelle**: Soll der Skill `async_create_issue` automatisch am erkannten Zustands-Ort platzieren (Coordinator, Setup, Service) oder den Snippet liefern und die Einbettung dem User überlassen? Aktuell platziert er am naheliegenden Ort und nennt ihn im Bericht.
- **Dedup bei mehreren Entries**: Eine `issue_id` pro ConfigEntry oder ein geteiltes Issue? `ha/repairs` lässt das offen; der Skill fragt im Zweifel nach.
- **Flow-Komplexität**: Ab wann lohnt ein mehrstufiger Flow statt `ConfirmRepairFlow` + Doku-Link? Aktuell deckt der Skill nur den Standardfall ab.
