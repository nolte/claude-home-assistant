# Skill: `ha-lovelace-solution`

Status: draft

## Kontext

Die Lovelace-/Frontend-Skill-Familie erzeugt je **ein** Artefakt aus einer eng gefassten Absicht: `ha-lovelace-card-scaffold` baut die Custom-Card selbst, `ha-card-editor-add` ergänzt einen `ha-form`-Config-Editor über `getConfigElement`, `ha-card-features-add` ergänzt ein Tile-/Card-Feature, `ha-badge-add` ein Custom-Badge, `ha-strategy-add` eine Dashboard-/View-Strategy und `ha-panel-add` ein vollflächiges Custom-Panel. Reale Frontend-Anforderungen sind aber selten ein einzelnes Artefakt: „eine Custom-Card für meine Pumpe mit visuellem Config-Editor und einem Tile-Feature" ist eine Kette aus `card-scaffold` → `card-editor` + `card-features`, bei der die Add-ons auf die zuvor erzeugte Card aufsetzen. Ein Nutzer, der die Skills nicht kennt, müsste diese Zerlegung selbst leisten — welches Frontend-Element, welcher Add-on, welche Reihenfolge, welche Datei/welches Custom-Element referenziert welches. Genau diese Mapping-Last soll der Nutzer nicht tragen.

Dieser Skill ist die **vorgelagerte Planungs- und Dispatch-Schicht** des Frontend-Clusters: Er nimmt eine unscharfe Frontend-Anforderung, zerlegt sie in die minimale Kombination von Artefakten, legt die Abhängigkeits-Reihenfolge fest, bestätigt den Plan mit dem Nutzer und dispatcht dann die zuständigen Owning-Skills nacheinander, wobei er die Identitäten (Card-Tag-Name, Datei-Pfad, Modul-Resource, `<domain>`) früherer Schritte als Eingaben der späteren durchreicht. Er generiert **selbst kein** Artefakt — Generierung und Spec-Konformität bleiben bei den Einzel-Skills. Eine Besonderheit des Frontend-Clusters: Wenn eine Card oder ein Panel ein Backend-Endpoint (ein WebSocket-Command) aufruft, lebt dieses Backend in einer Python-Custom-Integration — der Skill weist diese Abhängigkeit im Plan aus, faltet die Backend-Arbeit aber nicht in einen Frontend-Skill.

## Scope

Planung und Orchestrierung über die Lovelace-/Frontend-Skill-Familie: `ha-lovelace-card-scaffold`, `ha-card-editor-add`, `ha-card-features-add`, `ha-badge-add`, `ha-strategy-add`, `ha-panel-add` und — als Backend-Endpoint, den eine Card/ein Panel konsumiert — `ha-websocket-command-add`. Eine Anforderung pro Lauf → ein Artefakt-Plan → N dispatchte Owning-Aufrufe → ein Gesamt-Bericht. Der Skill entscheidet die *Kombination* (welche Artefakte, welcher Typ je Artefakt, welche Reihenfolge, welche Verdrahtung), nicht den Inhalt eines einzelnen Artefakts.

## Ziele

- Aus einer Prosa-Frontend-Anforderung die richtige *Kombination* von Artefakten ableiten, ohne dass der Nutzer die Frontend-Skill-Landschaft kennen muss
- Einen abarbeitbaren Artefakt-Plan in Abhängigkeits-Reihenfolge erstellen (pro Eintrag: Artefakt, Typ, zuständiger Skill, Abhängigkeit, Zweck) und vor jeder Generierung bestätigen lassen
- Die Einzel-Skills in korrekter Reihenfolge dispatchen und die Identitäten (Card-Tag/`custom:<type>`, Datei-Pfad, Modul-Resource, `<domain>`) früherer Artefakte als Eingaben der späteren durchreichen
- Eine Backend-Abhängigkeit (Card/Panel ruft einen WebSocket-Command) erkennen und ausweisen; das Command selbst über `ha-websocket-command-add` dispatchen, und wenn (noch) keine Custom-Integration existiert, auf `ha-integration-scaffold` als Backend-Voraussetzung verweisen statt Backend-Arbeit in einen Frontend-Skill zu falten
- Einen Gesamt-Bericht liefern, der alle erzeugten Dateien und ihre Verdrahtung benennt

## Nicht-Ziele

