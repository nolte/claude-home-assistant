# HA-Integration: Exceptions und Fehler-Übersetzungen

Status: draft

## Kontext

Wenn in einer Custom Integration etwas schiefgeht — ein Service-Action-Aufruf, eine Entity-Methode (z. B. *Set HVAC Mode*) oder ein Hintergrund-Task — muss der Fehler über eine HA-Exception signalisiert werden, deren Message dem Nutzer in der UI angezeigt wird. HA generiert diese Message entweder aus einem angehängten Übersetzungs-String oder aus dem Exception-Argument. Eine saubere Exception-Strategie unterscheidet, **wer** den Fehler verursacht hat: ein falsch bedienender Nutzer (`ServiceValidationError`) oder das System / das Gerät / die API (`HomeAssistantError`).

Die HA-Doku verlangt, dass Integrationen `ServiceValidationError` statt `ValueError` werfen, wenn der Nutzer etwas falsch gemacht hat — in diesem Fall wird der Stack-Trace nur auf Debug-Level geloggt, nicht voll ausgegeben. Für andere Fehler (z. B. ein Kommunikationsproblem mit einem Gerät) verlangt sie `HomeAssistantError`; hier wird der volle Stack-Trace ins Log geschrieben. Beide Klassen und ihre Subklassen unterstützen Lokalisierung über `translation_domain` / `translation_key`, mit den Strings in `strings.json` unter dem `exceptions:`-Schlüssel.

Quality-Scale-Marker: **Silver** (`action-exceptions` — Service-Actions werfen Exceptions bei Fehlern) und **Gold** (`exception-translations` — Exception-Messages sind übersetzbar). Diese Spec überführt beide Regeln in eine verbindliche Konvention für jede Custom Integration, die Skills aus diesem Plugin scaffolden.

## Ziele

- Die HA-Exception-Hierarchie als verbindliches Vokabular festschreiben: `HomeAssistantError` als Basis (Message wird dem Nutzer gezeigt), `ServiceValidationError` für ungültige Nutzereingaben, die `ConfigEntryError`-Familie für Setup-/Lifecycle-Fehler
- Die Verursacher-Unterscheidung erzwingen: Nutzer-Fehler → `ServiceValidationError` (kein voller Stack-Trace); System-/Geräte-Fehler → `HomeAssistantError` (Stack-Trace im Log)
- Übersetzbare Exceptions als Default verlangen: `translation_domain` + `translation_key` (+ optional `translation_placeholders`) statt hartkodierter Message-Strings
- Eine eindeutige Abgrenzung zwischen `raise` (Fehler signalisieren) und `log` (Diagnose-Information ohne Abbruch) ziehen
- Generische Catches und stilles Verschlucken von Fehlern verbieten

## Nicht-Ziele

- Coordinator-Error-Mapping (`UpdateFailed`, `ConfigEntryAuthFailed`, `ConfigEntryNotReady` im `_async_update_data`-Pfad) — wird in `ha/coordinator-patterns` definiert und hier nur referenziert, nicht dupliziert
- Service-/Action-Schema-Definition (Felder, Selektoren, Response-Typen) — fällt in `ha/services`
- Der vollständige Übersetzungs-Workflow (`strings.json`-Struktur, `translations/<lang>.json`, Sync-Mechanik) — fällt in `ha/translations`; diese Spec verlangt nur den `exceptions:`-Block und die Verdrahtung der Exception mit dem Übersetzungsschlüssel
- Frontend-seitige Fehlerdarstellung (Toasts, Repair-Issues, `ir.async_create_issue`) — eigene Folge-Spec, sobald sie konkret nötig wird

## Anforderungen

### Exception-Hierarchie

