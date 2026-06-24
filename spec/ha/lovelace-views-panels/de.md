# HA-Integration: Lovelace-Views und Custom-Panels

Status: draft

## Kontext

Über die einzelne Card hinaus erweitert HA zwei größere Frontend-Flächen: die **Custom-View** und das **Custom-Panel**. Beide werden — wie die Card — als Custom Element registriert; das Render-Framework ist frei (Lit Element, Preact oder ein anderes; nur React ist explizit ausgenommen).

Eine **Custom-View** überschreibt das Default-Masonry-Layout (Pinterest-artig) und definiert einen eigenen Layout-Mechanismus (z. B. ein Grid). Cards und Badges werden vom Core-Code erzeugt und gepflegt und der View übergeben; die View lädt sie und stellt sie in einem eigenen Layout dar. Das View-Element empfängt `hass`, `lovelace`, `index`, `cards` und `badges` als Properties und implementiert `setConfig`. Über das `lovelace`-Objekt erreicht die View den Dashboard-Zustand inkl. Edit-Mode und kann die Core-Dialoge zum Bearbeiten, Löschen und Hinzufügen einer Card auslösen. Referenziert wird die View per `type: custom:my-view`.

Ein **Custom-Panel** ist eine vollflächige Seite, aus der Sidebar verlinkt, mit Echtzeit-Zugriff auf das Home-Assistant-Objekt (Beispiele im Core: Dashboards, Map, Logbook, History). User registrieren eigene Panels über die `panel_custom`-Komponente in der `configuration.yaml`; das Panel-Element empfängt `hass`, `narrow`, `route` und `panel` als Properties.

Diese Spec deckt beide verwandten Flächen ab. Sie grenzt sich gegen die Schwester-Specs ab: `ha/lovelace-card-patterns` deckt die einzelne Card ab, `ha/lovelace-strategies` die programmatische Dashboard-Generierung; die `hass`-Datenkanäle sind in `ha/frontend-data-api` beschrieben.

Quality-Scale-Marker: Custom-Views und Custom-Panels sind **nicht Teil der HA-Quality-Scale** — das Pattern steht außerhalb der Skala.

## Ziele

- Custom-View als Layout-Container festschreiben, der das Default-Masonry-Layout durch einen eigenen Mechanismus (z. B. Grid) ersetzt
- View-Element als Custom Element mit dem von HA gelieferten Property-Set (`hass`, `lovelace`, `index`, `cards`, `badges`) etablieren
- Karten-Interaktion (Bearbeiten, Löschen, Hinzufügen) ausschließlich über die Core-Events des `lovelace`-Objekts laufen lassen, statt das Card-Lifecycle selbst nachzubauen
- Custom-Panel-Registrierung über `panel_custom` in der `configuration.yaml` als kanonischen Eintrittspunkt festschreiben
- Panel-Element mit dem von HA gelieferten Property-Set (`hass`, `narrow`, `route`, `panel`) etablieren
- JavaScript-Versionswahl (ES5 vs. aktuell) und den `embed_iframe`-Hinweis explizit machen, statt sie dem Zufall zu überlassen

## Nicht-Ziele

- Einzelne Card-Patterns (`HTMLElement`-Subklasse, `setConfig`-Validierung, Entity-Change-Detection) — abgedeckt in `ha/lovelace-card-patterns`
- Programmatische Dashboard-Generierung (Strategien, die ganze Views/Dashboards berechnen) — abgedeckt in `ha/lovelace-strategies`
- Detail-Schema der `hass`-Objekt-Datenkanäle (WebSocket, States, Services) — abgedeckt in `ha/frontend-data-api`
- Build-Stacks (Vite, esbuild, Rollup) und TypeScript-Migration — eigene Folge-Spec
- Theming durch View oder Panel selbst — beide konsumieren das HA-Theme, sie definieren keins

## Anforderungen

### Custom-View: Element & Properties (`hass`/`lovelace`/`cards`)

- **MUSS [MUST]** die View als Custom Element definieren — das Render-Framework ist frei (Lit, Preact o. ä.), aber **MUSS NICHT [MUST NOT]** React verwenden, da React explizit ausgenommen ist
- **MUSS [MUST]** die von HA gesetzten Properties akzeptieren: `hass` (`HomeAssistant`), `lovelace` (`Lovelace`), `index` (`number`), `cards` (`Array<LovelaceCard | HuiErrorCard>`) und `badges` (`LovelaceBadge[]`)
- **MUSS NICHT [MUST NOT]** Cards oder Badges selbst erzeugen — diese werden vom Core-Code erstellt und gepflegt und der View übergeben; die View lädt sie und stellt sie in einem eigenen Layout dar
- **SOLLTE [SHOULD]** ein nicht-triviales Layout (z. B. Grid) liefern, das über das Default-Masonry-Layout hinausgeht — sonst rechtfertigt die Custom-View ihren Aufwand nicht

### Custom-View: `setConfig` & Custom-Data

- **MUSS [MUST]** `setConfig(config)` mit der Signatur `setConfig(config: LovelaceViewConfig): void` implementieren
- **SOLLTE [SHOULD]** Card-Level-Persistenzdaten über den `view_layout`-Block in der Card-Konfiguration ablegen (z. B. `key`, X/Y-Koordinaten, `width`, `height`), wenn die View Position oder Dimension einer Card speichern muss
- **MUSS NICHT [MUST NOT]** View-spezifische Persistenzdaten an anderer Stelle als im `view_layout`-Block der jeweiligen Card unterbringen — `view_layout` ist der vorgesehene Speicherort

### Custom-View: Karten-Interaktion (`lovelace`)

