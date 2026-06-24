# HA-Integration: Lovelace-Card-Editor (`ha-form`)

Status: draft

## Kontext

Eine Custom Lovelace Card kann mehr liefern als ein YAML-konfigurierbares Render-Target: sie kann ihre eigene grafische Konfigurations-Oberfläche im Dashboard-Card-Editor mitbringen. HA fragt dazu beim Card-Type statische Hooks ab — `getConfigElement` für ein Custom-Editor-Element, `getConfigForm` für den eingebauten Form-Editor (`ha-form`), und `getStubConfig` für eine Default-Config beim Drag-and-Drop aus dem Card-Picker. Editor-Element und Card kommunizieren ihre Konfigurationsänderungen über ein `config-changed`-CustomEvent zurück ans Dashboard.

Diese Spec deckt **ausschließlich** die grafische Konfigurations-Editor-Oberfläche ab. Der Basis-Card-Lifecycle — Datei-Layout unter `www/`, Auto-Registrierung in `__init__.py`, `setConfig`, `set hass`, Shadow-DOM-CSS, `getCardSize`/`getGridOptions` — ist im Schwester-Spec `ha/lovelace-card-patterns` (Portfolio-House-Style, Vanilla-JS) kodifiziert und wird hier **nicht dupliziert**, nur referenziert.

Hinweis zur Basisklasse: Die offiziellen Editor-Beispiele aus der HA-Dokumentation verwenden `LitElement`; der Portfolio-Standard in `ha/lovelace-card-patterns` ist Vanilla-JS. Beide sind gültig — ein Custom-Element bleibt ein Custom-Element. Diese Spec bleibt basisklassen-agnostisch und schreibt weder Lit noch Vanilla-JS für das Editor-Element vor.

Quality-Scale-Marker: Custom Cards sind **nicht Teil der HA-Quality-Scale**; der Card-Editor ist eine Frontend-Lieferform und steht wie das Schwester-Spec außerhalb der Skala.

## Ziele

- Den grafischen Card-Editor als bewusste, getrennte Lieferform der Custom Card etablieren — nicht als Beiwerk des Render-Codes
- `getConfigElement` für nicht-triviale Editoren und `getConfigForm` (`ha-form`) für einfache Konfigurations-Anforderungen klar gegeneinander abgrenzen
- Das `config-changed`-CustomEvent (`bubbles`, `composed`, `detail.config`) als alleinigen Rückkanal vom Editor zum Dashboard festschreiben
- `getStubConfig` für sinnvolle Default-Configs beim Drag-and-Drop aus dem Card-Picker zur Vorgabe machen
- Den `ha-form`-Form-Editor mit Schema (Selektoren), `computeLabel` und `assertConfig` als bevorzugten Weg für einfache Editoren verankern
- Den Card-Vorschlag pro Entity (`getEntitySuggestion`) als opt-in-Mechanismus dokumentieren, ohne den Card-Picker zu verrauschen

## Nicht-Ziele

- Basis-Card-Lifecycle (`setConfig`, `set hass`, Shadow DOM, CSS, `getCardSize`, `getGridOptions`, Auto-Registrierung) — abgedeckt in `ha/lovelace-card-patterns`
- Die vollständige Selektor-Options-Liste — kanonisch im Frontend-Repo unter `ha-form/types.ts`, hier nur referenziert, nicht kopiert
- Übersetzungen der Editor-Labels — eigene Achse, adressiert in `ha/translations`
- Daten-Beschaffung im Editor (`hass`-States, Service-Calls) jenseits der Editor-Lifecycle-Properties — adressiert in `ha/frontend-data-api`
- `tap_action`, `more-info` oder andere Card-Interaktions-Pattern — nicht Teil der grafischen Editor-Oberfläche

## Anforderungen

### `getConfigElement` & Editor-Element

