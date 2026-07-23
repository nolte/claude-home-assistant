# HA Dashboard: Card- und Panel-Sizing

Status: draft

## Kontext

Eine Custom-Lovelace-Card oder ein Panel muss deklarieren, wie groß sie ist. Home
Assistant hat **zwei** unabhängige Sizing-Kanäle und **drei** View-Typen, die sie
unterschiedlich konsumieren — und der nützlichste Wert ist undokumentiert. Deshalb
raten Autoren regelmäßig und liefern Cards aus, die in einem View korrekt rendern
und in einem anderen brechen.

- **Sections-View** liest `getGridOptions()` — ein 12-Spalten-Grid, in dem jede
  Card ein Rechteck aus Grid-Zellen belegt (`columns` × `rows`).
- **Masonry- und Panel-Views sowie Stacks** lesen das Legacy-`getCardSize()` —
  eine Höhe in ~50px-Einheiten zur Verteilung der Cards in Spalten.

Der Ausgangsfall: Die Custom-Cards in `nolte/kamerplanter-ha` deklarierten je einen
**festen, geratenen** `rows`-Wert. Im **Sections-View-Edit-Mode** pinnt ein
numerischer `rows` die Card auf eine feste Pixelhöhe (den `.fit-rows`-Höhen-`calc`);
höhere, content-abhängige Cards liefen aus ihrer Grid-Zelle über, und HA verankert
seine Edit-Mode-Overlays (Drag-Handle, gestrichelte `+`-Add-Zone, Drop-Indicator)
an der **Grid-Zellen-Grenze**, nicht an der realen Content-Box — die Overlays landen
mitten im Card-Content. Der Fix war `rows: "auto"`. Ihn zu finden erforderte das
Lesen der Frontend-Source, weil die Developer-Docs den Wert `"auto"` nicht
dokumentieren.

Dieser Spec ist das kanonische, source-basierte **Entscheidungsverfahren**: Welche
Größen-Deklaration (`getGridOptions` + `getCardSize`) rendert eine Card angesichts
ihres Designs und ihrer Content-Variabilität über **alle** View-Typen, **beide**
Modi (view / edit) und **alle** Device-Größen korrekt?

**Abgrenzung.** Dieser Spec besitzt ausschließlich das *Sizing-Entscheidungs­verfahren*.
Card-Interna und der `getGridOptions`/`getCardSize`-Lifecycle leben in
`ha/lovelace-card-patterns`; der breitere Layout-/Arrangement-Guardrail-Katalog
(inklusive der Pixel-Breiten- und `columns: "full"`-Antipatterns) lebt in
`ha/lovelace-layout-antipatterns`; der View-/Panel-Element-Kontrakt in
`ha/lovelace-views-panels`; Card-Features in `ha/lovelace-card-features`.
Überschneidungen werden per Slug referenziert, nicht wiederholt.

**Evidenz-Stufen.** HA-interne Fakten werden gegen die offiziellen Docs und die
Frontend-Source verifiziert, nicht aus dem Gedächtnis behauptet
(`ha/upstream-docs-verification`). Jede Aussage trägt ihre Stufe:

- `[doc: dev]` — verifiziert gegen die Developer-Docs
  (`developers.home-assistant.io/docs/frontend/custom-ui/*`); die Seite ist benannt.
- `[src]` — bestätigt gegen die HA-Frontend-Source
  (`github.com/home-assistant/frontend@dev`); die Datei ist benannt.
- `[rationale]` — im dokumentierten/source-belegten Modell begründet, aber
  hergeleitet, kein wörtliches Zitat.

Quality-Scale-Marker: Dashboard-Layout und Custom-Cards sind **nicht Teil der
HA-Quality-Scale** — dies ist ein nolte-Portfolio-Guardrail und liegt außerhalb der
Scale.

## Ziele

- Einen deterministischen Entscheidungsbaum liefern, der die Content-Form einer Card
  auf eine Größen-Deklaration abbildet, die in Sections-, Masonry- und Panel-Views,
  im View- und im Edit-Mode korrekt ist.
- Die Beziehung `getGridOptions` ↔ `getCardSize` explizit machen: Welcher View-Typ
  liest welche, und wann beide implementiert sein müssen.
- Die CSS-Vorbedingungen kodifizieren, die eine Card erfüllen muss, damit
  `rows: "auto"` ihren realen Content misst.
- Den Wert `rows: "auto"` und die `.fit-rows`-Höhenmechanik mit Source-Zitaten
  festhalten, da die Developer-Docs sie auslassen.
- Das Edit-Mode-Overlay-Anchoring erklären, damit Autoren verstehen, *warum* eine
  falsche Höhe Overlap erzeugt.

## Nicht-Ziele

