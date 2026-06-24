# HA-Integration: Repairs und Issue-Registry

Status: draft

## Kontext

Home Assistant führt eine **Issue-Registry**, über die Integrationen den User auf Probleme hinweisen, die seine Aufmerksamkeit oder sein Eingreifen verlangen — Deprecations, veraltete Backend-Versionen, Fehlkonfigurationen. Solche Issues erscheinen im Frontend unter „Repairs". Ein Issue ist entweder **fixable** (der User kann es über einen `RepairsFlow` direkt im UI lösen) oder **informativ** (es verlinkt auf eine Doku-Seite, der User behebt es selbst).

HA stellt dafür `homeassistant.helpers.issue_registry.async_create_issue(...)` zum Anlegen und `async_delete_issue(...)` zum Entfernen bereit. Fixable Issues brauchen ein `repairs.py`-Modul mit `async_create_fix_flow(...)`, das einen `RepairsFlow` zurückgibt. Die Issue-Texte leben übersetzt in `strings.json` unter `issues:`. Entscheidend ist die Abgrenzung: Repairs sind für Zustände gedacht, gegen die der User *etwas tun kann* — transiente Verbindungsfehler gehören **nicht** in die Issue-Registry, sondern in das Coordinator-Fehlerhandling (`UpdateFailed`, `entity-unavailable`).

Quality-Scale-Marker: **Gold** (`repair-issues` ist eine Gold-Regel: Repair-Issues und Repair-Flows werden eingesetzt, sobald User-Intervention nötig ist).

## Ziele

- `async_create_issue` als Standard-Weg etablieren, den User auf actionable Probleme hinzuweisen (Deprecations, veraltete Backend-Versionen, Fehlkonfiguration)
- Die Trennung zwischen fixable (`RepairsFlow`) und informativen Issues sauber definieren
- Issue-Texte konsequent über `strings.json`/`issues:` übersetzbar machen — keine hartkodierten Strings
- Den Issue-Lebenszyklus (anlegen, aktualisieren, löschen) an den tatsächlichen Problem-Zustand binden, damit veraltete Issues nicht stehen bleiben
- Repairs scharf von transienten Laufzeitfehlern abgrenzen, die in das Coordinator-Fehlerhandling gehören

## Nicht-Ziele

- System-Health-Modul (`system_health.py`) — eigener HA-Mechanismus, eigene Folge-Spec
- Issues, die eine Integration im Namen einer *anderen* Integration anlegt (`issue_domain`) — selten und außerhalb des Standard-Patterns dieser Spec
- Mehrstufige Repair-Flows mit komplexer User-Eingabe — diese Spec deckt den `ConfirmRepairFlow`-Standardfall ab; aufwendige Flows sind ein eigenes Thema
- Frontend-Darstellung der Repairs-Karte — gehört zum HA-Core, nicht zur Integration

## Anforderungen

### Issue erstellen

- **MUSS [MUST]** Issues über `homeassistant.helpers.issue_registry.async_create_issue(hass, domain, issue_id, ...)` anlegen — manuelle Manipulation der Registry oder direkte Persistenz ist verboten
- **MUSS [MUST]** beim Anlegen mindestens `domain`, `issue_id`, `is_fixable`, `severity` (`IssueSeverity`) und `translation_key` setzen — `issue_id` ist innerhalb der `domain` eindeutig
- **SOLLTE [SHOULD]** bei Deprecations `breaks_in_ha_version` setzen, damit der User die Version sieht, ab der das Verhalten bricht
- **KANN [MAY]** `translation_placeholders`, `learn_more_url` und `data` ergänzen — `data` ist beliebig und wird dem User nicht angezeigt, sondern an den Repair-Flow durchgereicht
- **MUSS [MUST]** `severity` aus `IssueSeverity` wählen — `ERROR` wenn aktuell etwas kaputt ist, `WARNING` wenn etwas in Zukunft bricht (z. B. API-Abschaltung); `CRITICAL` ist reserviert und nur für echten Panik-Zustand

### Fixable vs. informativ

- **MUSS [MUST]** `is_fixable=True` nur setzen, wenn ein `RepairsFlow` existiert, der das Problem tatsächlich behebt — ein fixable Issue ohne Flow ist ein Bruch
- **MUSS [MUST]** `is_fixable=False` setzen, wenn der User das Problem nur selbst lösen kann (z. B. Backend updaten, Konfiguration ändern) — dann **SOLLTE [SHOULD]** `learn_more_url` auf die Anleitung zeigen
- **MUSS NICHT [MUST NOT]** Repair-Issues für reine „etwas ist kaputt"-Meldungen anlegen, gegen die der User nichts tun kann — Repair-Issues müssen actionable und informativ über das Problem sein

### Repair-Flow

- **MUSS [MUST]** für fixable Issues ein `repairs.py`-Modul im `custom_components/<domain>/`-Ordner enthalten
- **MUSS [MUST]** in `repairs.py` `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow` als Top-Level-Async-Funktion exportieren — HA ruft sie auf, wenn der User den Repair startet, und routet anhand von `issue_id` zum passenden Flow
- **MUSS [MUST]** den Flow von `homeassistant.components.repairs.RepairsFlow` ableiten und einen `async_step_init` als Einstieg implementieren; für den reinen Bestätigungs-Fall **KANN [MAY]** stattdessen `ConfirmRepairFlow` verwendet werden
- **MUSS [MUST]** den Flow mit `self.async_create_entry(title="", data={})` abschließen, sobald die Reparatur erfolgreich war — ein erfolgreich abgeschlossener Flow entfernt das Issue automatisch aus der Registry

