# HA-Integration: Lovelace-Card-Entity-Selector-Filter

Status: draft

## Kontext

Ein Custom-Lovelace-Card-Editor (`static getConfigElement()`) bietet dem User Formularfelder, um die Card zu konfigurieren — darunter typischerweise ein oder mehrere **Entity-Auswahl-Dropdowns**. Home Assistant rendert solche Dropdowns über den `entity`-Selector (`ha-form` + `selector: { entity: {...} }`). Ohne Filter listet dieser Selector **alle** Entities (oder alle einer Domain) der gesamten Installation auf. Bei Installationen mit hunderten Entities ist die Auswahl dadurch nicht nur unübersichtlich, sondern lädt zur **Fehlauswahl** ein: Der User greift eine Entity, die syntaktisch passt (`sensor.*`), aber semantisch nicht das ist, was die Card erwartet.

Konkreter Auslöser aus `nolte/kamerplanter-ha`: Die Care-Card erwartet in ihren zwei Feldern die **Hub-Aggregat-Sensoren** (`<domain>_tasks_due_today` / `<domain>_tasks_overdue`, erkennbar an einem `plants`-Listen-Attribut). Der ungefilterte Picker ließ aber auch **Einzelpflanzen-Sensoren** (Befallsdruck, Karenzzeit, Tage-seit-Inspektion) zu. Diese tragen einen Einzelwert ohne `plants`-Attribut — die Card kann daraus keine Liste bauen und bleibt im echten Dashboard leer, während die hartkodierte Editor-Vorschau weiterhin gut aussieht. Das Problem ist also unsichtbar bis zum Live-Betrieb.

