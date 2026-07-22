# Skill: `ha-pixoo-solution`

Status: draft

## Kontext

Die Divoom-Pixoo-Skill-Familie erzeugt je **ein** Artefakt aus einer eng umrissenen Absicht: `ha-pixoo-page-author` baut eine `pages_data`-Seite (das Info-Layout und die Canvas), `ha-pixoo-pixel-art-author` füllt einen Seiten-Slot mit einer detaillierten Pixel-Art-Grafik (Schattierung/Konturen, prozedurale Komponenten oder ein 64×64-Bildplan) und `ha-pixoo-animation-author` ergänzt die zeitliche Dimension (eine animierte `components`-Seite plus die treibende Automation). Reale Pixoo-Anforderungen sind selten ein einzelnes Artefakt: „eine animierte Regenseite, gesteuert von der Wetter-Entität, mit einem Batterie-Icon" ist eine Kette aus Seite → Pixel-Art → Animation, bei der jedes Add-on auf der zuvor erzeugten Seite aufbaut. Wer die Skills nicht kennt, müsste diese Zerlegung selbst leisten — welches Artefakt, welche Reihenfolge, welche Seitenstruktur und Ziel-Entität den nächsten Schritt speisen. Genau diese Zuordnungslast soll die Nutzerin nicht tragen.

Dieser Skill ist die **Eingangstür und vorgelagerte Planungs-/Dispatch-Schicht** des Pixoo-Clusters: Er nimmt eine unscharfe Pixoo-Anzeige-Anforderung, zerlegt sie in die minimale Artefakt-Kombination, legt die Abhängigkeitsreihenfolge fest, bestätigt den Plan mit der Nutzerin und dispatcht dann die zuständigen Skills nacheinander — dabei fädelt er die Identitäten (die `pages_data`-Seitenstruktur, Komponentenpositionen, die gewählte Palette/Ramps und die Ziel-Entität `sensor.<name>_current_page`) früherer Schritte in die Eingaben späterer ein. Er erzeugt **kein** Artefakt selbst — Generierung und Spec-Konformität bleiben bei den einzelnen Skills. Geräte-Setup, Discovery, Config-Flow und Services sind **Nutzung** der bestehenden `divoom_pixoo`-Integration (gemäß `ha/divoom-pixoo`), kein Authoring, und bleiben außerhalb des Scopes.

## Scope

Planung und Orchestrierung über die Divoom-Pixoo-Skill-Familie: `ha-pixoo-page-author`, `ha-pixoo-pixel-art-author` und `ha-pixoo-animation-author`. Eine Anforderung pro Lauf → ein Artefakt-Plan → N dispatchte zuständige Aufrufe → ein Gesamt-Bericht. Der Skill entscheidet über die *Kombination* (welche Artefakte, welcher Typ je Artefakt, welche Reihenfolge, welche Verdrahtung), nicht über den Inhalt eines einzelnen Artefakts. Grundlagen-Specs für den Domänen-Contract: `ha/divoom-pixoo`, `ha/pixoo-pixel-art`, `ha/pixoo-pixel-art-animation`.

## Ziele

- Die richtige *Kombination* von Artefakten aus einer Prosa-Pixoo-Anforderung ableiten, ohne dass die Nutzerin die Pixoo-Skill-Landschaft kennt
- Einen verarbeitbaren Artefakt-Plan in Abhängigkeitsreihenfolge erzeugen (je Eintrag: Artefakt, Typ, zuständiger Skill, Abhängigkeit, Zweck) und ihn vor jeder Generierung bestätigen lassen
- Die einzelnen Skills in korrekter Reihenfolge dispatchen und die Identitäten (`pages_data`-Seitenstruktur, Komponentenpositionen, Palette/Ramps, Ziel-Entität `sensor.<name>_current_page`) früherer Artefakte in die Eingaben späterer einfädeln
- Das Authoring einer Anzeige von der **Nutzung** der Integration (Geräte-Setup, IP/`scan_interval`, Entity-Verdrahtung) abgrenzen und Letztere außerhalb des Scopes halten, mit Verweis auf `ha/divoom-pixoo`
- Einen Gesamt-Bericht liefern, der jedes erzeugte Artefakt und seine Verdrahtung benennt

## Nicht-Ziele

