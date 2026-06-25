# Skill: `ha-strategy-add`

Status: draft

## Kontext

`ha/lovelace-strategies` definiert die Frontend-Lieferform, die Dashboards und/oder Views **programmatisch generiert**, statt sie statisch zu deklarieren: Custom Strategies sind Custom Elements mit einer statischen `static async generate(config, hass)`-Methode, die aus einer kleinen Strategy-`config` die volle Struktur zurückgibt. Es gibt zwei Arten — eine **Dashboard-Strategy** (`generate → { views: [...] }`) und eine **View-Strategy** (`generate → { cards: [...] }`). Beide werden wie Custom Cards als Dashboard-Resource (Modul) geladen, über `customElements.define("ll-strategy-dashboard-<id>", …)` bzw. `ll-strategy-view-<id>` registriert und im Config über `strategy.type: custom:<id>` referenziert. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt **eine** Strategy (Dashboard oder View) in einem **bestehenden** Frontend-Modul: die Strategy-Klasse mit der statischen `generate(config, hass)`, die `customElements.define`-Registrierung, das Resource-Laden, optional `getConfigElement`/`getCreateSuggestions` und — bei Dashboard-Strategies — den `window.customStrategies`-Push für den Community-Dashboard-Dialog. Quality-Scale-Marker: **nicht Teil der HA-Quality-Scale** (portfolio-spezifisch). Der Skill arbeitet offline und deployt nie in eine laufende HA-Instanz.

## Scope

Ergänzung genau einer Strategy pro Lauf (`dashboard` oder `view`) in einem bestehenden Frontend-Modul (typisch `custom_components/<domain>/www/`): die Strategy-Klasse, die statische `static async generate(config, hass)`, die `customElements.define("ll-strategy-dashboard-<id>"/"ll-strategy-view-<id>", …)`-Registrierung, das Resource-Laden (z. B. `StaticPathConfig` in `__init__.py`), die optionale grafische Konfiguration (`getConfigElement` + `setConfig` + `config-changed`) und — für Dashboard-Strategies — der `window.customStrategies`-Push mit optionalem `getCreateSuggestions`. Der Skill liest `ha/lovelace-strategies` und validiert.

## Ziele

- Aus der beschriebenen Generierungs-Absicht die richtige Art (Dashboard vs. View) wählen und spec-konform ergänzen
- Den `generate`-Vertrag erzwingen: Dashboard-Strategy liefert `{ views: [...] }`, View-Strategy liefert `{ cards: [...] }` — eine View-Strategy gibt **nie** ein `views`-Array zurück
- Registrierung (`customElements.define` mit korrektem `ll-strategy-…`-Präfix), Referenzierung (`strategy.type: custom:<id>`) und Resource-Laden als verbindliches Pattern erzwingen
- Den `hass`-Zugriff auf Areas/Devices/Entities über `hass.callWS(...)` mit `Promise.all`-Parallelisierung und Config-Defaults deterministisch und schnell halten — die Generierung blockiert das initiale Dashboard-Rendering
- Optional die grafische Konfiguration und die Community-Dashboard-Auffindbarkeit (`window.customStrategies`, `getCreateSuggestions`) korrekt verdrahten

## Nicht-Ziele

- Statische Custom Cards (eine Card, kein Generator) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Custom-View-Layout-Elemente und Panels (eigenes View-Layout statt generierter Cards) — `ha/lovelace-views-panels`
- Custom Badges — `ha/lovelace-badges`
- Das Frontend-Daten-API-Pattern (`callWS`, Registry-Abfragen) im Detail — `ha/frontend-data-api`
- Build-Stacks (TypeScript, Lit, Vite) für Strategy-Module — eigene Folge-Spec
- Beiträge zum HA-Frontend-Repo selbst (eingebaute Strategies) — nur als Resource geladene Custom Strategies sind hier adressiert

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a dashboard strategy", „auto-generate views with a strategy", „create a custom Lovelace strategy"
  - „generate this dashboard / view programmatically"
  - „füge eine Strategy hinzu", „generiere die Views automatisch über eine Strategy"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Generierungs-Absicht (Prosa), aus der der Skill Art und `<id>` ableitet
- **KANN [MAY]** erfassen: `kind` (`dashboard`/`view`), die `<id>`, welche Registry-Daten (Areas/Devices/Entities) die Generierung braucht, ob eine grafische Konfiguration (`getConfigElement`) nötig ist und — für Dashboard-Strategies — ob der `window.customStrategies`-Push erfolgen soll

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein bestehendes Frontend-Modul ist (z. B. `custom_components/<domain>/manifest.json` existiert; `domain` lesen, falls vorhanden)
- **MUSS [MUST]** die Art ableiten (oder erfragen) und bestätigen: Dashboard-Strategy generiert die View-Liste, View-Strategy generiert die Cards eines einzelnen Views
- **MUSS [MUST]** die `ha/lovelace-strategies`-Spec lesen
- **MUSS NICHT [MUST NOT]** eine bestehende Strategy / `<id>` / `customElements.define`-Registrierung überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (pro Art, aus `ha/lovelace-strategies`)

