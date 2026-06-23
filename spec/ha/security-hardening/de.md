# HA-Integration: Security-Hardening

Status: draft

## Kontext

Eine Custom Integration ist ein Stück Drittanbieter-Code, das im selben Prozess wie HA Core läuft, vollen Lese-/Schreibzugriff auf den HA-State hat und im Standard-Betrieb mit gespeicherten User-Credentials arbeitet. Sicherheits-Lücken in einer Custom Integration sind deshalb keine isolierten Bugs, sondern reichen direkt in das HA-System hinein. Drei Klassen von Lücken haben sich in der Praxis wiederholt gezeigt: (1) **API-Path-Injection** — der HTTP-Client baut Requests aus User-Eingabe ohne Pfad-Validierung; (2) **Bearer-Token-Leakage** — Tokens werden für Pfade gesendet, für die sie nicht bestimmt sind; (3) **Multi-Instance-Service-Ambiguity** — ein Service-Aufruf trifft das falsche Backend, weil die Disambiguation-Logik fehlt.

`nolte/kamerplanter-ha` hat in Commit `242c08f (2026-04-25 "fix(security): harden HTTP client, config flow, and service handlers")` ein zusammenhängendes Hardening-Bundle eingespielt: API-Path-Whitelist über `_API_PATH_RE`, Bearer-Gating nur für validierte Pfade, Input-Validierung im Config-Flow (URL-Format, Credential-Charakter-Set), Ambiguity-Detection in Service-Handlern. Diese Spec überführt die einzelnen Hardening-Maßnahmen in eine generische, von Skills enforce-bare Verpflichtung.

Quality-Scale-Marker: **Silver** (Eingabe-Validierung und sichere Default-Werte sind Silver-Pflicht); einzelne Maßnahmen (Bearer-Gating, Path-Whitelist) gehen über Silver hinaus, sind aber portfolio-Pflicht.

## Ziele

- API-Path-Injection durch Pfad-Whitelist-Validierung im HTTP-Client verhindern
- Bearer-Tokens nur an validierte API-Pfade senden — User-eingegebene URLs dürfen niemals den Token „mitschleppen"
- User-Input im Config-Flow mit strikter Format-Validierung absichern, sodass fehlerhafte oder bösartige Eingaben nicht erst in der Coordinator-Schleife auffallen
- Multi-Instance-Disambiguation in Service-Handlern als Sicherheits-Pflicht (nicht nur UX-Frage) etablieren — ein Service-Aufruf darf nicht das falsche Backend mutieren
- Diagnostics-Redaction (siehe `ha/diagnostics`) als Pflicht-Kanal sicherstellen, sodass keine Secrets in Bug-Reports landen

## Nicht-Ziele

- Backend-seitige Authentifizierung / Autorisierung — das Backend ist außerhalb des Plugin-Scopes
- TLS-Konfiguration / Certificate-Pinning auf HTTP-Client-Ebene — eigene Folge-Spec, sobald die erste Integration es konkret braucht
- HA-Frontend-Härtung (XSS, CSP) — adressiert HA Core selbst; Lovelace-Cards greifen darauf nicht ein, sofern sie keine `dangerouslySetInnerHTML`-Äquivalente nutzen
- Penetration-Testing-Methodik — adressiert nicht das Skill-Output, sondern Review-Praxis
- Audit-Logging in HA — eigene HA-Mechanik

## Anforderungen

### API-Path-Whitelist

- **MUSS [MUST]** im HTTP-Client der Integration eine Pfad-Whitelist als Modul-Konstante (typisch eine kompilierte Regex `_API_PATH_RE`) führen — der Whitelist-Eintrag matched die erlaubten Pfade des konkreten Backends (z. B. `^/api/(v1|v2)/(plants|locations|tanks|tasks|alerts)(/[a-zA-Z0-9_-]+)*/?$`)
- **MUSS [MUST]** vor jedem HTTP-Request den Ziel-Pfad gegen die Whitelist prüfen und bei Mismatch eine `ValueError` (oder eine integration-spezifische `<Domain>InvalidPathError`) raisen
- **SOLLTE [SHOULD]** die Whitelist als positive Liste führen (nur erlaubte Pfade) statt als negative Liste (verbotene Pfade) — positive Listen versagen sicher, negative Listen vergessen Edge-Cases
- **MUSS NICHT [MUST NOT]** User-Eingabe-Pfade ohne Whitelist-Validierung an den HTTP-Client weiterreichen — der Pfad darf an keiner Stelle aus User-Eingabe geraten, ohne durch die Validierung zu laufen

