# Skill: `ha-panel-ux-audit`

Status: draft

## Kontext

Die Panel-Familie kann jetzt Panels bauen (`ha-panel-author` End-to-End, `ha-panel-add` das bloße Grundgerüst), aber nichts bewertet ein fertiges Panel aus **Nutzer**-Sicht — ob ein Mensch es tatsächlich benutzen kann und vor allem, ob es auf einem Telefon funktioniert. Home Assistant wird stark über die mobile Companion-App genutzt, also fällt ein Panel, das nur auf einem breiten Desktop-Viewport gut liest, bei einem großen Teil seiner realen Nutzung durch. Die bestehenden Specs tragen die maßgeblichen Fakten bereits — `ha/lovelace-layout-antipatterns` E1 (die `narrow`-Property und der dokumentierte Mobile-Single-Column-Collapse), die Delivery-Shape- und Layout-Guardrails, `ha/lovelace-card-patterns` (Theming, Entity-Change-Disziplin) und `ha/frontend-data-api` (unavailable-guarded State) —, aber kein Skill auditiert ein Panel gegen sie plus allgemeine UX- und Barrierefreiheits-Heuristiken.

Dieser Skill ist der **UX-Experte** der Panel-Familie: ein read-only, statisches Audit auf Panel-Ebene, das einen Severity-sortierten Verbesserungs-Report erzeugt, mit **Mobile-Geräte-Nutzbarkeit als verpflichtender Kern-Dimension**. Er modifiziert das Panel nie; der Report ist zum Lesen und Handeln gedacht und wird — auf Wunsch — an `ha-panel-author` als priorisierte Arbeitsliste übergeben. Er ist das panel-bezogene UX-Geschwister der Integrations-Audit-Skills `ha-quality-scale-audit` und `ha-security-audit`. Quality-Scale-Marker: Custom Panels und Views sind **nicht Teil der HA-Quality-Scale**; dieses Audit steht außerhalb der Skala.

## Scope

Statisches Audit genau eines Panel-Ebenen-Artefakts pro Lauf — ein Custom-Sidebar-Panel-Element (plus dessen `panel_custom`-Registrierung), ein Panel-Mode-View oder ein Custom-View — gegen den bindenden Spec-Satz plus UX-/Barrierefreiheits-Heuristiken, mit einem Severity-sortierten Report samt konkreter, spec-referenzierter Verbesserungsvorschläge und einer destillierten Arbeitsliste für `ha-panel-author`. Das Audit liest nur Code und Config; es rendert das Panel nicht, treibt keine Live-Instanz und testet nicht auf echten Geräten, und es editiert nie etwas.

## Ziele

- Ein Panel aus Nutzer-Sicht bewerten, mit Mobile-Geräte-Nutzbarkeit als verpflichtender Dimension, und ein explizites **Mobile-Usability-Verdikt** (PASS / NEEDS-WORK) ausgeben
- Gegen die bestehenden Specs auditieren (`ha/lovelace-views-panels`, `ha/lovelace-layout-antipatterns`, `ha/lovelace-card-patterns`, `ha/frontend-data-api`) und in jedem Finding die governierende Regel referenzieren
- HA-Fakten und UX-Heuristiken sauber trennen — Heuristiken sind gekennzeichnet und werden nie als HA-Fakten behauptet
- Severity-sortierte, umsetzbare Findings erzeugen, deren Verbesserungsvorschläge `ha-panel-author` direkt als Arbeitsliste konsumieren kann
- Strikt read-only bleiben — `git status` ist nach dem Lauf unverändert

## Nicht-Ziele