- **MUSS [MUST]** ausschließlich HA-Exceptions aus `homeassistant.exceptions` werfen, deren Message dem Nutzer angezeigt werden darf — `HomeAssistantError` ist die Basisklasse, ihre Message wird in der UI gezeigt
- **MUSS [MUST]** `ServiceValidationError` (eine `HomeAssistantError`-Subklasse) für ungültige Nutzereingaben an einen Service / eine Action verwenden — sie wird geworfen, **bevor** die eigentliche Arbeit beginnt, und ohne vollen Stack-Trace ausgegeben
- **MUSS [MUST]** die `ConfigEntryError`-Familie (`ConfigEntryError`, `ConfigEntryAuthFailed`, `ConfigEntryNotReady`) ausschließlich im Setup-/Lifecycle-Kontext verwenden, nicht in Action-Handlern (das Coordinator-Mapping dieser Klassen lebt in `ha/coordinator-patterns`)
- **MUSS NICHT [MUST NOT]** bare `Exception`, `ValueError` oder andere nicht-HA-Exceptions an die UI propagieren lassen — sie erzeugen einen vollen Stack-Trace ohne nutzbare Nutzer-Message

### Nutzer-Fehler vs. System-Fehler

- **MUSS [MUST]** Fehler, die durch falsche Bedienung entstehen (ungültige Eingabe, Referenz auf etwas Nicht-Existentes), als `ServiceValidationError` werfen — der Stack-Trace erscheint dann nur auf Debug-Level
- **MUSS [MUST]** Fehler, die im Service / System selbst entstehen (Netzwerkfehler, Geräte-Kommunikationsproblem, Bug), als `HomeAssistantError` werfen — der volle Stack-Trace wird ins Log geschrieben
- **MUSS [MUST]** die Validierung des Nutzer-Inputs durchführen, **bevor** kostspielige oder seiteneffektbehaftete Arbeit beginnt — `ServiceValidationError` signalisiert „nichts wurde verändert“
- **SOLLTE [SHOULD]** die ursprüngliche Low-Level-Exception als Cause behalten, wenn ein System-Fehler auf `HomeAssistantError` gemappt wird (`raise HomeAssistantError(...) from err`), damit der Stack-Trace im Log nicht verloren geht

### Übersetzbare Exceptions

- **MUSS [MUST]** geworfene Exceptions mit `translation_domain=DOMAIN` und `translation_key="<key>"` annotieren, statt die Message-Strings hartzukodieren — die Exception-Klasse muss von `HomeAssistantError` erben, damit die Übersetzung greift
- **MUSS [MUST]** die zugehörigen Message-Strings in `strings.json` unter dem `exceptions:`-Schlüssel definieren, mit je einem `message`-Feld pro `translation_key`
- **KANN [MAY]** `translation_placeholders={...}` an die Exception übergeben, um dynamische Werte in die übersetzte Message einzusetzen (z. B. den betroffenen Entity-Namen oder Zeitwert)
- **SOLLTE [SHOULD]** `translation_key`-Namen sprechend und stabil wählen (z. B. `end_date_before_start_date`, `cannot_connect_to_schedule`), da sie Teil des Übersetzungs-Contracts gegenüber `ha/translations` sind
- **MUSS NICHT [MUST NOT]** denselben `translation_key` mit unterschiedlichen Platzhalter-Erwartungen wiederverwenden — jeder Schlüssel hat einen festen Message-Vertrag

### Action-/Service-Fehlerbehandlung

- **MUSS [MUST]** in jedem Service-/Action-Handler ungültige Eingaben als `ServiceValidationError` und tatsächliche Ausführungsfehler als `HomeAssistantError` werfen (siehe `ha/services` für die Schema-Seite des Handlers)
- **MUSS [MUST]** API-spezifische Low-Level-Exceptions im Handler abfangen und auf die passende HA-Exception mappen (`except MyConnectionError as err: raise HomeAssistantError(...) from err`), statt sie roh durchzureichen
- **MUSS NICHT [MUST NOT]** einen Fehler im Handler still verschlucken (leerer `except`, `pass`, oder Rückgabe eines Erfolgs-Sentinels trotz Fehler) — jeder Fehler wird als Exception signalisiert oder bewusst geloggt
- **MUSS NICHT [MUST NOT]** bare `raise Exception(...)` oder `raise ValueError(...)` in einem Handler verwenden — der Nutzer erhielte dann keine brauchbare Message

