# Skill: `ha-solution`

Status: draft

## Kontext

Es gibt vier Domänen-Frontdoors — `ha-integration-solution` (Python-Custom-Integration-Backend), `ha-lovelace-solution` (Lovelace/Frontend), `ha-automation-solution` (YAML-Automationen/Helper) und `ha-pixoo-solution` (Divoom-Pixoo-Anzeige) — aber **keinen Orchestrator darüber**. Die Domänen-Auswahl beruht auf implizitem Skill-Beschreibungs-Matching, und eine echt domänenübergreifende Anfrage (z. B. eine Custom-Card + die zugrunde liegende Integration + eine Automation) fällt zwischen die vier Frontdoors: Wer eine gemischte Anforderung hat, muss selbst auf der richtigen Domänen-Lösung landen, und kein einzelner Skill besitzt eine domänenübergreifende Anfrage.

Dieser Skill ist der **oberste Router**: Er klassifiziert eine unscharfe Home-Assistant-Anforderung in eine oder mehrere Domänen, routet jeden Teil an die zuständige `*-solution` und fädelt die geteilten Identitäten (`domain`, `entity_id`s, Card-Tags, Command-Types) über Domänengrenzen. Er besitzt keine Domänen-Artefakte und macht keine domäneninterne Zerlegung — jede Domänen-Lösung behält ihr eigenes Plan-Freigabe-Gate, ihre Zerlegung, ihr Dispatch und ihre Spec-Konformität.

## Scope

Domänen-Klassifikation und domänenübergreifendes Routing über der `ha-*-solution`-Familie. Eine Anforderung pro Lauf → ein Domänen-Plan → N dispatchte `*-solution`s in Abhängigkeitsreihenfolge → ein Gesamt-Bericht. Der Router entscheidet, *welche Domänen* eine Anforderung umspannt, *in welcher Reihenfolge* sie laufen und *welche Identitäten* über Grenzen gefädelt werden — nie den Inhalt eines einzelnen Domänen-Artefakts.

## Ziele

- Jede Home-Assistant-Anforderung an einem einzigen Eingangspunkt annehmen und an die korrekte(n) Domänen-Lösung(en) routen, ohne dass die Nutzerin die Domänen-Landschaft kennt
- Die Anforderung in eine oder mehrere von Integration/Backend, Lovelace/Frontend, YAML-Automation und Pixoo klassifizieren
- Eine domänenübergreifende Anforderung über die relevanten `*-solution`s in Abhängigkeitsreihenfolge zerlegen und die geteilten Identitäten (`domain`, `entity_id`s, Device-IDs, Card-Tag/`custom:<type>`, Command-`type`) über Domänengrenzen fädeln
- Die Domänen-Lösungen zur Laufzeit gegen das lebende `ha-*-solution`-Inventar auflösen, sodass eine hinzugefügte oder umbenannte Domänen-Lösung routbar ist, ohne diesen Skill zu ändern
- Sauber gegen die vier Domänen-Lösungen abgrenzen: Eine Single-Domain-Anforderung routet direkt an ihre zuständige `*-solution`

## Nicht-Ziele

- Die eigene Artefakt-Zerlegung, Generierung und Spec-Konformität einer Domäne — das bleibt bei der zuständigen `*-solution` und ihrer Familie
- Selbst irgendein Artefakt erzeugen
- Die interne Zerlegung oder die Berichte einer Domänen-Lösung neu bewerten oder neu planen — der Router reicht sie weiter
- Deployment in eine laufende HA-Instanz oder Import dorthin — die Domänen-Lösungen und ihre Agenten besitzen das

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** bei ergebnisorientierten HA-Anfragen aktivieren, bei denen die Domäne unklar ist oder mehrere umspannt:
  - „eine Custom-Card für meine Pumpe, die Integration dahinter und eine Automation, die darauf reagiert"
  - „eine Komplettlösung: Integration + Dashboard + Pixoo-Status-Seite"
  - „baue mir eine komplette HA-Lösung für …", „ich brauche Integration, Dashboard und Automation für …"
