# Skill: `ha-panel-add`

Status: draft

## Kontext

`ha/lovelace-views-panels` definiert zwei größere Frontend-Flächen jenseits der einzelnen Card: die **Custom-View** (überschreibt das Default-Masonry-Layout, rendert vom Core gelieferte Cards/Badges in einem eigenen Layout) und das **Custom-Panel** (eine vollflächige, aus der Sidebar verlinkte Seite mit Echtzeit-Zugriff auf das Home-Assistant-Objekt; Core-Beispiele: Dashboards, Map, Logbook, History). Beide werden als Custom Element registriert; das Render-Framework ist frei (Lit, Preact o. ä.), nur React ist explizit ausgenommen. Dieser Skill operationalisiert den **Custom-Panel**-Teil der Spec — nicht die Custom-View. Quality-Scale-Marker: Custom-Panels sind **nicht Teil der HA-Quality-Scale**; das Pattern steht außerhalb der Skala.

Dieser Skill ergänzt **ein** Custom-Panel in einer **bestehenden** Integration bzw. einem bestehenden Frontend-Repo: das Panel-Custom-Element (empfängt `hass`, `narrow`, `route` und `panel` als Properties, registriert via `customElements.define(...)`), die JS-Modul-Verdrahtung und die Registrierung über `panel_custom` in der `configuration.yaml` (`url_path`, `module_url`, optional `sidebar_title`/`sidebar_icon`/`config`/`embed_iframe`) — spec-konform zu `ha/lovelace-views-panels`. Vor der Generierung trennt er das Custom-Panel sauber von einer Panel-Mode-View (Single-Card-Layout im Dashboard) und von der Custom-View als Layout-Container.

## Scope

Ergänzung genau eines Custom-Panels pro Lauf in einem bestehenden Repo: das Panel-Custom-Element (Lit oder anderes Nicht-React-Framework) mit dem von HA gelieferten Property-Set, die ES-Modul-Datei und der `panel_custom`-Eintrag in der `configuration.yaml` mit eindeutigem `url_path` und `module_url`, optional `sidebar_title`/`sidebar_icon`/`config`/`embed_iframe` sowie — falls nötig — die ES5-Adapter-Verdrahtung. Der Skill liest `ha/lovelace-views-panels` und validiert offline.

## Ziele

- Aus einer beschriebenen vollflächigen Sidebar-Seite ein Custom-Panel spec-konform ergänzen, abgegrenzt von Custom-View und Panel-Mode-View
- Das Panel als Custom Element (kein React) mit dem von HA gelieferten Property-Set (`hass`, `narrow`, `route`, `panel`) etablieren und über `customElements.define(...)` registrieren
- Den `hass`-Property-Kanal als einzigen Zugang zum HA-Zustand erzwingen — kein Zugriff außerhalb von `hass`
- Die Registrierung über `panel_custom` in der `configuration.yaml` als kanonischen Eintrittspunkt mit eindeutigem `url_path` und `module_url` festschreiben
- Die JS-Versionswahl (aktuell statt ES5, ES5-Adapter nur falls nötig) und den `embed_iframe`-Hinweis explizit machen

## Nicht-Ziele

- Custom-View als Layout-Container (überschreibt Masonry, rendert Core-Cards/Badges via `ll-*`-Events) — abgedeckt in `ha/lovelace-views-panels` (View-Teil), nicht von diesem Skill generiert
- Eine einzelne Card oder eine Panel-Mode-View (Single-Card-Layout im Dashboard) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Programmatische Dashboard-Generierung (Strategien, die ganze Views/Dashboards berechnen) — `ha/lovelace-strategies`
- WebSocket-Commands, die das Panel aufruft — `ha/frontend-websocket-commands`
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`
- Build-Stacks (Vite, esbuild, Rollup), TypeScript-Migration und Theming durch das Panel selbst — eigene Folge-Specs

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a custom panel", „register a sidebar panel", „create a full-page custom panel"
  - „expose this as a full-page page in the sidebar"
  - „füge ein Custom-Panel hinzu", „registriere ein Sidebar-Panel"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Beschreibung der vollflächigen Seite (Prosa), aus der der Skill `url_path` und Panel-Namen ableitet
- **KANN [MAY]** erfassen: `url_path`, `sidebar_title`/`sidebar_icon`, einen `config`-Block (wird zur Laufzeit als `panel.config` verfügbar), ob ES5-Support nötig ist und ob `embed_iframe` gesetzt werden soll

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein bestehendes Repo ist und der Zielort für `module_url` auflösbar ist (z. B. `www/`/`/local/` oder ein gebündelter Frontend-Pfad)
- **MUSS [MUST]** den Lieferform-Check fahren: deckt eine Custom-View (Layout im Dashboard) oder eine Panel-Mode-View (Single-Card) den Bedarf, **SOLLTE [SHOULD]** der Skill darauf hinweisen; nur ein echter Bedarf an einer vollflächigen, aus der Sidebar verlinkten Seite rechtfertigt das Custom-Panel
- **MUSS [MUST]** die `ha/lovelace-views-panels`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes Panel-Element, einen `url_path` oder einen `panel_custom`-Eintrag überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/lovelace-views-panels`)

