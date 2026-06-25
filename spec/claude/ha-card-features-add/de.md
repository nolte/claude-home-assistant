# Skill: `ha-card-features-add`

Status: draft

## Kontext

`ha/lovelace-card-features` definiert die Card-Feature-Schicht: die kleinen interaktiven Control-Reihen, die **innerhalb** einer Host-Card (z. B. der Tile-Card) gerendert werden und deren Kontext erben — nicht ein eigenständiges Dashboard-Element. Ein Feature wird wie eine Custom Card als JavaScript-Modul ausgeliefert, das ein Custom Element (`HTMLElement` oder `LitElement`) definiert, und wird über `window.customCardFeatures.push({ type, name, ... })` registriert, damit es im Card-Editor auswählbar ist. Es empfängt `hass`, eine über `setConfig(config)` gesetzte `config` und ein `context`-Objekt mit der `entity_id` (bzw. `area_id`) der Parent-Card. Ein `isSupported(hass, context)`-Prädikat entscheidet, ob das Feature auf die gewählte Entity anwendbar ist; konfigurierbare Features liefern zusätzlich `static getConfigElement` und `static getStubConfig`. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt **ein** Card-Feature in einem **bestehenden** Frontend-Modul: das Feature-Custom-Element mit `setConfig`, `hass`-Setter, dem `isSupported(hass, context)`-Prädikat als einziger Quelle der Wahrheit, dem `render()` der Control-Reihe, optional `static getStubConfig`/`static getConfigElement` und der Registrierung über `window.customCardFeatures` plus `customElements.define` — spec-konform zu `ha/lovelace-card-features`. Custom Cards und Card-Features sind **nicht Teil der HA-Quality-Scale**; das Pattern ist portfolio-spezifisch.

## Scope

Ergänzung genau eines Card-Features pro Lauf in einem bestehenden Frontend-Modul (neben der Custom Integration und ihren Custom Cards im selben Repo): das Feature-Custom-Element, `setConfig(config)` mit Reject-Pfad, der `hass`-Setter, das `isSupported(hass, context)`-Prädikat (im `render()` **und** im Registrierungs-Eintrag verwendet), das `render()` der Control-Reihe mit `this.hass.callService(...)`, optional `static getStubConfig`/`static getConfigElement`, und die Registrierung über `window.customCardFeatures.push({ type, name, ... })` plus `customElements.define("<feature-type>", <FeatureClass>)`. Der Skill liest `ha/lovelace-card-features` und validiert offline.

## Ziele

- Aus einer beschriebenen Schnellsteuerung das passende Feature ableiten und spec-konform ergänzen
- Das Feature über `window.customCardFeatures.push({ type, name, ... })` registrieren (Pflicht-Properties `type` und `name`) und das Element via `customElements.define("<feature-type>", <FeatureClass>)` registrieren, damit der `type` aufgelöst wird
- Den synchronen `setConfig`-Lifecycle erzwingen: `this.config = config` übernehmen, eine ungültige Config mit `throw new Error("Invalid configuration")` ablehnen
- Den Kontextfluss als Vertrag kodieren: `hass`, `config`, `context` als Properties; die Ziel-`stateObj` aus `this.hass.states[this.context.entity_id]` auflösen; fehlenden `context`/`entity_id` abfangen; `null` rendern, solange `config`/`hass`/`context` fehlen oder die Entity nicht unterstützt wird
- Das `isSupported(hass, context)`-Prädikat als **eine** Quelle der Wahrheit etablieren — dieselbe Funktion im `render()` und im `customCardFeatures`-Eintrag
- Bei Interaktion den passenden Service via `this.hass.callService(domain, service, { entity_id })` aufrufen und `ev.stopPropagation()` setzen, damit der Klick nicht an die Host-Card durchschlägt
- HA-CSS-Custom-Properties (`--feature-height`, `--feature-border-radius`, `--feature-button-spacing`) für die HA-Default-Integration verwenden

## Nicht-Ziele

