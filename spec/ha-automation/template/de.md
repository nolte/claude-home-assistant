# HA-Automation: Template-Integration nutzen

Status: draft

## Kontext

Die `template`-Integration erzeugt **Template-Entitäten**: Entitäten, deren Zustand, Verfügbarkeit, Attribute und (bei aktorischen Domänen) Aktionen aus Jinja2-Templates über andere Entitäten abgeleitet werden. Sie ist das deklarative Werkzeug, um aus vorhandenen Zuständen einen neuen, sauberen Wert zu berechnen — etwa einen kombinierten Sensor, einen abgeleiteten `binary_sensor` oder einen virtuellen Schalter, der mehrere Geräte zusammenfasst.

Die reale HA-Einordnung ist **Helper** (Helfer-Integration) plus die jeweiligen Entitäts-Domänen — nicht „Automation". Im Integrations-Katalog steht `template` als Helfer; jede erzeugte Entität landet in ihrer Ziel-Domäne (`sensor.*`, `binary_sensor.*`, `switch.*` usw.). Die Integration kennt zwei grundverschiedene Betriebsarten: **state-based** (re-rendert automatisch, sobald eine referenzierte Entität wechselt) und **trigger-based** (re-rendert ausschließlich, wenn ein deklarierter Trigger feuert). Diese Unterscheidung ist das Herzstück hochwertiger Template-Nutzung und der Kern der Abgrenzung weiter unten.

Diese Spec überführt die offizielle Nutzungs-Doku in eine verbindliche Konvention für die vom Plugin erzeugten Template-Entitäten. Sie verweist für das Automations-Grundmodell (Trigger/Bedingung/Aktion) auf `ha-automation/automation` und für die Namens-Mechanik auf `ha/naming-conventions`.

Verifizierte Quellen: `/integrations/template/` (moderner `template:`-Block, state-based vs. trigger-based, Domänen-Katalog, per-Entität-Schlüssel) sowie `/docs/configuration/templating/` und `/template-functions/` (`has_value`, `is_number`, `float`/`int` mit Default, `default`-Filter, `states`/`is_state`/`state_attr`).

## Wann verwenden

Verwende die `template`-Integration immer dann, wenn aus vorhandenen Entitäten **deklarativ ein neuer Wert, Zustand oder eine neue Entität abgeleitet** werden soll — als Single Source of Truth, die sich selbst aktualisiert, statt einen Wert per Automation in einen Helfer zu schreiben. Typische Anwendungsfälle:

- **Abgeleiteter Sensor** — aus mehreren Quell-Entitäten einen sauberen `sensor`/`binary_sensor` berechnen (Kombination, Formatierung, Schwellwert-Logik), der von selbst re-rendert, sobald eine Quelle wechselt (state-based)
- **Virtueller Aktor** — einen `switch`/`light`/`cover`/`fan` mit `state`-Template plus Aktions-Schlüsseln (`turn_on`/`turn_off`, `set_value`, `select_option`) bauen, der mehrere Geräte unter einer Entität zusammenfasst
- **Eingefrorener Schnappschuss / Ereignis-Wert** — einen Wert nur zu einem bestimmten Moment fortschreiben (bei einem `event`, zu einer Uhrzeit, beim `homeassistant`-Start) über eine trigger-based Entität mit `triggers`/`conditions`/`actions`
- **Re-Render-Lawine vermeiden** — bei vielen oder häufig wechselnden Abhängigkeiten eine trigger-based Entität wählen, die nur zum gewünschten Moment neu berechnet, statt bei jeder Quell-Änderung
- **Robuste Verfügbarkeit** — über ein `availability`-Template und die Guard-Idiome (`has_value`, `is_number`, `float(default)`) bewusst `unavailable` melden, statt bei `unavailable`/`unknown`-Quellen einen falschen Wert zu liefern