- **MUSS [MUST]** das Panel als Custom Element definieren — das Render-Framework ist frei (Lit, Preact o. ä.), aber **MUSS NICHT [MUST NOT]** React verwenden, da React explizit ausgenommen ist
- **MUSS [MUST]** das Element über `customElements.define(...)` registrieren
- **MUSS [MUST]** die von HA gesetzten Properties akzeptieren: `hass` (object, aktueller HA-Zustand), `narrow` (boolean) und `panel` (object; Config verfügbar als `panel.config`)
- **SOLLTE [SHOULD]** zusätzlich `route` (object) akzeptieren, das HA dem Panel-Element setzt
- **MUSS NICHT [MUST NOT]** auf den HA-Zustand außerhalb des `hass`-Property zugreifen — `hass` ist der Echtzeit-Kanal zum Home-Assistant-Objekt
- **MUSS [MUST]** das Panel über die `panel_custom`-Komponente in der `configuration.yaml` registrieren, mit pro Eintrag eindeutigem `url_path` und dem Panel-Modul über `module_url` (ES-Module, z. B. `module_url: /local/example-panel.js`)
- **SOLLTE [SHOULD]** `sidebar_title` und `sidebar_icon` setzen, damit das Panel sinnvoll aus der Sidebar verlinkt wird
- **KANN [MAY]** über den `config`-Block beliebige Daten an das Panel durchreichen (zur Laufzeit als `panel.config`) und **KANN [MAY]** `embed_iframe` setzen, wenn das Panel im Iframe statt direkt im Frontend ausgeliefert werden soll
- **SOLLTE [SHOULD]** ohne ES5-Support ausliefern, solange keine breitere Browser-Unterstützung nötig ist; **MUSS [MUST]** bei nötigem ES5-Support den ES5-Adapter vor dem Definieren laden, via `window.loadES5Adapter().then(function() { customElements.define('my-panel', MyCustomPanel) })`
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: das Panel ist ein Custom Element (kein React) und akzeptiert `hass`, `narrow`, `route`, `panel`; es wird über `customElements.define(...)` registriert; es greift nicht außerhalb von `hass` auf den HA-Zustand zu; der `panel_custom`-Eintrag in der `configuration.yaml` hat einen eindeutigen `url_path` und `module_url`; ES5-Support lädt — falls nötig — den Adapter vor `customElements.define`
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/lovelace-views-panels` (Panel-Teil) liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als ein Panel pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** eine Custom-View, eine Card oder eine Strategie generieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill fährt den Lieferform-Check (Custom-Panel vs. Custom-View vs. Panel-Mode-View) und ergänzt nur bei echtem Vollflächen-Bedarf
- [ ] Das Panel ist ein Custom Element (kein React) und akzeptiert `hass`, `narrow`, `route` und `panel` (Config via `panel.config`)
- [ ] Das Element wird über `customElements.define(...)` registriert und greift nicht außerhalb von `hass` auf den HA-Zustand zu
- [ ] Das Panel ist in `configuration.yaml` über `panel_custom` mit eindeutigem `url_path` registriert
- [ ] Das Panel-Modul ist über `module_url` (ES-Module) referenziert; `sidebar_title`/`sidebar_icon` gesetzt, wo sinnvoll
- [ ] ES5-Support lädt — falls nötig — den ES5-Adapter via `window.loadES5Adapter()` vor `customElements.define`
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **nicht Teil der HA-Quality-Scale**

## Offene Fragen

- **View vs. Panel als Lieferform**: Wann reicht eine Custom-View (Layout im Dashboard) und wann braucht es ein vollflächiges Custom-Panel (eigene Sidebar-Seite)? `ha/lovelace-views-panels` lässt eine Heuristik offen; der Skill fährt den Lieferform-Check fall-zu-fall.
- **`route`-Property-Tiefe**: Die `panel`-API-Tabelle listet `hass`, `narrow` und `panel`, das Beispiel rendert aber zusätzlich `route`. Ist `route` garantiert gesetzt? Aktuell akzeptiert der Skill es als SHOULD.
- **`js_url` vs. `module_url`**: Die Registrierung unterstützt sowohl klassische Skripte (`js_url`) als auch ES-Module (`module_url`). Der Skill verlangt durchgängig `module_url`; wann `js_url` noch sinnvoll ist, bleibt offen.
- **`embed_iframe`-Trade-offs**: Wann lohnt sich das Iframe-Embedding (Isolation vs. direkter `hass`-Zugriff)? Der Skill setzt es nur auf expliziten Wunsch.
