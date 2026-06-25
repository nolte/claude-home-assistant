# Skill: `ha-reproduce-state-add`

Status: draft

## Kontext

`ha/reproduce-state` definiert das Scene-Support-Pattern einer Integration: Damit die Entities einer Domain in **Scenes** aufgenommen und beim Aktivieren wiederhergestellt werden können, braucht der Integrations-Ordner ein konventionsbasiertes Plattform-Modul `reproduce_state.py` mit der Top-Level-Async-Funktion `async_reproduce_states(hass, states, context=None)`. Diese Funktion bekommt ein `Iterable[State]` und treibt jede Entity über die **passenden Service-Actions** der eigenen Domain in genau diesen State — nie über direkte State-Manipulation. Bislang gibt es keinen Skill, der das ergänzt. Der Quality-Scale-Marker ist **Bronze**, weil Reproduce-State die Voraussetzung dafür ist, dass die Entities einer Domain überhaupt in Scenes aufnehmbar und wiederherstellbar sind.

Dieser Skill ergänzt Scene-/Reproduce-State-Support in einer **bestehenden** Integration: das Modul `reproduce_state.py`, die `async_reproduce_states`-Funktion samt per-Entity-`async_reproduce_state`-Coroutinen, das State→Service-Call-Mapping (State-String plus relevante Attribute), den Idempotenz-Skip für bereits passende Entities und die Kontext-Weitergabe — spec-konform zu `ha/reproduce-state`. Die Generierung ist offline; der Skill deployt nie in eine laufende HA-Instanz.

## Scope

Ergänzung des Reproduce-State-Plattform-Moduls in einer bestehenden `custom_components/<domain>/`-Integration: die Datei `reproduce_state.py`, die Top-Level-Funktion `async_reproduce_states(hass, states, context=None)`, die pro Entity gesammelten `async_reproduce_state`-Coroutinen, das State→Service-Call-Mapping inkl. relevanter Attribute, der Idempotenz-Skip und die Kontext-Weitergabe an die ausgelösten Service-Calls. Der Skill liest `ha/reproduce-state` und validiert.

## Ziele

- Aus den setzbaren States einer Domain ein spec-konformes `reproduce_state.py` mit `async_reproduce_states(hass, states, context=None)` als einzigem Einstiegspunkt ableiten
- Die Signatur erzwingen: `states` als `Iterable[State]`, `context` optional, Rückgabe `None`; `Context`/`HomeAssistant`/`State` aus `homeassistant.core`
- Das State→Service-Call-Mapping als alleinige Reproduktions-Logik festlegen — Ziel-State wird über Service-Actions hergestellt, nie über `hass.states.async_set`
- Die State-Attribute beim Mapping berücksichtigen, soweit die Ziel-State-Reproduktion sie erfordert
- Die Reproduktion idempotent halten (bereits passende Entities überspringen) und den `context` an die ausgelösten Service-Calls weiterreichen

## Nicht-Ziele

- Das Schreiben/Definieren von Scenes selbst — `ha-automation/scene` (Scenes sind eine HA-Kern-Komponente; hier wird nur das Reproduzieren durch die Domain ergänzt)
- Die Service-Actions / das `services.yaml`, die das Mapping aufruft — `ha-service-definition-generator` / `ha/services` (hier nur konsumiert)
- Die Entity-Command-Methoden selbst (`async_turn_on` etc.), die die States tatsächlich setzen — die jeweilige Entity-Plattform
- Significant-Change und Diagnostics — eigene kleine HA-Plattform-Module, eigene Specs
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add reproduce_state", „make my entities scene-capable", „add scene support to this integration"
  - „let these entities be restored when a scene is activated"
  - „füge Scene-/Reproduce-State-Support hinzu", „mach meine Entities scene-fähig"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die setzbaren States der Domain (Prosa), aus denen der Skill das State→Service-Call-Mapping ableitet
