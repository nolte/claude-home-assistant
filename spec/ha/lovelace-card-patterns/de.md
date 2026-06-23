# HA-Integration: Lovelace-Card-Patterns

Status: draft

## Kontext

Custom Lovelace Cards sind die Frontend-Erweiterung einer HA Custom Integration: ein JavaScript-Modul, das einen `HTMLElement` registriert, von HA als Card-Type erkannt wird und im Dashboard ausgewählt werden kann. Die HA-Card-API ist deklarativ-aufgebaut — die Card empfängt das `hass`-Objekt als Property-Setter, rendert ihren Zustand via Shadow DOM, und liefert Lifecycle-Callbacks (`setConfig`, `getCardSize`, `getGridOptions`, `getConfigElement`, `getStubConfig`) zurück, die das Card-Picker-UI und das Resize-Verhalten steuern.

`nolte/kamerplanter-ha` liefert Custom Cards als Vanilla-JS unter `custom_components/<domain>/www/`, **auto-registriert** in `__init__.py` über `StaticPathConfig`, sodass User die Cards nicht manuell in Lovelace-Resources eintragen müssen. Das Repo kodifiziert in `spec/ha-integration/LOVELACE-CARD-PATTERNS.md` zusätzlich drei nicht-offensichtliche Regeln: (1) **Entity-Change-Detection** im `set hass`-Callback verhindert unnötiges Re-Rendering bei jedem HA-State-Tick; (2) **HA-CSS-Custom-Properties** (`var(--primary-text-color)`, …) statt hardcodierter Farben; (3) **`getGridOptions`** für responsive Card-Layouts.

Diese Spec überführt das Pattern in eine generische Verpflichtung. Die Lovelace-Card lebt im selben Repo wie die Custom Integration, ist aber eine getrennte Lieferform — Card-Entwicklung kann unabhängig von Integration-Entwicklung passieren.

Quality-Scale-Marker: **Bronze** (Custom Cards sind nicht Teil der HA-Quality-Scale; das Pattern hier ist nolte-portfolio-spezifisch und steht außerhalb der Skala).

## Ziele

- Vanilla-JS als Standard-Stack für Custom Cards festschreiben — kein Lit, kein React, kein Build-Step (zumindest für die initiale Generation; Build-Stack ist eigene Folge-Spec)
- Auto-Registrierung der Cards aus dem `www/`-Ordner in `__init__.py` zur Pflicht machen — User muss nichts manuell zu Lovelace-Resources hinzufügen
- Entity-Change-Detection als Default-Pattern im `set hass`-Callback etablieren
- Shadow DOM als Default-Render-Target — keine Style-Leaks ins HA-Frontend
- HA-CSS-Custom-Properties statt hardcodierter Farben — die Card respektiert das aktive HA-Theme automatisch
- `getGridOptions` für responsive Card-Größen, sodass Cards in HA-Sections (HA 2024.3+) sinnvoll skalieren

## Nicht-Ziele

- Build-Stacks (Vite, esbuild, Rollup, Webpack) — eigene Folge-Spec, sobald die erste Card einen Build-Step rechtfertigt
- TypeScript / Lit-basierte Cards — eigene Folge-Spec
- Custom-Card-Editor-UIs (über `getConfigElement` hinaus) — adressiert hier nur als Mindest-Vorgabe, nicht als Detail-Pattern
- HACS-Distribution für Standalone-Cards (außerhalb einer Integration) — andere Lieferachse
- Frontend-Theming durch die Card selbst — Cards konsumieren das HA-Theme, sie definieren keins

## Anforderungen

### Card-Datei-Layout

- **MUSS [MUST]** Custom Cards unter `custom_components/<domain>/www/<card-name>.js` ablegen
- **SOLLTE [SHOULD]** pro Card-Type ein eigenes JS-Modul führen — keine Mega-Datei mit mehreren Cards
- **KANN [MAY]** zusätzliche Assets (SVG-Icons, lokal gehostete Fonts) im selben `www/`-Ordner ablegen, solange sie über die Auto-Registrierung erreichbar bleiben
- **MUSS NICHT [MUST NOT]** Cards in einem zweiten, parallelen `www/`-Ordner auf Repository-Wurzel-Ebene ablegen — der HA-Integration-`www/` ist die kanonische Quelle