- Ein einzelnes Artefakt und dessen Spec-Konformität erzeugen — das bleibt bei `ha-pixoo-page-author`, `ha-pixoo-pixel-art-author`, `ha-pixoo-animation-author`
- Geräte-/Integrations-Setup, Discovery, Config-Flow, IP/`scan_interval`-Änderungen oder Entity-Verdrahtung — das ist **Nutzung** der bestehenden `divoom_pixoo`-Integration gemäß `ha/divoom-pixoo`, kein Authoring
- Deployment in eine laufende HA-Instanz oder das Schreiben der erzeugten Konfiguration in eine Live-HA-Config — nur Generierung
- Eigene Validierungs- oder Konformitätslogik — jeder dispatchte Skill validiert sein eigenes Artefakt; dieser Skill aggregiert nur die Berichte

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** bei zusammengesetzten, ergebnisorientierten Pixoo-Anfragen aktivieren, bei denen die Nutzerin die Anzeige beschreibt, nicht das Artefakt:
  - „baue mir eine Pixoo-Anzeige für meine Wärmepumpenleistung und ein Batterie-Icon"
  - „eine animierte Regenseite, gesteuert von der Wetter-Entität"
  - „eine Fortschrittsseite für die Spülmaschine plus einen Summer-Alarm"
  - „baue mir eine Pixoo-Anzeige für…", „zeig den Status von X auf dem Divoom"
- **SOLLTE [SHOULD]** nicht aktivieren, wenn die Anforderung klar ein einzelnes Pixoo-Artefakt ist (eine Seite, eine Pixel-Art-Grafik, eine Animation — der zuständige Einzel-Skill greift direkt); im Zweifel plant dieser Skill und schlägt einen Ein-Artefakt-Plan vor

### Eingaben

- **MUSS [MUST]** erfassen: `requirement` (Prosa, das gewünschte Pixoo-Anzeige-Ergebnis)
- **KANN [MAY]** erfassen: `target_dir` (Repo- / HA-Config-Root, an dispatchte Skills durchgereicht), `device_entity` (die Ziel-Entität `sensor.<name>_current_page`, das Service-Ziel gemäß `ha/divoom-pixoo`) und `palette` (ein gemeinsamer Palette-/Ramp-Satz, um Seiten kohärent zu halten, gemäß `ha/pixoo-pixel-art`)

### Pre-Flight

- **MUSS [MUST]** prüfen, dass `requirement` nicht leer ist; bei Unterspezifikation 1–3 gezielte Fragen stellen (welche Info, statisch vs. animiert, Ziel-Geräte-Entität, Palette), bevor geplant wird
- **MUSS [MUST]** eine Authoring-Anforderung von reinem Integrations-Setup abgrenzen; ist die Anfrage Geräte-Setup / Config-Flow / `scan_interval` / Entity-Verdrahtung, sie als **Nutzung** der bestehenden Integration gemäß `ha/divoom-pixoo` benennen und stoppen, statt Artefakte zu planen

### Zerlegungs-Heuristik (Anforderung → Artefakt-Typ → Skill)

- **MUSS [MUST]** jeden zuständigen Skill zur Laufzeit auflösen, indem die Anforderung gegen das lebende Pixoo-`ha-pixoo-*`-Skill-Inventar (die genannte Zuständigkeit jedes Kandidaten) abgeglichen wird, nicht aus einer eingefrorenen Namensliste — die Zuordnungen unten sind ein illustrativer Anker, bei jedem Lauf neu aufgelöst, sodass ein zur Familie hinzugefügter oder entfernter Skill dispatchbar ist, ohne den Orchestrator zu ändern (analog zu `issue-orchestrate`). Läuft der Skill im Plugin-Quellbaum, `Glob skills/ha-pixoo-*/SKILL.md` und jede `description:` lesen; lässt sich das lebende Inventar echt nicht aufzählen, auf die Anker-Tabelle zurückfallen und die degradierte Auflösung vermerken
- **MUSS [MUST]** ein Info-Layout (Text/Daten, Spezialseite PV/progress_bar/fuel, natives channel/clock/gif/visualizer) auf eine `pages_data`-Seite via `ha-pixoo-page-author` abbilden — Schritt 1, sobald eine Seite gebraucht wird, da sie die Canvas und die Ziel-Entität besitzt
- **MUSS [MUST]** eine detaillierte Pixel-Art-Grafik (Icon, Illustration mit Schattierung/Konturen, eingebettet in eine Seite) auf `ha-pixoo-pixel-art-author` abbilden, abhängig von der Seite, deren Slot sie füllt
- **MUSS [MUST]** eine bewegte Anzeige (Bewegung, Farbanimation, Ticken/Pulsen) auf `ha-pixoo-animation-author` abbilden (animierte `components`-Seite plus treibende Automation), abhängig von der Seite, die sie animiert
- **MUSS [MUST]** die Artefakte minimal halten — eine schlichte Info-Seite braucht kein Pixel-Art- oder Animations-Add-on

### Plan & Dispatch