- Eine vollständige Custom Card (Card-Datei-Layout, Auto-Registrierung, `set hass`-Lifecycle, `getCardSize`/`getGridOptions`) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Der grafische Config-Editor des Features (Detail-Mechanik von `getConfigElement`) — `ha/lovelace-card-editor`
- Badges als eigene Dashboard-Lieferform — eigene Folge-Spec
- Die Detail-Struktur des `hass`-Objekts und der Frontend-Datenzugriffe — `ha/frontend-data-api`
- Build-Stacks (Vite/esbuild/Rollup) und ein verbindlicher TypeScript-/Lit-Stack — eigene Folge-Spec
- Auslieferung / Laden des Feature-JS im Frontend (`StaticPathConfig`) — `ha/lovelace-card-patterns`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a tile feature", „create a custom card feature", „add a control row to the tile card"
  - „expose a quick control inside the tile card for this entity"
  - „füge ein Tile-Feature hinzu", „erstelle ein Custom-Card-Feature"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root mit dem bestehenden Frontend-Modul) und die Schnellsteuerung (Prosa), aus der der Skill `type`, `name` und die Ziel-Domain ableitet
- **KANN [MAY]** erfassen: `feature_type` (der `customElements`-Typ und `customCardFeatures`-`type`), `name` (Editor-Label), die Ziel-Domain bzw. das Anwendbarkeits-Prädikat, ob das Feature konfigurierbar ist (z. B. ein `label`), und ob es entity- statt area-gebunden ist

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein bestehendes Frontend-Modul enthält, in das das Feature ergänzt werden kann
- **MUSS [MUST]** die `ha/lovelace-card-features`-Spec lesen
- **MUSS [MUST]** das Anwendbarkeits-Prädikat bestätigen: an welche Domain/Entity bindet das Feature, und ist es entity- oder area-gebunden
- **MUSS NICHT [MUST NOT]** ein bestehendes Feature / einen bestehenden `feature_type` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/lovelace-card-features`)

- **MUSS [MUST]** das Feature über `window.customCardFeatures = window.customCardFeatures || []; window.customCardFeatures.push({ type, name, ... })` registrieren und die Pflicht-Properties `type` und `name` setzen
- **MUSS [MUST]** das Element via `customElements.define("<feature-type>", <FeatureClass>)` registrieren und von `HTMLElement` oder `LitElement` erben lassen
- **MUSS [MUST]** `setConfig(config)` implementieren (`this.config = config`) und eine fehlende/ungültige Config mit `throw new Error("Invalid configuration")` ablehnen
- **MUSS [MUST]** `hass`, `config` und `context` als Properties führen (die Host-Card setzt sie) und die Ziel-`stateObj` aus `this.hass.states[this.context.entity_id]` auflösen, wobei fehlender `context`/`entity_id` abgefangen wird
- **MUSS [MUST]** `null` (kein Rendering) zurückgeben, solange `config`/`hass`/`context` nicht gesetzt sind oder das Feature die Entity nicht unterstützt
- **MUSS [MUST]** Controls rendern und bei Interaktion via `this.hass.callService(domain, service, { entity_id })` auf der Ziel-Entity aufrufen
- **SOLLTE [SHOULD]** `ev.stopPropagation()` im Interaktions-Handler aufrufen, damit der Klick nicht an die Host-Card durchschlägt
- **SOLLTE [SHOULD]** eine `isSupported(hass, context)`-Funktion bereitstellen, die `boolean` zurückgibt, die `stateObj` aus `context.entity_id` über `hass.states` auflöst, `false` bei fehlender `stateObj` zurückgibt und die Anwendbarkeit anhand der Domain prüft (nicht anhand eines einzelnen Entity-IDs)
- **MUSS [MUST]** dieselbe Prädikat-Funktion im `render()` (vor dem Rendern der Controls) **und** im `isSupported`-Eintrag von `window.customCardFeatures` verwenden — eine Quelle der Wahrheit
- **SOLLTE [SHOULD]** für konfigurierbare Features `static getStubConfig()` implementieren, das eine Default-Config inkl. `type: "custom:<feature-type>"` zurückgibt, und `configurable: true` im `customCardFeatures`-Eintrag setzen; für eine grafische Konfiguration `static getConfigElement()` ergänzen (Detail in `ha/lovelace-card-editor`)
- **MUSS NICHT [MUST NOT]** `getConfigElement`/`getStubConfig` für ein Feature ohne zusätzliche Konfiguration verlangen — `configurable` bleibt dann beim Default `false`
- **KANN [MAY]** `context.area_id` lesen, wenn das Feature an die Area der Parent-Card statt an eine einzelne Entity gebunden ist
- **SOLLTE [SHOULD]** die HA-CSS-Custom-Properties `--feature-height`, `--feature-border-radius` und `--feature-button-spacing` für die HA-Default-Integration verwenden
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: das Feature ist via `window.customCardFeatures.push({ type, name, ... })` registriert (`type`/`name` gesetzt); das Element ist via `customElements.define` registriert und erbt von `HTMLElement`/`LitElement`; `setConfig` ist implementiert und wirft bei ungültiger Config; die Ziel-`stateObj` wird aus `this.hass.states[this.context.entity_id]` aufgelöst (fehlender `context`/`entity_id` abgefangen); `render()` liefert `null` ohne `config`/`hass`/`context`; Interaktion ruft `this.hass.callService(...)` auf; dieselbe Prädikat-Funktion wird in `render()` und `isSupported` verwendet; konfigurierbare Features setzen `configurable: true` plus `getStubConfig`/`getConfigElement`
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/lovelace-card-features` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**, portfolio-spezifisch)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als ein Feature pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** eine vollständige Custom Card oder einen grafischen Config-Editor implementieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Feature ist via `window.customCardFeatures.push({ type, name, ... })` registriert; `type` und `name` sind gesetzt
- [ ] Das Element ist via `customElements.define("<feature-type>", <FeatureClass>)` registriert und erbt von `HTMLElement`/`LitElement`
- [ ] `setConfig(config)` ist implementiert; eine ungültige Config wirft `Error`
- [ ] Bei Interaktion wird ein Service via `this.hass.callService(domain, service, { entity_id })` auf der Ziel-Entity aufgerufen
- [ ] Die Ziel-`stateObj` wird aus `this.hass.states[this.context.entity_id]` aufgelöst; fehlender `context`/`entity_id` wird abgefangen
- [ ] `render()` liefert `null`, solange `config`/`hass`/`context` fehlen oder das Feature die Entity nicht unterstützt
- [ ] `isSupported(hass, context)` ist gesetzt und gibt `false` zurück, wenn keine `stateObj` existiert
- [ ] Dieselbe Prädikat-Funktion wird im `render()` und im `isSupported`-Eintrag verwendet
- [ ] Konfigurierbare Features setzen `configurable: true` und liefern `getStubConfig`/`getConfigElement`
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker (nicht Teil der HA-Quality-Scale, portfolio-spezifisch)

## Offene Fragen

- **`isSupported` SHOULD oder MUSS**: `ha/lovelace-card-features` führt das Prädikat als SHOULD; ein fehlendes Prädikat lässt den Editor das Feature für jede Entity vorschlagen. Soll der Skill es bei einer geräte-/domain-spezifischen Steuerung faktisch erzwingen?
- **Vanilla vs. Lit**: Der HA-Doc nutzt `LitElement`, `ha/lovelace-card-patterns` schreibt für Cards Vanilla-`HTMLElement` fest. Folgt der Skill dem Vanilla-Mandat der bestehenden Cards oder erlaubt er Lit für Features? Aktuell folgt er dem im Ziel-Modul vorgefundenen Stil.
- **Editor-Tiefe**: `getStubConfig`/`getConfigElement` werden nur als SHOULD geführt und auf `ha/lovelace-card-editor` verwiesen. Wann ist ein konfigurierbares Feature ohne grafischen Editor noch akzeptabel?
- **Auslieferung**: Wie wird das Feature-JS in der Integration ausgeliefert und im Frontend geladen — über denselben `StaticPathConfig`-Mechanismus wie Custom Cards? Offen in `ha/lovelace-card-features`; der Skill ergänzt nur das Modul, nicht den Auslieferungspfad.