### Auto-Registrierung in `__init__.py`

- **MUSS [MUST]** in `async_setup_entry` (oder einem dedizierten Setup-Hook) jede Card-Datei aus `custom_components/<domain>/www/` über `await hass.http.async_register_static_paths([StaticPathConfig(url_path=..., path=..., cache_headers=False)])` registrieren
- **MUSS [MUST]** `cache_headers=False` setzen — sonst landen aktualisierte Card-JS-Dateien für User mit gecachten Browser-Resources im Stale-Zustand
- **SOLLTE [SHOULD]** zusätzlich den Card-Type über `frontend.add_extra_js_url(hass, url_path)` registrieren, sobald HA das nativ pro Integration unterstützt — aktuell Workaround über `frontend.async_register_built_in_panel` oder dynamische Lovelace-Resource-Ergänzung
- **MUSS NICHT [MUST NOT]** den User auffordern, die Card manuell in Lovelace-Resources einzutragen — Auto-Registrierung ist Pflicht

### `HTMLElement`-Subklasse

- **MUSS [MUST]** die Card als Subklasse von `HTMLElement` definieren — keine Lit / React / Vue-Wrapper
- **MUSS [MUST]** `customElements.define("<card-type>", <CardClass>)` aufrufen, mit `<card-type>` in lowercase-kebab-case, präfigiert mit dem Integration-Domain (z. B. `domain-resource-card`)
- **MUSS [MUST]** `window.customCards = window.customCards || []; window.customCards.push({type: "<card-type>", name: "...", description: "...", preview: false})` aufrufen, damit die Card im Lovelace-Card-Picker erscheint
- **MUSS [MUST]** `connectedCallback()` implementieren, das `attachShadow({mode: "open"})` aufruft und initiales Rendering anstößt — keine Direkt-Manipulation des Light-DOM

### `setConfig(config)` Lifecycle

- **MUSS [MUST]** `setConfig(config)` implementieren — HA ruft das auf, sobald der User die Card-Konfiguration speichert
- **MUSS [MUST]** ungültige Konfigurationen mit `throw new Error("...")` ablehnen — HA fängt den Error und rendert eine Fehler-Card
- **SOLLTE [SHOULD]** Schema-Pflichtfelder in `setConfig` prüfen (`if (!config.entity) throw new Error("entity is required")`)
- **MUSS NICHT [MUST NOT]** I/O oder asynchrone Calls in `setConfig` ausführen — der Lifecycle ist synchron

### `set hass(hass)` mit Entity-Change-Detection

- **MUSS [MUST]** `set hass(hass)` als Setter-Property implementieren — HA setzt ihn bei jedem State-Tick
- **MUSS [MUST]** Entity-Change-Detection durchführen, **bevor** ein Re-Render ausgelöst wird — Vergleich `this._hass?.states[id] !== hass.states[id]` über alle vom Card konsumierten Entities
- **MUSS NICHT [MUST NOT]** bei jedem `hass`-Setter-Call rendern — HA tickt mehrfach pro Sekunde; ein blankes Re-Render bei jedem Tick brennt CPU-Zyklen für nichts
- **SOLLTE [SHOULD]** initiales Render erzwingen, wenn `this._rendered` noch `false` ist (`if (changed || !this._rendered) this._render(); this._rendered = true`)

### `getCardSize` und `getGridOptions`

- **MUSS [MUST]** `getCardSize()` implementieren und einen Wert >= 1 zurückgeben (jede Einheit entspricht ~50px in der Vor-Sections-Lovelace-Welt)
- **SOLLTE [SHOULD]** `getGridOptions()` implementieren — HA 2024.3+ Sections-Layout nutzt das, um die Card responsiv zu skalieren; Default-Form: `return { columns: 6, rows: 3, min_columns: 3, min_rows: 2 }`
- **KANN [MAY]** dynamische `getGridOptions()` führen, wenn die Card je nach Konfiguration unterschiedliche Größen braucht — das Return-Objekt wird pro Render evaluiert

### `getConfigElement` und `getStubConfig`