### Übersetzungen

- **MUSS [MUST]** den `translation_key` jedes Issues in `strings.json` unter `issues:` mit `title` und `description` hinterlegen — keine hartkodierten User-sichtbaren Strings im Python-Code
- **MUSS [MUST]** alle in `translation_placeholders` referenzierten Platzhalter im Übersetzungstext auflösen, damit der gerenderte Text vollständig ist
- **SOLLTE [SHOULD]** den Repair-Flow-Schritten (`step_id`) ebenfalls Übersetzungen in `strings.json` zuordnen, damit Formular-Titel und -Beschreibung lokalisiert sind
- Übersetzung folgt im Detail der Schwester-Spec `ha/translations`

### Issue-Lebenszyklus (löschen/aktualisieren)

- **MUSS [MUST]** ein Issue über `async_delete_issue(hass, domain, issue_id)` entfernen, sobald die Integration feststellt, dass der zugrunde liegende Zustand behoben ist — sonst bleibt ein veraltetes Issue in der Registry stehen
- **SOLLTE [SHOULD]** ein erneutes `async_create_issue` mit derselben `issue_id` nutzen, um ein bestehendes Issue zu aktualisieren — die Registry führt es weiter unter der eindeutigen `issue_id`
- **SOLLTE [SHOULD]** `is_persistent=True` setzen, wenn das Problem nur im Moment seines Auftretens erkennbar ist (z. B. fehlgeschlagenes Update, unbekannte Aktion in einer Automation) — dann wird das Issue auch nach einem HA-Neustart wieder angezeigt
- **SOLLTE [SHOULD]** `is_persistent=False` lassen, wenn der Zustand bei jedem Start neu prüfbar ist (z. B. veraltete Backend-Version) — die Integration legt das Issue beim nächsten Start ohnehin neu an, falls es noch besteht
- **MUSS NICHT [MUST NOT]** sich darauf verlassen, dass HA Issues automatisch räumt — das Anlegen *und* Löschen liegt in der Verantwortung der Integration

### Abgrenzung zu transienten Fehlern

- **MUSS NICHT [MUST NOT]** transiente Verbindungs- oder API-Fehler als Repair-Issue anlegen — ein kurzzeitig nicht erreichbares Backend ist kein actionable Problem für den User
- **MUSS [MUST]** transiente Fehler stattdessen im Coordinator über `UpdateFailed` melden, sodass die Entitäten als `entity-unavailable` markiert werden — Details in der Schwester-Spec `ha/coordinator-patterns`
- **SOLLTE [SHOULD]** ein Issue nur dann anlegen, wenn ein wiederkehrender oder dauerhafter Zustand vorliegt, gegen den der User konkret etwas tun kann (z. B. ungültige Credentials nach Passwort-Rotation, abgekündigte API)

## Akzeptanzkriterien

- [ ] Jedes `async_create_issue` setzt `domain`, `issue_id`, `is_fixable`, `severity` und `translation_key`
- [ ] Kein `async_create_issue` mit `is_fixable=True` ohne zugehörigen `RepairsFlow` in `repairs.py`
- [ ] `repairs.py` existiert und exportiert `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow`, sobald ein fixable Issue angelegt wird
- [ ] Jeder `translation_key` aus `async_create_issue` ist in `strings.json` unter `issues:` mit `title` und `description` aufgelöst
- [ ] Eine `grep`-Suche nach hartkodierten User-Strings in `async_create_issue`-Aufrufen (statt `translation_key`) liefert keine Treffer
- [ ] Zu jedem behebbaren Zustand existiert ein `async_delete_issue`-Pfad, der das Issue nach Behebung entfernt
- [ ] Transiente Verbindungsfehler werden über `UpdateFailed` im Coordinator gemeldet, nicht über `async_create_issue`
- [ ] Quality-Scale-Marker: **Gold**

## Offene Fragen

- **`is_persistent`-Default**: Soll die Spec einen Default vorgeben oder pro Issue-Typ entscheiden lassen? Aktuell als SOLLTE pro Fall formuliert; ein kalibrierter Default-Trigger fehlt.
- **Repair-Flow-Komplexität**: Ab welcher Komplexität lohnt ein mehrstufiger Flow gegenüber `ConfirmRepairFlow` plus Doku-Link? Aktuell nicht abgegrenzt.
- **Issue-vs-ConfigEntryError-Schwelle**: Das Quality-Scale-Beispiel kombiniert ein informatives Issue mit `raise ConfigEntryError`. Wann reicht das Issue allein, wann braucht es zusätzlich den harten Setup-Abbruch?
- **Deduplizierung bei mehreren Entries**: Bei mehreren ConfigEntries derselben Domain — eine `issue_id` pro Entry oder ein geteiltes Issue? Aktuell nicht standardisiert.
