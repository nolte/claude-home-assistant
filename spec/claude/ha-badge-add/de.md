# Skill: `ha-badge-add`

Status: draft

## Kontext

`ha/lovelace-badges` definiert die Custom-Badge-Schicht des Frontends: die kleinen Status-Widgets, die oben in einer Lovelace-View über allen Cards sitzen. Ein Custom Badge wird — sehr ähnlich zur Custom Card — als JavaScript-Modul ausgeliefert, das ein Custom Element (`HTMLElement`- oder `LitElement`-Subklasse) via `customElements.define("<badge-type>", <BadgeClass>)` registriert, von HA als Badge-Type erkannt wird und im Badge-Picker des Dashboards auswählbar ist. Die API ist deklarativ: das Badge empfängt `hass` als Property-Setter (HA setzt es bei jedem State-Tick) und die User-Konfiguration via `setConfig(config)` (HA ruft es selten auf); wirft `setConfig` einen Error, rendert HA ein Fehler-Badge. Optionale statische Methoden (`getConfigElement`, `getStubConfig`) treiben das grafische Editor-UI. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt **ein** Custom Badge in einem **bestehenden** Frontend-Modul: das Badge-Custom-Element (mit `setConfig`, `hass`-Setter und Render), optional `getConfigElement` / `getStubConfig`, und den `window.customBadges`-Registrierungs-Eintrag (`type`, `name`, `description`) — spec-konform zu `ha/lovelace-badges`. Der Quality-Scale-Marker ist **nicht Teil der HA-Quality-Scale** (außerhalb der Skala).

## Scope

Ergänzung genau eines Custom Badge pro Lauf in ein bestehendes Frontend-Modul (`www/`-Ordner einer Integration oder ein eigenständiges Lovelace-Modul): das Badge-Custom-Element (Subklasse von `HTMLElement` oder `LitElement`), der `setConfig(config)`-Lifecycle, das `hass`-Property-Setter-Pattern, der `customElements.define`-Aufruf, der `window.customBadges`-Push (mindestens `type` und `name`), optional `getConfigElement` / `getStubConfig`, und die Dashboard-Referenzierung über `type: "custom:<badge-type>"` plus den `module`-Resource-Hinweis. Der Skill liest `ha/lovelace-badges` und validiert offline.

## Ziele

- Aus einer beschriebenen Status-Anzeige ein Custom Badge als Custom Element (`HTMLElement`/`LitElement`-Subklasse) erzeugen, registriert via `customElements.define`
- Den `setConfig(config)`-Lifecycle und das `hass`-Property-Setter-Pattern als Pflicht-Vertrag erzwingen — Update bei jedem State-Tick, `throw new Error` bei ungültiger Config
- Das Badge im Badge-Picker sichtbar machen über einen Push in `window.customBadges` mit mindestens `type` und `name`
- Das grafische Editor-UI (`getConfigElement` / `getStubConfig`) als optionale, aber empfohlene Schicht anbieten — analog zum Card-Editor
- Die Dashboard-Referenzierung (`type: "custom:<badge-type>"` in der `badges:`-Liste) und die `module`-Resource dokumentieren

## Nicht-Ziele

- Custom Cards (die größeren Inhalts-Bausteine) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Tile-Card-Features — `ha/lovelace-card-features`
- Dashboard-Strategien — `ha/lovelace-strategies`
- Das `config-changed`-Detail-Pattern des grafischen Editors — `ha/lovelace-card-editor`, hier nur als Mindest-Vorgabe referenziert
- Das `hass`-Zugriffs-Pattern und die Frontend-Daten-API — `ha/frontend-data-api`
- Das eingebaute Entity-Badge (HA-nativ) und Build-Stacks (Vite/esbuild/Rollup, TS/Lit-Pipelines)

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a custom badge", „create a Lovelace badge", „register a custom badge"
  - „füge ein Custom-Badge hinzu", „erstelle ein Lovelace-Badge"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Status-Anzeige (Prosa), aus der der Skill den Badge-Inhalt und die konsumierte Entity ableitet
