# Skill: `ha-card-editor-add`

Status: draft

## Kontext

`ha/lovelace-card-editor` definiert die grafische Konfigurations-Editor-Oberfläche einer Custom Lovelace Card: HA fragt statische Hooks am Card-Type ab — `getConfigElement` für ein Custom-Editor-Element, `getConfigForm` für den eingebauten Form-Editor, `getStubConfig` für eine Default-Config beim Drag-and-Drop. Editor-Element und Card kommunizieren Konfigurationsänderungen über ein `config-changed`-CustomEvent (`bubbles`, `composed`, `detail.config`) zurück ans Dashboard. Bislang ergänzt kein Skill diese Oberfläche; der Basis-Card-Lifecycle (Datei-Layout, `setConfig`, `set hass`, Registrierung) gehört in `ha/lovelace-card-patterns` und wird von `ha-lovelace-card-scaffold` erzeugt.

Dieser Skill ergänzt einen `ha-form`-basierten visuellen Konfigurations-Editor in eine **bestehende** Custom Card: das Editor-Custom-Element (eine `LitElement` mit `setConfig` und einem `render()` über `<ha-form>` mit Schema und `computeLabel`), den Card-Hook `static getConfigElement()`, `static getStubConfig()` für die Default-Config, sowie die Registrierung per `customElements.define` — spec-konform zu `ha/lovelace-card-editor`. Die Generierung ist offline; der Skill deployt nie in eine laufende HA-Instanz.

## Scope

Ergänzung **eines** visuellen `ha-form`-Editors pro Lauf in eine bestehende Custom Card unter `www/` (oder dem deklarierten Card-Pfad): das Editor-Element (`LitElement` mit `setConfig`, `hass`-Setter, `render()` über `<ha-form>` mit `schema`/`.data`/`.computeLabel` und `_valueChanged`-Handler, der `config-changed` dispatcht), `static getConfigElement()` auf der Card-Klasse, `static getStubConfig()` ohne `type:`-Parameter und die `customElements.define`-Registrierung. Der Skill liest `ha/lovelace-card-editor` und validiert.

## Ziele

- Aus einer bestehenden Card und ihrer Konfigurations-Form ein registriertes Editor-Element ableiten und spec-konform ergänzen
- Den `getConfigElement`-Vertrag erzwingen: `static getConfigElement()` gibt ein per `customElements.define` registriertes Element zurück
- Das `config-changed`-Event als alleinigen Rückkanal festschreiben: `bubbles: true`, `composed: true`, neue Config in `event.detail.config`, nur bei tatsächlicher Änderung dispatchen
- Den `ha-form`-Editor mit `schema` (Selektoren bevorzugt), `computeLabel` und — wo das Formular es braucht — `computeHelper`/`assertConfig` verankern
- `getStubConfig()` ohne `type:`-Parameter als Default-Config beim Drag-and-Drop sicherstellen
- Den Editor-Lifecycle wahren: `setConfig(config)` mutiert die Config nicht; Änderungen fließen ausschließlich über `config-changed`

## Nicht-Ziele

- Greenfield-Scaffolding der Card selbst (Datei-Layout, `set hass`, Render, Registrierung) — `ha-lovelace-card-scaffold`
- Basis-Card-Lifecycle und Portfolio-House-Style — `ha/lovelace-card-patterns`
- Entity-Selektor-Filterung (Domain-, Device-Class-, Supported-Features-Filter im Selektor) — `ha/lovelace-card-entity-selector`
- Der eingebaute Form-Editor `getConfigForm` als Alternative zum Custom-Element — referenziert, aber nicht der erzeugte Pfad dieses Skills
- Übersetzungen der Editor-Labels — eigene Achse, `ha/translations`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a config editor to my card", „wire up the ha-form editor", „make my card configurable in the UI"
  - „give my card a visual editor", „add getConfigElement to my card"
  - „füge meiner Card einen Editor hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die existierende Card (Datei/Klassenname), für die der Editor ergänzt wird
- **KANN [MAY]** erfassen: die Konfigurations-Felder und ihre Selektoren (`entity`, `text`, `boolean`, …), den Editor-Element-Tag-Namen und ob `computeHelper`/`assertConfig` nötig sind

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass die Ziel-Card existiert (Card-Datei unter dem deklarierten Card-Pfad, registriert per `customElements.define`); existiert keine Card, an `ha-lovelace-card-scaffold` verweisen und abbrechen
- **MUSS [MUST]** prüfen, dass die Card noch keinen Editor-Hook (`getConfigElement` oder `getConfigForm`) trägt; bei Kollision abbrechen, statt einen zweiten Hook zu ergänzen
- **MUSS [MUST]** die `ha/lovelace-card-editor`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes Editor-Element oder einen bestehenden Tag-Namen überschreiben

### Generierungs-Regeln (aus `ha/lovelace-card-editor`)

