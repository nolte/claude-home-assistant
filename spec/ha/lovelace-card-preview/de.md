# HA-Integration: Lovelace-Card-Preview

Status: draft

## Kontext

Eine Custom Lovelace Card wird in **zwei** Preview-Flächen gezeigt, und sie richtig hinzubekommen ist das, was eine Card im Dashboard fertig wirken lässt:

1. Das **Card-Picker-Gallery-Tile** — wenn die Card `preview: true` in ihrem `window.customCards`-Eintrag registriert, rendert der Picker eine **Live-Instanz** der Card im Tile; sonst zeigt das Tile nur den `description`-Text der Card.
2. Die **Editor-Live-Preview** — während der User die Card editiert (`getConfigElement` / `getConfigForm`), rendert HA eine Live-`hui-card`-Preview, an die aktuelle Config gebunden, und re-rendert sie bei jedem `config-changed`-Event.

Beide Previews rendern die Card über ihren normalen `setConfig` / `set hass`-Lifecycle; die Config, die das Picker-Tile rendert, kommt aus `getStubConfig`. In der **Editor**-Preview setzt HA zusätzlich eine boolean `preview`-Property (und, für Rückwärtskompatibilität, eine Legacy-`editMode`-Property) auf das Card-Element, damit die Card weiß, dass sie previewt wird, und sich anpassen kann.

Diese Spec deckt das **Preview-Verhalten spezifisch** ab. Sie grenzt gegen ihre Geschwister ab und referenziert sie per Slug, statt zu duplizieren: Der Basis-Card-Lifecycle (`setConfig`, `set hass`, Shadow DOM, `getCardSize`/`getGridOptions`, `window.customCards`-Registrierung, `getStubConfig`) ist `ha/lovelace-card-patterns`; das Editor-Element, `getConfigElement`/`getConfigForm`, `config-changed` und `getStubConfig`-Detail sind `ha/lovelace-card-editor`; Card-Sizing/Layout ist `ha/lovelace-layout-antipatterns`.

**Evidenz-Tiers.** HA-interne Fakten müssen gegen die offizielle Doku verifiziert werden, nicht aus dem Gedächtnis behauptet (`ha/upstream-docs-verification`). Das Preview-Surface ist in der offiziellen Doku ungewöhnlich dünn — die Developer-Card-Doku erwähnt `preview` nur als Inline-`preview: false // Optional`-Kommentar und dokumentiert keine Card-Element-`preview`-Property und keine Preview-Korrektheits-Regeln. Jede Regel unten ist getaggt:

- `[doc]` — in der offiziellen Developer-Doku belegt (`developers.home-assistant.io/docs/frontend/custom-ui/custom-card/`); zitiert oder paraphrasiert.
- `[src]` — gegen den HA-Frontend-Quellcode (`github.com/home-assistant/frontend`) verifiziert, weil die Doku schweigt; die Quelle ist die Autorität für den exakten Identifier/das Verhalten.
- `[policy]` — eine nolte-Portfolio-Regel (z. B. Preview-Korrektheit); **keine** HA-dokumentierte Anforderung, als solche gekennzeichnet.

Quality-Scale-Marker: Custom Cards sind **nicht Teil der HA-Quality-Scale**; die Preview ist ein Frontend-Lieferform-Belang und steht außerhalb der Skala.

## Ziele

- Die Card-Picker-Preview bewusst machen — `preview: true` plus ein `getStubConfig`, das ein echtes, nicht-fehlerhaftes Tile rendert — statt das Tile per Default als bloßen Description-Text zu belassen
- Die Editor-Live-Preview verlässlich machen — ein Render deterministisch aus `setConfig`/`hass`, sodass die Preview die aktuelle Config bei jedem `config-changed` sofort widerspiegelt
- Etablieren, dass die Card die `preview`- (und Legacy-`editMode`-)Property liest, um den Editor-Preview-Kontext zu erkennen
- Echte Side-Effects (Service-Calls, Actions) während der Preview verbieten und einen graziösen Placeholder statt eines geworfenen Errors bei unvollständiger oder Empty-Entity-Config verlangen — die Preview-Korrektheits-Latte des Portfolios
- HA-Fakten, Frontend-Quellcode-Fakten und Portfolio-Policy sauber trennen, sodass keine Regel auf einer undokumentierten Annahme beruht, die als dokumentiert dargestellt wird

## Nicht-Ziele

