# HA-Integration: Lovelace-Card-Features (Tile-Features)

Status: draft

## Kontext

Manche Dashboard-Cards unterstützen [Features](https://www.home-assistant.io/dashboards/features/) — kleine interaktive Widgets, die innerhalb einer Card (z. B. der Tile-Card) Schnellsteuerungen für die gebundene Entity hinzufügen. HA liefert eine Reihe eingebauter Features, doch ein Repo ist nicht auf diese Auswahl beschränkt: Eigene Features werden auf demselben Weg definiert wie Custom Cards — als JavaScript-Modul, das ein Custom Element registriert.

Das Trennende zur Card: Ein Card-Feature ist kein eigenständiges Dashboard-Element, sondern wird **innerhalb** einer Host-Card gerendert und erbt deren Kontext. Es empfängt `hass`, eine über `setConfig` gesetzte `config` und ein `context`-Objekt, das die Entity (`entity_id`) bzw. Area (`area_id`) der Parent-Card trägt — die Entity, auf die das Feature wirkt. Ein `isSupported(hass, context)`-Prädikat entscheidet, ob das Feature für die gewählte Entity überhaupt anwendbar ist; konfigurierbare Features liefern zusätzlich `static getConfigElement` und `static getStubConfig`.

Diese Spec überführt das Custom-Card-Feature-Pattern in eine generische Verpflichtung für nolte-Portfolio-Repos. Card-Features leben im selben Repo wie die Custom Integration und ihre Custom Cards, sind aber eine getrennte Lieferform — die interaktiven Controls innerhalb einer Tile-/anderen Card, nicht die Card selbst.

Abgrenzung: `ha/lovelace-card-patterns` deckt die Custom Cards ab (Card-Datei-Layout, Auto-Registrierung, `set hass`-Lifecycle, Shadow DOM); diese Spec deckt ausschließlich Card-Features ab. Editor-UI-Mechanik (`getConfigElement`) wird in `ha/lovelace-card-editor` vertieft; der Datenfluss aus `hass` ist in `ha/frontend-data-api` beschrieben. Doppelungen werden per Slug referenziert, nicht wiederholt.

Quality-Scale-Marker: Custom Cards und Custom Card-Features sind **nicht Teil der HA-Quality-Scale**; das Pattern hier ist nolte-portfolio-spezifisch und steht außerhalb der Skala.

## Ziele

- Registrierung eigener Card-Features über `window.customCardFeatures` als verbindlichen Weg festschreiben, damit Features im Card-Editor auswählbar werden
- Das Feature-Element als Custom Element (Vanilla `HTMLElement` oder `LitElement`) mit synchronem `setConfig`-Lifecycle etablieren
- Den Kontextfluss (`hass`, `config`, `context` mit `entity_id` / `area_id`) als Standard-Vertrag zwischen Host-Card und Feature kodifizieren
- Das `isSupported(hass, context)`-Prädikat verpflichtend machen, damit der Editor Features nur für kompatible Entities vorschlägt
- Konfigurierbare Features über `configurable: true` plus `static getConfigElement` / `static getStubConfig` ermöglichen
- HA-CSS-Custom-Properties (`--feature-height`, `--feature-border-radius`, `--feature-button-spacing`) für die Integration in das HA-Default-Design verwenden

## Nicht-Ziele

- Custom Cards selbst (Card-Datei-Layout, Auto-Registrierung, `set hass`-Lifecycle, `getCardSize` / `getGridOptions`) — abgedeckt durch `ha/lovelace-card-patterns`
- Detail-Mechanik der Editor-UI über das Minimum hinaus — abgedeckt durch `ha/lovelace-card-editor`
- Detail-Struktur des `hass`-Objekts und der Frontend-Datenzugriffe — abgedeckt durch `ha/frontend-data-api`
- Build-Stacks (Vite, esbuild, Rollup, Webpack) und TypeScript / Lit als verbindlicher Stack — eigene Folge-Spec
- HACS-Distribution für Standalone-Features außerhalb einer Integration — andere Lieferachse

## Anforderungen

### Feature registrieren (`window.customCardFeatures`)

- **MUSS [MUST]** das Feature über `window.customCardFeatures = window.customCardFeatures || []; window.customCardFeatures.push({ type, name, ... })` registrieren, damit es im Card-Editor erscheint
- **MUSS [MUST]** im Push-Objekt die Pflicht-Properties `type` und `name` setzen
- **SOLLTE [SHOULD]** `isSupported` als `(hass, context) => boolean` setzen, damit der Editor das Feature nur bei kompatibler Entity vorschlägt
- **KANN [MAY]** `configurable` setzen — `true`, wenn das Feature zusätzliche Konfiguration hat (z. B. ein `label`); Default ist `false`
- **MUSS [MUST]** das Element zusätzlich via `customElements.define("<feature-type>", <FeatureClass>)` registrieren, damit der `type` aufgelöst werden kann

### Feature-Element & `setConfig`

- **MUSS [MUST]** das Feature als Custom Element definieren, das von `HTMLElement` oder `LitElement` erbt — analog zur Definition einer Custom Card
- **MUSS [MUST]** `setConfig(config)` implementieren und die übergebene Config übernehmen (`this.config = config`)
- **MUSS [MUST]** eine fehlende oder ungültige Config mit `throw new Error("Invalid configuration")` ablehnen
- **MUSS [MUST]** Controls rendern und bei Interaktion den passenden Service über `this.hass.callService(domain, service, { entity_id })` aufrufen (z. B. `button.press` auf der Ziel-Entity)
- **SOLLTE [SHOULD]** `ev.stopPropagation()` im Interaktions-Handler aufrufen, damit der Klick nicht an die Host-Card durchschlägt

### Kontext (`hass`, `stateObj`)

- **MUSS [MUST]** `hass`, `config` und `context` als Properties des Feature-Elements führen — die Host-Card setzt sie
- **MUSS [MUST]** die Ziel-`stateObj` aus `this.hass.states[this.context.entity_id]` auflösen und behandeln, dass `context` bzw. `context.entity_id` fehlen kann
- **MUSS [MUST]** `null` (bzw. kein Rendering) zurückgeben, solange `config`, `hass` oder `context` noch nicht gesetzt sind oder das Feature die Entity nicht unterstützt
- **KANN [MAY]** `context.area_id` lesen, wenn das Feature an die Area der Parent-Card statt an eine einzelne Entity gebunden ist
- **SOLLTE [SHOULD]** die HA-CSS-Custom-Properties `--feature-height` (42px), `--feature-border-radius` (12px) und `--feature-button-spacing` (12px) verwenden, um in das HA-Default-Design zu passen

### `supported(stateObj)`-Prädikat

- **SOLLTE [SHOULD]** eine `isSupported(hass, context)`-Funktion bereitstellen, die `boolean` zurückgibt und entscheidet, ob das Feature auf die gewählte Entity anwendbar ist
- **MUSS [MUST]** im Prädikat die `stateObj` aus `context.entity_id` über `hass.states` auflösen und `false` zurückgeben, wenn keine `stateObj` existiert
- **SOLLTE [SHOULD]** die Anwendbarkeit anhand der Domain prüfen (z. B. `stateObj.entity_id.split(".")[0] === "button"`), nicht anhand eines einzelnen Entity-IDs
- **MUSS [MUST]** dieselbe Prädikat-Funktion sowohl im `render()` (vor dem Rendern der Controls) als auch im `isSupported`-Eintrag von `window.customCardFeatures` verwenden — eine Quelle der Wahrheit

### Konfigurierbare Features (`getConfigElement` / `getStubConfig`)

- **SOLLTE [SHOULD]** für konfigurierbare Features `static getStubConfig()` implementieren, das eine Default-Config inklusive `type: "custom:<feature-type>"` zurückgibt
- **SOLLTE [SHOULD]** für eine grafische Konfiguration `static getConfigElement()` implementieren — funktioniert wie bei normalen Custom Cards
- **MUSS [MUST]** `configurable: true` im `window.customCardFeatures`-Eintrag setzen, sobald das Feature zusätzliche Config-Optionen anbietet
- **MUSS NICHT [MUST NOT]** `getConfigElement` / `getStubConfig` für ein Feature ohne zusätzliche Konfiguration verlangen — `configurable` bleibt dann beim Default `false`

## Akzeptanzkriterien

- [ ] Feature ist via `window.customCardFeatures.push({ type, name, ... })` registriert; `type` und `name` sind gesetzt
- [ ] Das Element ist via `customElements.define("<feature-type>", <FeatureClass>)` registriert und erbt von `HTMLElement` oder `LitElement`
- [ ] `setConfig(config)` ist implementiert; eine ungültige Config wirft `Error`
- [ ] Bei Interaktion wird ein Service via `this.hass.callService(domain, service, { entity_id })` auf der Ziel-Entity aufgerufen
- [ ] Die Ziel-`stateObj` wird aus `this.hass.states[this.context.entity_id]` aufgelöst; fehlender `context` / `entity_id` wird abgefangen
- [ ] `render()` liefert `null`, solange `config` / `hass` / `context` fehlen oder das Feature die Entity nicht unterstützt
- [ ] `isSupported(hass, context)` ist gesetzt und gibt `false` zurück, wenn keine `stateObj` existiert
- [ ] Dieselbe Prädikat-Funktion wird im `render()` und im `isSupported`-Eintrag verwendet
- [ ] Konfigurierbare Features setzen `configurable: true` und liefern `getStubConfig` / `getConfigElement`
- [ ] Styling nutzt `--feature-height` / `--feature-border-radius` / `--feature-button-spacing` für die HA-Default-Integration
- [ ] Quality-Scale-Marker: nicht Teil der HA-Quality-Scale (portfolio-spezifisch)

## Offene Fragen

- **`isSupported` SHOULD oder MUSS**: Der HA-Doc empfiehlt `isSupported`, macht es aber optional. Ein fehlendes Prädikat lässt den Editor das Feature für jede Entity vorschlagen. Sollte das Portfolio es zur Pflicht erheben?
- **Editor-Tiefe**: `getConfigElement` / `getStubConfig` werden hier nur als SHOULD geführt und auf `ha/lovelace-card-editor` verwiesen. Wann ist ein konfigurierbares Feature ohne grafischen Editor noch akzeptabel?
- **Vanilla vs. Lit**: Der HA-Doc-Beispielcode nutzt `LitElement`; `ha/lovelace-card-patterns` schreibt für Cards Vanilla-`HTMLElement` fest. Soll für Features dasselbe Vanilla-Mandat gelten oder ist Lit hier erlaubt?
- **`area_id`-Features**: Der Kontext exponiert neben `entity_id` auch `area_id`. Wie sieht ein area-gebundenes Feature aus, und wann ist das gegenüber einem entity-gebundenen Feature sinnvoll? Aktuell nur als KANN geführt.
- **Registrierung / Auslieferung**: Wie wird das Feature-JS in der Integration ausgeliefert und im Frontend geladen — über denselben `StaticPathConfig`-Mechanismus wie Custom Cards (siehe `ha/lovelace-card-patterns`) oder separat?