- Die Generierung eines einzelnen Artefakts samt Spec-Konformität — das bleibt bei `ha-lovelace-card-scaffold`, `ha-card-editor-add`, `ha-card-features-add`, `ha-badge-add`, `ha-strategy-add`, `ha-panel-add`, `ha-websocket-command-add`
- Das Scaffolding der Python-Custom-Integration, in der ein WebSocket-Command-Backend lebt — das ist `ha-integration-scaffold` (der Skill erkennt nur, dass es nötig ist, und verweist)
- Deployment in eine laufende HA-Instanz oder das Eintragen von Dashboard-/Resource-Konfiguration in eine reale Lovelace-Config — Generierung only
- Eine eigene Validierungs- oder Konformitäts-Logik — jeder dispatchte Skill validiert sein eigenes Artefakt; dieser Skill aggregiert nur die Berichte

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf zusammengesetzte, lösungsorientierte Frontend-Anfragen aktivieren, bei denen der Nutzer das Ergebnis, nicht das Artefakt beschreibt:
  - „build a custom card with an editor and a feature"
  - „create a dashboard strategy plus a badge"
  - „set up a custom panel with a WebSocket backend"
  - „baue mir eine Lovelace-Card mit Editor (und Tile-Feature)", „richte ein Custom-Panel mit WebSocket-Backend ein"
- **SOLLTE [SHOULD]** nicht aktivieren, wenn die Anforderung klar ein einzelnes Frontend-Artefakt ist (dann greift direkt der zuständige Einzel-Skill); im Zweifel plant dieser Skill und schlägt einen Ein-Artefakt-Plan vor

### Eingaben

- **MUSS [MUST]** erfassen: `requirement` (Prosa, das gewünschte Frontend-Ergebnis)
- **KANN [MAY]** erfassen: `target_dir` (Repo-Root) und `domain` der bestehenden Integration, bestehende Card-/Modul-Identitäten (Tag-Name, Datei-Pfad), die als Quellen dienen

### Pre-Flight

- **MUSS [MUST]** `requirement` als nichtleer prüfen; bei Unterspezifikation gezielt 1–3 Rückfragen stellen (welches Geräte-/Entity-Ziel, JS oder Lit/TS, welcher Tag-Name, ob ein Backend-Endpoint nötig ist), bevor er plant
- **MUSS [MUST]** prüfen, ob die Anforderung einen Backend-Endpoint (WebSocket-Command) verlangt; wenn ja, das im Plan ausweisen — und wenn (noch) keine Custom-Integration existiert, `ha-integration-scaffold` als Voraussetzung benennen, statt die Backend-Arbeit in einen Frontend-Skill zu pressen

### Zerlegungs-Heuristik (Anforderung → Artefakt-Typ → Skill)

- **MUSS [MUST]** eine eigenständige Custom-Card (das sichtbare Karten-Element) auf `ha-lovelace-card-scaffold` abbilden — Schritt 1, sobald eine Card gebraucht wird
- **MUSS [MUST]** einen visuellen Config-Editor für eine Card (`ha-form` über `getConfigElement`) auf `ha-card-editor-add` abbilden, abhängig von der Card
- **MUSS [MUST]** ein Tile-/Card-Feature (interaktive Control-Row in der Tile-Card und anderen Host-Cards) auf `ha-card-features-add` abbilden, abhängig von einem Frontend-Modul
- **MUSS [MUST]** ein Custom-Badge auf `ha-badge-add`, eine Dashboard-/View-Strategy (Auto-Generierung von Views/Cards) auf `ha-strategy-add` und ein vollflächiges Custom-Panel auf `ha-panel-add` abbilden — jeweils eigenständige Top-Level-Frontend-Elemente
- **MUSS [MUST]** einen Backend-Endpoint, den eine Card oder ein Panel aufruft, auf `ha-websocket-command-add` (Python-Seite) abbilden; das Command lebt in einer Custom-Integration und ist deren Voraussetzung (`ha-integration-scaffold`, falls nicht vorhanden)
- **MUSS [MUST]** die Artefakte minimal halten — keine Add-ons erzeugen, die ein einzelnes Artefakt bereits abdeckt

### Plan & Dispatch

