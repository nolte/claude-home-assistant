# Skill: `ha-blueprint-scaffold`

Status: draft

## Kontext

Ein Home-Assistant-Blueprint ist ein reines YAML-Artefakt (Automation, Script oder Template-Entity) mit `!input`-Platzhaltern, das Nutzer ohne Code befüllen ([`ha/blueprint-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/blueprint-patterns/de.md)). Anders als eine Custom Integration gibt es hier keinen Python-Code, kein Coordinator-Lifecycle und keinen Test-Harness — die gesamte Qualität entscheidet sich an Schema-Korrektheit, Selector-UX und Template-Robustheit. Das macht das Erzeugen eines Blueprints zu einem eng umrissenen Draft-Validate-Iterate-Vorgang.

Dieser Skill ist der **Einstiegspunkt** für genau diesen Vorgang. Er übernimmt nicht selbst die Generierung, sondern sammelt die Intent- und Pfad-Parameter, führt eine schlanke Pre-Flight aus und **dispatcht den Agent [`ha-blueprint-author`](https://github.com/nolte/claude-home-assistant/blob/develop/agents/ha-blueprint-author.md)**, der den generativen Loop (Draft → Offline-Validierung → Reparatur → Conformance-Report) in einer eigenen Tool-Session kapselt. Der Skill spiegelt anschließend den Report des Agents zurück an den Nutzer.

Die Trennung folgt dem etablierten Muster „Skill = Aktivierung + Eingabe-Sammlung + Pre-Flight + Dispatch + Report-Relay; Agent = schwergewichtiger Generierungs-Loop". Sie hält die Hauptkonversation frei vom Validierungs-Churn (wiederholte YAML-Renders, Lint-Ausgaben) und gibt dem Nutzer einen klaren, einzelnen Slash-Command-Einstieg.

## Scope

Der Skill erzeugt **ein** Blueprint pro Aufruf für **eine** Domain (`automation`, `script` oder `template`). Er dispatcht für die eigentliche Generierung den `ha-blueprint-author`-Agent und reimplementiert dessen Loop nicht inline. Er schreibt keinen Python-Code, importiert nichts in eine laufende HA-Instanz und bündelt keine Mehrfach-Blueprints.

## Ziele

- Einen einzelnen, auffindbaren Einstiegspunkt (`/claude-home-assistant:ha-blueprint-scaffold`) für die Blueprint-Erstellung bereitstellen
- Die für den Agent nötigen Parameter (Intent, Domain, Zielpfad, Autor, optional `source_url`) interaktiv vollständig sammeln, bevor dispatcht wird
- Eine Pre-Flight ausführen, die Kollisionen (bestehendes Blueprint) und Pfad-Probleme **vor** dem Dispatch abfängt
- Den `ha-blueprint-author`-Agent als alleinigen Generierungs-Pfad nutzen — der Skill erzeugt das YAML nicht selbst
- Den CONFORMANT/NEEDS-WORK-Report des Agents plus den geschriebenen Dateipfad transparent an den Nutzer zurückspiegeln

## Nicht-Ziele

- Die generative Logik selbst — die liegt vollständig im `ha-blueprint-author`-Agent und in `ha/blueprint-patterns`
- Custom-Integration-Scaffolding (`ha-integration-scaffold`), Lovelace-Cards (`ha-lovelace-card-scaffold`), Integration-Services (`ha-service-definition-generator`)
- Import, Deployment oder Push eines Blueprints in eine laufende HA-Instanz
- Editieren/Versionieren eines bereits veröffentlichten Blueprints jenseits eines Neu-Drafts — rückwärtskompatible Updates regelt `ha/blueprint-patterns`; ein dedizierter Augment-Skill kann später folgen
- Mehrere Blueprints in einem Aufruf

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „scaffold a blueprint for <intent>"
  - „create an automation blueprint"
  - „turn this automation into a blueprint"
  - „draft a motion-light blueprint"
  - „schreibe ein Blueprint für <Intent>"
  - „erstelle ein Automations-Blueprint"
  - „mach aus dieser Automation ein Blueprint"
- **MUSS NICHT [MUST NOT]** aktivieren bei:
  - Custom-Integration-Scaffolding (`ha-integration-scaffold`)
  - Lovelace-Card-Scaffolding (`ha-lovelace-card-scaffold`)
  - Integration-Service-Definition (`ha-service-definition-generator`)
  - Import/Deployment in eine laufende HA-Instanz

### Eingabe-Sammlung

- **MUSS [MUST]** vor dem Dispatch den `intent` (was das Blueprint tun soll, in Prosa) erfassen — ohne Intent kein Dispatch
- **MUSS [MUST]** die `domain` bestimmen (`automation`, `script`, `template`); fehlt sie, gilt `automation` als Default, der im Report explizit genannt wird
- **SOLLTE [SHOULD]** Zielpfad (`target_dir`), `author` und — falls das Blueprint geteilt werden soll — `source_url` erfassen; fehlende Werte fallen auf dokumentierte Defaults zurück
- **MUSS [MUST]** jeden gewählten Default im Dispatch und im zurückgespiegelten Report sichtbar machen — kein stilles Defaulten

### Pre-Flight

- **MUSS [MUST]** prüfen, dass der Zielpfad existiert bzw. unter einem schreibbaren Verzeichnis liegt, **bevor** dispatcht wird
- **MUSS [MUST]** eine Kollision mit einem bestehenden Blueprint gleichen Pfads abfangen und mit zitiertem Pfad abbrechen statt zu überschreiben
- **SOLLTE [SHOULD]** bei Schreiben in einen HA-Config-Baum den kanonischen Zielpfad `blueprints/<domain>/<author>/<file>.yaml` herleiten und dem Nutzer vor dem Dispatch zur Bestätigung anzeigen

### Dispatch und Report-Relay

- **MUSS [MUST]** die eigentliche Generierung an den `ha-blueprint-author`-Agent delegieren und dessen Loop nicht inline nachbauen
- **MUSS [MUST]** alle gesammelten Parameter (Intent, Domain, Pfad, Autor, `source_url`, `min_version`) an den Agent durchreichen
- **MUSS [MUST]** den CONFORMANT/NEEDS-WORK-Report des Agents plus den relativen Dateipfad an den Nutzer zurückspiegeln
- **MUSS NICHT [MUST NOT]** den vollständigen Blueprint-YAML inline ausgeben, wenn der Nutzer es nicht verlangt — die geschriebene Datei ist das Artefakt
- **SOLLTE [SHOULD]** bei einem NEEDS-WORK-Report die vom Agent genannten Caller-Follow-ups als nächste Entscheidungen an den Nutzer weiterreichen

## Akzeptanzkriterien

- [ ] Der Skill aktiviert auf die genannten EN- und DE-Trigger-Phrasen und nicht auf die abgegrenzten Nachbar-Fälle
- [ ] `intent` wird vor dem Dispatch erfasst; ohne Intent erfolgt kein Dispatch
- [ ] `domain` ist bestimmt (Default `automation` wird, falls gewählt, explizit genannt)
- [ ] Pre-Flight bricht bei Pfad-Kollision mit zitiertem Pfad ab, ohne zu überschreiben
- [ ] Die Generierung läuft über den `ha-blueprint-author`-Agent; der Skill baut den Loop nicht inline nach
- [ ] Alle gesammelten Parameter werden an den Agent durchgereicht
- [ ] Der Agent-Report (CONFORMANT/NEEDS-WORK) plus Dateipfad wird an den Nutzer zurückgespiegelt
- [ ] Jeder gewählte Default ist im Report sichtbar gemacht

## Offene Fragen

- **Interaktivität vs. Ein-Schuss**: Soll der Skill bei unvollständigem Intent gezielt nachfragen (mehr Runden) oder mit dokumentierten Defaults sofort dispatchen? Aktuell ist „Intent ist Pflicht, Rest defaultet" gewählt.
- **Augment-Schwester**: Braucht es analog zu `ha-coordinator-add` einen `ha-blueprint-augment`-Skill für additive, rückwärtskompatible Edits an einem bestehenden Blueprint? Erst bei konkretem Bedarf.
- **Validierungs-Gate**: Die Pre-Flight prüft Pfad/Kollision, nicht Schema. Soll der Skill ein optionales Post-Dispatch-Gate führen, das den Agent-Report auf CONFORMANT prüft, bevor er als „fertig" gilt? Hängt an der in `ha/blueprint-patterns` offenen Validierungs-Toolchain.
