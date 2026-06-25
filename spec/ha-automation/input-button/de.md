# HA-Automation: input_button nutzen

Status: draft

## Kontext

`input_button` ist eine **Helfer-Integration** (HA-Kategorie *Helper*): Sie stellt einen **zustandslosen Knopf** bereit, der per Benutzer-Interaktion in der Oberfläche oder per Aktion „gedrückt" wird. Er hat keinen `on`/`off`-Zustand — der Zustand einer `input_button`-Entität ist laut Doku ein **Zeitstempel** des letzten Drucks. Sein einziger Zweck ist es, einen Auslöse-Impuls zu erzeugen, auf den Automationen reagieren.

Auf Konfigurationsebene wird ein `input_button` über die UI (Einstellungen → Geräte & Dienste → Helfer) oder als YAML unter dem Top-Level-Schlüssel `input_button` angelegt. Die Integration hat eine echte Integrations-Karte; ihre reale Einordnung ist **Helper**. Typischer Einsatz: ein manueller „Jetzt ausführen"-Knopf auf einem Dashboard, der eine Automation startet, ohne dass ein Folgezustand verwaltet werden muss.

Verifizierte Quelle: [`/integrations/input_button/`](https://www.home-assistant.io/integrations/input_button/) (Konfigurationsschlüssel `name`/`icon`, Dienste `press`/`reload`, Zustand = Zeitstempel des letzten Drucks, `state`-Trigger-Beispiel). Namens-Mechanik referenziert über `ha/naming-conventions`.

## Wann verwenden

Verwende `input_button` für einen **manuellen, UI-getriebenen Auslöse-Impuls** ohne Folgezustand — einen zustandslosen Knopf, der eine Automation oder ein Skript anstößt. Typische Anwendungsfälle:

- **„Jetzt ausführen"-Knopf** — ein Dashboard-Knopf, der eine Automation oder ein Skript manuell startet, ohne dass ein Schaltzustand zu verwalten ist
- **Reaktion per `state`-Trigger** — auf den Druck reagieren, weil sich der Zeitstempel ändert (ohne `to`/`from`-Prüfung)
- **Programmatisches Auslösen** — den Knopf per `input_button.press` aus einer anderen Automation oder einem Skript drücken
- **Dashboard-Bedienung** — als `button`/`tile` mit `input_button.press`-Aktion oder `entities`-Zeile manuell auslösbar machen
- **„Zuletzt gedrückt"-Anzeige** — den Zeitstempel im Template-/Trigger-Kontext lesen, um den letzten Druck darzustellen

Ein `input_button` ist das richtige Werkzeug, sobald ein **manueller Impuls** ohne zu speichernden Folgezustand gebraucht wird. Geht es um einen persistenten Zustand, eine wiederverwendbare Sequenz, einen realen Ereignis-Trigger oder eine Optionsauswahl, greift ein anderer Baustein (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines `input_button` (Schlüssel, Zustandslosigkeit) verbindlich festschreiben
- Den korrekten Einsatz als manueller UI-Auslöser fixieren, der eine Automation oder ein Skript anstößt
- Den exponierten Dienst (`input_button.press`) und das Triggern per `state`-Trigger festlegen
- Klar abgrenzen, wann ein `input_button` **nicht** das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Modell der Automation selbst — `ha-automation/automation`
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur das Trigger-Muster
- Die Namens-Dimension (`name`, snake_case-`object_id`, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Persistente Schalt- oder Wertzustände — `input_boolean` (`ha-automation/input-boolean`) bzw. `input_number` (`ha-automation/input-number`)

## Anforderungen

### Konfiguration

- **MUSS [MUST]** einen `input_button` über den Top-Level-Schlüssel `input_button` mit mindestens einer object_id strukturieren; pro Eintrag sind die Schlüssel `name` und `icon` optional (es gibt keinen Wert-/Initialzustands-Schlüssel)
- **MUSS [MUST]** die `object_id` als snake_case-Slug und den `name` englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)
- **MUSS NICHT [MUST NOT]** einen `initial`- oder Wert-Schlüssel erwarten — der `input_button` ist zustandslos; sein Zustand ist ausschließlich der Zeitstempel des letzten Drucks und überdauert keinen Neustart als sinnvoller Wert
- **KANN [MAY]** `icon` setzen, um das Element in der Oberfläche zu kennzeichnen

### Nutzung in Automationen & Templates

- **MUSS [MUST]** auf einen Druck per **`state`-Trigger** auf die Entität reagieren (laut Doku-Beispiel `trigger: state` / `entity_id: input_button.x`) — der Trigger feuert, weil sich der Zeitstempel ändert; ein `to`/`from` ist nicht erforderlich
- **SOLLTE NICHT [SHOULD NOT]** auf einen bestimmten Zustands**wert** eines `input_button` prüfen (er ist nur ein wechselnder Zeitstempel) — der reine Übergang ist das Signal
- **MUSS [MUST]** zum programmatischen Auslösen den dokumentierten Dienst `input_button.press` verwenden (Ziel über `target.entity_id`); `input_button.reload` lädt die YAML-Helfer neu
- **KANN [MAY]** das Element auf einem Dashboard über einen `button`/`tile` mit `input_button.press`-Aktion oder eine `entities`-Zeile einbinden, um es manuell auslösbar zu machen
- **KANN [MAY]** im Template-/Trigger-Kontext den Zeitstempel als „zuletzt gedrückt am" lesen, wenn die Anzeige des letzten Drucks erwünscht ist

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** einen `input_button` verwenden, um einen Zustand zu **speichern** (ein/aus, ein Wert) — er ist zustandslos und behält nur einen Zeitstempel; für einen persistenten Schaltzustand nutze ein **`input_boolean`** (`ha-automation/input-boolean`), für einen Zahlenwert ein **`input_number`** (`ha-automation/input-number`)
- **SOLLTE NICHT [SHOULD NOT]** einen `input_button` als Träger einer wiederverwendbaren Aktions**sequenz** missverstehen — der Knopf hat keine `sequence`; er feuert nur einen Trigger. Soll die Sequenz von mehreren Stellen aufrufbar sein, gehört sie in ein **Skript** (`ha-automation/script`), das einen aufrufbaren Dienst exponiert; der Knopf kann das Skript dann anstoßen
- **SOLLTE NICHT [SHOULD NOT]** einen `input_button` einführen, wo die Automation ohnehin durch ein reales Ereignis (Sensor, Zeit, Zustandswechsel) ausgelöst wird — der dedizierte Trigger (`ha-automation/automation`) ist direkter; ein `input_button` ist nur für **manuelle/UI-getriebene** Auslösung gedacht
- **SOLLTE NICHT [SHOULD NOT]** mehrere `input_button` als verkappte Optionsauswahl anlegen (ein Knopf je Wert), um einen Parameter zu setzen — dafür ist ein **`input_select`** oder ein **`input_number`** das passende Konstrukt, weil es den gewählten Wert tatsächlich hält

## Akzeptanzkriterien

- [ ] Jeder Helfer wird über den Top-Level-Schlüssel `input_button` mit snake_case-`object_id` und englischem `name` ≤50 Zeichen angelegt
- [ ] Es wird kein `initial`-/Wert-Schlüssel verwendet; die Zustandslosigkeit wird respektiert
- [ ] Reaktion auf einen Druck erfolgt über einen `state`-Trigger ohne Prüfung eines konkreten Zustandswerts
- [ ] Programmatisches Auslösen erfolgt über `input_button.press` mit `target.entity_id`
- [ ] Kein `input_button` speichert einen Schalt- oder Zahlenwert (dafür `input_boolean`/`input_number`)
- [ ] Kein `input_button` ersetzt ein `script` (keine `sequence`) oder eine `input_select`/`input_number`-Auswahl
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