### Bearer-Token-Gating

- **MUSS [MUST]** den Bearer-Token (oder API-Key, OAuth-Token) **nur dann** in den `Authorization`-Header eines Requests einsetzen, wenn der Ziel-Pfad die Path-Whitelist passiert hat
- **MUSS NICHT [MUST NOT]** Tokens an Pfade außerhalb der Whitelist senden — selbst wenn der Pfad `/api/...` aussieht, aber nicht in der Whitelist steht: Token weglassen
- **SOLLTE [SHOULD]** die Bearer-Setzung in einer einzigen Helper-Methode (`_with_auth(headers)`) bündeln, die die Whitelist-Prüfung einbezieht — verhindert, dass Token-Setzung an mehreren Stellen dupliziert und leicht ge-bypassed wird
- **MUSS NICHT [MUST NOT]** Tokens loggen — auch nicht im DEBUG-Level; Logging-Statements müssen Tokens redacten oder weglassen

### Config-Flow-Input-Validierung

- **MUSS [MUST]** User-eingegebene URLs im User-/Reauth-/Reconfigure-Flow strikt validieren:
  - URL-Format (gültiges `scheme://host[:port]/path`-Schema)
  - Erlaubte Schemas: `http`, `https` — keine `file:`, `gopher:`, `data:` oder andere
  - Hostname / IP innerhalb erwarteter Bereiche, falls die Integration LAN-only sein soll
- **MUSS [MUST]** API-Keys und ähnliche Credentials auf Format-Pattern prüfen (typisch: `^[A-Za-z0-9_-]{20,}$` oder integration-spezifischer Präfix wie `sk_live_…`) — verhindert Tippfehler, vor allem aber HTML-/Shell-Escapes, die durchrutschen
- **SOLLTE [SHOULD]** Format-Verletzungen mit `vol.Match` / `vol.All(str, vol.Length(min=N))` direkt im `vol.Schema(...)` deklarativ prüfen statt mit imperativen `if`-Ketten im Handler
- **MUSS [MUST]** Validierungs-Fehler vor dem ersten API-Aufruf werfen — fehlerhafte Eingabe darf nicht erst beim Backend auffallen

### Multi-Instance-Service-Disambiguation

- **MUSS [MUST]** in Service-Handlern die in `ha/services` beschriebene Disambiguation-Logik anwenden — kein Service-Aufruf darf den falschen ConfigEntry treffen
- **MUSS [MUST]** bei Mehrfach-Match-Risiko (mehrere Entries derselben Integration, mehrere Resources mit gleichem Backend-Schlüssel) explizit nach `entry_id` fragen oder mit `ServiceValidationError` abbrechen
- **MUSS NICHT [MUST NOT]** stille Auswahl auf den ersten Entry zurückfallen, wenn mehrere matchen — das ist ein Sicherheits-Risiko, weil der User glaubt, eine andere Aktion getriggert zu haben

### Diagnostics-Redaction

- **MUSS [MUST]** `async_redact_data` für jeden in `entry.data` / `entry.options` gespeicherten Credential-Eintrag verwenden (siehe `ha/diagnostics`) — Diagnostics-Dumps landen in Foren-Posts und dürfen keine Secrets enthalten
- **MUSS NICHT [MUST NOT]** Credentials in Coordinator-Daten leaken — wenn das Backend selbst Auth-Material in API-Antworten zurückspielt (z. B. Refresh-Tokens), gehört es ebenfalls in `TO_REDACT`

