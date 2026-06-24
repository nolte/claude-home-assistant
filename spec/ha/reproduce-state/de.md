# HA-Integration: Reproduce-State (Scene-Support)

Status: draft

## Kontext

Home Assistant unterstützt **Scenes**. Eine Scene ist eine Sammlung von (partiellen) Entity-States. Wird eine Scene aktiviert, versucht HA, die richtigen Service-Actions aufzurufen, um die in der Scene festgelegten States herzustellen. Integrationen sind dafür verantwortlich, HA die Fähigkeit hinzuzufügen, für ihre Domain die richtigen Service-Actions aufzurufen, um die States einer Scene zu reproduzieren.

Den Einstieg liefert HA über ein **Scaffold-Template**: aus einer HA-Dev-Umgebung erzeugt `python3 -m script.scaffold reproduce_state` das Modul samt Methoden-Gerüst. Wer den manuellen Weg geht, legt im Integrations-Ordner eine Datei `reproduce_state.py` an und implementiert die Methode `async_reproduce_states`. Diese Methode bekommt eine Liste von `State`-Objekten und treibt die Entities über die passenden Service-Calls in genau diese States. Diese Spec überführt das HA-Reproduce-State-Plattform-Pattern in eine generische Verpflichtung für Integrationen, deren Domain Scene-Support tragen soll.

Quality-Scale-Marker: **Bronze** (Reproduce-State ist die Voraussetzung dafür, dass die Entities einer Domain überhaupt in Scenes aufgenommen und wiederhergestellt werden können).

## Ziele

- `reproduce_state.py` als Standard-Modul für jede Domain etablieren, deren Entities Teil von Scenes sein sollen
- `async_reproduce_states` als einzigen Einstiegspunkt definieren, über den HA die States einer Scene reproduziert
- Das Mapping von Target-`State` auf Service-Calls als alleinige Reproduktions-Logik festlegen — keine direkte State-Manipulation
- Reproduktion idempotent halten — Entities, die bereits im Target-State sind, werden übersprungen

## Nicht-Ziele

- Das Schreiben/Definieren von Scenes selbst — Scenes sind eine HA-Kern-Komponente, diese Spec deckt nur das Reproduzieren der States durch die Domain ab
- Service-Definition und `services.yaml` — die aufgerufenen Service-Actions werden über `ha/services` definiert, hier nur konsumiert
- Significant-Change und Diagnostics — eigene kleine HA-Plattform-Module, eigene Specs
- Persistenz oder Historie von States — Reproduce-State stellt einen Ziel-State her, verwaltet aber keine State-Verläufe

## Anforderungen

### Zweck (Scene-Support)

- **MUSS [MUST]** vorhanden sein, sobald die Entities einer Domain in Scenes aufnehmbar und über Scene-Aktivierung wiederherstellbar sein sollen — ohne `reproduce_state.py` kann HA die States dieser Domain nicht reproduzieren
- **MUSS [MUST]** die States über die passenden Service-Actions herstellen — eine Scene ist eine Sammlung (partieller) Entity-States, und das Aktivieren einer Scene ruft die richtigen Service-Actions auf, um diese States herzustellen
- **KANN [MAY]** über den klassischen Scene-Aktivierungs-Pfad hinaus auch durch direktes Anwenden von States genutzt werden — der Mechanismus reproduziert eine übergebene Liste von States unabhängig davon, woher sie stammt

### `reproduce_state.py`-Platform

- **MUSS [MUST]** ein Modul `reproduce_state.py` im Integrations-Ordner enthalten, sobald die Domain Scene-Support tragen soll
- **SOLLTE [SHOULD]** das HA-Scaffold-Template als Einstieg nutzen — `python3 -m script.scaffold reproduce_state` aus einer HA-Dev-Umgebung erzeugt das Modul und das Methoden-Gerüst
- **MUSS [MUST]** die Plattform-Funktion auf Modul-Ebene als Top-Level-Async-Funktion exportieren — HA erkennt `reproduce_state.py` als konventionsbasiertes Plattform-Modul und ruft die Funktion auf

### `async_reproduce_states`-Signatur

