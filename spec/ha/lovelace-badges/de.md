# HA-Integration: Lovelace-Badges

Status: draft

## Kontext

Badges sind kleine Widgets, die oben in einer Lovelace-View über allen Cards sitzen. HA liefert ein eingebautes Badge (das Entity-Badge), aber Integrationen können eigene Custom Badges definieren und nutzen. Ein Custom Badge wird — sehr ähnlich zur Custom Card — als JavaScript-Modul ausgeliefert, das einen Custom Element (`HTMLElement`/`LitElement`-Subklasse) registriert, von HA als Badge-Type erkannt wird und im Badge-Picker des Dashboards ausgewählt werden kann.

Diese Spec deckt ausschließlich **Custom Badges** ab — die kleinen Status-Elemente am Kopf einer View. Custom Cards (die größeren Inhalts-Bausteine) sind in `ha/lovelace-card-patterns` geregelt; das grafische Editor-UI ist in `ha/lovelace-card-editor` geregelt; der Zugriff auf das `hass`-Objekt und die Frontend-Daten-API ist in `ha/frontend-data-api` geregelt. Diese Spec dupliziert diese Regeln nicht, sondern verweist auf sie per Slug.

Die Badge-API ist deklarativ aufgebaut: Das Badge empfängt das `hass`-Objekt als Property-Setter (HA setzt es bei jedem State-Tick) und die User-Konfiguration via `setConfig(config)` (HA ruft es auf, wenn sich die Konfiguration ändert — selten). Wirft `setConfig` einen Error, rendert HA ein Fehler-Badge. Optionale statische Methoden (`getConfigElement`, `getStubConfig`) treiben das grafische Editor-UI.

Quality-Scale-Marker: Custom Badges sind **nicht Teil der HA-Quality-Scale** — das Pattern hier steht außerhalb der Skala.

## Ziele

- Custom Badges als Custom Element (`HTMLElement`/`LitElement`-Subklasse) festschreiben, registriert via `customElements.define`
- Das Badge im Badge-Picker des Dashboards sichtbar machen über einen Push in `window.customBadges`
- Den `setConfig(config)`-Lifecycle und das `hass`-Property-Setter-Pattern als Pflicht-Vertrag etablieren
- Das grafische Editor-UI (`getConfigElement`/`getStubConfig`) als optionale, aber empfohlene Schicht anbieten — analog zum Card-Editor
- Die Dashboard-Referenzierung über `type: custom:<badge-name>` dokumentieren

## Nicht-Ziele

- Custom Cards — geregelt in `ha/lovelace-card-patterns`, hier nicht dupliziert
- Detail-Pattern des grafischen Editor-UIs (Event-Verdrahtung, `config-changed`-Dispatch) — geregelt in `ha/lovelace-card-editor`, hier nur als Mindest-Vorgabe referenziert
- Zugriffs-Pattern auf das `hass`-Objekt und die Frontend-Daten-API — geregelt in `ha/frontend-data-api`
- Das eingebaute Entity-Badge — HA-nativ, keine Custom-Erweiterung
- Build-Stacks (Vite, esbuild, Rollup) und TypeScript/Lit-Build-Pipelines — eigene Folge-Spec

## Anforderungen

### Badge definieren (`HTMLElement`)

- **MUSS [MUST]** das Badge als Custom Element definieren — Subklasse von `HTMLElement` (oder `LitElement`)
- **MUSS [MUST]** dem Element frei überlassen, wie es sein DOM rendert — Polymer, Angular, Preact oder ein anderes etabliertes Framework ist erlaubt, **außer** React
- **SOLLTE [SHOULD]** das Badge in einer eigenen Datei unter `<config>/www/<badge-name>.js` ablegen und als Resource vom Typ `module` registrieren
- **MUSS NICHT [MUST NOT]** React als Rendering-Framework verwenden — Custom Elements und React sind in HA-Badges nicht kompatibel

### Registrierung (`window.customBadges`)

- **MUSS [MUST]** `customElements.define("<badge-type>", <BadgeClass>)` aufrufen — der Tag-Name bestimmt den Badge-Type `custom:<badge-type>`
- **SOLLTE [SHOULD]** ein Objekt, das das Badge beschreibt, in das Array `window.customBadges` pushen, damit das Badge im Badge-Picker-Dialog des Dashboards erscheint (`window.customBadges = window.customBadges || []; window.customBadges.push({...})`)
- **MUSS [MUST]** im Push-Objekt mindestens die Pflicht-Properties `type` und `name` setzen
- **KANN [MAY]** die optionalen Properties `description`, `documentationURL` und `preview` setzen — `documentationURL` fügt einen Hilfe-Link im Frontend-Badge-Editor hinzu; `preview` defaultet auf `false`