- **KANN [MAY]** erfassen: die konkreten Service-Actions je State, die relevanten Attribute pro State, und ob die Reproduktion parallel (`asyncio`) erfolgen soll

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** bestätigen, dass die Domain in Scenes erwartbar verwendet wird und setzbare Ziel-States hat; rein lesende Sensor-Domains ohne setzbaren Ziel-State **SOLLTEN [SHOULD]** abgeraten bekommen (Reproduce-State **KANN [MAY]** dort entfallen)
- **MUSS [MUST]** die `ha/reproduce-state`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes `reproduce_state.py` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/reproduce-state`)

- **MUSS [MUST]** ein Modul `reproduce_state.py` im Integrations-Ordner erzeugen und **SOLLTE [SHOULD]** dem HA-Scaffold-Muster folgen (`python3 -m script.scaffold reproduce_state` als Referenz-Gerüst, nicht live ausgeführt)
- **MUSS [MUST]** `async_reproduce_states(hass, states, context=None)` als Top-Level-Async-Funktion exportieren; `states` ist `Iterable[State]`, `context` ein optionaler `Context`, der Rückgabewert `None`
- **MUSS [MUST]** `Context`, `HomeAssistant` und `State` aus `homeassistant.core` beziehen
- **MUSS [MUST]** pro Entity eine `async_reproduce_state`-Coroutine sammeln (eine je übergebenem `State`) und diese ausführen — `async_reproduce_states` aggregiert nur, die Reproduktions-Logik je Entity liegt in der per-Entity-Coroutine
- **MUSS [MUST]** jeden übergebenen `State` auf die passende(n) Service-Action(s) der eigenen Domain abbilden, die die Entity in genau diesen State treiben — der Ziel-State wird nie direkt gesetzt
- **MUSS [MUST]** die State-Attribute des `State`-Objekts beim Mapping berücksichtigen, soweit die Ziel-State-Reproduktion sie erfordert
- **MUSS NICHT [MUST NOT]** den State direkt manipulieren (z. B. `hass.states.async_set`) statt über Service-Actions
- **SOLLTE [SHOULD]** Entities überspringen, die bereits im Target-State sind (State-String, ggf. relevante Attribute) — für diese ist kein Service-Call nötig
- **SOLLTE [SHOULD]** den übergebenen `context` an die ausgelösten Service-Calls weiterreichen, damit die Reproduktions-Aktionen demselben Kontext zugeordnet bleiben
- **KANN [MAY]** mehrere Entities parallel reproduzieren (`asyncio.gather` über die per-Entity-Coroutinen) und einen vorwärtskompatiblen `reproduce_options`-Parameter vorsehen, sofern die Ziel-HA-Version ihn durchreicht
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `reproduce_state.py` existiert; `async_reproduce_states(hass, states, context=None)` ist Top-Level-Async und gibt `None` zurück; `states` ist `Iterable[State]`; `Context`/`HomeAssistant`/`State` stammen aus `homeassistant.core`; jeder `State` wird auf Service-Action(s) abgebildet; eine `grep`-Suche nach `hass.states.async_set` liefert keine Treffer; bereits passende Entities werden übersprungen; `context` wird weitergereicht
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/reproduce-state` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Bronze**)

### Verbote

- **MUSS NICHT [MUST NOT]** den State der Entity direkt setzen statt über Service-Actions
- **MUSS NICHT [MUST NOT]** Scenes definieren oder die aufgerufenen Service-Actions selbst implementieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] `reproduce_state.py` existiert im Integrations-Ordner der Domain
- [ ] `async_reproduce_states(hass, states, context=None)` ist als Top-Level-Async-Funktion exportiert und gibt `None` zurück
- [ ] `states` ist als `Iterable[State]` typisiert; `Context`/`HomeAssistant`/`State` stammen aus `homeassistant.core`
- [ ] Jeder übergebene `State` wird auf passende Service-Action(s) abgebildet (inkl. relevanter Attribute), über per-Entity-`async_reproduce_state`-Coroutinen
- [ ] Eine `grep`-Suche nach `hass.states.async_set` in `reproduce_state.py` liefert keine Treffer
- [ ] Entities, die bereits im Target-State sind, werden übersprungen
- [ ] Der übergebene `context` wird an die ausgelösten Service-Calls weitergereicht
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **Bronze**

## Offene Fragen

- **Idempotenz-Vergleich**: Wie streng vergleicht der Skip-Pfad „bereits im Target-State" — nur den State-String oder auch alle Attribute? `ha/reproduce-state` formuliert es als SHOULD ohne kalibrierte Vergleichstiefe; der Skill folgt dem Doc-Muster und fragt im Zweifel nach.
- **`reproduce_options`-Parameter**: Neuere HA-Versionen reichen reproduktionsspezifische Optionen durch. Die zugrunde liegende Quelle führt nur `context`; ob/wie der Skill `reproduce_options` verbindlich in die Signatur aufnimmt, ist offen — aktuell als KANN.
- **Parallelität**: Bis zu welcher Entity-Anzahl ist paralleles Reproduzieren über `asyncio` sinnvoll, ab wann drohen Backend-Rate-Limits? Aktuell als KANN ohne Schwelle.
- **Partielle States**: Eine Scene kann partielle States enthalten. Wie geht das Mapping mit fehlenden Attributen um — Best-Effort oder strikte Validierung? Nicht standardisiert; fall-zu-fall.
