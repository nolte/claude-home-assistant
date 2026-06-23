# HA-Integration: Diagnostics

Status: draft

## Kontext

Home Assistant lässt sich über jeden ConfigEntry einen **Diagnostics-Dump** ziehen — der User klickt im Frontend „Download Diagnostics", HA serialisiert den ConfigEntry plus die von der Integration bereitgestellten Daten zu einer JSON-Datei und liefert sie als Download. Diese Datei landet typischerweise in Issue-Reports und Foren-Posts. Genau deswegen ist sauberes **Redaction** Pflicht: Credentials, API-Keys, Tokens und Multi-Tenant-Identifier dürfen nicht im Klartext im Dump landen, sonst werden sie versehentlich öffentlich.

HA stellt dafür `homeassistant.components.diagnostics.async_redact_data(data, to_redact)` bereit — ein rekursiver Walker, der alle Keys aus dem `to_redact`-Set durch `**REDACTED**` ersetzt. `nolte/kamerplanter-ha` validiert das Pattern mit einem `TO_REDACT`-Set (`api_key`, `password`, `token`, `tenant_slug`) und einer schmalen `async_get_config_entry_diagnostics(hass, entry)`-Funktion, die den ConfigEntry-Data plus Coordinator-Snapshots dumped. Diese Spec überführt das Pattern in eine generische Verpflichtung.

Quality-Scale-Marker: **Silver** (Diagnostics mit Redaction ist eine Silver-Pflicht, sobald die Integration Auth-Credentials oder andere sensible Daten in `entry.data` ablegt).

## Ziele

- `diagnostics.py` als Standard-Modul für jede Custom Integration mit Auth-basiertem Backend etablieren
- Redaction über `async_redact_data` zur Pflicht machen — manuelle Kürzungslogik verbieten
- Coordinator-Daten als Standard-Bestandteil des Diagnostics-Dumps definieren, damit Bug-Reports den Datenstand reflektieren
- Drift zwischen Setup-Schlüsseln und Redaction-Set verhindern — was in `entry.data` als Credential abgelegt wird, muss in `TO_REDACT` stehen

## Nicht-Ziele

- Device-spezifische Diagnostics (`async_get_device_diagnostics`) — eigene Folge-Spec, sobald die erste Integration sie braucht
- Redaction-Schema-Migration zwischen Versionen — wenn Felder umbenannt werden, müssen `TO_REDACT` und der Migrate-Path konsistent gepflegt werden, das ist aber kein Spec-Thema
- Externe Diagnostic-Tools (Sentry, OpenTelemetry) — leben außerhalb von HA-Diagnostics
- Repairs- und System-Health-Module — eigene HA-Mechanismen, eigene Folge-Specs

## Anforderungen

### `diagnostics.py`-Existenz

- **MUSS [MUST]** ein `diagnostics.py`-Modul im `custom_components/<domain>/`-Ordner enthalten, sobald die Integration Auth-Credentials oder andere als sensibel klassifizierte Daten in `entry.data` ablegt
- **MUSS [MUST]** in `diagnostics.py` mindestens `async_get_config_entry_diagnostics(hass, entry) -> dict` als Top-Level-Async-Funktion exportieren — HA ruft sie automatisch auf, sobald der User „Download Diagnostics" am Entry klickt
- **KANN [MAY]** zusätzlich `async_get_device_diagnostics(hass, entry, device) -> dict` exportieren, wenn pro Device ein dedizierter Dump sinnvoll ist; das ist ein eigener HA-Eintrag im Device-Detail-Menü

### `async_redact_data` als Pflicht

- **MUSS [MUST]** `homeassistant.components.diagnostics.async_redact_data(data, to_redact)` für jede Verschachtelung verwenden, die einen User-Eingabe-Pfad enthält (`entry.data`, `entry.options`, Diagnose-Coordinator-Daten, falls sie API-Antwort-Felder mit sensiblen Daten enthalten)
- **MUSS NICHT [MUST NOT]** manuelle Redaction-Logik (`if "api_key" in d: d["api_key"] = "***"`) verwenden — das skaliert nicht über Verschachtelung und ist fehleranfällig bei Refactoring
- **MUSS NICHT [MUST NOT]** sensible Felder vor dem Dump aus den Daten löschen (`del d["api_key"]`) — das verhindert das Debugging des Felds (z. B. Längen-Verifikation oder Format-Check); `**REDACTED**` reicht und ist die HA-Konvention

### `TO_REDACT`-Set