- **MUSS [MUST]** ein Editor-Custom-Element als `LitElement` erzeugen, das `setConfig(config)` implementiert und die `hass`-Property als Setter akzeptiert
- **MUSS [MUST]** das Element per `customElements.define("<domain>-<card>-editor", <EditorClass>)` registrieren, mit lowercase-kebab-case und Integration-Domain-Präfix
- **MUSS [MUST]** `static getConfigElement()` auf der Card-Klasse definieren, das `document.createElement("<domain>-<card>-editor")` zurückgibt
- **SOLLTE [SHOULD]** den Editor als `ha-form`-getriebene Oberfläche umsetzen: im `render()` `<ha-form>` mit `.hass`, `.data` (der aktuellen Config), `.schema` (eine Liste, ein Eintrag pro Feld mit `name` und bevorzugt `selector`) und `.computeLabel` rendern und den `value-changed`-Event von `<ha-form>` an einen `_valueChanged`-Handler binden — `<ha-form>` im Custom-Element ist der gewählte Implementierungsweg dieses Skills, nicht von `ha/lovelace-card-editor` für den `getConfigElement`-Pfad vorgeschrieben (dort ist `ha-form` an den eingebauten `getConfigForm`-Pfad gebunden); gegen die offizielle HA-Doku verifizieren
- **MUSS [MUST]** im `_valueChanged`-Handler ein `config-changed`-Event mit `bubbles: true`, `composed: true` und `detail: { config: <neueConfig> }` dispatchen
- **MUSS NICHT [MUST NOT]** `config-changed` feuern, wenn die Config unverändert ist, und **MUSS NICHT [MUST NOT]** die in `setConfig` übergebene Config mutieren (nur lesen / lokal kopieren)
- **MUSS [MUST]** `static getStubConfig()` auf der Card definieren, das eine Default-Config **ohne** den `type:`-Parameter zurückgibt
- **SOLLTE [SHOULD]** `computeLabel(schema)` für feldspezifische Labels bereitstellen; Rückgabe `undefined` überlässt HA die bekannte Übersetzung generischer Feldnamen wie `entity`
- **SOLLTE [SHOULD]** `computeHelper(schema)` für längere Hilfetexte und `assertConfig(config)` (wirft `Error` bei inkompatibler Eingabe) ergänzen, wo das Formular sie braucht
- **SOLLTE [SHOULD]** Selektoren (`{ selector: { entity: {} } }`, `{ selector: { text: {} } }`, …) gegenüber nativen Form-Typen bevorzugen; Selektor-Optionen jenseits der hier genannten gegen `ha-form/types.ts` verifizieren
- **SOLLTE [SHOULD]** das Editor-Element in einer separaten `<card-name>-editor.js`-Datei führen, sobald es nicht-trivial wird — konsistent mit `ha/lovelace-card-patterns`
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: das Editor-Element ist eine `LitElement` mit `setConfig` und `hass`-Setter, per `customElements.define` registriert; `static getConfigElement()` gibt dieses Element zurück; `render()` nutzt `<ha-form>` mit `schema`/`.data`/`.computeLabel`; der Handler dispatcht `config-changed` mit `bubbles`/`composed` und `detail.config`, ohne unveränderte Config zu feuern; `static getStubConfig()` liefert eine Config ohne `type:`; die Card trägt genau einen Editor-Hook
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/lovelace-card-editor` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (außerhalb der HA-Quality-Scale, Frontend-Lieferform)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als einen Editor pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** den Basis-Card-Lifecycle oder die Card selbst (neu) scaffolden — das ist `ha-lovelace-card-scaffold`
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill prüft, dass eine Ziel-Card existiert und noch keinen Editor-Hook trägt, und liest `ha/lovelace-card-editor`
- [ ] Editor-Element ist eine `LitElement` mit `setConfig(config)` und akzeptiert die `hass`-Property
- [ ] Editor-Element ist per `customElements.define` registriert, lowercase-kebab-case mit Integration-Domain-Präfix
- [ ] `static getConfigElement()` auf der Card gibt das registrierte Editor-Element zurück
- [ ] `render()` nutzt `<ha-form>` mit `.data`, `.schema` (ein Eintrag pro Feld mit `name`/`selector`) und `.computeLabel`
- [ ] Der Handler dispatcht `config-changed` mit `bubbles: true`, `composed: true` und `detail.config`, und feuert nicht bei unveränderter Config
- [ ] `static getStubConfig()` liefert eine Default-Config **ohne** `type:`-Parameter
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker (außerhalb der Skala, Frontend-Lieferform)

## Offene Fragen

- **Lit-Verfügbarkeit**: Die Editor-Beispiele der HA-Doku nutzen `LitElement` (typischerweise per CDN/Bundle eingebunden). Wenn die Ziel-Card Vanilla-JS ist (Portfolio-Standard in `ha/lovelace-card-patterns`), bringt der Skill eine Lit-Abhängigkeit ein — soll er stattdessen einen Vanilla-JS-Editor erzeugen oder die Lit-Quelle explizit erfragen? Aktuell folgt er dem Brief (`LitElement`) und weist auf die Abhängigkeit hin.
- **`getConfigForm`-Alternative**: `ha/lovelace-card-editor` zieht für einfache Cards den eingebauten `getConfigForm`-Pfad vor. Wann rät der Skill zu `getConfigForm` statt eines Custom-Elements ab — und ist das ein eigener Generierungspfad? Aktuell erzeugt er den `getConfigElement`-Pfad und nennt `getConfigForm` als Alternative.
- **Selektor-Drift**: `ha-form/types.ts` ist die kanonische Selektor-Quelle, driftet aber über HA-Releases. Welche HA-Frontend-Version pinnt der Skill als Referenz für verfügbare Selektoren?
