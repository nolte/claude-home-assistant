# Skill: `ha-security-audit`

Status: draft

## Kontext

`ha/security-hardening` definiert das Hardening-Bundle: API-Path-Whitelist, Bearer-Gating, Config-Flow-Input-Validierung, Multi-Instance-Service-Disambiguation, Diagnostics-Redaction, Logging-Disziplin. Eine bestehende Integration kann diese Maßnahmen voll, teilweise oder gar nicht umgesetzt haben — ohne Audit ist nicht entscheidbar, welcher Stand vorliegt. Ein menschliches Review erkennt einzelne Risiken, vergisst aber regelmäßig die Cross-Modul-Sicht (z. B. ist Bearer-Setzung an *einer* Stelle gegen Whitelist abgesichert, aber an einer zweiten nicht).

Dieser Skill auditiert eine Integration gegen alle MUSS-Regeln aus `ha/security-hardening`, produziert einen strukturierten Bericht mit Findings pro Regel, und liefert pro Finding eine konkrete Code-Stelle plus Remediation-Vorschlag. Er **schreibt nichts** — die Behebung bleibt manuell oder via einen anderen Skill.

## Scope

Read-only Audit. Der Skill liest die Code-Dateien, führt `grep`-basierte Pattern-Checks aus, parsed `manifest.json`, prüft `diagnostics.py`-`TO_REDACT`-Konsistenz mit `entry.data`-Schlüsseln. Er macht keine destruktiven Operationen, kein Auto-Fix, kein Commit.

## Ziele

- Vollständigkeits-Bericht über alle `ha/security-hardening`-MUSS-Regeln pro auditierter Integration
- Pro Finding: Pfad-Datei-Zeilen-Referenz, Klassifikation (high / medium / low), Remediation-Vorschlag (welcher Skill behebt es, welche manuelle Edit-Aktion)
- Cross-Modul-Sicht: Findings aggregieren Treffer aus mehreren Modulen pro Regel (z. B. Bearer-Setzung an mehreren Stellen)
- Quality-Scale-Bewusstsein: jeder Finding hat einen Quality-Scale-Tier-Marker, der zeigt, welcher Tier durch den Fix erreicht wird

## Nicht-Ziele

- Auto-Fix der Findings — destruktive Edits sind manueller Schritt
- Backend-Penetration-Testing — der Skill auditiert die Integration; Backend-Sicherheit ist außerhalb
- Performance-Audit — eigener Skill, falls überhaupt sinnvoll
- Code-Quality-Audit (Ruff, Type-Hints, Test-Coverage) — eigene Tools / Skills

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „run a security audit on the integration"
  - „audit security hardening"
  - „check the integration against ha/security-hardening"
  - „prüfe die Integration gegen das Security-Hardening"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root)
- **KANN [MAY]** erfassen: `severity_threshold` (`low` / `medium` / `high`); Default `low` (alle Findings melden)

### Pre-Flight

- **MUSS [MUST]** prüfen:
  1. `target_dir` ist git-Repo
  2. `target_dir/custom_components/<domain>/manifest.json` existiert
  3. `target_dir/custom_components/<domain>/api.py` existiert (oder Skill notiert, dass kein API-Client vorhanden ist und überspringt API-Audit)

### Audit-Checks

Pro Regel aus `ha/security-hardening` führt der Skill den folgenden Check aus:

#### API-Path-Whitelist

- **MUSS [MUST]** in `api.py` nach einer kompilierten Regex-Konstante (`_API_PATH_RE` oder ähnlich) suchen und prüfen, ob jeder HTTP-Aufruf (`session.get`, `session.post`, `session.put`, `session.patch`, `session.delete`) durch eine Validierungs-Funktion läuft
- **Finding wenn**: keine Pfad-Whitelist gefunden → high; Whitelist existiert, aber mindestens ein HTTP-Call umgeht sie → high

#### Bearer-Token-Gating

- **MUSS [MUST]** nach `Authorization`-Header-Setzungen in `api.py` und allen anderen Modulen suchen; jede Setzung außerhalb einer dedizierten `_with_auth(...)`-Helper-Funktion ist ein Finding
- **Finding wenn**: `Authorization` an mehr als einer Stelle gesetzt → high; Setzung ohne vorherige Path-Whitelist-Prüfung → high

#### Config-Flow-Input-Validierung