- **MUSS [MUST]** ein `TO_REDACT`-Set als Modul-Konstante in `diagnostics.py` definieren
- **MUSS [MUST]** alle Schlüssel in `entry.data`, die als Credentials oder identifizierende Daten klassifiziert sind, im Set führen — typische Einträge: `api_key`, `password`, `token`, `secret`, `auth`, `bearer`, plus integration-spezifische Tenant-/Account-Slugs
- **MUSS [MUST]** das Set bei jedem `entry.data`-Schema-Wechsel synchron pflegen — neue Auth-Felder triggern einen Eintrag in `TO_REDACT`
- **SOLLTE [SHOULD]** Multi-Tenant-Identifier (`tenant_slug`, `tenant_id`, `org_id`) im Set führen — auch wenn sie nicht streng „Credentials" sind, sind sie identifizierend und deshalb tendenziell aus Foren-Reports rauszuhalten
- **KANN [MAY]** das Set über Plattform-Module hinweg teilen, wenn die Integration mehrere Diagnose-Hooks führt — eine zentrale Konstante in `const.py` ist dann sauberer als Duplikate

### Coordinator-Daten im Dump

- **SOLLTE [SHOULD]** den aktuellen `coordinator.data` jedes registrierten Coordinators in den Dump aufnehmen — das macht Bug-Reports debugfähig, weil der Datenstand zum Fehlerzeitpunkt sichtbar bleibt
- **MUSS [MUST]** `async_redact_data` auch auf Coordinator-Daten anwenden, wenn die API-Antwort sensible Felder enthält (z. B. `tenant_slug` in Resource-Listen)
- **KANN [MAY]** Coordinator-Daten auf einen Subset reduzieren, wenn der volle Dump zu groß wäre — typisch reicht „erstes Item pro Liste" oder „Aggregat-Statistik"

### Struktur des Dumps

Empfohlene (nicht zwingende) Top-Level-Struktur des Rückgabe-Dicts:

```text
{
  "entry_data": <async_redact_data(entry.data, TO_REDACT)>,
  "entry_options": <async_redact_data(entry.options, TO_REDACT)>,
  "coordinator_data": {
    "<role>": <async_redact_data(coordinator.data, TO_REDACT)>,
    ...
  },
  "manifest_version": <manifest.json:version>,
  "ha_version": <homeassistant.const.__version__>
}
```

- **SOLLTE [SHOULD]** den Manifest- und HA-Versions-String im Dump mit­führen — vereinfacht Triage
- **KANN [MAY]** zusätzliche Felder wie Letzten Coordinator-Update-Timestamp, Anzahl Entitäten, oder Cache-Statistiken aufnehmen
- **MUSS NICHT [MUST NOT]** beliebige Logs oder Stack-Traces im Dump mit­schicken — HA-Logs liegen in einer separaten Datei; das Diagnostics-Dump ist für strukturierte Daten

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/diagnostics.py` existiert
- [ ] `async_get_config_entry_diagnostics(hass, entry) -> dict` ist als Top-Level-Async-Funktion exportiert
- [ ] `TO_REDACT` ist als Modul-Konstante (oder in `const.py`) definiert und enthält alle Auth-/Identifier-Felder, die in `entry.data` landen
- [ ] Jeder Lookup über `entry.data` und `entry.options` ist mit `async_redact_data(..., TO_REDACT)` gewrappt
- [ ] Coordinator-Daten sind im Dump mit Redaction enthalten (sofern sie sensible Felder tragen)
- [ ] Eine `grep`-Suche nach `del .*api_key`, `del .*password`, `del .*token` in `diagnostics.py` liefert keine Treffer
- [ ] Eine `grep`-Suche nach `"REDACTED"` als manueller String in `diagnostics.py` (statt `async_redact_data`-Aufruf) liefert keine Treffer
- [ ] Quality-Scale-Marker: **Silver**

## Offene Fragen

- **`async_get_device_diagnostics`-Schwelle**: Wann verlangt die Spec den Device-Hook? Aktuell als KANN; ein kalibrierter Trigger fehlt.
- **Coordinator-Daten-Größe**: Bis zu welcher Größe ist der volle Dump zumutbar? Aktuell als „typisch reicht erstes Item pro Liste" formuliert; eine konkrete Schwelle (z. B. 500 KB) ist nicht standardisiert.
- **Redaction-Tiefe**: `async_redact_data` walked rekursiv. Genügt das für tief verschachtelte Strukturen (Multi-Level-API-Antworten), oder braucht es einen Path-basierten Override-Mechanismus?
- **Multi-Tenant-Identifier-Klassifikation**: Sind `tenant_slug`/`org_id` immer redact-würdig oder nur in Public-Forum-Kontext? Aktuell als SHOULD formuliert.
