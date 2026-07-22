# Skill: `ha-panel-author`

Status: draft

## Kontext

Die Lovelace-/Frontend-Skill-Familie hat einen minimalen Panel-Scaffolder — `ha-panel-add` —, der ein Custom-Panel (das Custom Element plus die `panel_custom`-Registrierung) konform zu `ha/lovelace-views-panels` (Custom-Panel-Teil) erzeugt. Das ist das richtige Werkzeug für ein bloßes Grundgerüst, aber ein realer Panel-Bedarf ist selten nur das Skelett: Er entscheidet, *welche* Fläche gebaut wird (ein vollflächiges Sidebar-Panel, ein Panel-Mode-View oder ein Custom-View-Layout-Container), liest seine Daten über den richtigen Kanal, ruft womöglich ein WebSocket-Backend, und muss Layout-, Responsive-, Performance- und Theming-Disziplin über mehrere Specs gleichzeitig einhalten.

Dieser Skill ist der **Senior-Panel-Entwickler** der Familie. Er nimmt einen beschriebenen vollflächigen oder Dashboard-Flächen-Bedarf und entwickelt ihn End-to-End zur Produktionsreife, wobei er das Ergebnis an den vollen relevanten Spec-Satz bindet: `ha/lovelace-views-panels` (Delivery-Shapes), `ha/lovelace-layout-antipatterns` (Layout-/Anordnungs-Guardrails), `ha/frontend-data-api` (der `hass`-Datenkanal), `ha/frontend-websocket-commands` (ein Backend-Endpoint, den das Panel aufruft) und `ha/lovelace-card-patterns` (Shadow-DOM-/Theme-/Entity-Change-Disziplin). Er erfindet das Grundgerüst nicht neu — dafür dispatcht er `ha-panel-add` — und er generiert das Python-Backend nicht — dafür dispatcht er `ha-websocket-command-add` und weist `ha-integration-scaffold` als Voraussetzung aus. Quality-Scale-Marker: Custom Panels und Views sind **nicht Teil der HA-Quality-Scale**; das Pattern steht außerhalb der Skala.

## Scope

Entwicklung genau einer Panel-Lösung pro Lauf, End-to-End, in ein bestehendes Repo. Der Skill entscheidet die Delivery-Shape (Custom-Sidebar-Panel / Panel-Mode-View / Custom-View), präsentiert einen Senior-Build-Plan und baut dann: Für ein Custom-Panel dispatcht er `ha-panel-add` für das Grundgerüst und entwickelt es (Datenanbindung, responsives `narrow`, Layout-Disziplin, Entity-Change-Detection, Shadow-DOM-Theming und — falls nötig — ein dispatchtes WebSocket-Command); für einen Panel-Mode-View oder Custom-View erzeugt er die entsprechende Config/das Element gemäß den governierenden Specs. Er liest den bindenden Spec-Satz und validiert offline, mit einem Multi-Spec-Konformitätsbericht. Er entscheidet *Shape und Entwicklung* einer Panel-Lösung, nicht den Inhalt unbezogener Artefakte.

## Ziele

- Ein produktionsreifes Panel aus einem beschriebenen Bedarf entwickeln, abgegrenzt vom bloßen Grundgerüst (`ha-panel-add`) und vom Multi-Artefakt-Orchestrator (`ha-lovelace-solution`)
- Die Delivery-Shape-Entscheidung explizit und begründet machen — Custom-Sidebar-Panel vs. Panel-Mode-View vs. Custom-View — gemäß `ha/lovelace-views-panels` und `ha/lovelace-layout-antipatterns`
- `ha-panel-add` für das Custom-Panel-Grundgerüst wiederverwenden, statt Element und `panel_custom`-Registrierung von Hand zu schreiben
- Daten über den dokumentierten Kanal verdrahten (`hass` / `hass.callWS`) gemäß `ha/frontend-data-api`, und jeden Backend-Endpoint als WebSocket-Command in einer Python-Integration halten (dispatcht, nicht eingefaltet)
- Layout-, Responsive- (`narrow`), Performance- (Entity-Change-Detection) und Shadow-DOM-Theming-Disziplin über die angewandten Specs erzwingen
- Einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an jede vom Build berührte Spec anknüpft

## Nicht-Ziele