### Logging-Abgrenzung

- **MUSS [MUST]** `raise` verwenden, wenn die Operation fehlschlägt und dem Nutzer ein Fehler gemeldet werden muss — eine geloggte Zeile ohne `raise` lässt den Aufrufer fälschlich Erfolg annehmen
- **SOLLTE [SHOULD]** `_LOGGER.debug/warning/error` für nicht-abbrechende Diagnose-Information verwenden (z. B. ein einzelner übersprungener Anreicherungs-Eintrag), wobei jede geloggte Zeile genug Kontext für die Lokalisierung enthält
- **MUSS NICHT [MUST NOT]** denselben Fehler sowohl loggen als auch werfen, sodass er doppelt im Log erscheint — entweder `raise` (HA loggt ihn), oder bewusst loggen ohne `raise`
- **MUSS NICHT [MUST NOT]** Geheimnisse (API-Keys, Tokens, Passwörter) oder vollständige Roh-Payloads in geloggte Fehler oder Exception-Messages schreiben (siehe `ha/security-hardening` für die Redaction-Pflicht)

## Akzeptanzkriterien

- [ ] Jeder Service-/Action-Handler wirft `ServiceValidationError` für ungültige Nutzereingaben und `HomeAssistantError` für Ausführungsfehler
- [ ] Kein Handler propagiert bare `Exception` oder `ValueError` an die UI
- [ ] Nutzer-Input wird validiert, bevor seiteneffektbehaftete Arbeit beginnt
- [ ] Auf `HomeAssistantError` gemappte System-Fehler behalten die Original-Exception via `from err`
- [ ] Geworfene Exceptions tragen `translation_domain` und `translation_key`, ihre Klasse erbt von `HomeAssistantError`
- [ ] `strings.json` enthält einen `exceptions:`-Block mit je einem `message` pro verwendetem `translation_key`
- [ ] Dynamische Werte in Messages werden über `translation_placeholders` eingesetzt, nicht durch String-Interpolation
- [ ] Kein Handler verschluckt Fehler still (kein leerer `except` / `pass` über einem Fehlerpfad)
- [ ] Kein Fehler wird zugleich geloggt und geworfen (keine doppelte Log-Ausgabe)
- [ ] Quality-Scale-Marker sind gesetzt: **Silver** (`action-exceptions`) und **Gold** (`exception-translations`)

## Offene Fragen

- **`ServiceValidationError`-Platzhalter-Konvention**: Sollen Validierungs-Exceptions standardmäßig `translation_placeholders` mit dem betroffenen Feldnamen führen, oder reicht eine statische Message pro Validierungsfall? `kamerplanter-ha` hat dafür noch kein einheitliches Muster.
- **Repair-Issues vs. Exceptions**: Wann ist ein persistenter Repair-Issue (`ir.async_create_issue`) der richtige Kanal statt einer Exception pro Aufruf? Eigene `ha/repairs`-Spec, sobald die erste Integration langlebige Fehlerzustände meldet.
- **Entity-Methoden-Abdeckung**: Die HA-Doku nennt Entity-Methoden (z. B. *Set HVAC Mode*) gleichrangig mit Service-Actions. Soll diese Spec separate Akzeptanzkriterien für Entity-Methoden-Handler führen, oder genügt die Handler-Verallgemeinerung?
- **Übersetzungs-Coverage-Gate**: Soll ein Test erzwingen, dass jeder im Code verwendete `translation_key` einen Eintrag im `exceptions:`-Block hat (und umgekehrt kein toter Key existiert)? Die Mechanik dafür gehört zu `ha/translations`.