- Card-Lifecycle, Registrierung und Rendering-Framework-Wahl — siehe
  `ha/lovelace-card-patterns` und `ha/lovelace-views-panels`.
- Der vollständige Layout-/Arrangement-Antipattern-Katalog — siehe
  `ha/lovelace-layout-antipatterns` (dieser Spec referenziert ihn, wiederholt ihn nicht).
- Ein Build-Stack, TypeScript oder eine Lit-Migration — separates Anliegen.
- Runtime-Verifikation auf einer laufenden HA-Instanz — `ha-integration-deployer` /
  `ha-integration-verifier`.

## Feld-Referenz (Source of Truth)

`getGridOptions()` liefert `LovelaceGridOptions` `[src: src/panels/lovelace/types.ts]`:

```ts
export interface LovelaceGridOptions {
  columns?: number | "full";
  rows?: number | "auto";
  max_columns?: number;
  min_columns?: number;
  min_rows?: number;
  max_rows?: number;
}
```

- `columns` — Grid-Zellen-Breite. Eine Zahl oder `"full"` (spannt die ganze
  Section). Default `12`, wenn `getGridOptions` fehlt `[doc: dev]`; der
  Frontend-Fallback ist `DEFAULT_GRID_SIZE = { columns: 12, rows: "auto" }`
  `[src: src/panels/lovelace/common/compute-card-grid-size.ts]`. Die Docs empfehlen
  ein Vielfaches von 3 (`3, 6, 9, 12`) für den Default `[doc: dev]`.
- `rows` — Grid-Zellen-Höhe. Eine Zahl (**feste** Höhe) **oder** `"auto"`
  (**content-gemessene** Höhe). Der Wert `"auto"` ist auf der Custom-Card-Seite
  **nicht dokumentiert** `[doc: dev]`; er ist source-belegt `[src: types.ts]` und
  ist der eigene Default des Frontends.
- `min_columns` / `max_columns` / `min_rows` / `max_rows` — die responsiven
  Grenzen, innerhalb derer der User skalieren darf. Dokumentierte Defaults:
  `min_columns = 1`, `min_rows = 1` `[doc: dev]`.

Ein Legacy-Pendant `LovelaceLayoutOptions` trägt dieselben Felder unter einem
`grid_`-Präfix (`grid_columns`, `grid_rows`, …) `[src: types.ts]`; neue Cards nutzen
`getGridOptions()` / `LovelaceGridOptions`.

`getCardSize()` liefert eine Höhe, bei der **1 Einheit ≈ 50px** ist; der Default ist
`1`, wenn undefiniert; sie darf ein `Promise<number>` für lazy Content liefern
`[doc: dev]`.

### Wie die Section die Felder rendert `[src: src/panels/lovelace/sections/hui-grid-section.ts]`

- Das Section-Grid deklariert `grid-auto-rows: auto;`.
- Die `fit-rows`-Klasse — die eine **feste** Pixelhöhe pinnt — wird **genau dann**
  angewandt, wenn `typeof rows === "number"`. Eine `rows: "auto"`-Card ist nie
  `.fit-rows`; sie wächst mit `grid-auto-rows`.
- `--row-size` / `--column-size` werden aus den Optionen **nur bei numerischen
  Werten** gesetzt; für `"auto"` / `"full"` bleiben sie `undefined`.
- Die feste Höhe ist:

  ```css
  .card.fit-rows {
    height: calc(
      (var(--row-size, 1) * (var(--row-height) + var(--row-gap))) - var(--row-gap)
    );
  }
  ```

  Mit den Section-Defaults `--row-height: 56px` und `--row-gap: 8px`
  (`--ha-section-grid-row-height` / `--ha-section-grid-row-gap`; Spalten-Gap
  `--ha-section-grid-column-gap: 8px`) ist ein numerisches `rows = N` exakt
  `N × (56 + 8) − 8` px.
- **Edit-Mode** fügt jeder Card `min-height: calc((var(--row-height) - var(--row-gap)) / 2)`
  (= `24px`) hinzu, und die Add-Zone ist `.add { height: var(--row-height) }`
  (= `56px`). Diese Overlays werden gegen die **Grid-Zelle** gelayoutet, sodass eine
  Zelle, die kürzer als der Content ist, sie über den Content legt — der
  Ausgangs-Bug.

## Requirements

### R1 — Sizing-Modell aus der Content-Form wählen `[rationale]`

- **MUSS [MUST]** die Card vor der Größen-Deklaration klassifizieren: Ist ihre
  gerenderte Höhe **content-abhängig** (Entity-Listen, Timelines, Logbücher,
  variable Sektionen, deren Höhe nicht aus der Config bekannt ist) oder
  **deterministisch** (ein festes Layout, dessen Höhe aus der Config folgt)?