- Das bloße Ein-Panel-Grundgerüst ohne Senior-Entwicklung (nur Element + `panel_custom`) — `ha-panel-add` (von diesem Skill fürs Grundgerüst dispatcht)
- Eine einzelne Custom-Card — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Eine Multi-Artefakt-Frontend-Lösung über die ganze Familie (Card + Editor + Feature + Badge + Strategy + Panel) — `ha-lovelace-solution` (die diesen Skill für den Panel-Teil dispatchen kann)
- Programmatische Dashboard-/View-Generierung (Strategien) — `ha-strategy-add` / `ha/lovelace-strategies`
- Die Python-Custom-Integration, in der ein WebSocket-Command-Backend lebt — `ha-integration-scaffold` (der Skill erkennt nur den Bedarf und dispatcht/flaggt ihn)
- Build-Stacks (Vite, esbuild, Rollup), TypeScript-Migration und Theme-Definition durch das Panel selbst — eigene Folge-Specs
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „build a proper custom panel for…", „develop a full-page HA panel that shows…", „I need a senior-grade dashboard panel"
  - „entwickle ein vollwertiges Custom-Panel für…", „baue mir ein produktionsreifes HA-Panel"
- **SOLLTE NICHT [SHOULD NOT]** aktivieren, wenn der Nutzer nur das bloße Grundgerüst (`ha-panel-add`) oder eine Multi-Artefakt-Frontend-Lösung (`ha-lovelace-solution`) will; im Zweifel entscheidet dieser Skill die Delivery-Shape und schlägt einen Plan vor

### Eingaben

- **MUSS [MUST]** erfassen: `need` (Prosa, das gewünschte Panel-/Seiten-Ergebnis)
- **KANN [MAY]** erfassen: `target_dir` (Repo-Root), `domain` der bestehenden Integration, `data_sources` (Entities/Registries/WebSocket-Daten), `backend_needed` und einen `delivery_shape`-Override

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `need` nichtleer ist, `target_dir` ein bestehendes Repo ist und das `module_url`-Ziel auflösbar ist
- **MUSS [MUST]** den bindenden Spec-Satz lesen: `ha/lovelace-views-panels`, `ha/lovelace-layout-antipatterns`, `ha/frontend-data-api`, `ha/frontend-websocket-commands`, `ha/lovelace-card-patterns`
- **MUSS [MUST]** die Delivery-Shape-Entscheidung durchführen und vor dem Bauen mit dem Nutzer bestätigen
- **MUSS [MUST]** bestimmen, ob ein Backend-Endpoint nötig ist; wenn ja, die WebSocket-Command-Abhängigkeit ausweisen und, wenn keine Integration existiert, die `ha-integration-scaffold`-Voraussetzung

### Delivery-Shape-Entscheidung

- **MUSS [MUST]** zwischen einem Custom-Sidebar-Panel (vollflächig), einem Panel-Mode-View (eine full-width Card) und einem Custom-View (Layout-Container) gemäß `ha/lovelace-views-panels` wählen und die Wahl mit Begründung präsentieren
- **MUSS [MUST]** `ha/lovelace-layout-antipatterns` auf die Wahl anwenden — ein Panel-Mode-View hält genau eine Card und keine Badges (A1/A2); nur ein echter Vollseiten-Sidebar-Bedarf rechtfertigt ein Custom-Panel
- **SOLLTE [SHOULD]** auf das leichtere Werkzeug verweisen, wenn ein bloßes Grundgerüst (`ha-panel-add`) oder eine Strategy (`ha-strategy-add`) den Bedarf deckt

### Entwicklungs-Regeln