- **MUSS [MUST]** eine Async-Funktion `async_reproduce_states(hass, states, context=None)` exportieren, wobei `states` ein `Iterable[State]` ist und `context` ein optionaler `Context`
- **MUSS [MUST]** die Typen aus `homeassistant.core` beziehen — `Context`, `HomeAssistant`, `State`
- **MUSS [MUST]** `None` zurückgeben — die Funktion erzeugt ihre Wirkung über Service-Calls, nicht über einen Rückgabewert

### State→Service-Call-Mapping

- **MUSS [MUST]** jeden übergebenen `State` auf die passende(n) Service-Action(s) abbilden, die die Entity in genau diesen State treiben — der Ziel-State wird nicht direkt gesetzt, sondern über Service-Calls hergestellt
- **MUSS [MUST]** die State-Attribute des `State`-Objekts beim Mapping berücksichtigen, soweit die Ziel-State-Reproduktion sie erfordert — ein State umfasst neben dem State-String auch Attribute
- **MUSS NICHT [MUST NOT]** den State der Entity direkt manipulieren (z. B. über `hass.states.async_set`) statt über Service-Actions — die HA-Konvention ist die Reproduktion über die richtigen Service-Calls

### Idempotenz & Kontext

- **SOLLTE [SHOULD]** Entities überspringen, die bereits im Target-State sind — für diese ist kein Service-Call nötig
- **SOLLTE [SHOULD]** den übergebenen `context` an die ausgelösten Service-Calls weiterreichen, damit die durch die Reproduktion ausgelösten Aktionen demselben Kontext zugeordnet bleiben
- **KANN [MAY]** mehrere Entities parallel reproduzieren (`asyncio`), wenn die Reproduktion mehrerer States gleichzeitig erfolgen soll

### Wann implementieren

- **MUSS [MUST]** implementiert werden, sobald die Domain erwartbar in Scenes verwendet wird — andernfalls werden ihre Entities zwar von einer Scene erfasst, aber beim Aktivieren der Scene nicht wiederhergestellt
- **KANN [MAY]** entfallen, solange die Domain keine in Scenes wiederherstellbaren States hat (z. B. rein lesende Sensor-Domains ohne setzbaren Ziel-State)

## Akzeptanzkriterien

- [ ] `reproduce_state.py` existiert im Integrations-Ordner der Domain
- [ ] `async_reproduce_states(hass, states, context=None)` ist als Top-Level-Async-Funktion exportiert und gibt `None` zurück
- [ ] `states` wird als `Iterable[State]` typisiert; `Context`/`HomeAssistant`/`State` stammen aus `homeassistant.core`
- [ ] Jeder übergebene `State` wird auf passende Service-Action(s) abgebildet (inkl. relevanter Attribute)
- [ ] Eine `grep`-Suche nach `hass.states.async_set` in `reproduce_state.py` liefert keine Treffer (Reproduktion läuft über Service-Calls)
- [ ] Entities, die bereits im Target-State sind, werden übersprungen
- [ ] Der übergebene `context` wird an die ausgelösten Service-Calls weitergereicht
- [ ] Quality-Scale-Marker: **Bronze**

## Offene Fragen

- **Idempotenz-Vergleich**: Wie streng vergleicht der Skip-Pfad „bereits im Target-State" — nur den State-String oder auch alle Attribute? Aktuell als SHOULD ohne kalibrierte Vergleichstiefe formuliert.
- **`reproduce_options`-Parameter**: Neuere HA-Versionen reichen reproduktionsspezifische Optionen durch. Die zugrunde liegende Quelle führt nur `context`; ob/wie `reproduce_options` verpflichtend wird, ist offen.
- **Parallelität**: Bis zu welcher Anzahl Entities ist paralleles Reproduzieren über `asyncio` sinnvoll, ab wann drohen Rate-Limits am Backend? Aktuell als KANN ohne Schwelle.
- **Partielle States**: Eine Scene kann partielle States enthalten. Wie geht das Mapping mit fehlenden Attributen um — Best-Effort oder strikte Validierung? Nicht standardisiert.