- Content-abhängig → der `"auto"`-Zweig (R2). Deterministisch → der
  Computed-Fixed-Zweig (R3). Eine Card, die unsicher ist, **MUSS [MUST]** auf
  `"auto"` defaulten, passend zum eigenen `DEFAULT_GRID_SIZE` des Frontends
  `[src: compute-card-grid-size.ts]`.

### R2 — Content-abhängige Cards nutzen `rows: "auto"` `[src: hui-entities-card.ts]`

- **MUSS [MUST]** `rows: "auto"` aus `getGridOptions()` liefern, plus einen
  `columns`-Default und einen `min_columns`-Boden. Das kanonische Beispiel ist
  `hui-entities-card`:

  ```ts
  public getGridOptions(): LovelaceGridOptions {
    return { columns: 12, rows: "auto", min_columns: 3 };
  }
  ```

- **MUSS [MUST]** die CSS-Vorbedingungen aus R5 erfüllen, damit
  `grid-auto-rows: auto` den realen Content messen kann.
- **MUSS NICHT [MUST NOT]** `min_rows` / `max_rows` auf einer `"auto"`-Card setzen,
  außer um eine echt skalierbare Spanne zu begrenzen; ein festes `min_rows` führt
  einen Boden wieder ein, den der Content überschreiten kann.

### R3 — Deterministische Cards berechnen ein numerisches `rows` und pinnen `min_rows: rows` `[src: hui-tile-card.ts]`

- **MUSS [MUST]** `rows` aus der Config berechnen und `min_rows: rows` liefern,
  damit der User die Card nicht unter ihren realen Content schrumpfen kann. Das
  kanonische Beispiel ist `hui-tile-card`:

  ```ts
  public getGridOptions(): LovelaceGridOptions {
    const columns = 6;
    let min_columns = 6;
    let rows = 1;
    // … rows pro Feature-Zeile / vertikalem Layout inkrementieren …
    return { columns, rows, min_columns, min_rows: rows };
  }
  ```

- **MUSS [MUST]** das numerische `rows` mit der realen gerenderten Höhe synchron
  halten; ein Unter-Zählen reproduziert den Edit-Mode-Overlay-Overlap (siehe R6).

### R4 — `getCardSize()` neben `getGridOptions()` implementieren `[doc: dev]` `[rationale]`

- **SOLLTE [SHOULD]** **beide** Callbacks implementieren. `getGridOptions()`
  steuert nur den **Sections**-View; `getCardSize()` steuert **Masonry**- und
  **Panel**-Views sowie **Stacks**. Eine Card mit nur `getGridOptions()` defaultet
  in Masonry auf Größe `1` (≈50px) und verteilt falsch; eine Card mit nur
  `getCardSize()` fällt in Sections auf `{ columns: 12, rows: "auto" }` (volle
  Breite) zurück.
- **MUSS [MUST]** `getCardSize()` dasselbe Content-Modell widerspiegeln lassen:
  content-abhängige Cards leiten es aus dem Content ab (wie `hui-entities-card`
  Title/Entities/Header/Footer summiert) `[src]`; deterministische Cards liefern
  eine feste, mit dem berechneten `rows` konsistente Zahl (wie `hui-tile-card`)
  `[src]`.
- **KANN [MAY]** ein `Promise<number>` aus `getCardSize()` liefern, wenn die Höhe
  von lazy definierten Child-Elementen abhängt `[doc: dev]`.

### R5 — CSS-Vorbedingungen für `rows: "auto"` `[src: hui-grid-section.ts]` `[rationale]`

Damit `grid-auto-rows: auto` die Card misst, **MUSS NICHT [MUST NOT]** der
Card-Root:

- eine feste `height` oder `height: 100%` auf dem Card-Root setzen (verhindert die
  Messung);
- `overflow: hidden` so nutzen, dass es den gemessenen Content abschneidet;
- `position: absolute` auf dem Root nutzen (kollabiert die gemessene Box auf 0).

Feste Pixel-**Höhen auf innerem Content sind in Ordnung** — `"auto"` misst die
gerenderte Box (das grenzt zu `ha/lovelace-layout-antipatterns` B4 ab, das innere
Höhen von äußerem Breiten-Pinning unterscheidet).

### R6 — Edit-Mode explizit berücksichtigen `[src: hui-grid-section.ts]`

- **MUSS [MUST]** den Edit-Mode-Overlay-Overlap als Sizing-Defekt behandeln, nicht
  als kosmetischen: Weil Overlays an der Grid-Zelle verankert sind (`min-height 24px`,
  Add-Zone `56px`), platziert eine Zelle, die kürzer als der Content ist, sie falsch.
- **MUSS [MUST]** ihn über den korrekten Zweig lösen — `rows: "auto"` (R2) für
  content-abhängige Cards, oder ein korrekt berechnetes numerisches `rows` mit
  `min_rows: rows` (R3) — nie durch das Tunen eines geratenen festen `rows`.