- **MUSS [MUST]** für Dashboard-Strategies eine `static async generate(config, hass)` definieren, die `{ views: [...] }` zurückgibt, und die volle Dashboard-Struktur aus der übergebenen `config` ableiten
- **MUSS [MUST]** für View-Strategies eine `static async generate(config, hass)` definieren, die `{ cards: [...] }` zurückgibt
- **MUSS NICHT [MUST NOT]** aus einer View-Strategy ein `views`-Array zurückgeben — View-Strategies liefern ausschließlich `cards`
- **SOLLTE [SHOULD]** Werte aus `config` mit Defaults absichern (z. B. `const title = config.title || "…"`), damit die Strategy auch ohne vollständige Config rendert
- **KANN [MAY]** pro generiertem View eine `strategy`-Referenz statt eines fertigen `cards`-Arrays setzen, sodass die View-Strategy die Cards erst beim Öffnen generiert; und Daten der Dashboard-Strategy über Strategy-Options an die View-Strategy durchreichen, statt sie pro View erneut abzufragen
- **MUSS [MUST]** die Strategy-Klasse über `customElements.define("ll-strategy-dashboard-<id>", …)` (Dashboard) bzw. `customElements.define("ll-strategy-view-<id>", …)` (View) registrieren und sie wie eine Custom Card als Dashboard-Resource (Modul) laden — ohne geladene Resource ist die Strategy nicht auflösbar
- **MUSS [MUST]** die Referenzierung über `strategy.type: custom:<id>` dokumentieren — `<id>` ohne den `ll-strategy-dashboard-`/`ll-strategy-view-`-Präfix
- **MUSS [MUST]** Registry-Daten über `hass.callWS(...)` abfragen, wenn die Generierung Areas/Devices/Entities braucht (`config/area_registry/list`, `config/device_registry/list`, `config/entity_registry/list`), und unabhängige Abfragen über `Promise.all([...])` parallelisieren
- **SOLLTE [SHOULD]** die Generierung deterministisch und schnell halten — gleiche `config` plus gleicher `hass`-Zustand ergeben dieselbe Struktur; die Generierung blockiert das initiale Dashboard-Rendering
- **SOLLTE [SHOULD]** bei grafischer Konfiguration ein `static getConfigElement()` definieren, dessen Config-Element ein `setConfig(config)` implementiert und Änderungen über ein `config-changed`-CustomEvent (`bubbles: true, composed: true, detail: { config: newConfig }`) zurückmeldet; `configRequired = true` setzen, wenn die Strategy ohne Config nicht funktioniert, sonst `noEditor = true`
- **SOLLTE [SHOULD]** eine Dashboard-Strategy über `window.customStrategies.push({...})` für den Community-Dashboard-Dialog registrieren; der Push **MUSS [MUST]** `type` (Strategy-Type ohne `custom:`-Präfix) und `strategyType: "dashboard"` setzen und **KANN [MAY]** `name`/`description`/`documentationURL` sowie ein `static getCreateSuggestions(hass)` (Default-`title`/`icon`) ergänzen
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: die `generate`-Methode ist statisch + async und liefert die art-korrekte Form (`{ views }` bzw. `{ cards }`, View-Strategy ohne `views`); die `customElements.define`-Registrierung trägt das korrekte `ll-strategy-…-<id>`-Präfix; die Strategy ist als Dashboard-Resource (Modul) geladen; `strategy.type: custom:<id>` ist dokumentiert; Registry-Zugriff (falls vorhanden) läuft über `hass.callWS` mit `Promise.all`; eine vorhandene grafische Konfiguration liefert `getConfigElement` + `setConfig` + `config-changed`; ein vorhandener `window.customStrategies`-Push trägt `type` und `strategyType: "dashboard"`
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/lovelace-strategies` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**, portfolio-spezifisch)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Strategy pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** eine statische Custom Card, ein Panel/View-Layout oder ein Badge als Strategy ausgeben — diese gehen an die jeweilige Schwester-Schicht
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet die Art ab (oder erfragt sie) und bestätigt Dashboard-vs-View vor der Generierung
- [ ] Dashboard-Strategy hat `static async generate(config, hass)` und liefert `{ views: [...] }`; View-Strategy hat `static async generate(config, hass)` und liefert `{ cards: [...] }` (kein `views`-Array)
- [ ] Strategy ist via `customElements.define("ll-strategy-dashboard-<id>", …)` bzw. `ll-strategy-view-<id>` registriert und als Dashboard-Resource (Modul) geladen
- [ ] Referenzierung über `strategy.type: custom:<id>` ist dokumentiert
- [ ] Registry-Zugriff (Areas/Devices/Entities) läuft über `hass.callWS(...)`, unabhängige Abfragen via `Promise.all` parallelisiert
- [ ] Grafische Konfiguration (falls vorhanden) liefert `getConfigElement` mit `setConfig` und `config-changed`-Event
- [ ] Community-Dashboard (falls Dashboard-Strategy) ist via `window.customStrategies`-Push mit `type` und `strategyType: "dashboard"` registriert; `getCreateSuggestions(hass)` (falls vorhanden) liefert `title`/`icon` als Default-Vorschläge
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **nicht Teil der HA-Quality-Scale** (portfolio-spezifisch)

## Offene Fragen

- **Modul-Layout**: Liegen Strategies immer unter `custom_components/<domain>/www/` (wie Custom Cards) oder rechtfertigt ein eigenständiges Frontend-Modul ohne Integration ein anderes Resource-Layout? Aktuell folgt der Skill dem Card-Layout und fragt im Zweifel nach.
- **Dashboard- + View-Strategy in einem Lauf**: Eine Dashboard-Strategy delegiert oft an eine View-Strategy. Soll der Skill das Paar trotz „eine Strategy pro Lauf" gemeinsam ergänzen dürfen, oder strikt zwei Läufe verlangen? Aktuell strikt einer pro Lauf.
- **Determinismus-Grenze**: `hass.states` tickt; wie weit darf die Generierung auf live-States reagieren, ohne das initiale Rendering merklich zu verzögern? `ha/lovelace-strategies` lässt es offen.
- **`configRequired` vs. `getCreateSuggestions`**: Wie spielen erzwungener Config-Editor und vorgeschlagene Default-Werte zusammen, wenn beide gesetzt sind? Fall-zu-fall.