- **SOLLTE [SHOULD]** nicht aktivieren, wenn die Domäne bereits eindeutig und einzeln ist (die zuständige `ha-*-solution` greift direkt) oder die Anforderung ein einzelnes klares Artefakt ist (der zuständige Einzel-Skill greift)

### Eingaben

- **MUSS [MUST]** erfassen: `requirement` (Prosa, das gewünschte HA-Ergebnis)
- **KANN [MAY]** erfassen: `target_dir` (Repo- / HA-Config-Root, an die Domänen-Lösungen durchgereicht) und `known_identities` (eine bestehende `domain`, `entity_id`s oder ein Card-Tag, als Quellen zu fädeln)

### Pre-Flight

- **MUSS [MUST]** prüfen, dass `requirement` nicht leer ist; dann die Anforderungs-Konfidenz einschätzen — eine klar spezifizierte Anforderung nutzt den leichten Pfad (1–3 gezielte Fragen: welches Geräte-/Entity-Ziel, ob eine Dashboard-Oberfläche gewünscht ist, ob eine Automation reagieren soll), während eine Anforderung unterhalb einer Konfidenzschwelle (vages oder breites domänenübergreifendes Ergebnis, ungenannte Ziele, unklarer Scope) **MUSS [MUST]** zuerst `requirements-elicit` dispatchen und gegen das bestätigte Anforderungs-Artefakt klassifizieren, analog zum `issue-orchestrate`-Upstream-Gate — bevor klassifiziert wird
- **MUSS [MUST]** eine klar single-domain Anforderung direkt an die zuständige `*-solution` routen, statt eine Routing-Schicht hinzuzufügen

### Klassifikations- & Routing-Regeln

- **MUSS [MUST]** die zuständige Domänen-Lösung für jeden klassifizierten Teil zur Laufzeit auflösen, indem die Anforderung gegen das lebende `ha-*-solution`-Skill-Inventar (die genannte Zuständigkeit jedes Kandidaten) abgeglichen wird, nicht aus einer eingefrorenen Namensliste — die Klassifikations-Zuordnungen sind ein illustrativer Anker, bei jedem Lauf neu aufgelöst, sodass eine zur Familie hinzugefügte oder entfernte Domänen-Lösung routbar ist, ohne den Router zu ändern (analog zum Runtime-Lookup-Dispatch von `issue-orchestrate`)
- **MUSS [MUST]** die Anforderung in eine oder mehrere Domänen klassifizieren — Integration/Backend → `ha-integration-solution`, Lovelace/Frontend → `ha-lovelace-solution`, YAML-Automation → `ha-automation-solution`, Pixoo → `ha-pixoo-solution`
- **MUSS [MUST]** vor dem Routen einen Domänen-Plan als Tabelle in Abhängigkeitsreihenfolge präsentieren: je Eintrag `#`, Domäne, zuständige `*-solution`, Abhängigkeit (`depends-on`), gefädelte Identitäten, Zweck — und auf explizite Bestätigung warten
- **MUSS [MUST]** die Domänen-Lösungen in Abhängigkeitsreihenfolge dispatchen — ein Backend vor dem Frontend/der Automation, die es konsumiert; die typische Reihenfolge ist Integration/Backend → Lovelace/Frontend → Automation → Pixoo — und die in einer Domäne erzeugten Identitäten (`domain`, `entity_id`s, Device-IDs, Card-Tag/`custom:<type>`, Command-`type`) in die Eingaben abhängiger Domänen-Lösungen fädeln
- **MUSS NICHT [MUST NOT]** ein Artefakt erzeugen oder die eigene Artefakt-Zerlegung einer Domäne durchführen; jede Domäne läuft über ihre zuständige `*-solution`, die ihr eigenes Plan-Freigabe-Gate behält
- **MUSS [MUST]** stoppen und berichten, wenn eine dispatchte `*-solution` (oder einer ihrer Schritte) NEEDS-WORK zurückgibt, statt eine abhängige Domäne auf einem unfertigen Vorgänger zu routen
- **MUSS [MUST]** alle Bezeichner über die Domänen hinweg konsistent halten gemäß `ha/naming-conventions` und domänenübergreifende HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Gesamt-Bericht