- Der Basis-Card-Lifecycle und die `window.customCards`-Registrierungs-Mechanik — `ha/lovelace-card-patterns`
- Das Editor-Element, `getConfigElement`/`getConfigForm`, der `config-changed`-Vertrag und das `getStubConfig`-Feld-Detail — `ha/lovelace-card-editor` (diese Spec referenziert sie für den Preview-Effekt, nicht ihre Definition)
- Card-Sizing und Grid-/Layout-Verhalten — `ha/lovelace-layout-antipatterns` und `ha/lovelace-card-patterns`
- Theming, Translations und `getEntitySuggestion` (der Community-Card-Suggestion-Mechanismus) — eigene Achsen
- Custom Panels und ihre Config-/Options-Ansicht — ein eigenes Frontend-Surface

## Anforderungen

### Card-Picker-Preview (`window.customCards` `preview`)

- **MUSS [MUST]** `preview: true` im `window.customCards`-Eintrag der Card setzen, wenn die Card eine **Live-Preview** im Card-Picker rendern soll — `[doc]` dokumentiert das Feld (`preview: false // Optional - defaults to false`); `[src]` der Picker mappt `preview` auf `showElement` und instanziiert nur dann ein echtes Card-Element im Tile, sonst rendert er den `description`-Text (`hui-card-picker.ts`)
- **MUSS [MUST]** ein `getStubConfig` (gemäß `ha/lovelace-card-editor`) bereitstellen, das eine Config zurückgibt, die das `setConfig` der Card akzeptiert, sodass das `preview: true`-Tile eine echte, nicht-fehlerhafte Preview rendert statt einer Fehler-Card — `[src]` der Picker baut die Config des Preview-Elements aus `getStubConfig`, wenn keine explizite Config übergeben wird
- **SOLLTE [SHOULD]** `description` in jedem Fall setzen — es ist der Picker-Tile-Fallback-Text, wenn `preview` `false` ist, und der Hilfe-Text im Card-Editor `[doc]`
- **MUSS NICHT [MUST NOT]** sich auf `getCardSize()` / `getGridOptions()` verlassen, um das **Picker-Tile** zu dimensionieren — das Gallery-Tile ist CSS-gesteuert, nicht durch diese Methoden dimensioniert; sie steuern die Editor-Preview und das echte Dashboard, nicht das Picker-Tile `[src]`

### Editor-Live-Preview & `config-changed`

- **MUSS [MUST]** den Render der Card deterministisch aus `setConfig(config)` und dem `hass`-Setter halten, sodass die Live-`hui-card`-Preview des Editors die aktuelle Config sofort widerspiegelt — HA re-rendert die Preview, wann immer der Editor `config-changed` dispatcht `[doc]` (Vertrag detailliert in `ha/lovelace-card-editor`)
- **MUSS NICHT [MUST NOT]** First-Render-State so cachen, dass ein späteres `setConfig` ignoriert wird — die Live-Preview spielt `setConfig` beim Editieren erneut ab, sodass eine von der Card ignorierte Config-Änderung die Preview kaputt aussehen lässt `[src]`
- **SOLLTE [SHOULD]** sich auf die Entity-Change-Detection aus `ha/lovelace-card-patterns` verlassen, sodass die Live-Preview bei Config-/State-Änderung re-rendert ohne blankes Re-Render bei jedem `hass`-Tick

### Die `preview`-Element-Property (Editor-Kontext)

- **MUSS [MUST]** die boolean `preview`-Property lesen, die HA auf das Card-Element setzt, um den **Editor-Preview**-Kontext zu erkennen — `[src]` der `hui-card`-Wrapper setzt `element.preview` (`true` im `<hui-card … preview>` des Edit-Card-Dialogs); diese Property ist **nicht** in der offiziellen Doku
- **SOLLTE [SHOULD]** auch die Legacy-`editMode`-Property honorieren, die HA „for backwards compatibility" auf denselben Wert setzt, wenn die Card auf älteren Frontends laufen muss `[src]`
- **MUSS NICHT [MUST NOT]** annehmen, dass das **Picker-Gallery-Tile** `preview` setzt — `[src]` der Picker-Pfad setzt nur `hass` auf das Tile-Element, nicht `preview`; nur die Editor-Preview setzt es. Eine Card, die sich im Picker-Tile speziell verhalten muss, kann diesen Kontext daher nicht über `preview` erkennen

### Preview-Korrektheit `[policy]`

