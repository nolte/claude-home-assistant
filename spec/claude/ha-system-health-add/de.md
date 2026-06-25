# Skill: `ha-system-health-add`

Status: draft

## Kontext

`ha/system-health` definiert die System-Health-Schicht: eine Integration nimmt teil, indem sie ein `system_health.py`-Modul mit einer `@callback`-dekorierten, synchronen `async_register(hass, register)`-Funktion bereitstellt, die über `register.async_register_info(async_health_info)` einen Info-Callback registriert. Der `async_health_info(hass) -> dict`-Callback liefert das auf der System-Health-Seite angezeigte Dict, dessen Werte beliebige Typen sein dürfen — inklusive Coroutines. Für Coroutine-Werte zeigt das Frontend einen Warte-Indikator und aktualisiert das Item automatisch, sobald das Ergebnis vorliegt. Für Erreichbarkeits-Items stellt die Plattform den Helfer `system_health.async_check_can_reach_url(hass, url)` bereit. Bislang gibt es keinen Skill, der das ergänzt. Wichtig: System-Health ist der **At-a-Glance-Status** (kurze Werte direkt im Frontend), nicht der vollständige, herunterladbare Dump — das ist `ha/diagnostics`.

Dieser Skill ergänzt eine System-Health-Info-Schicht in einer **bestehenden** Integration: das `system_health.py`-Modul, die `@callback async_register`-Funktion, den `async_health_info`-Callback mit seinem Info-Dict, die Erreichbarkeits-Items über `async_check_can_reach_url` und die `system_health`-`strings.json`-Einträge — spec-konform zu `ha/system-health`. Vor der Generierung prüft er, ob die Integration überhaupt einen sinnvollen At-a-Glance-Status hat.

## Scope

Ergänzung der System-Health-Info-Schicht in einer bestehenden `custom_components/<domain>/`-Integration: das `system_health.py`-Modul, die `@callback async_register(hass, register) -> None`-Funktion, der `register.async_register_info(...)`-Aufruf (optional mit Manage-URL `/config/<domain>`), der `async_health_info(hass) -> dict`-Callback, die Info-Items (Werte und Erreichbarkeits-Checks über `async_check_can_reach_url`) und die `strings.json`-`system_health:`-Einträge. Der Skill liest `ha/system-health` und validiert.

## Ziele

- Aus dem beschriebenen Backend-Zustand sinnvolle At-a-Glance-Items ableiten (Erreichbarkeit, verbundener Server, Kontingent) und spec-konform ergänzen
- Den Registrierungs-Vertrag erzwingen: `@callback`-dekorierte, synchrone `async_register`, die `register.async_register_info(async_health_info)` aufruft
- Teure Checks als **Coroutine** (ohne vorheriges `await`) in das Info-Dict legen, damit das Frontend nicht blockiert
- Erreichbarkeits-Items über `system_health.async_check_can_reach_url(hass, url)` standardisieren statt manueller HTTP-Probes
- Den User vor Diagnose-Überladung bewahren: kurze Status-Werte hier, vollständige Dumps in `ha/diagnostics`

## Nicht-Ziele

- Vollständige, redigierte Diagnose-Dumps — `ha-diagnostics-augment` / `ha/diagnostics` (eigene Redaction-Pflicht)
- User-seitige Probleme, die eine Aktion erfordern (Repairs-Issues, `async_create_issue`) — `ha-repairs-add` / Repairs
- Die Detail-Übersetzung der Info-Keys über `strings.json` — Sache der Translation-Spec; hier nur als Verweis
- Externe Monitoring-Systeme (Prometheus, Healthcheck-Endpoints) — leben außerhalb von HA-System-Health
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add system health info", „show my integration on the system health page"
  - „surface the backend reachability / remaining quota on the system health page"
  - „füge System-Health-Infos hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und den Backend-Zustand (Prosa), aus dem der Skill die Info-Items ableitet
