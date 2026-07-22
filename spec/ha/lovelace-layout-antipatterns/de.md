# HA-Dashboard: Layout- und Card-Anordnungs-Antipatterns

Status: draft

## Kontext

Die Lovelace-Skills und -Agents, die dieses Plugin ausliefert (`ha-lovelace-card-scaffold`, `ha-panel-add`, `ha-strategy-add`, `ha-lovelace-solution`, `ha-card-features-add`, `ha-badge-add`), können Dashboard-Layouts erzeugen, die **rendern, aber fragil sind**: Sie brechen bei HA-Frontend-Updates, ignorieren das native Grid-Modell oder hängen an Third-Party-Tooling, das HA-Core nicht kennt. Ein Layout, das „gerade funktioniert", ist nicht der Maßstab — HA-Kompatibilität muss über Releases und View-Typen hinweg halten.

Der bestehende `ha/lovelace-*`-Cluster beschreibt, **wie** man Cards, Views, Panels und Strategien baut. Keiner davon ist ein **Antipattern-Katalog** mit Fokus auf Layout und Anordnung auf dem Dashboard. Diese Spec schließt die Lücke quer über den Cluster und dient als Guardrail-Referenz: Für jeden häufigen Layout-Fehler benennt sie den Fehler, den Grund, warum er falsch ist (warum er HA-Kompatibilität bricht), und die kompatible Alternative — damit Agents und Skills nicht etwas umsetzen, nur weil es gerade rendert.

**Evidenz-Tiers.** HA-interne Fakten müssen gegen die offizielle Doku verifiziert werden, nicht aus dem Gedächtnis behauptet (`ha/upstream-docs-verification`). Jeder Katalog-Eintrag ist mit seinem Evidenz-Tier getaggt, damit die Verifikations-Disziplin sichtbar bleibt:

