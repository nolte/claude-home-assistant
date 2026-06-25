# HA-Integration: Lovelace-Strategies

Status: draft

## Kontext

Custom Strategies sind Custom Elements, die Dashboards und/oder Views **programmatisch generieren**, statt sie statisch zu deklarieren (eingeführt in Home Assistant 2021.5). Eine Strategy startet typischerweise von einer kleinen Strategy-Config und liefert die volle Dashboard- bzw. View-Struktur zurück — vergleichbar mit einer JSON/YAML-Config, die zur Laufzeit in ein Dashboard gerendert wird. Die eingebauten HA-Dashboards (z. B. die Home-Overview- und Energy-Dashboards) sind selbst über Dashboard-Strategies gebaut.

Es gibt zwei Strategy-Arten: Eine **Dashboard-Strategy** generiert eine vollständige Dashboard-Konfiguration (`generate(config, hass)` liefert `{ views: [...] }`); eine **View-Strategy** generiert die Konfiguration eines einzelnen Views (`generate(config, hass)` liefert `{ cards: [...] }`). Beide werden — wie Custom Cards — als Dashboard-Resources geladen und haben Zugriff auf die Home-Assistant-API. Die Generierung läuft client-seitig im Frontend und hat über `hass` Zugriff auf States, Entities, Areas und Devices.

Diese Spec deckt ausschließlich Strategies ab, die Dashboards/Views **generieren**. Statische Custom Cards regelt `ha/lovelace-card-patterns`; Custom-View-Layout-Elemente regelt `ha/lovelace-views-panels`. Diese Spec referenziert beide per Slug und dupliziert sie nicht. Das `hass`-Datenzugriffs-Pattern (`callWS` auf die Registries) ist in `ha/frontend-data-api` vertieft.

Quality-Scale-Marker: **nicht Teil der HA-Quality-Scale** (Custom Strategies sind eine Frontend-Lieferform und stehen außerhalb der Skala; das Pattern hier ist nolte-portfolio-spezifisch).

## Ziele

- Die zwei Strategy-Arten klar trennen: Dashboard-Strategy (`generate → views`) gegen View-Strategy (`generate → cards`)
- Die Registrierung über das Custom-Element `ll-strategy-dashboard-<id>` / `ll-strategy-view-<id>` mit statischer `async generate(config, hass)` als verbindliches Pattern festschreiben
- Die Referenzierung im Dashboard-/View-Config über `strategy.type: custom:<id>` als kanonischen Einstieg etablieren
- Community-Dashboards über `window.customStrategies` im New-Dashboard-Dialog auffindbar machen
- `getCreateSuggestions(hass)` für Vorschlagswerte im Create-Dialog nutzbar machen
- Die grafische Strategy-Konfiguration über `getConfigElement` als Option vorsehen
- Den `hass`-Zugriff (Areas/Devices/Entities) deterministisch und schnell halten — die Generierung blockiert das initiale Dashboard-Rendering

## Nicht-Ziele

- Statische Custom Cards — geregelt in `ha/lovelace-card-patterns`, hier nicht dupliziert
- Custom-View-Layout-Elemente (eigenes View-Layout statt generierter Cards) — geregelt in `ha/lovelace-views-panels`
- Das Frontend-Daten-API-Pattern (`callWS`, Registry-Abfragen) im Detail — vertieft in `ha/frontend-data-api`
- Build-Stacks (TypeScript, Lit, Vite) für Strategy-Module — eigene Folge-Spec, sobald eine Strategy einen Build-Step rechtfertigt
- Beiträge zum HA-Frontend-Repo selbst (eingebaute Strategies) — diese Spec adressiert nur als Resource geladene Custom Strategies

## Anforderungen

### Dashboard-Strategy (`generate → views`)

- **MUSS [MUST]** eine statische, asynchrone Methode `static async generate(config, hass)` definieren, die ein Objekt mit einem `views`-Array zurückgibt
- **MUSS [MUST]** die volle Dashboard-Struktur aus der übergebenen Strategy-`config` ableiten — die `config` ist der kleine Startpunkt, der zur vollen Struktur expandiert wird
- **SOLLTE [SHOULD]** Werte aus `config` mit Defaults absichern (z. B. `const title = config.title || "My demo dashboard"`), damit die Strategy auch ohne vollständige Config rendert
- **KANN [MAY]** pro generiertem View eine `strategy`-Referenz statt eines fertigen `cards`-Arrays setzen, sodass eine View-Strategy die Cards erst beim Öffnen des Views generiert

### View-Strategy (`generate → cards`)

- **MUSS [MUST]** eine statische, asynchrone Methode `static async generate(config, hass)` definieren, die ein Objekt mit einem `cards`-Array zurückgibt
- **SOLLTE [SHOULD]** die View-Strategy nutzen, um die Cards eines einzelnen Views zu generieren, während eine Dashboard-Strategy die View-Liste erzeugt — das hält den ersten Dashboard-Load klein und baut jeden View erst beim Öffnen
- **KANN [MAY]** Daten, die die Dashboard-Strategy bereits abgefragt hat, über Strategy-Options an die View-Strategy durchreichen, statt sie pro View erneut abzufragen
- **MUSS NICHT [MUST NOT]** ein `views`-Array aus einer View-Strategy zurückgeben — View-Strategies liefern ausschließlich `cards`

### Registrierung & Referenzierung

