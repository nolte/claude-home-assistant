# Skill: `ha-panel-config-view-add`

Status: draft

## Kontext

`ha/lovelace-panel-config-view` definiert die Konfigurations-/Options-Fläche eines Custom-Panels — die Trennung zwischen Deploy-Zeit-`panel.config` (einmal bei Registrierung gesetzt, als `panel.config` gelesen, kein Write-Back) und laufzeit-editierbaren Optionen, die zwei Persistenz-Pfade (ein Custom-WebSocket-Command für Domain-/Shared-State, der `frontend/*_user_data`-Store für Per-User-UI-Präferenzen), die `ha-form` + `ha-selector`-Formular-Komposition und ein Admin-Gating, das serverseitig im Command-Handler durchgesetzt werden muss statt nur in der UI verborgen. Von `ha-panel-add` gescaffoldete Panels rendern Daten, liefern aber häufig gar keine Options-Ansicht — oder eine, die nirgends persistiert (Optionen beim Reload verloren), über den falschen Kanal persistiert (installationsweite Config im Per-User-Store) oder Admin nur im Frontend gatet.

Dieser Skill schließt diese Lücke: Er gibt einem **bestehenden** Panel eine vollständige, korrekte Konfigurations-/Options-Ansicht gemäß `ha/lovelace-panel-config-view` — vervollständigt die fehlenden Teile und validiert sie — und liefert einen Conformance-Report. Er ist das Panel-Config-Pendant zu `ha-card-editor-add` (das den Card-Config-Editor besitzt). Quality-Scale-Marker: Custom-Panels sind **nicht Teil der HA-Quality-Scale**; die Config-Ansicht ist eine Frontend-Lieferform außerhalb der Skala.

## Scope

Das Hinzufügen oder Vervollständigen der Konfigurations-/Options-Ansicht genau eines bestehenden Custom-Panels pro Lauf: jeden konfigurierbaren Wert als Deploy-Zeit-Config oder Laufzeit-Option klassifizieren, das Options-Formular aus `ha-form` + `ha-selector` zusammensetzen, einen Persistenz-Pfad verdrahten (einen Custom-WebSocket-Command via `hass.callWS` oder den `frontend/*_user_data`-Store) und Admin-only-Optionen in der UI gaten sowie serverseitig durchsetzen — dann Offline-Validierung. Der Skill liest `ha/lovelace-panel-config-view`, scaffoldet das Panel nicht und definiert den WebSocket-Command nicht.

## Ziele

- Deploy-Zeit-`panel.config` von laufzeit-editierbaren Optionen trennen, sodass kein Laufzeit-Wert eine YAML-Bearbeitung + Neustart braucht
- Domain-/Shared-Optionen über einen Custom-WebSocket-Command (`hass.callWS`, mit passendem Read- und wo relevant Subscribe-Command) und Per-User-UI-Präferenzen über den `frontend/*_user_data`-Store persistieren
- Das Options-Formular aus wiederverwendeten `ha-form` + `ha-selector`-Selectors statt roher Inputs zusammensetzen
- Admin-only-Optionen in der UI gaten (`require_admin` / `hass.user.is_admin`) und serverseitig im Command-Handler durchsetzen
- Die Evidenz-Tiers der Spec ehren — nie eine `[src]`/`[unsupported]`/`[policy]`-Regel als dokumentierten HA-Fakt präsentieren

## Nicht-Ziele

- Ein brandneues Panel scaffolden — `ha-panel-add`
- Den Backend-WebSocket-Command definieren (Decorator, Schema, `async_register_command`, Subscription-Lifecycle) — `ha-websocket-command-add` / `ha/frontend-websocket-commands`
- Der grafische Card-Config-Editor (`getConfigElement` / `getConfigForm` / `config-changed`) — `ha-card-editor-add` / `ha/lovelace-card-editor`
- Der Backend-Integration-Config-/Options-Flow (`config_flow.py`, `OptionsFlow`) — `ha/config-flow-patterns`
- Panel-Registrierung und der Element-Property-Contract — `ha/lovelace-views-panels`
- Theming, Übersetzungen und Deployen/Importieren in eine laufende HA-Instanz — eigene Achsen / nur Generierung

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** bei Formulierungen wie diesen aktivieren:
  - „add a settings view to my panel", „let users configure my panel", „persist my panel options", „add an options page to the custom panel"
  - „füge dem Panel eine Konfigurationsansicht hinzu", „das Panel soll Einstellungen speichern"
- **MUSS NICHT [MUST NOT]** für das Scaffolden eines neuen Panels (`ha-panel-add`), das Definieren des WebSocket-Commands (`ha-websocket-command-add`), den Card-Config-Editor (`ha-card-editor-add`) oder den Backend-Integration-Options-Flow (`ha/config-flow-patterns`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root)
- **KANN [MAY]** erfassen: `panel_file` (sonst entdeckt), `options` (die zu exponierenden Felder, jeweils Deploy-Zeit vs. Laufzeit klassifiziert), `persistence` (pro Options-Gruppe — Shared-WebSocket-Command vs. Per-User-User-Data-Store) und `admin_only` (welche Optionen Admin-only sind)

### Pre-Flight (in Reihenfolge — bei erstem Fehlschlag abbrechen)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo ist, und das Panel-JS-Modul lokalisieren; sein Element, `panel`/`panel.config`-Reads, `route`-Handling und jede bestehende Options-UI oder `hass.callWS`-Nutzung lesen
- **MUSS [MUST]** `ha/lovelace-panel-config-view` vor dem Generieren lesen und seine `[doc]`/`[src]`/`[unsupported]`/`[policy]`-Tiers ehren

