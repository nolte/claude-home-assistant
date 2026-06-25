# HA-Automation: input_boolean nutzen

Status: draft

## Kontext

`input_boolean` ist eine **Helfer-Integration** (HA-Kategorie *Helper*): Sie stellt eine vom Benutzer schaltbare, binäre Größe bereit, deren Zustand `on` oder `off` ist. Anders als ein `binary_sensor` misst sie nichts in der realen Welt — sie ist ein virtueller Schalter, den Menschen über die Oberfläche und Automationen über Aktionen umlegen. Typische Einsätze sind manuelle Übersteuerungen („Urlaubsmodus an"), Feature-Flags für Automationen und Gates, die eine Automation nur dann laufen lassen, wenn der Benutzer sie aktiviert hat.

Auf Konfigurationsebene wird ein `input_boolean` entweder über die UI (Einstellungen → Geräte & Dienste → Helfer) oder als YAML unter dem Top-Level-Schlüssel `input_boolean` angelegt. Die Integration hat eine echte Integrations-Karte im Katalog; ihre reale Einordnung ist **Helper**, nicht Sensor und nicht Gerät.

Verifizierte Quelle: [`/integrations/input_boolean/`](https://www.home-assistant.io/integrations/input_boolean/) (Konfigurationsschlüssel `name`/`initial`/`icon`, Dienste `turn_on`/`turn_off`/`toggle`/`reload`, Zustände `on`/`off`, Restore-Verhalten). Namens-Mechanik referenziert über `ha/naming-conventions`.

## Wann verwenden

Verwende `input_boolean` für einen **vom Benutzer schaltbaren An/Aus-Zustand**, den HA persistent hält und Menschen wie Automationen umlegen — kein gemessener Wahr/Falsch-Zustand der realen Welt. Typische Anwendungsfälle:

- **Manuelle Übersteuerung** — ein vom Bewohner gesetzter Modus-Schalter wie „Urlaubsmodus an" oder „Gästemodus", der das normale Verhalten gezielt aussetzt
- **Automations-Flag** — ein Feature-Flag, das eine Automation aktiviert/deaktiviert, ohne sie selbst zu ändern
- **Bedingungs-Gate** — als `state`-Bedingung (`state: "on"`) eine Automation nur dann laufen lassen, wenn das Flag aktiviert ist
- **Reaktion auf Umschaltung** — per `state`-Trigger (`to: "on"`) auf eine manuelle Übersteuerung durch den Benutzer reagieren
- **Dashboard-Schalter** — als `entities`-Zeile, `button`/`tile` mit `toggle`-Aktion oder `input_boolean`-Karte in der Oberfläche bedienbar machen

Ein `input_boolean` ist das richtige Werkzeug, sobald ein **benutzer-schaltbarer, persistenter An/Aus-Zustand** gebraucht wird. Geht es um einen gemessenen Zustand, einen Einmal-Auslöser, eine aufrufbare Sequenz oder eine Mehrfach-Auswahl, greift ein anderer Baustein (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Die YAML-/UI-Konfiguration eines `input_boolean` (Schlüssel, Restore-Semantik) verbindlich festschreiben
- Den korrekten Einsatz als Automations-Flag, manuelle Übersteuerung und Bedingungs-Gate fixieren
- Die exponierten Dienste (`turn_on`/`turn_off`/`toggle`) und das Lesen des Zustands aus Trigger/Bedingung/Template festlegen
- Klar abgrenzen, wann ein `input_boolean` **nicht** das richtige Werkzeug ist und welcher Baustein stattdessen greift

## Nicht-Ziele

- Das Trigger-/Bedingungs-/Aktions-Modell der Automation selbst — `ha-automation/automation`
- Template-Syntax im Allgemeinen — `/docs/configuration/templating/`, hier nur die Lese-Muster
- Die Namens-Dimension (`name`, snake_case-`object_id`, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Gemessene Wahr/Falsch-Zustände der realen Welt — `binary_sensor` bzw. `ha-automation/template`

## Anforderungen

### Konfiguration

- **MUSS [MUST]** ein `input_boolean` über den Top-Level-Schlüssel `input_boolean` mit mindestens einer object_id strukturieren; pro Eintrag sind die Schlüssel `name`, `initial`, `icon` optional (es gibt keinen Pflicht-Wert-Schlüssel)
- **MUSS [MUST]** die `object_id` als snake_case-Slug und den `name` englisch sowie ≤50 Zeichen halten (Mechanik: `ha/naming-conventions`)
- **SOLLTE [SHOULD]** den Schlüssel `initial` bewusst behandeln: Ist `initial` gesetzt, startet HA immer mit diesem Wert; ist `initial` nicht gesetzt, wird der Zustand vor dem Stopp wiederhergestellt (und ohne wiederherstellbaren Zustand `off`) — laut Doku
- **SOLLTE NICHT [SHOULD NOT]** `initial` setzen, wenn der vom Benutzer zuletzt gewählte Zustand einen Neustart überdauern soll — ein hart gesetztes `initial` überschreibt das Restore-Verhalten bei jedem Start
- **KANN [MAY]** `icon` setzen, um das Element in der Oberfläche zu kennzeichnen

### Nutzung in Automationen & Templates

- **MUSS [MUST]** den Zustand als `on`/`off` lesen: in Bedingungen per `state`-Bedingung (`state: "on"`), in Triggern per `state`-Trigger (`to: "on"`), in Templates per `is_state('input_boolean.x', 'on')` bzw. `states('input_boolean.x')`
- **SOLLTE [SHOULD]** ein `input_boolean` als **Gate-Bedingung** einsetzen, um eine Automation nur bei aktiviertem Flag laufen zu lassen, statt das Gate in jeder Aktion einzeln zu prüfen
- **MUSS [MUST]** zum programmatischen Umschalten die dokumentierten Dienste `input_boolean.turn_on`, `input_boolean.turn_off` und `input_boolean.toggle` verwenden (Ziel über `target.entity_id`); `input_boolean.reload` lädt die YAML-Helfer neu
- **KANN [MAY]** auf den `state`-Trigger eines `input_boolean` reagieren, um auf eine manuelle Übersteuerung durch den Benutzer zu reagieren
- **KANN [MAY]** das Element auf einem Dashboard über eine `entities`-Zeile, einen `button`/`tile` mit `toggle`-Aktion oder eine `input_boolean`-Karte einbinden

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** ein `input_boolean` als Träger eines **gemessenen** Wahr/Falsch-Zustands der realen Welt verwenden (z. B. „Tür offen", „Bewegung erkannt") — dafür ist ein **`binary_sensor`** oder ein **Template-Binary-Sensor** (`ha-automation/template`) das richtige Konstrukt, weil dieser eine echte Messquelle hat und nicht vom Benutzer editierbar ist
- **SOLLTE NICHT [SHOULD NOT]** ein `input_boolean` nutzen, um einen **berechneten/abgeleiteten** booleschen Ausdruck zu „speichern", den eine Automation per `turn_on`/`turn_off` nachführt — das ist anfällig (Race-Conditions, Drift nach Neustart) und verliert die Quelle; stattdessen einen **Template-Binary-Sensor** definieren, der den Ausdruck deklarativ ableitet
- **SOLLTE NICHT [SHOULD NOT]** ein `input_boolean` als Auslöser für eine wiederverwendbare Aktionssequenz zweckentfremden (Flag setzen → Automation lauscht), wenn die Sequenz manuell/mehrfach aufrufbar sein soll — dafür ist ein **Skript** (`ha-automation/script`) gedacht, das einen aufrufbaren Dienst exponiert
- **SOLLTE NICHT [SHOULD NOT]** ein `input_boolean` als reinen Einmal-Auslöser (Knopfdruck ohne Folgezustand) verwenden — dafür ist ein **`input_button`** (`ha-automation/input-button`) gedacht, das zustandslos ist und keinen `off`-Zustand zurücklassen muss
- **SOLLTE NICHT [SHOULD NOT]** mehrere fast gleiche `input_boolean` für eine auswählbare Option anlegen (z. B. drei Booleans für drei Modi) — dafür ist ein **`input_select`** das passende Helfer-Konstrukt, weil es genau eine Option erzwingt

## Akzeptanzkriterien

- [ ] Jeder Helfer wird über den Top-Level-Schlüssel `input_boolean` mit snake_case-`object_id` und englischem `name` ≤50 Zeichen angelegt
- [ ] `initial` wird nur gesetzt, wenn ein fester Startwert erwünscht ist; soll der Zustand den Neustart überdauern, bleibt `initial` ungesetzt
- [ ] Zustand wird ausschließlich als `on`/`off` über `state`-Trigger/-Bedingung bzw. `is_state(...)`/`states(...)` gelesen
- [ ] Umschalten erfolgt über `input_boolean.turn_on`/`turn_off`/`toggle` mit `target.entity_id`
- [ ] Kein `input_boolean` trägt einen gemessenen oder berechneten Real-World-Zustand (dafür `binary_sensor`/Template-Sensor)
- [ ] Kein `input_boolean` ersetzt ein `input_button`, ein `script` oder ein `input_select`
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

Keine offenen Fragen.