- **MUSS [MUST]** für einen Custom-Editor `static getConfigElement()` auf der Card-Klasse definieren, das ein registriertes Custom-Element zurückgibt (`return document.createElement("<card-editor>")`) — HA zeigt dieses Element im Card-Editor des Dashboards an
- **MUSS [MUST]** das vom Editor zurückgegebene Element vorher per `customElements.define("<card-editor>", <EditorClass>)` registrieren, mit `<card-editor>` in lowercase-kebab-case und Integration-Domain-Präfix
- **SOLLTE [SHOULD]** das Editor-Element in einer separaten `<card-name>-editor.js`-Datei führen, sobald es nicht-trivial wird — konsistent mit `ha/lovelace-card-patterns`
- **SOLLTE NICHT [SHOULD NOT]** `getConfigElement` und `getConfigForm` gleichzeitig auf derselben Card definieren — eines von beiden genügt. HA dokumentiert sie als Alternativen (Custom-Editor-Element *oder* eingebauter Form-Editor), verbietet die Kombination aber nicht; dies ist daher eine Spec-Präferenz für Eindeutigkeit, keine HA-Vorgabe

### `config-changed`-Event

- **MUSS [MUST]** Konfigurationsänderungen aus dem Editor-Element über ein `config-changed`-Event zurück ans Dashboard kommunizieren — das Dashboard hört darauf und übernimmt die neue Config
- **MUSS [MUST]** das Event mit `bubbles: true` und `composed: true` konstruieren, damit es die Shadow-DOM-Grenze des Editors durchquert und das Dashboard erreicht
- **MUSS [MUST]** die neue Konfiguration in `event.detail.config` mitgeben (`event.detail = { config: newConfig }`)
- **MUSS NICHT [MUST NOT]** das `config-changed`-Event bei jedem Tastendruck blind feuern, wenn die Config unverändert ist — nur bei tatsächlicher Konfigurationsänderung dispatchen

### Built-in Form-Editor (`ha-form` + Selektoren)

- **SOLLTE [SHOULD]** für Cards mit relativ einfachen Konfigurations-Anforderungen den eingebauten Form-Editor statt eines Custom-Editor-Elements verwenden — via `static getConfigForm()`, das ein Form-Schema zurückgibt
- **MUSS [MUST]** aus `getConfigForm()` ein Objekt mit dem Pflicht-Key `schema` zurückgeben — eine Liste von Schema-Objekten, eines pro Formularfeld, jeweils mit `name` und (bevorzugt) `selector`
- **SOLLTE [SHOULD]** `computeLabel(schema)` für feldspezifische Labels und `computeHelper(schema)` für längere Hilfetexte unter dem Feld bereitstellen; Rückgabe `undefined` überlässt HA die bekannte Übersetzung generischer Feldnamen wie `entity`
- **SOLLTE [SHOULD]** `assertConfig(config)` definieren, das bei inkompatibler Eingabe einen `Error` wirft — das deaktiviert den visuellen Editor, bis ein Folge-Aufruf wieder fehlerfrei durchläuft
- **SOLLTE [SHOULD]** Selektoren (`{ selector: { entity: {} } }`, `{ selector: { text: {} } }`, …) gegenüber nativen Form-Typen wie `float` oder `boolean` bevorzugen; `grid`- und `expandable`-Container strukturieren komplexere Formulare
- **KANN [MAY]** die vollständige Selektor- und Schema-Options-Liste im Frontend-Repo unter `ha-form/types.ts` nachschlagen — die hier genannten Optionen sind nicht erschöpfend

### `getStubConfig` & Card-Vorschlag

- **SOLLTE [SHOULD]** `static getStubConfig()` definieren, das eine Default-Card-Konfiguration **ohne** den `type:`-Parameter (in JSON-Form) zurückgibt — der Card-Picker nutzt sie beim Drag-and-Drop
- **MUSS NICHT [MUST NOT]** den `type:`-Parameter in das `getStubConfig`-Rückgabeobjekt aufnehmen — der Card-Picker ergänzt ihn selbst
- **KANN [MAY]** die Card über `getEntitySuggestion(hass, entityId)` auf dem `window.customCards`-Eintrag für eine ausgewählte Entity vorschlagen — vorgeschlagene Custom Cards erscheinen im Card-Picker unter einem **Community**-Abschnitt (verfügbar ab HA 2026.6)
- **MUSS [MUST]** aus `getEntitySuggestion` `null` zurückgeben, wenn die Entity von der Card nicht sinnvoll unterstützt wird — die `hass`-Object-Prüfung auf Domain, Device-Class oder Supported-Features entscheidet darüber
- **MUSS [MUST]** in jedem zurückgegebenen Suggestion-Objekt das Pflichtfeld `config` mit dem `type:` inklusive `custom:`-Präfix mitgeben; das optionale `label` nur bei mehreren Varianten setzen
- **MUSS NICHT [MUST NOT]** die Card für jede beliebige Entity vorschlagen — das verrauscht den Picker und führt User zur falschen Card