- `[doc: user]` / `[doc: dev]` — wörtlich gegen die offizielle HA-Nutzer-Doku (`home-assistant.io/dashboards/*`) oder Developer-Doku (`developers.home-assistant.io/docs/frontend/custom-ui/*`) verifiziert; die Quell-Seite ist benannt.
- `[src]` — zusätzlich gegen den HA-Frontend-Quellcode (`github.com/home-assistant/frontend`) im Verifikations-Durchlauf bestätigt (siehe [Verification](#verification)).
- `[rationale]` — im dokumentierten Modell verankert, aber kein wörtliches Verbot; die Begründung ist ausgeführt, kein Doku-Zitat.
- `[community]` — in realer Community-Praxis beobachtet (Forum-Threads, Dashboard-Showcases, echter Card-Code), nicht in der offiziellen Doku belegt; als Korroboration genutzt, nie als HA-Fakt behauptet.
- `[policy]` — eine nolte-Portfolio-Regel, als solche gekennzeichnet; nicht als HA-Fakt dargestellt.

Diese Spec grenzt gegen ihre Geschwister ab: Card-Interna und Lifecycle liegen in `ha/lovelace-card-patterns`, Editor-Mechanik in `ha/lovelace-card-editor`, Feature-Widgets in `ha/lovelace-card-features`, Badge-Interna in `ha/lovelace-badges`, programmatische Generierung in `ha/lovelace-strategies`, und der View-/Panel-Element-Contract in `ha/lovelace-views-panels`. Überschneidungen werden per Slug referenziert, nicht wiederholt.

Quality-Scale-Marker: Dashboard-Layout und Custom Cards sind **nicht Teil der HA-Quality-Scale** — dieser Katalog ist ein nolte-Portfolio-Guardrail und steht außerhalb der Skala.

## Ziele

- Die häufigen Dashboard-Layout- und Card-Anordnungs-Fehler benennen, jeweils mit dem Fehler, dem Grund, warum er falsch ist, und der kompatiblen Alternative
- HA-Kompatibilität über Releases und View-Typen hinweg als bindende Randbedingung halten — „funktioniert gerade, aber fragil"-Layouts ablehnen
- Jede HA-interne Behauptung an einer konkreten offiziellen Doku-Seite verankern und ihr Evidenz-Tier taggen, sodass keine Anforderung auf Gedächtnis beruht
- Agents und Skills eine prüfbare Acceptance-Liste geben, die ein Layout vor Auslieferung durchfallen lässt, nicht danach
- Die Grenze ziehen zwischen nativen HA-Layout-Konstrukten (verpflichtend) und Third-Party-Layout-Tooling (verboten für generierte Artefakte)

## Nicht-Ziele

- Card-Interna, `set hass`-Lifecycle, Entity-Change-Detection, Shadow DOM, CSS-Custom-Properties — abgedeckt von `ha/lovelace-card-patterns`
- Card-Editor-UI-Mechanik (`ha-form`, `getConfigElement`) — abgedeckt von `ha/lovelace-card-editor`
- Card-Features / Tile-Features — abgedeckt von `ha/lovelace-card-features`
- Badge-Interna — abgedeckt von `ha/lovelace-badges`; diese Spec deckt nur ab, *wo Badges rendern und wo nicht*
- Programmatische Dashboard-/View-Generierung — abgedeckt von `ha/lovelace-strategies`
- Der Custom-View-/Panel-Element-Contract (Properties, `setConfig`, `ll-*`-Events) — abgedeckt von `ha/lovelace-views-panels`
- Theme-Definition, Python-Integration-Code, Blueprint-YAML und Namensregeln (`ha/naming-conventions`)

## Anforderungen

Der Katalog ist in A–E gruppiert. Jeder Eintrag nennt den **Antipattern**, **warum er falsch ist** und **stattdessen**, gefolgt von einer normativen Regel. RFC-2119-Schlüsselworte sind bindend; das eingeklammerte Evidenz-Tier hält fest, wie die Behauptung belegt ist.

### A. View-Typ-Wahl

- **A1 — Mehrere Cards in einem Panel-View.** `[doc: user]` `[src]` Ein Panel-View „must have exactly one card. This card is rendered full-width" (`home-assistant.io/dashboards/panel/`); das Frontend `hui-panel-view.ts` rendert nur `cards[0]` und zeigt eine Warnung, wenn mehr als eine Card konfiguriert ist. **Warum:** Die Randbedingung ist eine harte Regel, kein Hinweis — überzählige Cards rendern nicht (nur die erste), ein Panel ist kein Multi-Card-Container. **Stattdessen:** Den Inhalt in eine einzelne Stack- oder Grid-Card als die eine Card des Panels packen, oder einen Sections-View für echte Multi-Card-Seiten nutzen.
  - **MUSS NICHT [MUST NOT]** mehr als eine Card direkt in einen `type: panel`-View legen
  - **MUSS [MUST]** eine einzelne Container-Card (Stack/Grid) nutzen, wenn ein Panel zusammengesetzten Inhalt zeigen soll
- **A2 — Badges in Panel- oder Sidebar-Views erwarten.** `[doc: user]` „Sidebar and panel views do not support badges" und „badges do not show when view is in panel mode" (`home-assistant.io/dashboards/views/`). **Warum:** Das Feature ist in diesen Views by-design nicht unterstützt, also fehlt ein Status, den du als Badge sichtbar machen wolltest, schlicht. **Stattdessen:** Diesen Status in eine Card packen, oder einen View-Typ nutzen, der Badges unterstützt (Sections, Masonry).
  - **MUSS NICHT [MUST NOT]** sich auf `badges` in einem `type: panel`- oder `type: sidebar`-View verlassen
- **A3 — `type` weglassen und Sections erwarten.** `[doc: user]` `[src]` Wird `type` weggelassen, leitet das Frontend den View-Typ aus der Form des Views ab (`get-view-type.ts`): Ein View mit einer Top-Level-`cards:`-Liste defaultet auf **`masonry`** (die Legacy-Engine), während eine `sections:`-Liste oder ein leerer View auf **`sections`** defaultet und ein `panel: true`-Kurzschreiben ein Panel ergibt. Die offizielle Doku ist hier widersprüchlich — die Prosa sagt „Sections (default)", während die `type`-Parameter-Tabelle „default: masonry" sagt. **Warum:** Einen klassischen `cards:`-View ohne `type:` von Hand zu schreiben, landet still in Masonry — keine Sektions-Gruppierung, kein Drag-Rearrange, größenbasiertes Repacking — statt des angenommenen Sections-Layouts; und weil der abgeleitete Typ von der Schema-Form abhängt, ist er nicht zuverlässig vorhersehbar. **Stattdessen:** Den View-Typ explizit setzen.
  - **MUSS [MUST]** `type: sections` explizit setzen, wenn ein Sections-Layout beabsichtigt ist; **MUSS NICHT [MUST NOT]** sich auf den impliziten, form-abgeleiteten View-Typ-Default verlassen
- **A4 — Masonry für ein gruppiertes, angeordnetes Dashboard.** `[doc: user]` „The masonry view sorts cards in columns based on their card size" und „places the next card below the smallest card" (`home-assistant.io/dashboards/masonry/`); es hat keine native Gruppierung („to group cards, you have to use horizontal stack, vertical stack, or grid cards"). **Warum:** Masonry ordnet nach Card-Höhe, nicht nach Autor-Intention — Cards springen zwischen Spalten, wenn sich ihre Größen ändern, und es gibt kein Drag-Rearrange, sodass eine bewusste Anordnung nicht gehalten werden kann. **Stattdessen:** Einen Sections-View nutzen, wenn die Anordnung zählt. (Third-Party-`custom:layout-card` kann explizite Platzierung erzwingen, ist aber eine nicht-native Abhängigkeit — siehe D1.)
  - **SOLLTE [SHOULD]** `type: sections` für jedes Dashboard wählen, dessen Card-Anordnung bewusst statt beiläufig ist
- **A5 — In Sections bauen und später Konvertierung erwarten.** `[doc: user]` „you can migrate from a masonry to a sections view. Currently, you cannot migrate a sections view type into another view type" (`home-assistant.io/dashboards/views/`); die eingebaute Convert-Aktion ist Einbahn (masonry → sections) und erzeugt einen neuen zusätzlichen View, statt den Original-View umzuwandeln. **Warum:** Der automatische Konverter kann einen Sections-View nicht zu Panel/Sidebar/Masonry migrieren — Sections ist für das Tool ein Endzustand. (Man kann den `type` eines Views immer per YAML-Handbearbeitung ändern und die Cards neu anordnen, aber es gibt keinen automatischen Weg aus Sections heraus.) **Stattdessen:** Den View-Typ bewusst vorab wählen; nur `masonry → sections` ist eine unterstützte automatische Konvertierung.
  - **SOLLTE [SHOULD]** den View-Typ vorab gegen das Ziel-Layout wählen, statt auf eine spätere automatische Typ-Konvertierung zu bauen

### B. Custom-Card-Sizing im Grid

- **B1 — `getGridOptions()` an einer Custom Card weglassen.** `[doc: dev]` `[src]` „If you don't define this method, the card will take 12 columns and will ignore the rows of the grid" (`developers.home-assistant.io/docs/frontend/custom-ui/custom-card/`); der Frontend-Fallback ist `DEFAULT_GRID_SIZE = { columns: 12, rows: "auto" }` (`compute-card-grid-size.ts`). **Warum:** Jede Sektion ist 12 Spalten breit, also wird eine Card ohne Grid-Optionen auf volle Breite gezwungen und kann nicht neben einer anderen Card sitzen — sie verliert die Row-Kontrolle. Das ist ein schlechter Default, kein Crash: Flaggschiff-Cards liefern ohne aus (z. B. `mini-graph-card` implementiert nur `getCardSize()`). **Stattdessen:** `getGridOptions()` implementieren, das `columns` und `rows` (je eine Zahl, oder `columns: "full"` / `rows: "auto"`) mit `min_columns`/`max_columns`/`min_rows`/`max_rows`-Grenzen zurückgibt.
  - **SOLLTE [SHOULD]** `getGridOptions()` an jeder für den Sections-View gedachten Custom Card implementieren; Weglassen ist nur für eine Card akzeptabel, die wirklich die volle Sektionsbreite einnehmen soll
  - **SOLLTE [SHOULD]** `getGridOptions()` dem deprecateten `getLayoutOptions()` vorziehen (vom Frontend noch für Abwärtskompatibilität geshimmt)
- **B2 — Falschen oder geratenen `getCardSize()` zurückgeben.** `[doc: dev]` `[src]` `getCardSize()` gibt die Card-Höhe als Zahl (oder Promise) zurück, „a height of 1 is equivalent to 50 pixels", Default 1, und Home Assistant nutzt es, um „distribute the cards evenly over the columns in the masonry view". **Warum:** Es betrifft nur den **Masonry-View**-Spalten-Ausgleich (der Sections-View skaliert über `getGridOptions().rows`); ein Wert, der die reale Höhe nicht abbildet, verzerrt Masonrys Spalten-Ausgleich, sodass Cards in der falschen Spalte landen. **Stattdessen:** Eine realistische Höhenschätzung in 50px-Einheiten zurückgeben; für Cards, die Lazy-/Nested-Cards umschließen, die `getCardSize()` des Kindes asynchron auflösen (`customElements.whenDefined(...).then(() => el.getCardSize())`).
  - **MUSS [MUST]** `getCardSize()` implementieren, das eine realistische Höhe zurückgibt; **MUSS NICHT [MUST NOT]** eine willkürliche Konstante zurückgeben, die die gerenderte Höhe ignoriert
- **B3 — Default-Spalten kein Vielfaches von 3.** `[doc: dev]` `[src]` „For the number of columns, it's highly recommended to use multiple of 3 for the default value (`3`, `6`, `9` or `12`)". **Warum:** Das 12-Spalten-Grid teilt sauber in Drittel, also rastet ein Vielfaches-von-3-Default sauber gegen Nachbarn ein. Das gilt nur für den **Default**-`columns` — eine Spaltenzahl, die kein Vielfaches von 3 ist, ist ein explizit unterstützter „precise mode" (`isPreciseMode = columns % 3 !== 0` in `compute-card-grid-size.ts`), kein Fehler, und `min_columns`/`max_columns` dürfen beliebige Ganzzahlen sein (z. B. nutzt Mushroom `min_columns: 4`). **Stattdessen:** `columns` auf eines von 3/6/9/12 defaulten; bewusste Precise-Werte und min/max-Grenzen unbeschränkt lassen.
  - **SOLLTE [SHOULD]** `getGridOptions().columns` auf ein Vielfaches von 3 defaulten (`3`, `6`, `9`, `12`); ein Nicht-Vielfaches („precise mode") ist erlaubt, wo beabsichtigt
- **B4 — Hardcodierte Pixelbreiten, absolute Positionierung oder unnötiges `columns: full`.** `[rationale]` `[src]` Das dokumentierte Modell lässt HA Pixel aus Zellzahlen berechnen — „width of the section divided by 12 (approximately `30px`)" (`developers.home-assistant.io/.../custom-card/`) — und `columns: "full"` „enforce[s] your card to be full width". **Warum:** Eine Card, die ihre eigene äußere **Breite** in Pixeln fixiert oder sich absolut positioniert, um ihren Grid-Footprint zu erzwingen, bekämpft HAs responsive Sektions-Pixel-Rechnung und bricht bei Resize und auf Mobile. Fixe Pixel-**Höhen** für Inhalt sind *nicht* das Problem — `rows: "auto"` misst den gerenderten Inhalt, also sind innere Höhen in Ordnung. `columns: "full"` ist eine legitime, dokumentierte Option; der Antipattern ist, sie reflexartig zu setzen statt dann, wenn die Card wirklich die Sektion überspannt. **Stattdessen:** Zellzahlen via `getGridOptions()` deklarieren und HA den Footprint der Card skalieren lassen; relative Einheiten und HA-CSS-Custom-Properties nutzen (siehe `ha/lovelace-card-patterns`).
  - **MUSS NICHT [MUST NOT]** eine feste äußere **Breite** in px hardcodieren oder eine Custom Card absolut positionieren, um ihren Footprint im Grid zu erzwingen
  - **MUSS NICHT [MUST NOT]** `columns: "full"` setzen, außer die Card benötigt wirklich die volle Sektionsbreite
  - Fixe Pixel-**Höhen** für Inhalt sind akzeptabel — `rows: "auto"` misst sie
- **B5 — React für eine Custom Card oder ein Panel nutzen.** `[doc: dev]` `[src]` „You can use Polymer, Angular, Preact or any other popular framework (except for React …)" (`developers.home-assistant.io/.../custom-card/`); jede untersuchte Mainstream-Card (button-card, mini-graph-card, apexcharts-card, Mushroom, Bubble-Card) ist auf Lit gebaut, keine auf React. **Warum:** Eine Custom Card muss ein Custom Element sein, und React rendert nativ keins; die Doku schließt es aus. **Vorbehalt:** Die in der Doku zitierte Interop-Begründung ist älter als React 19 (das die Custom-Element-Interop verbesserte), und React kann *innerhalb* eines Custom-Element-Wrappers gehostet werden — aber das ist unkonventionell und abseits des Standardwegs. **Stattdessen:** Vanilla `HTMLElement` (Portfolio-Default, siehe `ha/lovelace-card-patterns`), Lit oder Preact.
  - **MUSS NICHT [MUST NOT]** eine Custom Card oder ein Panel mit React als Element-Render-Schicht bauen

### C. Struktur und Gruppierung

- **C1 — Ganzseitiges Layout aus tief verschachtelten Stacks bauen.** `[policy]`, mit einem `[doc: user]`-Gegenpol: Die Sections-Seite besagt, man kann „group cards without using horizontal or vertical stack cards" (`home-assistant.io/dashboards/sections/`), während die Stack-Seiten *sehr wohl* das Kombinieren eines Horizontal-Stacks in einem Vertical-Stack für ein kleines Grid demonstrieren. **Warum:** Verschachtelte Stacks sind der **Pre-Sections-Legacy-Ansatz** — vor dem Sections-View (ausgeliefert in HA 2024.3, Neu-Dashboard-Default ab 2024.11) waren sie die einzige Art, mehrspaltige Layouts zu bauen, und sie funktionieren heute weiter. Aber eine ganze Seite aus verschachtelten Stacks zu gerüsten liefert eine Struktur ohne Drag-Rearrange, mit brüchiger Verschachtelung und schlechtem responsivem Reflow, und ist mühsam zu editieren. Das ist ein veralteter, für neue Dashboards abzuratender Ansatz, **kein kaputter** — verschachtelte Stacks bleiben gültig, wo Sections das Layout nicht ausdrücken kann. **Stattdessen:** Einen Sections-View für Gruppierung auf Seitenebene nutzen und Stacks für enge lokale Komposition reservieren.
  - **SOLLTE [SHOULD]** einen Sections-View für Gruppierung auf Seitenebene bei neuen Dashboards nutzen; **SOLLTE NICHT [SHOULD NOT]** ganzseitiges Layout aus verschachtelten Vertical-/Horizontal-Stacks gerüsten, wenn ein Sections-View es ausdrückt
  - **KANN [MAY]** einen Horizontal-Stack in einem Vertical-Stack für ein kleines, in sich geschlossenes Cluster kombinieren, und **KANN [MAY]** verschachtelte Stacks behalten, wo ein Sections-Layout die beabsichtigte Anordnung nicht ausdrücken kann
- **C2 — Horizontal-Stack für viele oder ungleiche Cards.** `[rationale]` `[community]` Ein Horizontal-Stack lässt seine Cards „sit next to each other in the space of one column" (`home-assistant.io/dashboards/horizontal-stack/`) und teilt diese eine Spaltenbreite über sie auf. **Warum:** Je mehr Cards sich die Spalte teilen, desto schmaler wird jede, und in einem Single-Column-Mobile-Render quetscht die Reihe, statt umzubrechen. Der Gleichbreiten-Split und das Mobile-Quetschen sind **beobachtetes Community-Verhalten**, nicht in der offiziellen Horizontal-Stack-Doku belegt (die zu Breitenaufteilung und Mobile-Reflow schweigt); der Schmerz zeigt sich klar ab etwa vier oder mehr Cards oder gemischtem Inhalt. **Stattdessen:** Ein Sections-Grid oder eine Grid-Card mit sinnvoller `columns`-Zahl nutzen.
  - **SOLLTE NICHT [SHOULD NOT]** mehr als ein paar Cards (etwa vier oder mehr) in einen einzelnen Horizontal-Stack legen; **SOLLTE [SHOULD]** für breitere Cluster ein Sections-Grid oder eine Grid-Card bevorzugen
- **C3 — Grid-Card mit dem Sections-View-Grid verwechseln.** `[doc: user]` `[src]` Die Grid-**Card** (`type: grid`) hat `columns` (Default `3`) und `square` (Default `true`) und „will first fill the columns, automatically adding new rows as needed" (`home-assistant.io/dashboards/grid/`); Sections nutzt `type: grid` für den *Sektions-Wrapper*, der am responsiven 12-Spalten-Sections-Grid teilnimmt und die `columns`/`square`-Optionen der Card **nicht** übernimmt. **Warum:** Die `type: grid`-Namenskollision führt zum falschen Werkzeug — ein festes lokales NxM-Cluster gegenüber einer ganzseitigen responsiven Layout-Engine. **Stattdessen:** Die Grid-Card für ein festes lokales NxM-Cluster in einem View nutzen; einen Sections-View (dessen Sektionen `type: grid`-Wrapper sind) für ganzseitiges Layout.
  - **MUSS [MUST]** die Grid-Card (ein in `cards:` platzierter Container) vom Sections-Sektions-Wrapper (ebenfalls `type: grid`, aber mit dem Sections-Spalten-Modell) unterscheiden und das zum Layout-Scope passende wählen
- **C4 — Masonry mit Spacer- oder Leer-Cards austricksen.** `[rationale]` `[community]` Masonry „places the next card below the smallest card on the dashboard" (`home-assistant.io/dashboards/masonry/`); der Spacer-/Leer-Card-Trick ist eine verbreitete Community-Technik. **Warum:** Er ist gerade deshalb beliebt, weil Masonry-Platzierung größengekoppelt und unvorhersehbar ist — aber ein Spacer fester Größe hält seine Position nur, solange jede umgebende Card ihre aktuelle Höhe behält; jede Höhenänderung (State-Update, Ausklappen, responsiver Breakpoint) mischt die Spalten neu und lässt das beabsichtigte Layout kollabieren. Keine maßgebliche Quelle billigt Spacer. **Stattdessen:** Einen Sections-View nutzen, wo Platzierung explizit und deterministisch statt emergent ist.
  - **SOLLTE NICHT [SHOULD NOT]** Spacer-/Leer-Cards einfügen, um Masonrys Spaltenplatzierung zu steuern; **SOLLTE [SHOULD]** zu einem Sections-View wechseln, wenn Platzierung kontrolliert werden muss

### D. Third-Party-Tooling und Kompatibilität

- **D1 — Für generierte Artefakte von Third-Party-Layout-Tooling abhängen.** `[policy]` Third-Party-HACS-Layout-Add-ons (zum Beispiel layout-card, card-mod, stack-in-card) erzwingen Layouts, die HA-Core nativ nicht unterstützt. **Warum:** Sie brechen bei HA-Frontend-Updates, erfordern manuelle Installation und Registrierung zusätzlicher Resources durch den User, sind nicht aus einer Integration auto-registrierbar und bekommen keine Card-Picker- oder Editor-Integration — jedes davon verletzt die „HA-Kompatibilität jederzeit"-Anforderung für Artefakte, die dieses Plugin generiert. **Stattdessen:** Native Sections- / Grid- / Stack-Konstrukte plus `getGridOptions()` für Card-Sizing.
  - Scope: Dies verbietet *generierten / distribuierten* Artefakten, von Third-Party-Layout-Tooling abzuhängen. Es beurteilt **nicht** das eigene, **handgebaute** Dashboard eines Users, wo diese Tools Standard und legitim sind. Das Verbot ruht auf zwei Gründen — der Konsument hat die Resource womöglich nicht installiert/registriert (dann rendert das Artefakt gar nicht), und das Tooling greift in Frontend-Interna, die sich über Releases ändern (card-mod-Styling regredierte bei konkreten Frontend-Updates, z. B. 2025.1 und 2026.4).
  - **MUSS NICHT [MUST NOT]** Dashboard- oder Card-Artefakte generieren, die von Third-Party-Layout-Tooling abhängen (layout-card, card-mod, stack-in-card oder Äquivalente)
  - **MUSS [MUST]** das Ziel-Layout mit nativen HA-Konstrukten erreichen (Sections, Grid-Card, Stacks, `getGridOptions()`)
- **D2 — Drag-Rearrange oder Resize in Nicht-Sections-Views annehmen.** `[doc: user]` Im Sections-View „you can rearrange sections and cards by dragging them… This is not yet possible in other views" (`home-assistant.io/dashboards/sections/`). **Warum:** Einen Workflow um Drag-Rearrange (oder Drag-Resize) in Masonry/Panel/Sidebar zu bauen, verspricht eine Editor-Fähigkeit, die diese Views nicht bieten. **Stattdessen:** Einen Sections-View nutzen, wenn interaktives Umordnen Teil der beabsichtigten Experience ist.
  - **SOLLTE [SHOULD]** einen Sections-View wählen, wenn Drag-Rearrange erwartet wird; **MUSS NICHT [MUST NOT]** Nicht-Sections-Views als Drag-Rearrange-unterstützend dokumentieren

### E. Responsive- und Geräte-Verhalten

- **E1 — `narrow` und den Mobile-Single-Column-Collapse ignorieren.** `[doc: dev]` Ein Custom Panel empfängt `narrow` (boolean), „if the panel should render in narrow mode" (`developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/`); `[doc: user]` ein Sidebar-View: „on mobile, all cards are rendered in 1 column and kept in the order indicated in the YAML configuration" (`home-assistant.io/dashboards/sidebar/`) — dieser dokumentierte 1-Spalten-Collapse ist **Sidebar-spezifisch**; das Mobile-Spalten-Verhalten anderer Views ist undokumentiert (siehe Offene Fragen). **Warum:** Ein Panel, das `narrow` nie liest, oder eine Sidebar, deren Card-Reihenfolge den Mobile-Collapse ignoriert, läuft über oder liest sich auf Telefonen in falscher Reihenfolge. **Stattdessen:** Die `narrow`-Property in Custom Panels behandeln und Cards so ordnen, dass der Single-Column-Collapse noch korrekt liest.
  - **SOLLTE [SHOULD]** die `narrow`-Property in Custom Panels lesen und respektieren
  - **SOLLTE [SHOULD]** Cards so ordnen, dass ein Single-Column-Collapse (der dokumentierte Sidebar-/Mobile-Fall) eine sinnvolle Lesereihenfolge bewahrt

## Acceptance Criteria

- [ ] Jeder `type: panel`-View enthält genau eine Card (eine Container-Card, wenn zusammengesetzt) — A1
- [ ] Auf `badges` wird in keinem `type: panel`- oder `type: sidebar`-View gebaut — A2
- [ ] View-`type` ist explizit gesetzt; kein View verlässt sich auf den impliziten, form-abgeleiteten Default, wenn Sections beabsichtigt ist — A3
- [ ] Bewusst angeordnete Dashboards nutzen `type: sections`, nicht Masonry — A4/A5
- [ ] Jede generierte, für Sections gedachte Custom Card implementiert `getGridOptions()` (oder überspannt bewusst die volle Sektionsbreite) — B1
- [ ] Jede generierte Custom Card implementiert einen realistischen `getCardSize()` — B2
- [ ] Default-`getGridOptions().columns` ist ein Vielfaches von 3 (`3`/`6`/`9`/`12`), außer ein Precise-Wert ist beabsichtigt — B3
- [ ] Keine Custom Card hardcodiert eine feste äußere Pixelbreite oder absolute Positionierung, um ihren Grid-Footprint zu erzwingen; `columns: "full"` wird nur genutzt, wenn die volle Reihe wirklich erforderlich ist (fixe Inhalts-Höhen sind ok) — B4
- [ ] Keine Custom Card oder Panel wird mit React als Render-Schicht gebaut — B5
- [ ] Layout auf Seitenebene nutzt bei neuen Dashboards einen Sections-View, kein Nested-Stack-Gerüst — C1
- [ ] Horizontal-Stacks halten nur wenige Cards; breitere Cluster nutzen ein Sections-Grid oder eine Grid-Card — C2
- [ ] Grid-Card und Sections-Sektions-Wrapper werden nicht vermengt — C3
- [ ] Keine Spacer-/Leer-Cards werden zur Masonry-Platzierungssteuerung genutzt — C4
- [ ] Kein generiertes Artefakt referenziert Third-Party-Layout-Tooling (layout-card, card-mod, stack-in-card, …) — D1
- [ ] Kein Nicht-Sections-View wird als Drag-Rearrange-unterstützend dargestellt — D2
- [ ] Custom Panels lesen `narrow`; die Card-Reihenfolge übersteht den Single-Column-Mobile-Collapse — E1
- [ ] Jede HA-interne Behauptung in einem generierten Layout ist auf eine offizielle Doku-Seite oder den Frontend-Quellcode zurückführbar; `[rationale]`/`[community]`/`[policy]`-Einträge werden nicht als HA-Fakten dargestellt
- [ ] Quality-Scale-Marker: nicht Teil der HA-Quality-Scale (Portfolio-Guardrail)

## Verification

Dieser Katalog wurde am 2026-07-22 adversarial verifiziert: Für jeden Antipattern wurde eine permissive Negation („diese Praxis ist eigentlich in Ordnung") gegen reale HA-Dashboard-/Panel-Entwicklung getestet — den HA-Frontend-Quellcode (`github.com/home-assistant/frontend`: `get-view-type.ts`, `hui-panel-view.ts`, `types.ts`, `hui-card.ts`, `compute-card-grid-size.ts`), populäre Custom Cards (button-card, mini-graph-card, apexcharts-card, Mushroom, Bubble-Card) und Community-Praxis. **Kein Antipattern wurde widerlegt.** Ergebnisse:

- **Wie geschrieben bestätigt**: A2, A4, C3, C4, D2.
- **Bestätigt, Formulierung auf die jetzt inline stehende Nuance geschärft**: A1 (Panel rendert `cards[0]` plus Warnung — nicht still), A3 (weggelassener `type` ist form-abgeleitet, kein pauschaler `masonry`-Default), A5 (Einbahn gilt fürs Convert-Tool; manuelles YAML-Umtypen bleibt möglich), B2, B3, B4, B5, C1 (Legacy-Ansatz, nicht kaputt), C2 (community-beobachteter Mechanismus), D1 (auf generierte/distribuierte Artefakte gescopt), E1 (das Collapse-Zitat ist Sidebar-spezifisch).
- **Schweregrad korrigiert**: **B1 von MUST auf SHOULD herabgestuft** — `getGridOptions()` wegzulassen ist ein schlechter Default (volle Breite, Rows ignoriert), kein Crash; `mini-graph-card` liefert ohne aus.

Im Durchlauf aufgelöste Doku-Hazards (zuvor Offene Fragen):

- `getLayoutOptions()` ist eine reale, aber `@deprecated` Frontend-Methode, abgelöst durch `getGridOptions()`, noch für Abwärtskompatibilität geshimmt (`types.ts`, `hui-card.ts`). Neue Cards nutzen `getGridOptions()`; `LovelaceGridOptions` ist `{ columns?: number | "full"; rows?: number | "auto"; min_columns?; max_columns?; min_rows?; max_rows? }`.
- Der weggelassene `type`-Default ist form-abhängig in `get-view-type.ts` (`cards:` → masonry, `sections:` / leer → sections, `panel:` → panel); der Prosa-vs-Tabelle-Widerspruch der Doku ist textuell, das Verhalten aber definiert.
- Ein Panel mit mehr als einer Card rendert nur `cards[0]` und zeigt eine Warnung (`hui-panel-view.ts`); es wirft keinen Fehler.
- Sections wurde in HA 2024.3 ausgeliefert und ab 2024.11 zum Neu-Dashboard-Default.

## Offene Fragen

Verbleibende Doku-Hazards — ehrlich festgehalten statt behauptet. Jedes sollte gegen die offizielle Doku oder den Frontend-Quellcode neu geprüft werden, bevor eine nachgelagerte Spec es verhärtet.

- **`grid_options`-User-Override-Präzedenz**: Der nutzerseitige `grid_options`-YAML-Key und das card-seitige `getGridOptions()` werden beide vom Frontend (`hui-card`) angewendet, aber die genaue Merge-Präzedenz (User-Config vs. Card-Default) ist nicht dokumentiert. Hier nur über die card-seitige Methode behandelt.
- **`max_columns` / `dense_section_placement`**: Diese erscheinen in der Nutzer-Doku nur als UI-Label („Max number of sections wide", „Dense section placement"), ohne dokumentierten YAML-Key. Nicht als Config-Keys kodiert.
- **Sections-Resize-Handles**: Die Nutzer-Doku beschreibt Drag-*Rearrange*, aber nicht Drag-*Resize* von Cards in Grid-Einheiten. Die Resize-Fähigkeit existiert im Produkt, ist aber undokumentiert; D2s „oder Resize"-Klausel bleibt eine Rationale-Erweiterung, kein Doku-Zitat.
- **Masonry-Spaltenzahl / Breakpoints**: Die Nutzer-Doku nennt keine Spaltenzahl, keine Bildschirmbreiten-Anpassung und keine numerischen responsiven Breakpoints für irgendeinen View. E1s responsive Regeln bleiben auf dokumentiertem Niveau (Sidebar-1-Spalten-Collapse; Panel-`narrow`).
- **`getGridOptions()`-Einführungs-Release**: Sections wurde in 2024.3 ausgeliefert, aber das genaue Release, das die `getGridOptions()`-Card-Methode einführte, ist nicht an eine Doku-Aussage gepinnt.