### R7 — Responsive Columns über Devices `[doc: dev]` `[rationale]`

- **MUSS [MUST]** einen `columns`-Default (ein Vielfaches von 3 wird empfohlen) und
  einen `min_columns`-Boden deklarieren, damit die Card sinnvoll reflowt, wenn die
  Section auf Tablet und Mobile schmaler wird; **SOLLTE [SHOULD]** `max_columns`
  setzen, wenn die Card eine obere nützliche Breite hat.
- **MUSS [MUST]** `columns: "full"` für Cards reservieren, die die Section echt
  spannen, nicht als Reflex (siehe `ha/lovelace-layout-antipatterns` B4). Der
  device-spezifische Mobile-Single-Column-Collapse ist view-typ-abhängig und gehört
  `ha/lovelace-layout-antipatterns` E1 — referenziert, hier nicht wiederholt.

## Entscheidungsbaum

```
Ist die gerenderte Höhe der Card allein aus ihrer Config bekannt?
│
├─ NEIN (Listen, Timelines, Logbücher, variabler Content)
│      → getGridOptions: { columns: <Vielfaches-von-3>, rows: "auto", min_columns: <Boden> }
│      → getCardSize:    aus dem Content ableiten (Summe der Zeilen/Children)
│      → R5-CSS-Vorbedingungen erfüllen
│
└─ JA  (deterministisch, festes Layout)
       → rows aus der Config berechnen
       → getGridOptions: { columns, rows, min_columns, min_rows: rows[, max_*] }
       → getCardSize:    eine feste, mit rows konsistente Zahl
```

## Acceptance Criteria

- [ ] Die Card klassifiziert als content-abhängig oder deterministisch und nutzt den
      passenden Zweig (`rows: "auto"` vs. numerisches `rows` + `min_rows: rows`).
- [ ] `getGridOptions()` und `getCardSize()` sind **beide** implementiert und
      konsistent miteinander und mit dem gewählten Modell.
- [ ] Für `rows: "auto"`-Cards gelten die R5-CSS-Vorbedingungen (kein festes/`100%`
      Root-`height`, kein abschneidendes `overflow: hidden`, kein
      `position: absolute`-Root).
- [ ] Im Sections-View-**Edit-Mode** gibt es keinen Overlay-Overlap: Drag-Handle,
      gestrichelte `+`-Add-Zone und Drop-Indicator sitzen an der Zellen-Grenze, nicht
      im Content.
- [ ] Im Sections-View-**View-Mode** gibt es kein Content-Clipping und keinen
      Leerraum.
- [ ] Auf Desktop, Tablet und Mobile reflowt die Card innerhalb ihrer
      `min_columns`/`max_columns`-Grenzen ohne Overflow.
- [ ] In Masonry- und Panel-Views verteilt die Card sinnvoll (ein korrektes
      `getCardSize()`, nicht der Default `1`).
- [ ] Jede HA-interne Aussage in der erzeugten Card/im Spec trägt ein `[doc: dev]`-
      oder `[src]`-Zitat; keine Aussage wird aus dem Gedächtnis behauptet.

## Verifikation

Der Feld-Satz, der Wert `"auto"`, der `.fit-rows`-Höhen-`calc`, der
`grid-auto-rows: auto`-Default, das `typeof rows === "number"`-Gate für `.fit-rows`,
die Edit-Mode-`min-height`/Add-Zone-Höhen und die zwei kanonischen Card-Muster
wurden am 2026-07-22 gegen `github.com/home-assistant/frontend@dev` bestätigt
(`src/panels/lovelace/types.ts`, `.../common/compute-card-grid-size.ts`,
`.../sections/hui-grid-section.ts`, `.../cards/hui-entities-card.ts`,
`.../cards/hui-tile-card.ts`) sowie gegen die Developer-Docs
(`developers.home-assistant.io/docs/frontend/custom-ui/custom-card/`). Die
Developer-Docs-Auslassung von `rows: "auto"` ist oben festgehalten; die Source ist
dafür autoritativ.

## Offene Fragen

- Das genaue HA-Release, in dem jedes `LovelaceGridOptions`-Feld erstmals
  ausgeliefert wurde, ist hier nicht fixiert; der Sections-View ist HA 2024.3+ und
  der Feld-Satz ist auf `@dev` vorhanden. Eine „since version"-Tabelle pro Feld wird
  verschoben, bis eine versionierte Source zitiert werden kann.
- Das genaue Mobile-Column-Count-Verhalten pro View-Typ (jenseits des
  Sidebar-1-Spalten-Collapse, der `ha/lovelace-layout-antipatterns` E1 gehört) ist
  upstream undokumentiert und bleibt offen.