- **MUSS [MUST]** in `config_flow.py` nach `vol.Schema(...)`-Konstrukten suchen und prüfen, ob URL-Felder mit `vol.Match` (oder `cv.url`) validiert sind und API-Key-Felder mit `vol.Length`/`vol.Match`
- **Finding wenn**: URL-Feld ohne `vol.Match` → medium; API-Key-Feld ohne Pattern-/Length-Validierung → medium

#### Multi-Instance-Service-Disambiguation

- **MUSS [MUST]** in `__init__.py` (oder `services.py`) nach Service-Handlern suchen und prüfen, ob ein `_resolve_entry`-Helper aufgerufen wird, der bei Mehrdeutigkeit `ServiceValidationError` raised
- **Finding wenn**: Service-Handler ohne `_resolve_entry`-Aufruf → medium; `_resolve_entry`-Helper existiert, fängt aber Mehrdeutigkeit nicht → high

#### Diagnostics-Redaction

- **MUSS [MUST]** in `diagnostics.py` nach `async_redact_data`-Aufrufen suchen und prüfen, ob `TO_REDACT` jeden Schlüssel aus `entry.data` enthält, der einen Auth- oder Identifier-Charakter hat (heuristisch: `*key`, `*token`, `*password`, `*secret`, `*auth`, `*tenant*`)
- **Finding wenn**: `diagnostics.py` fehlt → medium; `async_redact_data` fehlt → medium; `TO_REDACT` hat Lücken (z. B. fehlt `tenant_slug`, der in `entry.data` als Schlüssel auftaucht) → low (oder medium, je nach Schlüssel-Charakter)

#### Logging-Disziplin

- **MUSS [MUST]** mit `grep` nach `_LOGGER\.[a-z]+\(.*api_key`, `_LOGGER\.[a-z]+\(.*token`, `_LOGGER\.[a-z]+\(.*password` suchen
- **Finding wenn**: Treffer in einem dieser Patterns → high

### Bericht-Format

- **MUSS [MUST]** den Bericht als strukturierte Markdown-Liste ausgeben mit folgenden Feldern pro Finding:
  - `id` — Finding-Nummer
  - `rule` — die `ha/security-hardening`-Regel
  - `severity` — high / medium / low
  - `path` — Datei + Zeilennummer
  - `evidence` — der konkrete Code-Snippet
  - `remediation` — empfohlener Fix; bei Skill-fixbaren Findings den Skill-Namen referenzieren
  - `quality_scale_impact` — welcher Quality-Scale-Tier durch den Fix erreicht wird
- **MUSS [MUST]** am Ende eine Zusammenfassung enthalten: Anzahl Findings pro Severity, Anzahl Findings pro Regel, Quality-Scale-Stand (Bronze ✓ / Silver ✓ / Gold ✗ / …)

### Verbote

- **MUSS NICHT [MUST NOT]** Code modifizieren — read-only Audit
- **MUSS NICHT [MUST NOT]** False-Positives unterdrücken ohne Begründung — wenn ein Pattern matcht, aber der Code aus anderen Gründen sicher ist, melden und als „prüfen" markieren

## Akzeptanzkriterien

- [ ] Skill liest `manifest.json`, `api.py`, `config_flow.py`, `__init__.py`, `services.py` (sofern vorhanden), `diagnostics.py`
- [ ] Skill produziert pro `ha/security-hardening`-Regel einen Audit-Eintrag (auch bei „pass")
- [ ] Findings sind nach Severity (high → low) sortiert
- [ ] Skill macht keine Datei-Modifikationen (`git status` unverändert nach Lauf)
- [ ] Skill-Output enthält Quality-Scale-Stand-Zusammenfassung

## Offene Fragen

- **Auto-Fix-Schwelle**: Wann lohnt ein eigener Skill, der Findings automatisch behebt? Aktuell jedes Finding manuell.
- **AST-basierte vs. Grep-basierte Checks**: Grep ist schnell und ausreichend für diese Patterns; AST-basierte Checks (über `ast`-Modul) wären präziser. Lohnt der Aufwand?
- **CI-Integration**: Soll der Skill als CI-Hook konsumierbar sein (Exit-Code != 0 bei high-Findings)? Aktuell nur interaktiver Skill.
- **Backend-Audit**: Welche Form von Backend-Audit (gegen die HTTP-API selbst) macht parallel Sinn? Aktuell Nicht-Ziel.
