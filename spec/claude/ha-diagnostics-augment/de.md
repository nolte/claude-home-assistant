# Skill: `ha-diagnostics-augment`

Status: draft

## Kontext

`ha/diagnostics` definiert den Diagnostics-Dump: HA serialisiert pro ConfigEntry den Entry plus integration-gelieferte Daten zu einer JSON-Datei, sobald der User „Download Diagnostics" klickt — diese Datei landet typischerweise in Issue-Reports und Foren-Posts. Genau deshalb ist sauberes Redaction Pflicht: Credentials, API-Keys, Tokens, Koordinaten und Multi-Tenant-Identifier dürfen nicht im Klartext im Dump landen. HA stellt dafür `homeassistant.components.diagnostics.async_redact_data(data, to_redact)` bereit — einen rekursiven Walker, der jeden Key aus dem `to_redact`-Set durch `**REDACTED**` ersetzt. Der Quality-Scale-Marker ist **Silver**, sobald die Integration Auth-Credentials oder andere sensible Daten in `entry.data` ablegt.

Dieser Skill reichert die Diagnostics einer **bestehenden** Integration über das nackte Scaffold-Baseline hinaus an: er erzeugt oder editiert `diagnostics.py` mit `async_get_config_entry_diagnostics` und optional `async_get_device_diagnostics`, die strukturierte Dicts liefern, und routet **jedes** Secret-/PII-/Credential-/Koordinaten-Feld über `async_redact_data` mit einem expliziten modul-konstanten `TO_REDACT`-Frozenset — spec-konform zu `ha/diagnostics`.

## Scope

Anreicherung der Diagnostics genau einer bestehenden `custom_components/<domain>/`-Integration: Erzeugen oder Editieren von `diagnostics.py` mit `async_get_config_entry_diagnostics(hass, entry) -> dict` (Pflicht) und optional `async_get_device_diagnostics(hass, entry, device) -> dict`, dem modul-konstanten `TO_REDACT`-Frozenset, dem `async_redact_data`-Wrapping jedes sensiblen Verschachtelungs-Pfads (`entry.data`, `entry.options`, sensible Coordinator-Daten) und der empfohlenen Dump-Struktur inkl. Coordinator-Snapshots und Versions-Strings. Der Skill liest `ha/diagnostics` und validiert.

## Ziele

- `diagnostics.py` über das Scaffold-Baseline hinaus anreichern: vollständige, strukturierte Dumps statt eines nackten Stubs
- Das modul-konstante `TO_REDACT`-Frozenset etablieren und mit dem `entry.data`-Schema synchron halten — was als Credential/Identifier abgelegt wird, steht in `TO_REDACT`
- `async_redact_data` für jeden sensiblen Pfad erzwingen — manuelle Redaction-Logik und Feld-Löschung verbieten
- Coordinator-Daten als Standard-Bestandteil des Dumps aufnehmen, damit Bug-Reports den Datenstand reflektieren, und auch sie redacten
- Optional `async_get_device_diagnostics` ergänzen, wenn ein Per-Device-Dump sinnvoll ist, mit demselben Redaction-Vertrag

## Nicht-Ziele

- Das Auditieren bestehender Redaction-Lücken (Findings-Report über alle Module) — `ha-security-audit`
- Der nackte Scaffold-Stub von `diagnostics.py` bei Greenfield-Anlage — `ha-integration-scaffold`
- Die Quality-Scale-Bewertung des Diagnostics-Rules über alle Regeln hinweg — `ha-quality-scale-audit` / `ha/quality-scale`
- Redaction-Schema-Migration zwischen Versionen (Feld-Umbenennung plus Migrate-Path) — eigene Folge-Spec
- Externe Diagnostic-Tools (Sentry, OpenTelemetry) und Repairs/System-Health — eigene HA-Mechanismen

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „enrich diagnostics", „add device diagnostics", „make sure diagnostics redacts secrets"
  - „route the API key through async_redact_data", „dump the coordinator data in diagnostics"
  - „erweitere die Diagnostics", „redacte die Secrets im Diagnostics-Dump", „füge Device-Diagnostics hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root), aus dem `custom_components/<domain>/` und die Auth-/Identifier-Felder in `entry.data` abgeleitet werden
- **KANN [MAY]** erfassen: die zusätzlichen `TO_REDACT`-Schlüssel über die abgeleiteten hinaus, ob `async_get_device_diagnostics` gewünscht ist, und ob Coordinator-Daten auf einen Subset reduziert werden sollen

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** den `entry.data`-/`entry.options`-Schlüsselraum aus Config-Flow und Setup ableiten und jeden Credential-/Identifier-/Koordinaten-Schlüssel als Redaction-Kandidat sammeln
- **MUSS [MUST]** die registrierten Coordinators ermitteln und prüfen, ob ihre Daten sensible Felder tragen
- **MUSS [MUST]** die `ha/diagnostics`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes `diagnostics.py` blind überschreiben — bei vorhandenem Modul editieren, nicht ersetzen