Eine Template-Entität ist das richtige Werkzeug, sobald ein Wert **aus anderen Zuständen berechnet** wird. Für zeitliche Ableitung oder Statistik die zweckgebauten Integrationen, für Seiteneffekte eine Automation (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Den **modernen `template:`-Konfigurationsblock** als Standard festschreiben und die Legacy-`platform: template`-Form ausschließen
- **state-based vs. trigger-based** als bewusste Entwurfsentscheidung erzwingen, statt Default-Verhalten blind zu übernehmen
- Den dokumentierten Domänen-Katalog (sensor, binary_sensor, number, select, switch, light, cover, fan, image, button, weather, alarm_control_panel, vacuum u. a.) als zulässige Ziele verbindlich machen
- Die per-Entität-Pflicht- und -Kürschlüssel (`state`, `availability`, `unique_id`, `device_class`, `state_class`, `attributes`, `name`) konsistent setzen
- Die **Unavailable-/Unknown-Guard-Idiome** (`has_value`, `is_number`, `float(default)`/`int(default)`, `availability`) als prüfbare Regeln verankern
- Klar abgrenzen, wann **keine** Template-Entität das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das vollständige Trigger-/Bedingungs-/Aktions-Modell für trigger-based Entitäten — Detailvertrag in `ha-automation/automation` (Trigger-Katalog) und `ha-automation/script` (Aktions-Syntax), hier nur die template-spezifischen Schlüssel
- Die allgemeine Jinja2-/Template-Syntax und der vollständige Funktionskatalog — `/docs/configuration/templating/` und `/template-functions/`, hier nur die Guard-relevanten Funktionen
- Zweck-spezifische Mathematik (zeitliche Ableitung, Statistik, Min/Max) — `ha-automation/derivative`, `ha-automation/statistics`, `ha-automation/min-max`
- Die Namens-Dimension (`name`, `unique_id`, snake_case, Englisch, ≤50 Zeichen, ASCII) — `ha/naming-conventions`, hier nur referenziert
- Quality-Scale — nicht zutreffend (Nutzungs-Spec)

## Anforderungen

### Konfiguration

- **MUSS [MUST]** Template-Entitäten im **modernen `template:`-Block** definieren — eine Liste von Konfigurationsblöcken, die je eine Domäne (`sensor:`, `binary_sensor:`, `switch:` …) mit einer Liste von Entitäten enthalten:

  ```yaml
  template:
    - sensor:
        - name: "Example"
          state: "{{ ... }}"
  ```

- **MUSS NICHT [MUST NOT]** die Legacy-Form `platform: template` unter der jeweiligen Domäne verwenden; sie ist überholt und mischt nicht mit dem modernen Block

- **MUSS [MUST]** als Ziel-Domäne ausschließlich eine der dokumentierten Template-Entitäts-Domänen wählen: `alarm_control_panel`, `binary_sensor`, `button`, `cover`, `device_tracker`, `event`, `fan`, `image`, `light`, `lock`, `number`, `select`, `sensor`, `switch`, `update`, `vacuum`, `weather`

- **MUSS [MUST]** jeder Entität ein stabiles `unique_id` geben, damit sie UI-anpassbar (Umbenennen, Bereich, Anpassen) ist; ohne `unique_id` ist die Entität nicht über die UI verwaltbar. `name` und `unique_id` folgen der Mechanik in `ha/naming-conventions`

- **MUSS [MUST]** für die meisten Domänen ein `state`-Template setzen (Pflicht-Schlüssel für den Entitätszustand); für aktorische Domänen zusätzlich die domänen-spezifischen Aktions-Schlüssel (z. B. `turn_on`/`turn_off` bei `switch`/`light`, `set_value` bei `number`, `select_option` bei `select`, `open_cover`/`close_cover`/`set_cover_position` bei `cover`)

- **SOLLTE [SHOULD]** ein `availability`-Template setzen, das `true`/`false` zurückgibt, sobald der Zustand aus unzuverlässigen Quellen abgeleitet wird — so wird die Entität bewusst `unavailable` statt einen falschen Wert zu liefern

- **SOLLTE [SHOULD]** bei Sensoren die passenden Klassifizierungs-Schlüssel setzen: `device_class`, `unit_of_measurement` und — für Langzeit-Statistik — `state_class` (`measurement`, `total`, `total_increasing`); bei `binary_sensor` `device_class` plus optional `delay_on`/`delay_off`/`auto_off`

- **KANN [MAY]** dynamische Darstellung über `icon`- und `picture`-Templates sowie zusätzliche `attributes` (Map aus Attribut-Templates) ergänzen

### state-based vs. trigger-based

- **MUSS [MUST]** zwischen **state-based** und **trigger-based** bewusst entscheiden und die Wahl begründen, wenn sie nicht offensichtlich ist:
  - *state-based*: keine `triggers`; die Entität **re-rendert automatisch**, sobald eine im Template referenzierte Entität wechselt
  - *trigger-based*: mit `triggers`; die Entität **re-rendert ausschließlich, wenn ein Trigger feuert** — laut Doku: „Trigger-based entities do not automatically update when states referenced in the templates change."

- **MUSS [MUST]** state-based wählen, wenn der Zielwert eine reine, billige Funktion der aktuellen Zustände ist (Ableitung, Kombination, Formatierung) — das ist der Normalfall

- **MUSS [MUST]** trigger-based wählen, wenn **Ereignis-Semantik** gebraucht wird: der Wert soll nur zu einem bestimmten Moment fortgeschrieben werden (z. B. bei einem `event`, zu einer Uhrzeit, beim `homeassistant`-Start), ein Schnappschuss soll eingefroren werden, oder eine **Re-Render-Lawine** bei vielen wechselnden Abhängigkeiten soll vermieden werden

- **KANN [MAY]** in trigger-based Entitäten die Schlüssel `triggers` (Trigger-Katalog wie in `ha-automation/automation`), `conditions` (Gate nach dem Trigger), `actions` (Skript-Syntax, deren Ergebnis-Variablen im Template sichtbar sind) und `variables`/`trigger_variables` (im Template verfügbare Key-Value-Paare) verwenden

- **MUSS [MUST]** beachten, dass nur **trigger-based** Sensoren/Binärsensoren ihren Zustand über einen Neustart **restaurieren**; state-based Entitäten werden nach dem Start neu berechnet

### Nutzung in Automationen & Templates

- **MUSS [MUST]** die erzeugte Entität wie jede native Entität referenzieren: als Trigger (`state`/`numeric_state` auf `sensor.*`/`binary_sensor.*`), als Bedingung, als Aktions-Ziel (`switch.*`, `light.*`, `number.*` …) und in Dashboards — die Domäne bestimmt die verfügbaren Trigger/Dienste

- **SOLLTE [SHOULD]** in jedem werterzeugenden Template gegen `unavailable`/`unknown` der Quell-Entitäten absichern, statt einen rohen `states('…')`-Wert direkt weiterzureichen:
  - `has_value('sensor.x')` prüft, ob eine Entität existiert und einen gültigen Zustand (nicht `unavailable`/`unknown`) hat
  - `is_number(value)` prüft, ob ein Wert in eine endliche Zahl konvertierbar ist, bevor gerechnet wird
  - `states('sensor.x') | float(0)` / `| int(0)` liefert einen definierten Default, wenn die Konvertierung fehlschlägt; der `default`-Filter deckt undefined/none ab

- **SOLLTE [SHOULD]** das `availability`-Template so formulieren, dass die Entität bei fehlender Datengrundlage `unavailable` meldet (z. B. `availability: "{{ has_value('sensor.source') }}"`), damit nachgelagerte Automationen nicht auf einen geratenen Default reagieren

- **KANN [MAY]** in den Templates die Variable `this` (das eigene Zustandsobjekt der Entität, u. a. für Self-Referencing-Attribute) und — in trigger-based Entitäten — `trigger` sowie `trigger_variables` verwenden

### Abgrenzung: Wann NICHT verwenden

- **SOLLTE NICHT [SHOULD NOT]** eine Automation einsetzen, die einen abgeleiteten Wert in einen `input_number`/`input_text` schreibt, wo eine **state-based Template-Entität** denselben Wert deklarativ liefert — die Template-Entität ist die deklarative Single Source of Truth, re-rendert von selbst, ist nicht versehentlich vom User editierbar und hat keine Schreib-Race-Conditions (Hintergrund: `ha-automation/automation`, `ha-automation/input-number`)

- **SOLLTE NICHT [SHOULD NOT]** eine **state-based** Template-Entität mit schwerer oder langsamer Logik bauen, die von vielen oder häufig wechselnden Entitäten abhängt — sie re-rendert bei **jeder** Abhängigkeits-Änderung und erzeugt eine Re-Render-Lawine; verwende stattdessen eine **trigger-based** Entität, die nur zum gewünschten Moment neu berechnet

- **MUSS NICHT [MUST NOT]** eine **trigger-based** Entität wählen, wo reine Ableitung aus aktuellen Zuständen genügt — sie aktualisiert **nicht** automatisch bei Zustandsänderungen der Quellen und liefert dann veraltete Werte; für laufende Ableitung ist state-based richtig

- **SOLLTE NICHT [SHOULD NOT]** zeitliche Ableitungen oder Statistik im Template nachbauen (Änderungsrate, gleitender Mittelwert, Min/Max über Zeit) — dafür gibt es die zweckgebauten Integrationen `ha-automation/derivative`, `ha-automation/statistics` und `ha-automation/min-max`, die Historie, Zeitfenster und Resampling korrekt behandeln

- **SOLLTE NICHT [SHOULD NOT]** Seiteneffekte (Dienst-Aufrufe, Benachrichtigungen, Schreiben in andere Entitäten) aus dem `state`-Template einer state-based Entität auslösen — Zustand-Templates sind seiteneffektfrei zu halten; für Seiteneffekte ist der `actions`-Block einer **trigger-based** Entität oder eine **Automation** (`ha-automation/automation`) zuständig

- **SOLLTE NICHT [SHOULD NOT]** einen rohen `states('sensor.x')`-Wert ohne `has_value`/`is_number`/`float(default)`-Guard in Rechnung, Bedingung oder `state` weiterreichen — beim Start oder bei `unavailable`/`unknown`-Quellen liefert das fehlerhafte oder leere Zustände; die Guard-Idiome sind Pflicht, kein Stil

## Akzeptanzkriterien

- [ ] Jede Template-Entität ist im modernen `template:`-Block definiert; keine `platform: template`-Legacy-Form
- [ ] Die Ziel-Domäne stammt aus dem dokumentierten Domänen-Katalog
- [ ] Jede Entität trägt ein stabiles `unique_id`; `name`/`unique_id` folgen `ha/naming-conventions`
- [ ] state-based vs. trigger-based ist bewusst gewählt und begründet, wenn nicht offensichtlich
- [ ] Aktorische Domänen definieren ihre Aktions-Schlüssel (z. B. `turn_on`/`turn_off`, `set_value`, `select_option`)
- [ ] Sensoren setzen wo sinnvoll `device_class`, `unit_of_measurement` und `state_class`
- [ ] Werterzeugende Templates sind gegen `unavailable`/`unknown` abgesichert (`has_value` / `is_number` / `float(default)` / `int(default)` / `availability`)
- [ ] Keine schwere/häufig re-rendernde Logik in einer state-based Entität; solche Fälle sind trigger-based
- [ ] Keine trigger-based Entität dort, wo laufende state-based Ableitung gebraucht wird
- [ ] Zeitliche/statistische Berechnungen nutzen die zweckgebauten Integrationen, nicht ein Template
- [ ] Keine Seiteneffekte aus einem state-Template; Seiteneffekte laufen im trigger-based `actions`-Block oder in einer Automation
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