- **MUSS [MUST]** zum Bearbeiten, Löschen oder Hinzufügen einer Card die Core-Frontend-Dialoge über die drei `ll-*`-Events auslösen — `ll-edit-card` (Detail `{ path }`), `ll-delete-card` (Detail `{ path }`) und `ll-create-card` (Detail: none) — statt das Card-Lifecycle selbst nachzubauen
- **MUSS [MUST]** das Event via `this.dispatchEvent(new CustomEvent("ll-edit-card", { detail: { path: [...] } }))` vom betroffenen Card-Element aus dispatchen, mit `path` als `[number]` oder `[number, number]`
- **SOLLTE [SHOULD]** den Edit-Mode-Zustand aus dem `lovelace`-Objekt (`editMode`) lesen, bevor Edit-Affordanzen (Bearbeiten/Löschen/Hinzufügen) angeboten werden

### Custom-Panel: Registrierung (`panel_custom`)

- **MUSS [MUST]** das Panel über die `panel_custom`-Komponente in der `configuration.yaml` registrieren
- **MUSS [MUST]** pro `panel_custom`-Eintrag ein eindeutiges `url_path` setzen — `url_path` muss für jede `panel_custom`-Konfiguration eindeutig sein
- **MUSS [MUST]** das Panel-Modul über `module_url` (ES-Module) referenzieren, z. B. `module_url: /local/example-panel.js`
- **KANN [MAY]** über den `config`-Block beliebige Daten an das Panel durchreichen — sie werden zur Laufzeit als `panel.config` verfügbar
- **SOLLTE [SHOULD]** `sidebar_title` und `sidebar_icon` setzen, damit das Panel sinnvoll aus der Sidebar verlinkt wird

### Custom-Panel: Element-Properties (`hass`/`narrow`/`route`/`panel`)

- **MUSS [MUST]** das Panel als Custom Element definieren und über `customElements.define(...)` registrieren
- **MUSS [MUST]** die von HA gesetzten Properties akzeptieren: `hass` (object, aktueller HA-Zustand), `narrow` (boolean, ob das Panel im Narrow-Mode rendert) und `panel` (object, Panel-Information; Config verfügbar als `panel.config`)
- **SOLLTE [SHOULD]** zusätzlich `route` (object) akzeptieren, das HA dem Panel-Element setzt
- **MUSS NICHT [MUST NOT]** auf den HA-Zustand außerhalb des `hass`-Property zugreifen — `hass` ist der Echtzeit-Kanal zum Home-Assistant-Objekt

### JS-Versionen & `embed_iframe`

- **SOLLTE [SHOULD]** ohne ES5-Support ausliefern, solange keine breitere Browser-Unterstützung nötig ist — die ES5-Variante hat weitere Browser-Reichweite, aber kostet Größe und Performance
- **MUSS [MUST]** bei nötigem ES5-Support den ES5-Custom-Elements-Adapter vor dem Definieren des Elements laden, via `window.loadES5Adapter().then(function() { customElements.define('my-panel', MyCustomPanel) })`
- **KANN [MAY]** `embed_iframe` in der `panel_custom`-Konfiguration setzen, wenn das Panel in einem Iframe eingebettet ausgeliefert werden soll, statt direkt ins Frontend geladen zu werden

## Akzeptanzkriterien

- [ ] Custom-View ist ein Custom Element (kein React) und akzeptiert `hass`, `lovelace`, `index`, `cards`, `badges`
- [ ] Custom-View erzeugt Cards/Badges nicht selbst, sondern rendert die vom Core gelieferten in einem eigenen Layout
- [ ] Custom-View implementiert `setConfig(config)` mit der `LovelaceViewConfig`-Signatur
- [ ] Card-Level-Persistenz läuft über den `view_layout`-Block der Card-Konfiguration
- [ ] Card-Interaktion läuft über `ll-edit-card` / `ll-delete-card` / `ll-create-card` mit korrektem `path`-Detail
- [ ] Custom-Panel ist in `configuration.yaml` über `panel_custom` mit eindeutigem `url_path` registriert
- [ ] Panel-Modul ist über `module_url` referenziert
- [ ] Panel-Element akzeptiert `hass`, `narrow`, `route` und `panel` (Config via `panel.config`)
- [ ] ES5-Support, falls nötig, lädt den ES5-Adapter via `window.loadES5Adapter()` vor `customElements.define`
- [ ] Quality-Scale-Marker: nicht Teil der HA-Quality-Scale

## Offene Fragen

- **View vs. Panel als Lieferform**: Wann ist eine Custom-View ausreichend (Layout im Dashboard) und wann braucht es ein vollflächiges Custom-Panel (eigene Sidebar-Seite)? Eine Heuristik für die Wahl fehlt.
- **`route`-Property-Tiefe**: Die `panel`-API-Tabelle listet `hass`, `narrow` und `panel`, das Beispiel-Element rendert aber zusätzlich `route`. Ist `route` garantiert gesetzt oder optional? Aktuell als SHOULD formuliert.
- **`embed_iframe`-Trade-offs**: Die Doku nennt `embed_iframe` als Option, ohne die Konsequenzen (Isolation vs. direkter `hass`-Zugriff) zu vertiefen. Wann lohnt sich das Iframe-Embedding?
- **ES5-Pflicht-Grenze**: Ab welcher Browser-Matrix rechtfertigt der ES5-Adapter den Größen- und Performance-Aufschlag? Aktuell als „nur wenn nötig" formuliert.
- **`js_url` vs. `module_url`**: Die Registrierung unterstützt sowohl klassische Skripte (`js_url`) als auch ES-Module (`module_url`). Wann ist `js_url` noch sinnvoll, statt durchgängig `module_url` zu verlangen?