- **MUSS [MUST]** vor jeder Generierung einen Artefakt-Plan als Tabelle in Abhängigkeits-Reihenfolge präsentieren: pro Eintrag `#`, Artefakt-Name/Tag, Typ, zuständiger Skill, Abhängigkeit (`depends-on`), Zweck — und explizite Bestätigung abwarten
- **MUSS NICHT [MUST NOT]** ein Artefakt selbst inline generieren; jede Generierung läuft über den zuständigen Einzel-Skill
- **MUSS [MUST]** die Skills in Abhängigkeits-Reihenfolge dispatchen (Card vor ihren Add-ons; Badges/Strategies/Panels unabhängig; ein WebSocket-Command als Backend, das die Card/das Panel konsumiert) und die Identitäten (Card-Tag/`custom:<type>`, Datei-Pfad, Modul-Resource, `<domain>`, Command-`type`) als Eingaben der abhängigen Schritte durchreichen
- **MUSS [MUST]** abbrechen und zurückmelden, wenn ein dispatchter Skill einen NEEDS-WORK-Bericht liefert, statt auf einem unfertigen Vorgänger-Artefakt weiterzubauen
- **MUSS [MUST]** alle Bezeichner über die Artefakte hinweg konsistent nach `ha/naming-conventions` halten und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Gesamt-Bericht

- **MUSS [MUST]** am Ende jeden erzeugten Datei-Pfad, das zugehörige Artefakt und die Verdrahtung (welches Element/welcher Tag welchen referenziert; welche Card welchen Command aufruft) auflisten
- **MUSS [MUST]** die aggregierten CONFORMANT / NEEDS-WORK-Berichte der Einzel-Skills weiterreichen, ohne sie neu zu bewerten

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Anforderung pro Lauf orchestrieren
- **MUSS NICHT [MUST NOT]** einen Plan ohne Nutzer-Bestätigung ausführen
- **MUSS NICHT [MUST NOT]** Backend-Arbeit (das WebSocket-Command-Backend oder die Custom-Integration) in einen Frontend-Skill falten
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder Dashboard-/Resource-Konfiguration in eine reale Lovelace-Config eintragen

## Akzeptanzkriterien

- [ ] Skill erfragt fehlende Eckdaten (Ziel-Entity, JS vs. Lit/TS, Tag-Name, Backend-Bedarf), bevor er plant
- [ ] Skill präsentiert einen Artefakt-Plan in Abhängigkeits-Reihenfolge und wartet auf Bestätigung
- [ ] Skill dispatcht die zuständigen Einzel-Skills statt selbst zu generieren
- [ ] Identitäten (Card-Tag, Datei-Pfad, Modul-Resource, `<domain>`, Command-`type`) früherer Artefakte werden als Eingaben der abhängigen Schritte durchgereicht
- [ ] Eine Backend-Abhängigkeit (WebSocket-Command) wird erkannt, an `ha-websocket-command-add` verwiesen und — falls keine Integration existiert — auf `ha-integration-scaffold` als Voraussetzung verwiesen
- [ ] Abbruch bei einem NEEDS-WORK-Vorgänger statt Weiterbau
- [ ] Gesamt-Bericht listet alle Dateien und die Verdrahtung und reicht die Einzel-Berichte weiter

## Offene Fragen

- **Agent- vs. Skill-Dispatch**: Sollen die Einzel-Schritte als Skills (sichtbar, sequentiell) oder über einen Generierungs-Agent (isoliert, parallel) ausgeführt werden? Aktuell Skill-Dispatch, weil die Plan-Bestätigung und die Identitäts-Verdrahtung (Card-Tag → Editor/Feature, Card → Command) im Nutzer-Kontext sichtbar bleiben sollen.
- **Backend-Grenze**: Wie tief soll der Skill die Backend-Voraussetzung verfolgen — nur das WebSocket-Command dispatchen oder auch eine fehlende Integration vor-scaffolden? Aktuell: Command dispatchen, fehlende Integration nur als Voraussetzung benennen.
- **TS/Lit vs. Vanilla-JS**: `ha-lovelace-card-scaffold` erzeugt Vanilla-JS, einige Add-ons sind LitElement-zentriert. Soll der Skill bei gemischten Anforderungen eine konsistente Framework-Wahl erzwingen oder pro Artefakt dem jeweiligen Owning-Skill überlassen? Aktuell pro Owning-Skill.
- **Bestehende-Config-Awareness**: Soll der Skill das `www/`-Verzeichnis und bestehende Modul-Resourcen einlesen, um Kollisionen früh zu erkennen? Aktuell vom Nutzer benannt.