`ha/lovelace-card-patterns` regelt den Card-Lifecycle und nennt den Card-Editor nur als Mindest-Vorgabe (dort Nicht-Ziel: „Custom-Card-Editor-UIs über `getConfigElement` hinaus"). `ha/services` verlangt für `services.yaml` bereits einen `entity`-Selector mit `integration`-Filter. Diese Spec überträgt diese Selector-Disziplin auf **Card-Editoren** und ergänzt das, was statische Filter allein nicht leisten: die präzise Einschränkung auf einen integrations-eigenen Entity-**Subtyp**.

Quality-Scale-Marker: **Bronze** (Custom-Card-Editoren stehen außerhalb der HA-Quality-Scale; das Pattern ist nolte-portfolio-spezifisch).

## Ziele

- Ungefilterte `entity`-Selektoren in Card-Editoren ausschließen
- Einen deklarativen Integrations-Basisfilter für jedes Entity-Feld verpflichtend machen
- Ein nachhaltiges, umbenennungs-stabiles Verfahren etablieren, um auf einen bestimmten Entity-Subtyp einzuschränken (Entity-Registry + `translation_key`)
- Fehlauswahl konstruktiv abfangen: robuster Fallback, Hilfetexte, defensive Card-Render-Logik

## Nicht-Ziele

- `services.yaml`-Selektoren — geregelt in `ha/services`
- Config-Flow-Selektoren und Voluptuous-Schemas — geregelt in `ha/config-flow-patterns`
- Allgemeiner Card-Lifecycle (`setConfig`, `set hass`, Grid-Optionen) — geregelt in `ha/lovelace-card-patterns`
- Definition der Entities selbst inkl. `device_class`-Vergabe — geregelt in `ha/entity-architecture`
- `target`-, `area`-, `device`- und `label`-Selektoren — eigene Achse, hier nur als Ausblick (Offene Fragen)

## Anforderungen

### Selektor statt Freitext

- **MUSS [MUST]** jedes Entity-Feld eines Card-Editors über den `entity`-Selector anbieten (`ha-form` + `selector: { entity: {...} }`), niemals als freies Textfeld
- **SOLLTE [SHOULD]** den Editor über `ha-form` + Schema bauen — `computeLabel` und `computeHelper` werden dann nativ unterstützt; ein handgebautes Picker-HTML ist nur bei nicht abbildbaren Sonderfällen gerechtfertigt

### Deklarativer Basisfilter

- **MUSS [MUST]** jeden `entity`-Selector mindestens auf die eigene Integration einschränken: `selector: { entity: { filter: [{ integration: "<domain>", domain: "<domain-der-entity>" }] } }`
- **MUSS NICHT [MUST NOT]** sich allein auf `domain: ["sensor"]` (o. ä.) verlassen — das lässt sämtliche Fremd-Sensoren der Installation zu und ist die Hauptursache der Fehlauswahl
- Hinweis: `filter` ist ein Objekt **oder eine Liste** von Kriterien-Objekten (OR-Verknüpfung); zulässige Kriterien sind `integration`, `domain`, `device_class`, `supported_features`

### Präzise Einschränkung auf den passenden Entity-Subtyp

Wenn die eigene Integration mehrere Entity-Typen liefert, von denen nur einer in das Feld passt, reicht der Integrations-Basisfilter nicht.

- **MUSS [MUST]** in diesem Fall weiter einschränken — der Basisfilter allein ist dann unzureichend
- **SOLLTE [SHOULD]** deklarativ über `device_class` / `supported_features` filtern, **wenn** die Ziel-Entities eine vom Selector unterstützte **Standard**-`device_class` tragen
- **SOLLTE [SHOULD]** andernfalls — der Regelfall für integrations-eigene Subtypen — `include_entities` zur Editor-Laufzeit dynamisch aus der **Entity-Registry** (`hass.entities`) aufbauen, gefiltert über `platform === "<domain>"` **und** den stabilen `translation_key` der Ziel-Entities:

  ```js
  // translation_key ueberlebt User-Umbenennungen und Mehrfachinstanzen,
  // anders als ein entity_id-String-Match.
  function pickByTranslationKey(hass, keys) {
    return Object.values(hass.entities)
      .filter((e) => e.platform === DOMAIN && keys.includes(e.translation_key))
      .map((e) => e.entity_id);
  }
  const ids = pickByTranslationKey(hass, ["tasks_due_today"]);
  const selector = ids.length
    ? { entity: { include_entities: ids } }
    : { entity: { filter: [{ integration: DOMAIN, domain: "sensor" }] } }; // Fallback
  ```

- **KANN [MAY]** als letzten Ausweg über ein stabiles State-/Attribut-Merkmal heuristisch filtern (z. B. Existenz eines Listen-Attributs), wenn kein `translation_key` trägt
- **MUSS NICHT [MUST NOT]** `include_entities` aus fragilen `entity_id`-String-Mustern ableiten — diese brechen bei User-Umbenennung und bei Mehrfach-Instanzen der Integration (`_2`-Suffix)

### Dynamisches Schema

- **MUSS [MUST]** das Editor-Schema pro Render aus dem aktuellen `hass` neu erzeugen (Funktion, nicht Modul-Konstante), sobald `include_entities` laufzeit-abhängig ist — sonst spiegelt der Picker die Entity-Registry nicht wider, solange Entities beim Öffnen des Editors noch nachladen

### Robuster Fallback

- **MUSS [MUST]** auf den deklarativen Basisfilter zurückfallen, wenn die dynamische Kandidatenliste leer ist (Entities noch nicht geladen oder keine gefunden)
- **MUSS NICHT [MUST NOT]** in diesem Fall `include_entities: []` setzen — ein leeres Include macht den Picker unbenutzbar und verschlimmert die Lage gegenüber gar keinem Filter

### Hilfetext, Defaults und defensive Card

- **MUSS [MUST]** jedes optionale oder potenziell mehrdeutige Entity-Feld mit einem Hilfetext (`computeHelper`) versehen, der den erwarteten bzw. Default-Sensor benennt und vor der typischen Fehlauswahl warnt
- **SOLLTE [SHOULD]** für optionale Entity-Felder einen sinnvollen Default-`entity_id` führen; ein leeres Feld **MUSS [MUST]** auf diesen Default zurückfallen
- **MUSS [MUST]** die Card-Render-Logik defensiv mit fehlender oder unpassend gewählter Entity umgehen — kein Crash, sondern leere bzw. erklärende Darstellung; die Editor-Vorschau **MUSS NICHT [MUST NOT]** mit hartkodierten Demo-Daten den Eindruck einer funktionierenden Konfiguration erwecken, ohne dass dies erkennbar ist

## Akzeptanzkriterien

- [ ] Kein Card-Editor verwendet einen `entity`-Selector ohne Filter
- [ ] Jeder `entity`-Selector filtert mindestens auf `integration: "<domain>"`
- [ ] Felder mit mehrdeutigem Subtyp schränken über `translation_key`-basiertes `include_entities` (oder `device_class`) weiter ein
- [ ] Bei leerer Kandidatenliste fällt der Selektor auf den Integrationsfilter zurück; nie ein leerer Picker
- [ ] Schemata mit laufzeit-abhängigem `include_entities` werden pro Render erzeugt
- [ ] Jedes mehrdeutige Entity-Feld trägt einen Hilfetext mit Default/Erwartung
- [ ] Eine `grep`-Suche nach `domain:` ohne begleitenden `integration`/`include_entities`-Filter liefert in Card-Editoren keine Treffer
- [ ] Quality-Scale-Marker: **Bronze**

## Offene Fragen

- **Label-Filter**: Der `entity`-Selector unterstützt aktuell keinen `label`-Filter (nur `integration`/`domain`/`device_class`/`supported_features`). Sobald HA das nachrüstet, wäre ein integrations-eigenes Label der deklarativ sauberste Subtyp-Filter — diese Spec dann darauf umstellen?
- **Integrationsfilter auch bei eindeutigen Feldern**: MUSS der Integrationsfilter selbst dann gelten, wenn nur ein einziger passender Typ existiert, oder reicht dort SOLLTE?
- **Geteiltes Editor-Util**: Lohnt ein gemeinsames JS-Hilfsmodul (`pickByTranslationKey`, Schema-Builder mit Fallback) über alle Cards der Integration, statt das Pattern pro Card zu wiederholen?
- **Verhältnis zu `ha/lovelace-card-patterns`**: Wird `getConfigElement` durch diese Spec faktisch zur MUSS-Anforderung, sobald eine Card überhaupt Entity-Felder hat (dort aktuell offene Frage „Card-Editor-Pflicht-Tiefe")?
