# Skill: `ha-card-preview-add`

Status: draft

## Kontext

`ha/lovelace-card-preview` definiert die zwei Preview-Flächen einer Custom Lovelace Card — das Card-Picker-Gallery-Tile (eine Live-Preview, wenn `preview: true` im `window.customCards`-Eintrag gesetzt ist, sonst `description`-Text) und die Editor-Live-Preview (`hui-card` an die aktuelle Config gebunden, re-gerendert bei `config-changed`) — plus die `preview`-Element-Property, die HA im Editor-Preview-Kontext setzt, und die Preview-Korrektheits-Regeln des Portfolios (keine echten Side-Effects während der Preview, ein graziöser Placeholder statt eines geworfenen Renders). Der Scaffold (`ha-lovelace-card-scaffold`) setzt `preview` und `getStubConfig` bei Greenfield, aber bestehende Cards liefern regelmäßig eine unvollständige oder kaputte Preview: `preview` fehlt, sodass der Picker nur Text zeigt, kein `getStubConfig`, sodass das Tile eine Fehler-Card rendert, ein Render, der späteres `setConfig` ignoriert, sodass die Editor-Preview einfriert, oder ein un-geguardetes `callService`, das eine echte Action während der Preview feuert.

Dieser Skill schließt die Lücke: Er macht die Preview einer **bestehenden** Card vollständig und korrekt gemäß `ha/lovelace-card-preview` — vervollständigt die fehlenden Preview-Teile und validiert sie — und liefert einen Konformitäts-Bericht. Er ist die Preview-Schwester von `ha-card-editor-add` (das den Config-Editor besitzt). Quality-Scale-Marker: Custom Cards sind **nicht Teil der HA-Quality-Scale**; die Preview ist eine Frontend-Lieferform außerhalb der Skala.

## Scope

Sicherstellung der Preview genau einer bestehenden Custom Card pro Lauf: das `window.customCards`-`preview`-Flag (wenn eine Live-Picker-Preview beabsichtigt ist), ein `getStubConfig`, das eine `setConfig`-valide Config zurückgibt, ein Render deterministisch aus `setConfig`/`hass` für die Editor-Live-Preview, das Lesen der `preview`/`editMode`-Element-Property, das Guarden echter Service-Calls/Actions hinter dieser Property, und ein graziöser Placeholder statt eines geworfenen Renders — dann Offline-Validierung. Der Skill liest `ha/lovelace-card-preview`, scaffoldet die Card nicht und baut den Editor nicht.

## Ziele

- Die Card-Picker-Preview einer bestehenden Card echt machen — `preview: true` plus ein `setConfig`-valides `getStubConfig`, sodass das Tile eine Live-Preview ist, keine Fehler-Card oder bloßer Text
- Die Editor-Live-Preview der Config folgen lassen — ein Render deterministisch aus `setConfig`/`hass`, der jedes `config-changed` widerspiegelt
- Die `preview`- (und Legacy-`editMode`-)Property lesen, um den Editor-Preview-Kontext zu erkennen
- Preview-Korrektheit erzwingen — kein echter Service-Call/keine Action/kein Side-Effect während der Preview, und ein graziöser Placeholder statt eines geworfenen Renders bei fehlender Entity oder unvollständiger Config
- Die Evidenz-Tiers der Spec honorieren — nie eine `[src]`/`[policy]`-Regel als dokumentierten HA-Fakt darstellen

## Nicht-Ziele

- Eine brandneue Card scaffolden — `ha-lovelace-card-scaffold`
- Der grafische Config-Editor (`getConfigElement` / `getConfigForm`) und das `getStubConfig`-Feld-Detail — `ha-card-editor-add` / `ha/lovelace-card-editor`
- Card-Sizing / Grid / Layout — `ha/lovelace-layout-antipatterns`
- Theming und Translations — eigene Achsen
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „make my card show a preview in the card picker", „the card preview is broken / empty", „ensure the card preview is implemented correctly"
  - „füge eine Vorschau für die Card hinzu", „die Card-Vorschau funktioniert nicht"