- **MUSS NICHT [MUST NOT]** einen echten Service-Call, eine Action oder einen anderen extern-sichtbaren Side-Effect ausführen, während `preview` (oder das Legacy-`editMode`) `true` ist — eine Preview darf nie ein echtes Gerät schalten, ein Formular absenden oder ein Backend aufrufen. `[policy]` — die HA-Doku erzwingt keine solche Regel; die `preview`/`editMode`-Property existiert genau, damit eine Card das *unterdrücken kann*, und das Portfolio macht die Unterdrückung verpflichtend
- **SOLLTE [SHOULD]** repräsentativen, in-sich-geschlossenen Inhalt in der Preview rendern — ein `getStubConfig`, das auf eine stabile Demo-Entity zeigt (oder synthetisierte Placeholder-Daten), sodass Picker-Tile und Editor-Preview sinnvoll aussehen, bevor der User eine echte Entity wählt `[policy]`
- **MUSS [MUST]** einen graziösen Placeholder (eine „Entity nicht gefunden" / „konfiguriere mich"-Meldung) rendern statt zu **werfen**, wenn die Stub- oder Live-Config unvollständig ist oder die referenzierte Entity fehlt/unavailable ist — ein geworfener Render in der Preview erscheint als kaputtes Tile `[policy]`, konsistent mit dem Missing-Entity-Handling der HA-Beispiel-Card `[doc]`

## Acceptance Criteria

- [ ] Die Card setzt `preview: true` in ihrem `window.customCards`-Eintrag, wenn eine Live-Picker-Preview beabsichtigt ist (sonst fällt sie bewusst auf `description`-Text zurück)
- [ ] Ein `getStubConfig` gibt eine Config zurück, die das `setConfig` der Card akzeptiert, sodass das `preview: true`-Tile ohne Fehler-Card rendert
- [ ] Der Render ist deterministisch aus `setConfig`/`hass`; die Editor-Live-Preview spiegelt jedes `config-changed` wider, ohne späteres `setConfig` zu ignorieren
- [ ] Die Card liest die `preview`-Property (und, wo nötig, Legacy-`editMode`), um den Editor-Preview-Kontext zu erkennen
- [ ] Kein echter Service-Call / keine Action / kein Side-Effect feuert, während `preview` (oder `editMode`) `true` ist
- [ ] Eine unvollständige oder Missing-Entity-Preview rendert einen graziösen Placeholder, nie einen geworfenen Render
- [ ] Picker-Tile-Sizing wird nicht als `getCardSize`/`getGridOptions`-folgend angenommen
- [ ] Jede Regel ist `[doc]` / `[src]` / `[policy]` getaggt; Frontend-Quellcode- und Portfolio-Fakten werden nicht als dokumentierte HA-Fakten dargestellt
- [ ] Quality-Scale-Marker: nicht Teil der HA-Quality-Scale (Frontend-Lieferform)

## Offene Fragen

- **Picker-Preview vs. Editor-Preview-Divergenz**: Die `preview`-Element-Property wird nur in der Editor-Preview gesetzt, nicht im Picker-Tile (`[src]`). Sollte eine Card „Ich bin das Picker-Gallery-Tile" überhaupt erkennen können, oder ist das bewusst opak? Kein HA-Mechanismus legt es heute offen.
- **`getStubConfig` als harte Preview-Anforderung**: Die Regel „ein valides `getStubConfig` ist für ein nicht-fehlerhaftes `preview: true`-Tile erforderlich" ist eine Source-Level-Inferenz, keine dokumentierte HA-Regel. Gibt es einen Fall, in dem `preview: true` ohne `getStubConfig` sinnvoll rendert?
- **`preview` vs. `editMode`-Lebensdauer**: `editMode` ist in der Quelle als Rückwärtskompatibilitäts-Alias dokumentiert. Wann kann das Portfolio den `editMode`-Read fallenlassen und sich allein auf `preview` verlassen (welcher HA-Frontend-Floor)?
- **Preview-Korrektheits-Durchsetzbarkeit**: Die No-Side-Effects-/Repräsentativ-Daten-Regeln sind `[policy]` ohne HA-Deckung. Lassen sie sich statisch prüfen (grep nach `callService`, geguarded durch einen `preview`/`editMode`-Check), oder brauchen sie einen Runtime-/gerenderten Check?
- **Doku-Drift**: Fast das gesamte Preview-Surface ist source-verifiziert, nicht doc-belegt. Wenn die HA-Doku später die `preview`-Property oder das Picker-Verhalten dokumentiert, sollten die `[src]`-Tags hier neu geprüft und zu `[doc]` befördert werden.