- **MUSS [MUST]** die Strategy-Klasse über `customElements.define("ll-strategy-dashboard-<id>", <Class>)` (Dashboard) bzw. `customElements.define("ll-strategy-view-<id>", <Class>)` (View) registrieren
- **MUSS [MUST]** die Strategy im Dashboard- bzw. View-Config über den `strategy`-Key mit `type: custom:<id>` referenzieren — `<id>` ohne den `ll-strategy-dashboard-`/`ll-strategy-view-`-Präfix
- **MUSS [MUST]** die Strategy wie eine Custom Card als Dashboard-Resource laden (Modul-Resource) — ohne geladene Resource ist die Strategy nicht auflösbar
- **SOLLTE [SHOULD]** Custom Cards, die eine Strategy in ihren generierten Output einbezieht, als eigene Resources importieren — Strategies und Custom Cards arbeiten nebeneinander

### Zugriff auf `hass` (Areas/Devices/Entities)

- **MUSS [MUST]** Registry-Daten über `hass.callWS(...)` abfragen, wenn die Generierung Areas, Devices oder Entities braucht (`config/area_registry/list`, `config/device_registry/list`, `config/entity_registry/list`)
- **SOLLTE [SHOULD]** unabhängige Registry-Abfragen über `Promise.all([...])` parallelisieren, statt sie zu serialisieren
- **SOLLTE [SHOULD]** die Generierung deterministisch und schnell halten — gleiche `config` plus gleicher `hass`-Zustand ergeben dieselbe Struktur; die Generierung blockiert das initiale Dashboard-Rendering
- **KANN [MAY]** `hass.config` lesen (z. B. `hass.config.location_name`), um generierte Inhalte zu personalisieren

### Grafische Konfiguration

- **SOLLTE [SHOULD]** `static getConfigElement()` definieren, das ein Custom Element für das Editieren der Strategy-Config zurückgibt — HA zeigt es im Dashboard-Settings-Dialog
- **MUSS [MUST]** das Config-Element ein `setConfig(config)` implementieren — HA ruft es beim Setup auf
- **MUSS [MUST]** Änderungen über ein `config-changed`-CustomEvent zurückmelden (`bubbles: true, composed: true, detail: { config: newConfig }`)
- **SOLLTE [SHOULD]** `configRequired = true` setzen, wenn die Strategy ohne Konfiguration nicht funktioniert — HA erzwingt dann den Config-Editor vor der Dashboard-Erstellung
- **KANN [MAY]** `noEditor = true` setzen, wenn die Strategy keine grafische Konfiguration unterstützt

### Community-Dashboard-Dialog

- **SOLLTE [SHOULD]** eine Dashboard-Strategy über `window.customStrategies = window.customStrategies || []; window.customStrategies.push({...})` registrieren, damit sie im New-Dashboard-Dialog unter „Community dashboards" erscheint (eingeführt in HA 2026.5)
- **MUSS [MUST]** beim Push `type` (der Strategy-Type ohne `custom:`-Präfix) und `strategyType: "dashboard"` setzen — beide sind Pflicht
- **KANN [MAY]** `name`, `description` und `documentationURL` setzen — friendly Name, Kurztext und Doku-Link für die Auswahl
- **SOLLTE [SHOULD]** `static getCreateSuggestions(hass)` definieren, das `title` und/oder `icon` als Default-Werte für den Create-Dialog vorschlägt — diese Werte sind nur Defaults und vom User änderbar

## Akzeptanzkriterien

- [ ] Dashboard-Strategy hat `static async generate(config, hass)` und liefert `{ views: [...] }`
- [ ] View-Strategy hat `static async generate(config, hass)` und liefert `{ cards: [...] }`
- [ ] Strategy ist via `customElements.define("ll-strategy-dashboard-<id>", ...)` bzw. `ll-strategy-view-<id>` registriert
- [ ] Dashboard-/View-Config referenziert die Strategy über `strategy.type: custom:<id>`
- [ ] Strategy ist als Dashboard-Resource (Modul) geladen
- [ ] Registry-Zugriff (Areas/Devices/Entities) läuft über `hass.callWS(...)`, unabhängige Abfragen parallelisiert via `Promise.all`
- [ ] Grafische Konfiguration (falls vorhanden) liefert ein `getConfigElement` mit `setConfig` und `config-changed`-Event
- [ ] Community-Dashboard ist via `window.customStrategies`-Push mit `type` und `strategyType: "dashboard"` registriert
- [ ] `getCreateSuggestions(hass)` (falls vorhanden) liefert `title`/`icon` als Default-Vorschläge
- [ ] Quality-Scale-Marker: **nicht Teil der HA-Quality-Scale** (portfolio-spezifisch)

## Offene Fragen

- **Strategy-Options vs. Re-Query**: Die Doku reicht Registry-Daten von der Dashboard- an die View-Strategy über Strategy-Options durch. Wann lohnt die Durchreichung gegenüber einer erneuten `callWS`-Abfrage pro View? Eine Heuristik für die Schwelle fehlt.
- **Determinismus-Grenze**: Die Generierung soll deterministisch sein, aber `hass.states` tickt. Wie weit darf eine Strategy auf live-States reagieren, ohne dass Re-Generierung das initiale Rendering merklich verzögert?
- **TypeScript/Lit-Migration**: Die Doku empfiehlt Lit `ReactiveElement` statt `HTMLElement` und Typisierung via TypeScript/JSDoc. Wann verlangt eine Folge-Spec einen Build-Step für Strategy-Module?
- **`frontend-data-api`-Überschneidung**: Das `callWS`-Registry-Pattern wird hier nur als Mindest-Vorgabe formuliert. Welche Abgrenzung zu `ha/frontend-data-api` gilt, sobald jene Spec existiert?
- **`configRequired` vs. `getCreateSuggestions`**: Beide steuern den Create-Flow. Wie spielen erzwungener Config-Editor und vorgeschlagene Default-Werte zusammen, wenn beide gesetzt sind?