- **MUSS NICHT [MUST NOT]** für das Scaffolden einer neuen Card (`ha-lovelace-card-scaffold`), das Bauen des Config-Editors (`ha-card-editor-add`) oder Card-Layout/-Sizing (`ha/lovelace-layout-antipatterns`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root)
- **KANN [MAY]** erfassen: `card_file` (sonst entdeckt), `picker_preview` (Default `true`) und `stub_entity` (eine stabile Demo-/repräsentative Entity oder Placeholder für `getStubConfig`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo ist, und das Card-JS-Modul lokalisieren; dessen `window.customCards`-Push, `setConfig`, Render und ein etwaiges `getStubConfig` lesen
- **MUSS [MUST]** `ha/lovelace-card-preview` vor der Generierung lesen und dessen `[doc]`/`[src]`/`[policy]`-Tiers honorieren

### Generierungs-Regeln

- **MUSS [MUST]** `preview: true` im `window.customCards`-Eintrag setzen, wenn `picker_preview`, und `description` als Fallback-Text gesetzt lassen
- **MUSS [MUST]** sicherstellen, dass ein `getStubConfig` eine Config zurückgibt, die das `setConfig` der Card akzeptiert (eine repräsentative `stub_entity` oder Placeholder), sodass das `preview: true`-Tile ohne Fehler-Card rendert
- **MUSS [MUST]** den Render deterministisch aus `setConfig`/`hass` halten, sodass die Editor-Live-Preview jedes `config-changed` widerspiegelt; **MUSS NICHT [MUST NOT]** First-Render-State cachen, der ein späteres `setConfig` ignoriert
- **MUSS [MUST]** die `preview`-Element-Property (und den Legacy-`editMode`-Alias) lesen, um den Editor-Preview-Kontext zu erkennen, und **MUSS NICHT [MUST NOT]** annehmen, dass das Picker-Tile `preview` setzt
- **MUSS [MUST]** jeden echten Service-Call / jede Action / jeden Side-Effect hinter einem `!preview && !editMode`-Check guarden (`[policy]` keine Side-Effects während der Preview), und **MUSS [MUST]** einen graziösen Placeholder rendern statt zu werfen bei fehlender Entity oder unvollständiger Config
- **MUSS NICHT [MUST NOT]** das Picker-Tile über `getCardSize`/`getGridOptions` dimensionieren (`[src]` das Gallery-Tile ist CSS-gesteuert)
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: das `preview`-Flag ist vorhanden, wenn beabsichtigt; `getStubConfig` gibt eine `setConfig`-valide Config zurück; der `preview`/`editMode`-Guard umschließt jeden Side-Effect; eine Missing-Entity-/unvollständige Config rendert einen Placeholder, keinen Throw
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an die `ha/lovelace-card-preview`-Akzeptanzkriterien plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**nicht Teil der HA-Quality-Scale**) anknüpft

### Verbote

- **MUSS NICHT [MUST NOT]** eine neue Card scaffolden oder den Config-Editor bauen
- **MUSS NICHT [MUST NOT]** einen echten Side-Effect un-geguarded lassen, sodass er während der Preview feuert
- **MUSS NICHT [MUST NOT]** eine `[src]`/`[policy]`-Regel als dokumentierten HA-Fakt darstellen
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] `preview: true` ist in `window.customCards` gesetzt, wenn eine Live-Picker-Preview beabsichtigt ist; `description` ist als Fallback erhalten
- [ ] `getStubConfig` gibt eine Config zurück, die das `setConfig` der Card akzeptiert (repräsentative Entity/Placeholder)
- [ ] Der Render ist deterministisch aus `setConfig`/`hass`; die Editor-Live-Preview spiegelt jedes `config-changed`
- [ ] Die Card liest die `preview`- (und Legacy-`editMode`-)Property; das Picker-Tile wird nicht als setzend angenommen
- [ ] Jeder echte Service-Call/jede Action ist geguarded, sodass keiner während der Preview feuert; eine Missing-Entity-/unvollständige Config rendert einen Placeholder, keinen Throw
- [ ] Der Bericht ist an `ha/lovelace-card-preview` verankert, benennt die geänderten Dateien und markiert nicht-Teil-der-Quality-Scale
- [ ] `[src]`/`[policy]`-Regeln werden nicht als dokumentierte HA-Fakten dargestellt

## Offene Fragen

- **Statische Durchsetzbarkeit der Preview-Korrektheit**: Die No-Side-Effects-Regel ist `[policy]`. Kann der Skill sie per Grep nach `callService`/Action-Calls ohne `preview`/`editMode`-Guard verifizieren, oder braucht es einen gerenderten Check?
- **`preview` vs. `editMode`-Floor**: `editMode` ist ein Rückwärtskompatibilitäts-Alias. Wann kann der Skill nur den `preview`-Read emittieren und `editMode` fallenlassen (welcher HA-Frontend-Floor)?
- **Editor-Kopplung**: `getStubConfig`-Detail gehört `ha-card-editor-add` / `ha/lovelace-card-editor`. Wenn die Card gar keinen Editor hat, ergänzt dieser Skill trotzdem `getStubConfig`, oder übergibt er an `ha-card-editor-add`?