### Logging-Disziplin

- **MUSS NICHT [MUST NOT]** API-Keys, Bearer-Tokens, Passwörter oder andere Credentials in Log-Statements führen — egal in welchem Log-Level
- **MUSS NICHT [MUST NOT]** vollständige API-Responses unredacted ins DEBUG-Log dumpen, wenn die Antwort sensible Felder enthält
- **SOLLTE [SHOULD]** für DEBUG-Diagnose eine eigene Helper-Funktion (`_safe_log(payload)`) definieren, die sensible Felder vor dem Logging entfernt
- **KANN [MAY]** Request-IDs / Correlation-IDs im Log führen — das hilft beim Trace und enthält keine Credentials

### Cross-Referenzen

- API-Path-Whitelist-Implementation und HTTP-Client-Form: Konsumenten-spezifisch in `nolte/kamerplanter-ha/custom_components/kamerplanter/api.py:50–64` referenziert; eine eigene `ha/api-client-patterns`-Spec ist eine Folge-Spec, sobald Skills HTTP-Clients direkt scaffolden
- Multi-Instance-Disambiguation-Helper: Detail in `ha/services` § Multi-Instance-Disambiguation
- Redaction-Set-Form: Detail in `ha/diagnostics` § `TO_REDACT`-Set

## Akzeptanzkriterien

- [ ] HTTP-Client der Integration enthält eine kompilierte Pfad-Whitelist (Regex oder ähnliche Konstrukt)
- [ ] Jeder HTTP-Request läuft durch die Whitelist-Validierung; Mismatches werfen eine integration-spezifische Exception
- [ ] Bearer-Token-Setzung ist in einer einzigen Helper-Methode gekapselt; die Helper-Methode ist die einzige Stelle, an der Auth-Header gesetzt werden
- [ ] Eine `grep`-Suche nach `Authorization` in den Source-Dateien (außer im API-Client-Helper) liefert keine Treffer
- [ ] Config-Flow-Schema verwendet `vol.Match`/`vol.Length` für URL- und Credential-Felder
- [ ] Service-Handler rufen den `_resolve_entry`-Helper aus `ha/services` und brechen bei Mehrdeutigkeit mit `ServiceValidationError` ab
- [ ] `diagnostics.py` redactet alle Credentials und Multi-Tenant-Identifier (siehe `ha/diagnostics`)
- [ ] Eine `grep`-Suche nach `_LOGGER\.[a-z]+\(.*api_key`, `_LOGGER\.[a-z]+\(.*token`, `_LOGGER\.[a-z]+\(.*password` liefert keine Treffer
- [ ] Quality-Scale-Marker: **Silver**

## Offene Fragen

- **API-Client-Spec-Reifegrad**: Aktuell ist die HTTP-Client-Form (`api.py`-Layout, Exception-Hierarchie, Path-Whitelist-Form) nur indirekt über kamerplanter-ha-Cross-Referenz definiert. Wann wird daraus eine eigene `ha/api-client-patterns`-Spec?
- **TLS-Verifikation-Default**: Sollen Skills `verify=True` (TLS-Cert-Validierung) als Default forcen, oder bleibt das Backend-spezifisch (manche selbst-signierte Local-Backends)?
- **Whitelist-Granularität**: Wie spezifisch muss die Path-Whitelist sein? Aktuell als „passende Backend-Pfade matchen" formuliert; eine Heuristik (Endpoint-pro-Endpoint vs. Top-Level-Bereich) fehlt.
- **Bearer-Token-Verbot in Logs Hard-Enforce**: Eine `grep`-basierte CI-Regel als Acceptance-Criterion; soll daraus ein verpflichtender Lint-Hook werden (z. B. ein bandit-/semgrep-Pattern), oder reicht der Code-Review?
- **Audit-Log-Ergänzung**: Soll die Spec audit-relevante Aktionen (Service-Aufrufe, Reauth-Vorgänge) in HA-System-Events spiegeln, damit User sie im Logbook nachvollziehen können?
