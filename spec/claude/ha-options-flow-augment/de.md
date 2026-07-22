# Skill: `ha-options-flow-augment`

Status: draft

## Kontext

Der initiale Scaffold (`ha-integration-scaffold`) liefert einen Basis-`OptionsFlow`, und `ha-coordinator-add` erweitert ihn um die eine Option, die er besitzt — das Coordinator-Poll-Intervall. Aber eine reale Integration wächst um Post-Setup-Einstellungen — ein Toggle, ein Schwellwert, ein Anzeige-Modus, ein Feature-Schalter — und es gibt keinen Skill, der eine *generische* Option in eine bestehende Integration nachrüstet. Diese Lücke zwingt den Entwickler zum Hand-Editieren des Options-Flows, wo die häufigen Fehler sind: die Option in `entry.data` statt `entry.options` speichern, sie ohne sicheren Default lesen und den Entry-Reload vergessen, wenn die Option das Setup ändert.

Dieser Skill schließt die Lücke: Er ergänzt **eine** generische Config-Option in den `OptionsFlow` einer bestehenden Integration, gespeichert in `entry.options`, mit typisiertem Selector, `strings.json`-/Translation-Einträgen, der Reload-on-Change-Verdrahtung und einem Test — non-destruktiv. Er ist die Options-Flow-Schwester von `ha-config-flow-augment` (das die Setup-Zeit-Config-Flow-Patterns besitzt). Quality-Scale-Marker: Options-Flow ist keine eigenständige Quality-Scale-Regel, aber Post-Setup-Konfigurierbarkeit stützt die Silver/Gold-User-Experience; der Skill steht außerhalb eines spezifischen Tiers.

## Scope

Ergänzung genau einer Post-Setup-Option pro Lauf in eine bestehende `custom_components/<domain>/`-Integration: der `OptionsFlow` (via `async_get_options_flow` erzeugt, falls nicht vorhanden, sonst dessen `async_step_init`-Schema erweitert) mit typisiertem Selector für den neuen `option_key`, die `entry.options`-Speicherung und der Safe-Default-Runtime-Read, die Reload-on-Change-Verdrahtung (`entry.add_update_listener` + `async_reload`), wenn die Option das Setup betrifft, die `options.step.init.data.<key>`-Strings + Translations, und ein Options-Flow-Test. Der Skill liest keine Setup-Zeit-`entry.data`, entscheidet `reload_on_change` und validiert offline.

## Ziele

- Eine generische Post-Setup-Option nachrüsten, ohne den User durch den initialen Scaffold zu zwingen, abgegrenzt von `ha-config-flow-augment` (Setup-Patterns) und `ha-coordinator-add` (die Poll-Intervall-Option)
- Die Option über `entry.options` mit sicherem Default speichern und lesen, nie `entry.data`
- Einen typisierten Selector für die Option nutzen statt eines Free-Strings, wenn ein bounded Type passt
- Den Entry-Reload verdrahten, wenn die Option das Setup betrifft, oder explizit angeben, dass ein Live-Read keinen Reload braucht
- Code, Strings, Translations und einen Test zusammen liefern — kein halbes Augment

## Nicht-Ziele

- Greenfield-Scaffold und der Basis-Options-Flow — `ha-integration-scaffold`
- Config-Flow-**Setup**-Patterns (Tenant-Step, Reauth, Reconfigure, Zeroconf, OAuth) — `ha-config-flow-augment`
- Die Coordinator-**Poll-Intervall**-Option speziell — `ha-coordinator-add` (besitzt sie)
- `entry.data`/`entry.options`-Form-Migration über einen Version-Bump — `ha-config-entry-migrate`
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add an option for X to the integration", „let the user configure X after setup", „retrofit an options flow"
  - „füge eine Option für X hinzu", „erweitere den Options-Flow"