### Generierungs-Regeln (aus `ha/diagnostics`)

- **MUSS [MUST]** `diagnostics.py` in `custom_components/<domain>/` erzeugen oder editieren und mindestens `async_get_config_entry_diagnostics(hass, entry) -> dict` als Top-Level-Async-Funktion exportieren
- **MUSS [MUST]** ein `TO_REDACT`-Frozenset als Modul-Konstante (oder in `const.py`, wenn über Hooks geteilt) definieren, das alle als Credential/Identifier klassifizierten `entry.data`-Schlüssel führt — typisch `api_key`, `password`, `token`, `secret`, `auth`, `bearer`, plus integration-spezifische Tenant-/Account-Slugs
- **SOLLTE [SHOULD]** Multi-Tenant-Identifier (`tenant_slug`, `tenant_id`, `org_id`) und Koordinaten (`latitude`, `longitude`) ins Set aufnehmen — identifizierend und deshalb aus Foren-Reports rauszuhalten
- **MUSS [MUST]** jeden Lookup über `entry.data` und `entry.options` mit `async_redact_data(..., TO_REDACT)` wrappen
- **MUSS NICHT [MUST NOT]** manuelle Redaction-Logik (`if "api_key" in d: d["api_key"] = "***"`) oder einen manuellen `"REDACTED"`-String verwenden — das skaliert nicht über Verschachtelung
- **MUSS NICHT [MUST NOT]** sensible Felder vor dem Dump löschen (`del d["api_key"]`) — `**REDACTED**` reicht und ist die HA-Konvention, die das Längen-/Format-Debugging erhält
- **SOLLTE [SHOULD]** den aktuellen `coordinator.data` jedes registrierten Coordinators aufnehmen und **MUSS [MUST]** `async_redact_data` auch darauf anwenden, wenn die API-Antwort sensible Felder trägt; **KANN [MAY]** den Dump auf einen Subset reduzieren, wenn der volle Dump zu groß wäre
- **KANN [MAY]** `async_get_device_diagnostics(hass, entry, device) -> dict` mit demselben Redaction-Vertrag ergänzen, wenn ein Per-Device-Dump gewünscht ist
- **SOLLTE [SHOULD]** Manifest- und HA-Versions-String mitführen; **MUSS NICHT [MUST NOT]** Logs oder Stack-Traces in den Dump schreiben
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `diagnostics.py` existiert; `async_get_config_entry_diagnostics` ist Top-Level-Async-Funktion; `TO_REDACT` ist Modul-Konstante und deckt alle Auth-/Identifier-Felder; jeder `entry.data`-/`entry.options`-Lookup ist gewrappt; Coordinator-Daten sind mit Redaction enthalten (sofern sensibel); `grep` nach `del .*(api_key|password|token)` und nach manuellem `"REDACTED"`-String liefert keine Treffer
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/diagnostics` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Silver**)

### Verbote

- **MUSS NICHT [MUST NOT]** sensible Felder über manuelle Logik kürzen oder löschen statt über `async_redact_data`
- **MUSS NICHT [MUST NOT]** den `entry.data`-Schlüsselraum raten — er wird aus Config-Flow/Setup abgeleitet, und Unsicherheiten werden erfragt
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/diagnostics.py` existiert und `async_get_config_entry_diagnostics(hass, entry) -> dict` ist als Top-Level-Async-Funktion exportiert
- [ ] `TO_REDACT` ist als Modul-Konstante (oder in `const.py`) definiert und enthält alle Auth-/Identifier-Felder aus `entry.data`
- [ ] Jeder Lookup über `entry.data` und `entry.options` ist mit `async_redact_data(..., TO_REDACT)` gewrappt
- [ ] Coordinator-Daten sind im Dump mit Redaction enthalten (sofern sie sensible Felder tragen)
- [ ] `grep` nach `del .*api_key`/`password`/`token` und nach manuellem `"REDACTED"`-String in `diagnostics.py` liefert keine Treffer
- [ ] Optional ergänztes `async_get_device_diagnostics` folgt demselben Redaction-Vertrag
- [ ] Bericht nennt die Datei-Pfade und den Quality-Scale-Marker **Silver**

## Offene Fragen

- **`async_get_device_diagnostics`-Schwelle**: Wann verlangt der Skill den Device-Hook statt ihn nur anzubieten? `ha/diagnostics` lässt ihn als KANN; der Skill ergänzt ihn auf Wunsch und fragt im Zweifel nach.
- **Koordinaten-Klassifikation**: Sind `latitude`/`longitude` immer redact-würdig? Der Skill nimmt sie als SOLLTE auf, weil sie identifizierend sind; eine kalibrierte Schwelle fehlt.
- **Coordinator-Daten-Größe**: Ab welcher Größe reduziert der Skill auf einen Subset? `ha/diagnostics` formuliert „erstes Item pro Liste typisch genug"; eine konkrete Schwelle ist nicht standardisiert.