- **MUSS [MUST]** am Ende jede Domäne, die gelaufene `*-solution` und die über Grenzen gefädelten Identitäten auflisten
- **MUSS [MUST]** den aggregierten CONFORMANT- / NEEDS-WORK-Bericht jeder Domänen-Lösung weiterreichen, ohne ihn neu zu bewerten

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Anforderung pro Lauf orchestrieren
- **MUSS NICHT [MUST NOT]** einen Domänen-Plan ohne Nutzer-Bestätigung ausführen
- **MUSS NICHT [MUST NOT]** die interne Zerlegung oder die Berichte einer Domänen-Lösung neu bewerten oder neu planen
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder dorthin importieren

## Akzeptanzkriterien

- [ ] Ein einziger Eingangspunkt nimmt jede HA-Anforderung an und routet sie an die korrekte(n) Domänen-Lösung(en)
- [ ] Eine unterspezifizierte Anforderung dispatcht `requirements-elicit` vor der Klassifikation; eine klar spezifizierte nutzt den schnellen 1–3-Fragen-Clarify-Pfad
- [ ] Die Anforderung wird in eine oder mehrere von Integration/Backend, Lovelace/Frontend, YAML-Automation, Pixoo klassifiziert
- [ ] Eine domänenübergreifende Anforderung wird über die relevanten `*-solution`s in Abhängigkeitsreihenfolge zerlegt, mit über Grenzen gefädelten Identitäten
- [ ] Domänen-Lösungen werden bei jedem Lauf gegen das lebende `ha-*-solution`-Inventar aufgelöst (eine hinzugefügte oder umbenannte Domänen-Lösung ist routbar, ohne den Router zu ändern)
- [ ] Eine Single-Domain-Anforderung routet direkt an die zuständige `*-solution`; der Skill grenzt sauber gegen die vier Domänen-Lösungen ab
- [ ] Stoppt bei einem NEEDS-WORK-Domänen-Ergebnis, statt eine abhängige Domäne weiterzurouten
- [ ] Gesamt-Bericht listet jede Domäne, die gelaufene Lösung, die gefädelten Identitäten und reicht die einzelnen Berichte weiter

## Offene Fragen

- **Solution- vs. Agent-Dispatch**: Sollen die Domänen-Lösungen als Skills (sichtbar, sequenziell) oder über Agenten (isoliert, parallel) laufen? Aktuell Skill-Dispatch, weil die domänenübergreifende Identitäts-Verdrahtung (Backend-`domain`/`entity_id`s → Frontend-Card / Automation) im Nutzerkontext sichtbar bleiben muss.
- **Doppeltes Gating**: Jede Domänen-`*-solution` hat ihr eigenes Plan-Freigabe-Gate, und der Router legt ein Domänen-Plan-Gate darüber. Soll die Router-Freigabe das Gate der ersten Domänen-Lösung subsumieren, um Gate-Ermüdung zu vermeiden, oder getrennt bleiben? Aktuell getrennt — der Router plant Domänen, jede Lösung plant ihre eigenen Artefakte.
- **Anforderungs-Konfidenz (entschieden)**: Eine unterspezifizierte domänenübergreifende Anforderung dispatcht `requirements-elicit` vor der Klassifikation, und eine klar spezifizierte nutzt den leichten 1–3-Fragen-Pfad — dasselbe Konfidenz-Gate wie die Schwester-`ha-*-solution`s, analog zum `issue-orchestrate`-Upstream-Gate.
- **Identitäts-Source-of-Truth**: Wenn mehrere Domänen je eine `entity_id` definieren könnten, welche Domäne besitzt sie? Aktuell ist die Backend-/Integrations-Domäne die Quelle und spätere Domänen konsumieren sie.