- **MUSS [MUST]** `ha-panel-add` für das Custom-Panel-Grundgerüst dispatchen, statt Panel-Element und `panel_custom`-Registrierung von Hand zu schreiben; **MUSS [MUST]** abbrechen und zurückmelden, wenn es NEEDS-WORK liefert
- **MUSS [MUST]** jedes Panel-/View-Element als Custom Element definieren und **MUSS NICHT [MUST NOT]** React verwenden (B5); **MUSS NICHT [MUST NOT]** den HA-State außerhalb der `hass`-Property zugreifen
- **MUSS [MUST]** an `ha/lovelace-layout-antipatterns` konformieren: `narrow` und den Mobile-Single-Column-Collapse respektieren (E1); nie von Third-Party-Layout-Tooling abhängen (D1); eine eingebettete Custom-Card deklariert `getGridOptions()`/`getCardSize()` und vermeidet feste äußere Pixelbreiten (B1/B2/B4)
- **MUSS [MUST]** State via `hass` und Registry-/Zusatzdaten via `hass.callWS(...)` gemäß `ha/frontend-data-api` lesen; **MUSS [MUST]** einen Backend-Endpoint, den das Panel aufruft, als WebSocket-Command in einer Python-Integration (`ha/frontend-websocket-commands`) implementieren, dispatcht via `ha-websocket-command-add`, und **MUSS NICHT [MUST NOT]** Backend-Logik ins Panel falten
- **MUSS [MUST]** Entity-Change-Detection vor dem Re-Render durchführen (kein blankes Re-Render bei jedem `hass`-Tick) und in Shadow DOM mit HA-CSS-Custom-Properties gemäß `ha/lovelace-card-patterns` rendern; **MUSS NICHT [MUST NOT]** Farben hardcodieren oder äußere Pixelbreiten erzwingen
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline gegen die angewandten Specs validieren: korrekte Delivery-Shape; Custom Element (kein React) mit `hass`-only-State-Zugriff; `panel_custom`-Registrierung (für ein Custom-Panel) mit eindeutigem `url_path` und `module_url`; Layout-Antipattern-Konformität (A1/A2/E1/D1 und Embedded-Card-B-Regeln); Daten via `hass`/`callWS`; ein Backend-Endpoint als dispatchtes WebSocket-Command, nicht eingefaltet; Entity-Change-Detection und Shadow-DOM-Theming vorhanden
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an jede vom Build berührte Spec anknüpft, plus die geänderten Datei-Pfade, alle Ergebnisse dispatchter Skills und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Panel-Lösung pro Lauf entwickeln
- **MUSS NICHT [MUST NOT]** das Custom-Panel-Grundgerüst von Hand schreiben, wenn `ha-panel-add` es erzeugen kann
- **MUSS NICHT [MUST NOT]** ein WebSocket-Backend ins Panel falten oder die Python-Integration selbst scaffolden
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] Die Delivery-Shape (Custom-Panel / Panel-Mode-View / Custom-View) ist vor dem Bauen entschieden, begründet und bestätigt
- [ ] Der bindende Spec-Satz ist vor der Generierung gelesen
- [ ] Das Custom-Panel-Grundgerüst wird durch Dispatch von `ha-panel-add` erzeugt, nicht von Hand geschrieben
- [ ] Jedes Element ist ein Custom Element (kein React) und greift den HA-State nur über `hass` zu
- [ ] Layout-Antipattern-Konformität hält — Panel-Mode-View hat eine Card und keine Badges (A1/A2), `narrow`/Single-Column-Collapse respektiert (E1), kein Third-Party-Layout-Tooling (D1), eingebettete Cards folgen B1/B2/B4
- [ ] Daten fließen über `hass`/`hass.callWS`; ein Backend-Endpoint ist ein dispatchtes WebSocket-Command, nicht ins Panel gefaltet
- [ ] Entity-Change-Detection und Shadow-DOM-Theming (HA-CSS-Custom-Properties) sind vorhanden; keine hardcodierten Farben oder erzwungenen äußeren Pixelbreiten
- [ ] Der Bericht benennt die angewandten Specs, die geänderten Datei-Pfade, Ergebnisse dispatchter Skills und den Quality-Scale-Marker **nicht Teil der HA-Quality-Scale**

## Offene Fragen

- **Überschneidung mit `ha-lovelace-solution`**: Der Orchestrator kann diesen Skill für den Panel-Teil einer Multi-Artefakt-Lösung dispatchen. Die genaue Übergabe (besitzt die Solution den Plan und dieser Skill nur den Panel-Build?) bleibt dem Orchestrator überlassen; ein fester Vertrag ist Folge-Arbeit.
- **Delivery-Shape-Heuristik**: `ha/lovelace-views-panels` überlässt die View-vs-Panel-Wahl der Einzelfall-Beurteilung. Dieser Skill entscheidet pro Lauf; eine kodifizierte Heuristik ist offen.
- **Tiefe der Embedded-Card-Generierung**: Wenn ein Panel maßgeschneiderte Cards einbettet, dispatcht dieser Skill `ha-lovelace-card-scaffold` pro Card oder rendert inline? Aktuell dispatcht er für eine wiederverwendbare Card und rendert Panel-only-Inhalt inline; die Schwelle ist offen.
- **`ha-panel-add`-Re-Dispatch bei Iteration**: Wenn die Senior-Entwicklung die Grund-Panel-Shape ändert, wird `ha-panel-add` neu ausgeführt oder das Grundgerüst in-place editiert? Aktuell in-place nach dem initialen Grundgerüst; ein Re-Dispatch-Vertrag ist offen.