- **MUSS [MUST]** vor jeder Generierung einen Artefakt-Plan als Tabelle in Abhängigkeitsreihenfolge präsentieren: je Eintrag `#`, Artefakt, Typ, zuständiger Skill, Abhängigkeit (`depends-on`), Zweck — und auf explizite Bestätigung warten
- **MUSS NICHT [MUST NOT]** ein Artefakt inline selbst erzeugen; jede Generierung läuft über den zuständigen Einzel-Skill
- **MUSS [MUST]** die Skills in Abhängigkeitsreihenfolge dispatchen — Seite → Pixel-Art → Animation: Die Seite definiert die Canvas und die Ziel-Entität, Pixel-Art füllt Grafik-Slots darin, die Animation umschließt das Ergebnis in einer phasengesteuerten Frame-Schleife — und die Identitäten (`pages_data`-Seitenstruktur, Komponentenpositionen, Palette/Ramps, Ziel-Entität `sensor.<name>_current_page`) in die Eingaben abhängiger Schritte einfädeln
- **MUSS [MUST]** stoppen und berichten, wenn ein dispatchter Skill einen NEEDS-WORK-Bericht zurückgibt, statt auf einem unfertigen Vorgänger-Artefakt aufzubauen
- **MUSS [MUST]** alle Bezeichner über die Artefakte hinweg konsistent halten und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`); für den Contract der Integration die Grundlagen-Specs lesen (`ha/divoom-pixoo`, `ha/pixoo-pixel-art`, `ha/pixoo-pixel-art-animation`), nicht aus dem Gedächtnis

### Gesamt-Bericht

- **MUSS [MUST]** am Ende jedes erzeugte Artefakt, seinen Typ und die Verdrahtung auflisten (welche Pixel-Art welchen Seiten-Slot füllt; welche Animation welche Seite treibt; die Ziel-Entität)
- **MUSS [MUST]** die aggregierten CONFORMANT- / NEEDS-WORK-Berichte der einzelnen Skills weiterreichen, ohne sie neu zu bewerten

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Anforderung pro Lauf orchestrieren
- **MUSS NICHT [MUST NOT]** einen Plan ohne Nutzer-Bestätigung ausführen
- **MUSS NICHT [MUST NOT]** Geräte-/Integrations-Setup (Config-Flow, `scan_interval`, Entity-Verdrahtung) in den Authoring-Flow falten — das ist **Nutzung** der Integration
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder das Gerät bzw. seinen Config-Entry verändern

## Akzeptanzkriterien

- [ ] Zuständige Skills werden bei jedem Lauf gegen das lebende Pixoo-`ha-pixoo-*`-Inventar aufgelöst (ein neu hinzugefügter oder umbenannter Familien-Skill ist dispatchbar, ohne den Orchestrator zu ändern); die Zerlegungs-Zuordnungen sind illustrativ, kein eingefrorenes geschlossenes Set
- [ ] Skill fragt fehlende Essentials ab (welche Info, statisch vs. animiert, Ziel-Entität, Palette), bevor geplant wird
- [ ] Skill präsentiert einen Artefakt-Plan in Abhängigkeitsreihenfolge und wartet auf Bestätigung
- [ ] Skill dispatcht die zuständigen Einzel-Skills, statt selbst zu generieren
- [ ] Identitäten (Seitenstruktur, Komponentenpositionen, Palette/Ramps, Ziel-Entität `sensor.<name>_current_page`) früherer Artefakte werden in die Eingaben abhängiger Schritte eingefädelt
- [ ] Authoring wird von Integrations-Setup abgegrenzt; eine Geräte-Setup-Anfrage wird als **Nutzung** der Integration gemäß `ha/divoom-pixoo` benannt und nicht als Artefakte geplant
- [ ] Stoppt bei einem NEEDS-WORK-Vorgänger, statt weiterzubauen
- [ ] Gesamt-Bericht listet jedes Artefakt und die Verdrahtung und reicht die einzelnen Berichte weiter

## Offene Fragen

- **Agent vs. Skill-Dispatch**: Sollen die einzelnen Schritte als Skills (sichtbar, sequenziell) oder über einen Generierungs-Agenten (isoliert, parallel) laufen? Aktuell Skill-Dispatch, weil die Plan-Bestätigung und die Identitäts-Verdrahtung (Seitenstruktur → Pixel-Art-Slot → Animationsphase, Ziel-Entität) im Nutzerkontext sichtbar bleiben sollen.
- **Palette-Kohärenz**: Soll der Skill eine einzige gemeinsame Palette über alle Seiten einer mehrseitigen Anforderung erzwingen oder sie je Artefakt dem zuständigen Skill überlassen? Aktuell wird eine gemeinsame Palette vorab erfasst und eingefädelt, aber nicht hart erzwungen.
- **Bewusstsein für bestehende Config**: Soll der Skill die bestehende `pages_data`-/Geräte-Konfiguration lesen, um Seitenindex- oder Entity-Kollisionen früh zu erkennen? Aktuell von der Nutzerin benannt.