### Generierungs-Regeln

- **MUSS [MUST]** jeden konfigurierbaren Wert als Deploy-Zeit-Config (→ `panel.config`) oder Laufzeit-Option (→ ein Persistenz-Pfad) klassifizieren; **MUSS NICHT [MUST NOT]** einen Wert, den der User zur Laufzeit ändert, hinter einer `configuration.yaml`-Bearbeitung + Neustart lassen
- **MUSS [MUST]** `panel.config` zur Laufzeit als `panel.config` lesen und **MUSS NICHT [MUST NOT]** es im Element mutieren, um State zu persistieren (`[unsupported]` kein dokumentierter Write-Back-Pfad)
- **MUSS [MUST]** Domain-/Shared-Optionen über einen Custom-WebSocket-Command, aufgerufen mit `hass.callWS`, persistieren, mit passendem Read- (und wo relevant Subscribe-) Command, und **MUSS NICHT [MUST NOT]** dafür einen Ad-hoc-HTTP-Endpoint oder Datei-Write erfinden
- **KANN [MAY]** Per-User-UI-Präferenzen über den `frontend/*_user_data`-Store persistieren und **MUSS NICHT [MUST NOT]** installationsweite Config dort ablegen (er ist pro User gekeyt)
- **MUSS [MUST]** das Options-Formular aus `ha-form`, gebunden an ein Schema aus `ha-selector`-Selector-Configs, zusammensetzen und HA-Selectors gegenüber rohen Inputs wiederverwenden
- **MUSS [MUST]** Admin-only-Controls in der UI auf `hass.user.is_admin` gaten **und** Admin-only-Writes serverseitig im Command-Handler durchsetzen (`require_admin` und `hass.user.is_admin` sind nur Frontend-Gates)
- **MUSS [MUST]** Identifier gemäß `ha/naming-conventions` benennen und HA-Internas gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: jeder Wert ist klassifiziert; `panel.config` wird nicht zum Persistieren mutiert; Shared-Optionen laufen über einen WebSocket-Command mit Read-Pfad; Per-User-Präferenzen laufen über den User-Data-Store; das Formular nutzt `ha-form`/Selectors; Admin-only-Writes sind serverseitig durchgesetzt
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Report liefern, verankert an den Akzeptanzkriterien von `ha/lovelace-panel-config-view`, plus die geänderten Dateipfade und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**)

### Verbote

- **MUSS NICHT [MUST NOT]** ein neues Panel scaffolden oder den WebSocket-Command selbst definieren
- **MUSS NICHT [MUST NOT]** eine Laufzeit-Option über `panel.config`-Mutation oder eine `configuration.yaml`-Bearbeitung persistieren
- **MUSS NICHT [MUST NOT]** Admin-only-Writes nur im Frontend durchsetzen (serverseitige Durchsetzung ist Pflicht)
- **MUSS NICHT [MUST NOT]** eine `[src]`/`[unsupported]`/`[policy]`-Regel als dokumentierten HA-Fakt präsentieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] Jeder konfigurierbare Wert ist Deploy-Zeit-`panel.config` vs. Laufzeit-Option klassifiziert; keine Laufzeit-Option braucht eine YAML-Bearbeitung + Neustart
- [ ] `panel.config` wird als `panel.config` gelesen und nie zum Persistieren von State mutiert
- [ ] Domain-/Shared-Optionen persistieren über einen Custom-WebSocket-Command (`hass.callWS`) mit passendem Read- (und wo relevant Subscribe-) Command
- [ ] Per-User-UI-Präferenzen persistieren über den `frontend/*_user_data`-Store, und keine installationsweite Config wird dort abgelegt
- [ ] Das Options-Formular ist aus `ha-form` + `ha-selector`-Selectors zusammengesetzt, nicht aus rohen Inputs
- [ ] Admin-only-Optionen sind in der UI gegatet und serverseitig im Command-Handler durchgesetzt
- [ ] Der Report ist an `ha/lovelace-panel-config-view` verankert, benennt die geänderten Dateien und markiert nicht-Teil-der-Quality-Scale
- [ ] `[src]`/`[unsupported]`/`[policy]`-Regeln werden nicht als dokumentierte HA-Fakten präsentiert

## Offene Fragen

- **WebSocket-Command-Kopplung**: der Persistenz-Command gehört `ha-websocket-command-add` / `ha/frontend-websocket-commands`. Wenn das Panel noch keinen Command hat, übergibt dieser Skill die Backend-Hälfte an `ha-websocket-command-add`, oder scaffoldet er einen Stub und delegiert die Definition?
- **`route`-Sub-Route vs. Same-Page-Region**: die Domain-Spec lässt `route`-getriebenes Sub-Routing als Offene Frage (source-verifiziert). Sollte dieser Skill per Default eine Same-Page-Options-Region wählen und `route` nur nutzen, wenn das Panel bereits routet?
- **Statische Prüfbarkeit des serverseitigen Admin-Gatings**: die Regel „Admin serverseitig durchsetzen" spannt den Frontend-Call und den Backend-Handler. Kann dieser Skill den Handler-Check verifizieren, oder ihn nur für `ha-websocket-command-add` zur Durchsetzung flaggen?