- **SOLLTE [SHOULD]** `static getConfigElement()` und `static getStubConfig()` implementieren — die HA-UI rendert dann den Custom-Editor und liefert eine Default-Config beim Drag-and-Drop
- **MUSS NICHT [MUST NOT]** den Editor in derselben Datei wie die Card definieren, wenn er nicht-trivial wird — eine separate `<card-name>-editor.js`-Datei ist sauberer

### Shadow DOM und CSS

- **MUSS [MUST]** den Card-Inhalt im Shadow DOM rendern, geöffnet via `attachShadow({mode: "open"})` in `connectedCallback`
- **MUSS [MUST]** HA-CSS-Custom-Properties verwenden statt Hardcoded-Farben:
  - `var(--primary-text-color)` für primären Text
  - `var(--secondary-text-color)` für sekundären Text
  - `var(--state-icon-color)` für Icon-Farben
  - `var(--error-color)` für Fehlermeldungen
  - `var(--divider-color)` für Trennlinien
  - `var(--ha-card-background)` und `var(--card-background-color)` für Card-Hintergründe
- **MUSS NICHT [MUST NOT]** Hexadezimal- oder benannte Farben als Default verwenden — die Card folgt dann nicht dem aktiven HA-Theme
- **SOLLTE [SHOULD]** `var(--ha-font-weight-bold)` und ähnliche Font-Properties verwenden, statt Font-Weights numerisch hartzucodieren

### Performance-Disziplin

- **MUSS NICHT [MUST NOT]** in `set hass` synchron blocken (kein `JSON.parse` über riesige States, kein `forEach` über tausende Entities) — die Hauptlast liegt in der Entity-Change-Detection, nicht im Setter
- **SOLLTE [SHOULD]** schwere DOM-Manipulationen in `requestAnimationFrame`-Callbacks bündeln, wenn das Re-Render mehr als ein paar Knoten anfasst

## Akzeptanzkriterien

- [ ] Card-Datei lebt unter `custom_components/<domain>/www/<card-name>.js`
- [ ] `__init__.py` registriert die Card-JS-Datei über `StaticPathConfig` mit `cache_headers=False`
- [ ] Card-Type ist via `customElements.define` registriert; Name ist lowercase-kebab-case mit Integration-Präfix
- [ ] Card erscheint im Lovelace-Card-Picker via `window.customCards`-Push
- [ ] `setConfig(config)` ist implementiert; ungültige Configs werfen `Error`
- [ ] `set hass(hass)` führt Entity-Change-Detection vor Re-Render
- [ ] `getCardSize()` und `getGridOptions()` sind implementiert
- [ ] Shadow DOM wird in `connectedCallback` via `attachShadow({mode: "open"})` aufgesetzt
- [ ] CSS verwendet HA-Custom-Properties (`var(--primary-text-color)`, …); keine hartkodierten Hex-Farben
- [ ] Eine `grep`-Suche nach `#[0-9A-Fa-f]{3,6}` im Card-Stylesheet liefert keine Treffer (außer in Custom-Property-Definitionen)
- [ ] Quality-Scale-Marker: **Bronze** (portfolio-spezifisch, nicht HA-Quality-Scale)

## Offene Fragen

- **TypeScript-Migration**: Wann verlangt eine Folge-Spec TypeScript / Lit-basierte Cards? `kamerplanter-ha` ist Vanilla-JS; ein Build-Step für Multi-File-Cards wird irgendwann unausweichlich.
- **Card-Editor-Pflicht-Tiefe**: `getConfigElement` und `getStubConfig` als SHOULD oder MUSS? Aktuell SHOULD — eine fehlende `getStubConfig` führt zu leeren Default-Cards beim Drag-and-Drop.
- **Auto-Registrierung-Mechanismus**: HA hat keine offizielle „pro Integration eine Card registrieren"-API. Aktuell über `StaticPathConfig` plus User-Hint zu Lovelace-Resources. Wann landet das nativ?
- **Multi-Card-Repos**: Wenn die Integration mehrere Cards liefert, wie ist das Layout? `www/<card-1>.js`, `www/<card-2>.js`, …? Aktuell formuliert; eine Heuristik für „eine Card pro Konzept" fehlt.
- **HACS-Frontend-Distribution für Standalone-Cards**: Außerhalb einer Integration distribuiert (HACS-Plugin-Kategorie statt Integration-Kategorie) — eigene Folge-Spec?
