# Skill: `ha-lovelace-card-scaffold`

Status: draft

## Kontext

Custom Lovelace Cards (siehe `ha/lovelace-card-patterns`) leben unter `custom_components/<domain>/www/<card-name>.js`, sind in `__init__.py` per `StaticPathConfig` auto-registriert, nutzen Vanilla JS plus Shadow DOM, machen Entity-Change-Detection im `set hass`-Setter, und bauen ihr Styling auf HA-CSS-Custom-Properties auf. Manueller Card-Code übersieht regelmäßig Pflicht-Lifecycle-Methoden (`getCardSize`, `getGridOptions`, `setConfig`-Validierung, `getStubConfig`), produziert hardcodierte Farben statt HA-Custom-Properties, oder vergisst die Auto-Registrierung in `__init__.py`.

Dieser Skill scaffold eine Vanilla-JS-Card mit allen Pflicht-Methoden, korrekter Shadow-DOM-Initialisierung, Entity-Change-Detection-Skelett, und Auto-Registrierungs-Block in `__init__.py`. Die konkrete Card-Logik (welche Daten gerendert werden, welches Layout, welche Interaktionen) bleibt Konsumenten-Aufgabe; der Skill liefert das spec-konforme Skelett.

## Scope

Der Skill scaffold **eine** Card pro Aufruf. Er löscht keine Cards, mergt keine, ändert keine bestehende Auto-Registrierung. Bei Konflikt (Card mit gleichem Namen existiert) bricht er ab.

## Ziele

- Card-Skelett mit allen `ha/lovelace-card-patterns`-MUSS-Methoden
- Auto-Registrierung in `__init__.py` ohne dass der User Lovelace-Resources manuell konfigurieren muss
- Shadow DOM plus HA-CSS-Custom-Properties-Skelett — kein hardcoded-Styling
- Entity-Change-Detection im `set hass`-Setter als Default-Pattern
- `getStubConfig` plus optional `getConfigElement`-Stub, sodass Drag-and-Drop in der Lovelace-UI funktioniert

## Nicht-Ziele

- TypeScript- oder Lit-basierte Cards — eigene Folge-Spec, sobald Build-Stack relevant wird
- Card-Editor-UI — der Skill scaffold einen `getConfigElement`-Stub; das eigentliche Editor-Interface bleibt Konsumenten-Aufgabe
- Multi-Card-Scaffolding pro Aufruf
- HACS-Plugin-Distribution für Standalone-Cards (außerhalb der Integration)

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „scaffold a Lovelace card for the integration"
  - „add a custom Lovelace card called `<name>`"
  - „erstelle eine Custom-Card für `<Resource>`"
- **MUSS NICHT [MUST NOT]** aktivieren bei Greenfield-Setup (`ha-integration-scaffold`) oder Card-Removal

### Eingaben

- **MUSS [MUST]** erfassen:
  - `target_dir`
  - `card_type` — lowercase-kebab-case, präfigiert mit `<domain>` (z. B. `<domain>-resource-card`)
  - `display_name` — Lovelace-Card-Picker-Name
  - `description` — Beschreibung im Card-Picker
  - `entity_types` — Liste der Entity-Plattformen, die die Card konsumiert (`sensor`, `binary_sensor`, …)
- **SOLLTE [SHOULD]** erfassen:
  - `preview` (Default `false`) — ob die Card im Picker eine Preview rendern soll
  - `grid_options` (Default `{columns: 6, rows: 3, min_columns: 3, min_rows: 2}`) — Sections-Layout-Defaults

### Pre-Flight

- **MUSS [MUST]** prüfen:
  1. `target_dir` ist git-Repo, sauber
  2. `<target_dir>/custom_components/<domain>/www/<card-name>.js` existiert nicht
  3. `__init__.py` enthält noch keinen `StaticPathConfig`-Eintrag für diesen Card-Namen

### Generator-Choreographie

- **MUSS [MUST]** `custom_components/<domain>/www/<card-name>.js` mit folgenden Bausteinen anlegen:
  - `class <PascalCardName> extends HTMLElement` — Top-Level-Klasse
  - `setConfig(config)` — wirft `Error` bei fehlenden Pflichtfeldern
  - `set hass(hass)` mit Entity-Change-Detection-Skelett
  - `getCardSize()` — Default `3`
  - `getGridOptions()` — aus Eingabe `grid_options`
  - `static getStubConfig()` — Default-Card-Config beim Drag-and-Drop
  - `static getConfigElement()` — Optional-Stub, der ein `<custom-card-name>-editor`-Element zurückgibt (Editor selbst bleibt User-Aufgabe)
  - `connectedCallback()` mit `attachShadow({mode: "open"})` und initialem Render-Aufruf
  - `_render()` — Skelett mit HA-CSS-Custom-Properties (`var(--primary-text-color)`, `var(--secondary-text-color)`, `var(--state-icon-color)`, `var(--ha-card-background)`, `var(--divider-color)`)
  - `customElements.define(card_type, <PascalCardName>)` und `window.customCards`-Push am Datei-Ende
- **MUSS [MUST]** in `__init__.py` einen Auto-Registrierungs-Block ergänzen, der `await hass.http.async_register_static_paths([StaticPathConfig(url_path=..., path=..., cache_headers=False)])` für die Card-Datei aufruft
- **MUSS [MUST]** `cache_headers=False` setzen — ohne diesen Wert landen aktualisierte Cards für Browser mit gecachten Resources im Stale-Zustand
- **MUSS NICHT [MUST NOT]** Hardcoded-Hex-Farben oder Pixel-Werte ohne CSS-Custom-Property-Wrap ins Skelett schreiben

### Test-Erweiterung

- **MUSS [MUST]** den `tests/test_lovelace_cleanup.py`-Test (sofern vorhanden, aus `ha-test-harness-augment`) um eine Assertion für die neu auto-registrierte Card erweitern — die `StaticPathConfig`-URL-Map muss den neuen Card-Pfad enthalten

### Verbote

- **MUSS NICHT [MUST NOT]** `cache_headers=True` setzen — siehe oben
- **MUSS NICHT [MUST NOT]** Externe-CDN-URLs als Asset-Quellen referenzieren — Cards laufen offline-fähig
- **MUSS NICHT [MUST NOT]** den User auffordern, Lovelace-Resources manuell einzutragen

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/www/<card-name>.js` existiert mit allen Pflicht-Methoden
- [ ] `__init__.py` enthält den Auto-Registrierungs-Block mit `cache_headers=False`
- [ ] `customElements.define(...)` und `window.customCards`-Push existieren am Datei-Ende
- [ ] Shadow DOM wird in `connectedCallback` per `attachShadow({mode: "open"})` aufgesetzt
- [ ] CSS verwendet HA-Custom-Properties — keine hardcodierten Hex-Farben
- [ ] `tests/test_lovelace_cleanup.py` (sofern vorhanden) enthält Assertion für die neue Card
- [ ] `ruff check custom_components/<domain>/__init__.py` läuft fehlerfrei

## Offene Fragen

- **Editor-Element-Pflicht-Tiefe**: `getConfigElement` als Stub vs. vollständiger Editor — Schwelle?
- **TypeScript-Migration**: Wann verlangt eine Folge-Spec TS/Lit?
- **Multi-Card-Repos**: Wenn die Integration mehrere Cards liefert, verändert sich das Layout? Aktuell jede Card als eigene Datei.
- **Card-Test-Pattern**: Vanilla-JS-Card-Tests sind selten in HA — gibt es Konvention?