### `setConfig` & `hass`

- **MUSS [MUST]** `setConfig(config)` implementieren — HA ruft es auf, wenn sich die Konfiguration ändert (selten)
- **MUSS [MUST]** ungültige Konfigurationen mit `throw new Error("...")` ablehnen — HA fängt den Error und rendert ein Fehler-Badge
- **MUSS [MUST]** das `hass`-Property als Setter implementieren — HA setzt es, wenn sich der HA-State ändert (häufig); das Badge muss sich bei jedem Set auf den neuesten State aktualisieren
- **SOLLTE [SHOULD]** den State der konsumierten Entity aus `hass.states[entityId]` lesen und einen sinnvollen Fallback (z. B. `unavailable`) rendern, wenn die Entity fehlt

### Grafische Konfiguration

- **SOLLTE [SHOULD]** eine statische Methode `getConfigElement()` definieren, die ein Custom Element für das Editieren der User-Konfiguration zurückgibt — HA zeigt es im Badge-Editor des Dashboards an
- **SOLLTE [SHOULD]** eine statische Methode `getStubConfig()` definieren, die eine Default-Badge-Konfiguration in JSON-Form (ohne den `type:`-Parameter) für den Badge-Type-Picker zurückgibt
- **KANN [MAY]** das Config-Element in einer separaten Datei (z. B. `<badge-name>-editor.js`) definieren und per `import` einbinden
- **MUSS NICHT [MUST NOT]** das `config-changed`-Event-Pattern hier ausformulieren — das grafische Editor-Detail-Pattern ist in `ha/lovelace-card-editor` geregelt

### Dashboard-Referenzierung

- **MUSS [MUST]** das Badge im Dashboard über `type: "custom:<badge-type>"` referenzieren, eingebettet in die `badges:`-Liste einer View
- **MUSS [MUST]** eine Resource mit der URL des Badge-Moduls und dem Typ `module` zur Dashboard-Konfiguration hinzufügen, bevor das Badge nutzbar ist
- **SOLLTE [SHOULD]** das Badge-Modul unter `/local/<badge-name>.js` erreichbar machen, wenn die Datei im `<config>/www`-Verzeichnis liegt — nach erstmaligem Anlegen des `www`-Ordners ist ein HA-Restart nötig, damit die Dateien erkannt werden

## Akzeptanzkriterien

- [ ] Badge ist als Subklasse von `HTMLElement` (oder `LitElement`) definiert; React wird nicht als Rendering-Framework verwendet
- [ ] `customElements.define("<badge-type>", <BadgeClass>)` ist aufgerufen
- [ ] Badge erscheint im Badge-Picker via `window.customBadges`-Push mit mindestens `type` und `name`
- [ ] `setConfig(config)` ist implementiert; ungültige Configs werfen `Error`
- [ ] `hass`-Property ist als Setter implementiert und aktualisiert das Badge bei jedem State-Tick
- [ ] `getConfigElement()` und `getStubConfig()` sind implementiert (oder bewusst weggelassen)
- [ ] Badge ist im Dashboard via `type: "custom:<badge-type>"` in der `badges:`-Liste referenziert
- [ ] Eine Resource vom Typ `module` mit der Badge-Modul-URL ist zur Dashboard-Konfiguration hinzugefügt
- [ ] Quality-Scale-Marker: **nicht Teil der HA-Quality-Scale** (außerhalb der Skala)

## Offene Fragen

- **Editor-Pflicht-Tiefe**: `getConfigElement` und `getStubConfig` als SOLLTE oder MUSS? Aktuell SOLLTE — ein fehlendes `getStubConfig` führt zu leeren Default-Badges beim Hinzufügen über den Picker.
- **`LitElement` vs. Vanilla-`HTMLElement`**: Die HA-Doku erlaubt beide. Soll das nolte-Portfolio analog zu `ha/lovelace-card-patterns` Vanilla-JS als Default festschreiben, oder ist `LitElement` für Badges akzeptabel?
- **Auto-Registrierung**: Sollen Badge-Module — analog zur Card-Auto-Registrierung in `ha/lovelace-card-patterns` — aus dem Integration-`www/`-Ordner automatisch registriert werden, statt eine manuelle Resource-Eintragung zu verlangen?
- **Abgrenzung zum Editor-Slug**: Wie tief darf die „Grafische Konfiguration" hier referenzieren, ohne das `config-changed`-Pattern aus `ha/lovelace-card-editor` zu duplizieren?