- Ein Panel bauen, entwickeln oder fixen — `ha-panel-author` (das diesen Report als `ux_audit_report` konsumieren kann)
- Ein bloßes Panel-Grundgerüst scaffolden — `ha-panel-add`
- Ein Gesamt-Integrations-Review (Quality-Scale, Security, Konsistenz) — `ha-integration-review`
- Die Interna einer einzelnen Custom-Card als Artefakt — `ha/lovelace-card-patterns`-Scope
- Findings automatisch fixen — dieser Skill ist read-only
- Das Panel rendern, eine Live-HA-Instanz treiben oder On-Device-Testing — nur statisches Audit; Live-Verifikation ist ein ergänzender manueller Schritt
- Eine wiederverwendbare HA-UX-/Mobile-Domänen-Spec definieren — die Rubrik lebt in dieser Skill-Spec; eine `spec/ha/*`-UX-Spec zu extrahieren ist möglicher Folge-Schritt

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „audit my panel's UX", „is this panel usable on mobile", „review the panel for usability and accessibility"
  - „auditiere die UX meines Panels", „ist das Panel auf dem Handy gut nutzbar", „prüfe das Panel auf Barrierefreiheit"
- **MUSS NICHT [MUST NOT]** für Bauen/Fixen eines Panels (`ha-panel-author`), Scaffolding (`ha-panel-add`) oder ein Gesamt-Integrations-Review (`ha-integration-review`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root)
- **KANN [MAY]** erfassen: `panel` (Pfad/Identifier des Panel-Artefakts; sonst entdeckt und bestätigt), `target_devices` (Mobile wird immer auditiert; Default `mobile + desktop`), `audience` und `severity_threshold` (Default `low`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo ist
- **MUSS [MUST]** das Panel-Artefakt lokalisieren (Custom-Panel-Element + `panel_custom`-Registrierung, oder die Panel-Mode-/Custom-View-Config); wenn keins existiert, auf `ha-panel-author` / `ha-panel-add` verweisen
- **MUSS [MUST]** den bindenden Spec-Satz lesen: `ha/lovelace-views-panels`, `ha/lovelace-layout-antipatterns`, `ha/lovelace-card-patterns`, `ha/frontend-data-api`
- **MUSS [MUST]** `target_devices` (Mobile immer enthalten) und die Severity-Schwelle bestätigen

### Audit-Dimensionen

- **MUSS [MUST]** die **Mobile-Usability**-Dimension in jedem Lauf auditieren und ein **Mobile-Usability-Verdikt** (PASS / NEEDS-WORK) ausgeben: Das Element liest/respektiert `narrow`; Inhalt kollabiert in einer sinnvollen Reihenfolge zu einer lesbaren einzelnen Spalte (`ha/lovelace-layout-antipatterns` E1); kein horizontaler Overflow oder feste äußere Pixelbreiten, die auf kleinen Viewports brechen (B4/E1); Touch-Targets sind bequem antippbar und es gibt keine Hover-only-Affordances (**[UX-Heuristik]**); Text ist ohne Pinch-Zoom lesbar
- **MUSS [MUST]** Delivery-Shape & Layout-Passung auditieren (`ha/lovelace-views-panels`; Panel-Mode-View hat eine Card und keine Badges — A1/A2; kein Third-Party-Layout-Tooling — D1; eingebettete Cards via `getGridOptions()`/`getCardSize()` dimensioniert — B1/B2/B4)
- **MUSS [MUST]** Lesbarkeit/Theming/Kontrast auditieren (`ha/lovelace-card-patterns`: HA-CSS-Custom-Properties, keine hardcodierten Farben; ausreichender Kontrast **[UX-Heuristik WCAG-AA]**) und State-Abdeckung (`ha/frontend-data-api`: Loading-/Empty-/Error-/`unavailable`-/Stale-States rendern; nie blank bei fehlender Entity)
- **MUSS [MUST]** Informations-Hierarchie & Dichte, Interaktions-Affordances & Feedback, Barrierefreiheit (Fokus-Reihenfolge, Tastatur-Bedienbarkeit, beschriftete Icon-only-Controls, Reduced-Motion — **[UX-Heuristik]**), gefühlte Performance (Entity-Change-Detection vor Re-Render; keine schwere synchrone Arbeit in `set hass` — `ha/lovelace-card-patterns`) und Navigation/Orientierung (Sidebar `title`/`icon`; `route`-Handling) auditieren
- **MUSS [MUST]** in jedem HA-Fakt-Finding die governierende Spec-Regel referenzieren und jedes allgemeine UX-/Barrierefreiheits-Finding als **[UX-Heuristik]** taggen, statt es als HA-Fakt darzustellen

### Report-Format

- **MUSS [MUST]** ausgeben: einen Header (Panel-Artefakt, `target_devices`, angewandter Spec-Satz); das **Mobile-Usability-Verdikt** (PASS / NEEDS-WORK) mit den ausschlaggebenden Findings; Severity-sortierte Findings (critical → high → medium → low), je mit Dimension, Ort (`file:line`), Defekt, Nutzer-Impact (für Mobile explizit benannt), konkretem Verbesserungsvorschlag und Spec-Referenz oder `[UX-Heuristik]`-Tag; eine destillierte geordnete **Arbeitsliste für `ha-panel-author`**; und einen **Limitations**-Abschnitt mit Findings, die Live-On-Device-Verifikation brauchen
- **MUSS [MUST]** jeden Verbesserungsvorschlag so formulieren, dass `ha-panel-author` direkt handeln kann; **MUSS NICHT [MUST NOT]** einen vagen Vorschlag ohne konkrete Änderung ausgeben

### Verbote

- **MUSS NICHT [MUST NOT]** das Panel-Element, seine Config oder irgendeine Datei modifizieren — `git status` ist nach dem Lauf unverändert
- **MUSS NICHT [MUST NOT]** das Panel rendern, eine Live-HA-Instanz treiben oder On-Device-Nutzbarkeit behaupten, die ein statisches Audit nicht beweisen kann
- **MUSS NICHT [MUST NOT]** eine UX-/Barrierefreiheits-Heuristik als HA-Fakt darstellen oder ein Finding ohne Spec-Referenz bzw. `[UX-Heuristik]`-Tag ausgeben

## Akzeptanzkriterien

- [ ] Der Lauf ist read-only — `git status` ist danach unverändert
- [ ] Die Mobile-Usability-Dimension ist auditiert und ein **Mobile-Usability-Verdikt** (PASS / NEEDS-WORK) ausgegeben; ein kritisches Mobile-Finding erzwingt NEEDS-WORK
- [ ] Findings sind Severity-sortiert (critical → high → medium → low), je mit Ort, Nutzer-Impact und konkretem Verbesserungsvorschlag
- [ ] Jedes Finding trägt eine governierende Spec-Referenz oder ein `[UX-Heuristik]`-Tag; Heuristiken werden nicht als HA-Fakten dargestellt
- [ ] Der bindende Spec-Satz ist vor dem Auditieren gelesen, und HA-spezifische Mobile-Fakten ruhen auf `ha/lovelace-layout-antipatterns` E1
- [ ] Der Report enthält eine destillierte, von `ha-panel-author` konsumierbare Arbeitsliste und einen Limitations-Abschnitt für Live-Verifikations-Punkte
- [ ] Quality-Scale-Marker: nicht Teil der HA-Quality-Scale (Portfolio-Audit)

## Offene Fragen

- **Wiederverwendbare UX-Domänen-Spec**: Die UX-/Mobile-Heuristiken leben in dieser Skill-Spec. Sollten sie in eine `spec/ha/*`-Panel-UX-/Mobile-Usability-Domänen-Spec (wie `ha/lovelace-layout-antipatterns`) extrahiert werden, die sowohl dieses Audit als auch `ha-panel-author` referenzieren? Ein Folge-Schritt.
- **Statisch vs. Live**: Das Audit ist statisch und kann On-Device-Nutzbarkeit nicht beweisen. Wann rechtfertigt ein Panel einen Live-Geräte-Verifikations-Durchlauf, und ist das ein eigener Agent/Skill?
- **Kontrast-/Touch-Target-Schwellen**: Die konkreten Zahlen (WCAG-AA-Ratios, ≈44–48px-Targets) sind externe Best Practice. Sollte der Skill spezifische Schwellen festpinnen oder deskriptiv bleiben?
- **Handoff-Vertrag mit `ha-panel-author`**: Die Arbeitsliste ist Prosa plus geordnete Liste. Braucht `ha-panel-author` ein strikteres maschinenlesbares Schema für den `ux_audit_report`-Input? Aktuell Prosa; ein Schema ist offen.