### Editor-Lifecycle (`setConfig`/`hass`)

- **MUSS [MUST]** im Editor-Element `setConfig(config)` implementieren — HA ruft es beim Setup des Config-Elements auf, um die aktuelle Konfiguration zu übergeben
- **MUSS [MUST]** im Editor-Element die `hass`-Property als Setter akzeptieren — HA aktualisiert sie bei State-Änderungen, ebenso das `lovelace`-Element mit Dashboard-Konfigurations-Informationen
- **MUSS NICHT [MUST NOT]** im Editor-`setConfig` die Card-Konfiguration mutieren — die übergebene Config nur lesen bzw. lokal kopieren und Änderungen ausschließlich über `config-changed` zurückmelden

## Akzeptanzkriterien

- [ ] `static getConfigElement()` gibt ein per `customElements.define` registriertes Editor-Element zurück
- [ ] Editor-Element ist lowercase-kebab-case mit Integration-Domain-Präfix benannt
- [ ] Card definiert bevorzugt nur einen Editor-Hook (`getConfigElement` *oder* `getConfigForm`)
- [ ] Editor dispatcht `config-changed` mit `bubbles: true`, `composed: true` und der neuen Config in `event.detail.config`
- [ ] Bei `getConfigForm`: Rückgabe enthält Pflicht-Key `schema` (eine Liste, ein Eintrag pro Feld mit `name` und `selector`)
- [ ] `computeLabel`/`computeHelper`/`assertConfig` sind vorhanden, wo das Formular sie braucht
- [ ] `static getStubConfig()` liefert eine Default-Config **ohne** `type:`-Parameter
- [ ] `getEntitySuggestion` (falls vorhanden) gibt `null` für nicht unterstützte Entities zurück und setzt `config` inkl. `custom:`-Präfix
- [ ] Editor-Element implementiert `setConfig(config)` und akzeptiert die `hass`-Property
- [ ] Selektor-Options jenseits der hier genannten sind gegen `ha-form/types.ts` verifiziert
- [ ] Quality-Scale-Marker: außerhalb der HA-Quality-Scale (Frontend-Lieferform, portfolio-spezifisch)

## Offene Fragen

- **`getConfigForm` vs. `getConfigElement`-Schwelle**: Ab welcher Konfigurations-Komplexität rechtfertigt sich ein Custom-Editor-Element gegenüber dem eingebauten Form-Editor? Aktuell qualitativ („relativ einfache Anforderungen") — eine harte Heuristik (Feldzahl, verschachtelte Container) fehlt.
- **`getEntitySuggestion`-Mindestversion**: Der Mechanismus ist erst ab HA 2026.6 verfügbar. Wie behandelt das Portfolio Cards, die auf älteren HA-Versionen laufen müssen — Feature-Detection, Hard-Floor auf 2026.6?
- **Selektor-Drift**: `ha-form/types.ts` ist die kanonische Quelle, driftet aber über HA-Releases. Wann pinnt das Portfolio eine HA-Frontend-Version als Referenz für verfügbare Selektoren?
- **Editor-Übersetzungen**: `computeLabel` kann eigene Übersetzungen liefern oder HAs bekannte Feldnamen-Übersetzungen nutzen. Wie greift das mit `ha/translations` ineinander — eigene Label-Übersetzungstabelle pro Card?
- **Editor-Datenkontext**: Das Editor-Element erhält `hass` und `lovelace`. Wie weit darf der Editor `hass`-States lesen (Entity-Vorbefüllung, Validierung), bevor das in `ha/frontend-data-api` gehört?