- **KANN [MAY]** erfassen: `badge_type` (der `customElements.define`-Tag-Name → `custom:<badge-type>`), den Anzeige-`name`, eine `description`, das Render-Framework (`HTMLElement` vs. `LitElement`), und ob ein grafischer Editor (`getConfigElement` / `getStubConfig`) erzeugt werden soll

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein bestehendes Frontend-Modul ist (ein `www/`-Verzeichnis bzw. ein vorhandenes Lovelace-Modul); andernfalls auf `ha-lovelace-card-scaffold` für Greenfield verweisen
- **MUSS [MUST]** den `badge_type`-Tag-Namen auflösen (ableiten + bestätigen) und gegen `ha/naming-conventions` prüfen
- **MUSS [MUST]** die `ha/lovelace-badges`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes Badge-Modul oder einen bestehenden `badge_type` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/lovelace-badges`)

- **MUSS [MUST]** das Badge als Custom Element definieren — Subklasse von `HTMLElement` (oder `LitElement`) — und via `customElements.define("<badge-type>", <BadgeClass>)` registrieren; der Tag-Name bestimmt den Badge-Type `custom:<badge-type>`
- **MUSS NICHT [MUST NOT]** React als Rendering-Framework verwenden — Custom Elements und React sind in HA-Badges nicht kompatibel
- **MUSS [MUST]** `setConfig(config)` implementieren und ungültige Konfigurationen mit `throw new Error("...")` ablehnen — HA fängt den Error und rendert ein Fehler-Badge
- **MUSS [MUST]** das `hass`-Property als Setter implementieren — das Badge aktualisiert sich bei jedem Set auf den neuesten State
- **SOLLTE [SHOULD]** den State der konsumierten Entity aus `hass.states[entityId]` lesen und einen sinnvollen Fallback (z. B. `unavailable`) rendern, wenn die Entity fehlt
- **SOLLTE [SHOULD]** einen Push in `window.customBadges` erzeugen (`window.customBadges = window.customBadges || []; window.customBadges.push({...})`), damit das Badge im Badge-Picker erscheint, mit mindestens den Pflicht-Properties `type` und `name`
- **KANN [MAY]** die optionalen Push-Properties `description`, `documentationURL` und `preview` setzen (`preview` defaultet auf `false`)
- **SOLLTE [SHOULD]** die statischen Methoden `getConfigElement()` (liefert ein Editor-Custom-Element) und `getStubConfig()` (liefert eine Default-Config ohne `type:`-Parameter) definieren — oder bewusst weglassen
- **MUSS NICHT [MUST NOT]** das `config-changed`-Event-Pattern hier ausformulieren — das ist in `ha/lovelace-card-editor` geregelt
- **SOLLTE [SHOULD]** das Badge in einer eigenen Datei unter `<config>/www/<badge-name>.js` ablegen und Bezeichner nach `ha/naming-conventions` benennen; HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)
- **MUSS [MUST]** die Dashboard-Referenzierung dokumentieren: `type: "custom:<badge-type>"` in der `badges:`-Liste einer View, plus eine `module`-Resource mit der Badge-Modul-URL (typischerweise `/local/<badge-name>.js`), wobei nach erstmaligem Anlegen des `www`-Ordners ein HA-Restart nötig ist

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: das Badge ist Subklasse von `HTMLElement`/`LitElement` (kein React); `customElements.define` ist aufgerufen; `setConfig` ist implementiert und wirft bei ungültiger Config; das `hass`-Property ist ein Setter; der `window.customBadges`-Push trägt mindestens `type` und `name`; `getConfigElement`/`getStubConfig` sind implementiert oder bewusst weggelassen; die Dashboard-Referenzierung und die `module`-Resource sind dokumentiert
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/lovelace-badges` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als ein Badge pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** React als Rendering-Framework verwenden
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder die Dashboard-/Resource-Konfiguration einer Live-Instanz schreiben

## Akzeptanzkriterien

- [ ] Badge ist als Subklasse von `HTMLElement` (oder `LitElement`) definiert; React wird nicht als Rendering-Framework verwendet
- [ ] `customElements.define("<badge-type>", <BadgeClass>)` ist aufgerufen
- [ ] Badge erscheint im Badge-Picker via `window.customBadges`-Push mit mindestens `type` und `name`
- [ ] `setConfig(config)` ist implementiert; ungültige Configs werfen `Error`
- [ ] `hass`-Property ist als Setter implementiert und aktualisiert das Badge bei jedem State-Tick
- [ ] `getConfigElement()` und `getStubConfig()` sind implementiert (oder bewusst weggelassen)
- [ ] Dashboard-Referenzierung (`type: "custom:<badge-type>"` in der `badges:`-Liste) und die `module`-Resource sind dokumentiert
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **nicht Teil der HA-Quality-Scale**

## Offene Fragen

- **Editor-Pflicht-Tiefe**: `getConfigElement` und `getStubConfig` als SOLLTE oder MUSS? Aktuell SOLLTE (analog `ha/lovelace-badges`) — ein fehlendes `getStubConfig` führt zu leeren Default-Badges beim Hinzufügen über den Picker.
- **`LitElement` vs. Vanilla-`HTMLElement`**: `ha/lovelace-badges` lässt beide offen. Soll der Skill analog zu `ha/lovelace-card-patterns` Vanilla-JS als Default festschreiben, oder ist `LitElement` für Badges akzeptabel?
- **Auto-Registrierung**: Soll der Skill — analog zur Card-Auto-Registrierung — den `window.customBadges`-Push aus dem Integration-`www/`-Ordner automatisieren, statt eine manuelle Resource-Eintragung zu verlangen?