- **KANN [MAY]** erfassen: die zu prüfenden Erreichbarkeits-URLs (`endpoints`), zusätzliche Werte (Kontingent, verbundener Server) und die optionale Manage-URL (`/config/<domain>`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** den Mehrwert-Check fahren: hat die Integration einen sinnvollen At-a-Glance-Status (Backend-Konnektivität oder Kontingent-Semantik)? Eine rein lokale Integration **KANN [MAY]** `system_health.py` entfallen lassen; der Skill **SOLLTE [SHOULD]** darauf hinweisen, statt leere Items zu erzeugen
- **MUSS [MUST]** die `ha/system-health`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes `system_health.py` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/system-health`)

- **MUSS [MUST]** ein `system_health.py`-Modul im `custom_components/<domain>/`-Ordner erzeugen
- **MUSS [MUST]** die Plattform-API aus `homeassistant.components.system_health` importieren (`SystemHealthRegistration` für die Type-Annotation der Registration)
- **MUSS [MUST]** eine `@callback`-dekorierte, **synchrone** `async_register(hass, register) -> None`-Funktion exportieren — die Registration ist synchron, nur die Info-Erhebung ist async
- **MUSS [MUST]** in `async_register` über `register.async_register_info(async_health_info)` den Info-Callback registrieren; **KANN [MAY]** eine Manage-URL als zweites Argument übergeben (z. B. `register.async_register_info(async_health_info, "/config/<domain>")`)
- **MUSS [MUST]** einen `async_health_info(hass) -> dict`-Callback bereitstellen, der das angezeigte Info-Dict zurückliefert
- **SOLLTE [SHOULD]** teure Checks (z. B. URL-Erreichbarkeit) als **Coroutine** (ohne vorheriges `await`) in das Dict setzen — das Frontend zeigt dann einen Warte-Indikator und aktualisiert das Item automatisch
- **SOLLTE [SHOULD]** für Erreichbarkeits-Items den Helfer `system_health.async_check_can_reach_url(hass, url)` verwenden statt einer eigenen HTTP-Probe; **KANN [MAY]** mehrere Erreichbarkeits-Items für unterschiedliche Endpoints führen, jeweils über einen eigenen Helfer-Aufruf
- **KANN [MAY]** Werte wie verbleibendes Request-Kontingent, verbrauchte Requests oder den aktuell verbundenen Server als Info-Items aufnehmen
- **MUSS NICHT [MUST NOT]** System-Health-Items mit Diagnose-Daten überladen, die in den `ha/diagnostics`-Dump gehören — die Seite ist für kurze Status-Werte
- **SOLLTE [SHOULD]** jeden Info-Key über die `system_health`-Sektion in `strings.json` übersetzen, damit das Frontend lesbare Beschreibungen statt roher Keys zeigt
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `system_health.py` existiert; `async_register(hass, register) -> None` ist mit `@callback` dekoriert und exportiert; `async_register` registriert den Info-Callback über `register.async_register_info(...)`; `async_health_info(hass) -> dict` ist definiert; teure Erreichbarkeits-Checks sind als Coroutine (ohne vorheriges `await`) gesetzt; Erreichbarkeits-Items nutzen `async_check_can_reach_url`; Info-Keys sind in `strings.json` unter `system_health:` übersetzt
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/system-health` liefern, plus die geänderten Datei-Pfade

### Verbote

- **MUSS NICHT [MUST NOT]** System-Health als Ersatz für `ha/diagnostics` verwenden — vollständige, strukturierte Dumps gehören in den Diagnostics-Download
- **MUSS NICHT [MUST NOT]** ein Konnektivitäts-Item in ein Repairs-Issue eskalieren — das ist `ha-repairs-add` / Repairs
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill fährt den At-a-Glance-Mehrwert-Check und rät rein lokalen Integrationen ohne sinnvollen Status ab
- [ ] `custom_components/<domain>/system_health.py` existiert
- [ ] `async_register(hass, register) -> None` ist mit `@callback` dekoriert und exportiert
- [ ] `async_register` registriert den Info-Callback über `register.async_register_info(...)`
- [ ] `async_health_info(hass) -> dict` ist als Info-Callback definiert und liefert das angezeigte Dict
- [ ] Teure Erreichbarkeits-Checks sind als Coroutine (ohne vorheriges `await`) im Info-Dict gesetzt
- [ ] Erreichbarkeits-Items nutzen `system_health.async_check_can_reach_url(hass, url)` statt manueller HTTP-Probes
- [ ] Info-Keys sind über die `system_health`-Sektion in `strings.json` übersetzt; Bericht nennt die Datei-Pfade

## Offene Fragen

- **Implementierungs-Schwelle**: Ab wann verlangt der Skill `system_health.py`? Aktuell als SOLLTE für Backend-gestützte Integrationen; ein kalibrierter Trigger (z. B. „jede Integration mit Cloud-IoT-Class") fehlt — `ha/system-health` lässt es offen.
- **Mehrere ConfigEntries**: Das Doc-Beispiel greift `async_entries(DOMAIN)[0]`. Wie soll der Callback bei mehreren Entries derselben Integration aggregieren? Aktuell nicht standardisiert; der Skill fragt im Zweifel nach.
- **Translation-Pflicht**: Ist die `strings.json`-Übersetzung der Info-Keys ein MUSS oder SOLLTE? `ha/system-health` formuliert SOLLTE; der Skill folgt dem.