- **MUSS NICHT [MUST NOT]** für Greenfield-Scaffold (`ha-integration-scaffold`), Setup-Zeit-Config-Flow-Patterns (`ha-config-flow-augment`) oder die Coordinator-Poll-Intervall-Option (`ha-coordinator-add`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root), `option_key` (lowercase snake_case), `option_type` (Selector/bounded Type) und `default`
- **KANN [MAY]** erfassen: `reload_on_change` (sonst abgeleitet und bestätigt) und ein `label`

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo mit sauberem Working-Tree ist und `custom_components/<domain>/config_flow.py` existiert; `domain` aus `manifest.json` lesen
- **MUSS NICHT [MUST NOT]** fortfahren, wenn `option_key` bereits im Options-Schema existiert — mit „option already present" abbrechen

### Generierungs-Regeln

- **MUSS [MUST]** die Option über `entry.options` speichern und lesen, nie `entry.data`; Runtime-Reads nutzen `entry.options.get(<key>, <default>)` mit einem zum Schema passenden Default
- **MUSS [MUST]** `async_get_options_flow(config_entry)` erzeugen, das einen `OptionsFlow` zurückgibt, falls nicht vorhanden, sonst das bestehende `async_step_init`-Schema erweitern; einen typisierten Selector nutzen (nie einen Free-String, wenn ein bounded Type passt)
- **MUSS [MUST]** die Reload-on-Change-Verdrahtung setzen, wenn die Option das Setup betrifft — `entry.async_on_unload(entry.add_update_listener(_async_update_listener))` mit einem Listener, der `await hass.config_entries.async_reload(entry.entry_id)` aufruft — oder explizit angeben, dass eine Live-Read-Option keinen Reload braucht
- **MUSS [MUST]** `options.step.init.data.<key>` und `data_description.<key>` in `strings.json` und allen `translations/<lang>.json` ergänzen, und einen Options-Flow-Test in `tests/test_config_flow.py`, der die Option setzt und assertet, dass sie in `entry.options` landet
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: die Option ist in `entry.options` (nicht `entry.data`); der Selector ist typisiert; der Runtime-Read trägt einen sicheren Default; die Reload-Verdrahtung ist vorhanden, wenn `reload_on_change`; Strings, Translations und der Test sind vorhanden
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an diese Akzeptanzkriterien plus die geänderten Datei-Pfade anknüpft

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Option pro Lauf ergänzen oder einen bestehenden Option-Key/-Wert überschreiben
- **MUSS NICHT [MUST NOT]** die Option in `entry.data` speichern
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] Die Option ist in `entry.options` gespeichert und daraus mit sicherem Default gelesen; `entry.data` ist unberührt
- [ ] Der `OptionsFlow` ist erzeugt (`async_get_options_flow`) oder sein Schema um einen typisierten Selector erweitert
- [ ] Reload-on-Change ist verdrahtet, wenn die Option das Setup betrifft, oder eine No-Reload-Notiz ist für eine Live-Read-Option angegeben
- [ ] `strings.json` + alle `translations/<lang>.json` tragen `options.step.init.data.<key>` (+ `data_description`)
- [ ] Ein Options-Flow-Test setzt die Option und assertet `entry.options[<key>]`
- [ ] Der Bericht benennt die geänderten Datei-Pfade; bestehende Optionen bleiben unverändert

## Offene Fragen

- **Multi-Option-Batches**: Ein Lauf ergänzt eine Option. Wenn mehrere Optionen auf einmal ergänzt werden, lohnt ein Batch-Modus, oder hält Eine-pro-Lauf die Review-Fläche sauber?
- **Reload-Heuristik**: `reload_on_change` wird abgeleitet und bestätigt. Gibt es eine kodifizierbare Regel, welche Options-Klassen immer/nie einen Reload brauchen?
- **Selector-Abdeckung**: Der Skill mappt `option_type` auf einen Selector. Welche HA-Selectors sind im Default-Mapping, und wann gewinnt ein bespoke `vol`-Schema gegen ein `selector({...})`?
