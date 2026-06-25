# HA-Automation: Python Script nutzen

Status: draft

## Kontext

Die `python_script`-Integration erlaubt es, kleine Python-Dateien als aufrufbare Aktionen auszuführen. Jede `.py`-Datei im Verzeichnis `<config>/python_scripts/` wird automatisch als Aktion `python_script.<dateiname>` exponiert und kann aus Automationen und Skripten aufgerufen werden. Aktiviert wird die Integration durch den leeren Eintrag `python_script:` in der `configuration.yaml`.

Die Ausführung läuft in einer **stark eingeschränkten Sandbox**: Es stehen die vorbereiteten Objekte `hass`, `data`, `logger`, `output` (sowie eingeschränkt `time`, `datetime`, `dt_util` und Builtins wie `min`/`max`) zur Verfügung. **`import` ist nicht möglich** — die Doku stellt ausdrücklich klar: „It is not possible to use Python imports with this integration." `hass` ist zudem beschnitten: „Access is only allowed to perform actions, set/remove states and fire events." Damit ist `python_script` kein vollwertiger Python-Interpreter, sondern ein eng begrenzter Ausweg für genau die wenigen Fälle, in denen die deklarative Skript-/Template-Syntax nicht ausreicht.

Reale Einordnung: `python_script` ist eine **fortgeschrittene Konfigurations-/Helfer-Integration** mit Integrations-Karte unter `/integrations/python_script/`, aber ohne verbindbares Gerät/Dienst. Im `ha-automation`-Korpus ist sie der letzte Ausweg, nicht das Standardwerkzeug: Die offizielle Doku selbst rät, sie nur dort einzusetzen, wo deklarative Mittel nicht genügen.

Verifizierte Quelle: [`/integrations/python_script/`](https://www.home-assistant.io/integrations/python_script/) (Aktivierung, `python_scripts/`-Verzeichnis, Sandbox-Objekte `hass`/`data`/`logger`/`output`, Import-Verbot, `response_variable`, `services.yaml`).

## Wann verwenden

Verwende `python_script` als **letzten Ausweg** für die wenigen Fälle, in denen die deklarative Skript-/Template-Syntax nicht ausreicht und eine kurze, importlose Python-Logik in der Sandbox genügt. Typische Anwendungsfälle:

- **Imperative Daten-Transformation** — eine Berechnung über `data`-Eingaben, deren Ergebnis über `output` per `response_variable` zurückgegeben wird, wenn ein Template zu umständlich wäre
- **Dynamischer Mehrfach-Aktionsaufruf** — über `hass.services.call(...)` in einer Schleife Aktionen für eine zur Laufzeit ermittelte Entitäten-Menge auslösen
- **Programmatisches State-Setzen** — mehrere States via `hass`-Sandbox-API setzen/entfernen, wo deklaratives YAML zu wiederholungslastig wäre
- **Custom-Event-Bridge** — mit `hass.bus.fire("event_name", {...})` ein benanntes Event mit berechneten Daten feuern, auf das Automationen triggern
- **Sandbox-sichere Hilfslogik** — kleine, in sich geschlossene Logik mit den erlaubten Builtins (`min`/`max`) und `time`/`datetime`/`dt_util`, dokumentiert über `services.yaml`

Ein `python_script` ist nur das richtige Werkzeug, wenn die Logik **deklarativ nicht ausdrückbar** ist und ohne Imports, Drittbibliotheken oder Netzwerk auskommt. Lässt sie sich als Skript/Template/Automation schreiben oder braucht sie HTTP/Bibliotheken/Nebenläufigkeit, ist ein anderer Baustein richtig (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Aktivierung, Ablage (`<config>/python_scripts/`) und Aufruf-Vertrag (`python_script.<name>`) verbindlich festschreiben
- Den Sandbox-Kontrakt (verfügbare Objekte, Import-Verbot, beschnittenes `hass`) als harte Grenze fixieren
- Den Datenfluss `data` (Eingabe) → `output` (Rückgabe via `response_variable`) als einzig dokumentierten Weg verankern
- `logger` als einzigen Logging-Pfad und die Dokumentation über `services.yaml` festschreiben
- Klar abgrenzen, dass `python_script` der Ausweg ist und **wann es NICHT** gewählt wird

## Nicht-Ziele

- Die deklarative Skript-/Aktions-Syntax (`choose`, `repeat`, `wait_*`, `response_variable` auf Skript-Ebene) — `ha-automation/script`
- Das Trigger-/Bedingungs-/Ausführungsmodell der Regel-Engine — `ha-automation/automation`
- Template-Syntax (Jinja) als deklarative Alternative — `/docs/configuration/templating/`
- Die Namens-Dimension (Datei-/Slug-Name, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Entwicklung einer vollwertigen Custom-Integration in Python (Imports, Netzwerk, Bibliotheken) — das ist Integrations-*Entwicklung*, kein Nutzungs-Scope

## Anforderungen

### Konfiguration und Ablage

- **MUSS [MUST]** die Integration durch den leeren Eintrag `python_script:` in `configuration.yaml` aktivieren; jede Skriptdatei liegt als `.py`-Datei in `<config>/python_scripts/`
- **MUSS [MUST]** den Dateinamen als snake_case-Slug (Kleinbuchstaben, Unterstriche) vergeben — er wird zur Aktion `python_script.<dateiname>`; Namens-Mechanik in `ha/naming-conventions`
- **SOLLTE [SHOULD]** jedes Skript über eine `<config>/python_scripts/services.yaml` mit Name, Beschreibung und Feldern dokumentieren, damit der UI-Editor sinnvolle Metadaten zeigt
- **KANN [MAY]** sich darauf verlassen, dass Änderungen ohne Neustart sofort greifen (kein Caching laut Doku); ein `python_script.reload` ist nicht erforderlich, um eine geänderte Datei zu aktivieren

### Sandbox-Kontrakt

- **MUSS NICHT [MUST NOT]** `import` verwenden — die Doku stellt klar: Imports sind in dieser Integration nicht möglich; ein Skript, das eine Bibliothek braucht, gehört nicht hierher
- **MUSS [MUST]** ausschließlich die bereitgestellten Objekte nutzen: `hass` (nur Aktionen ausführen, States setzen/entfernen, Events feuern), `data` (Eingabe-Dictionary), `logger` (Logging), `output` (Rückgabe-Dictionary); ergänzend stehen eingeschränkt `time`, `datetime`, `dt_util` und Builtins wie `min`/`max` bereit
- **MUSS [MUST]** beachten, dass `hass` beschnitten ist: erlaubt sind nur Aktionen, State-Manipulation und Event-Feuern — kein beliebiger Zugriff auf interne HA-Objekte
- **SOLLTE NICHT [SHOULD NOT]** auf Dateisystem, Netzwerk oder externe Prozesse zugreifen wollen — die Sandbox bietet dafür keine Objekte; solche Bedürfnisse sind ein Signal, das Werkzeug zu wechseln (siehe Abgrenzung)

### Aufruf, Eingabe, Rückgabe und Logging

- **MUSS [MUST]** Eingabeparameter ausschließlich über das `data`-Dictionary lesen (`data.get("name", "world")`); beim Aufruf werden sie als `data:`-Schlüssel der Aktion übergeben
- **MUSS [MUST]** Rückgabewerte ausschließlich über das `output`-Dictionary liefern und auf Aufrufer-Seite mit `response_variable` einsammeln (`response_variable: python_script_output`) — nicht über einen Umweg-Helfer (`input_*`)
- **MUSS [MUST]** Logging über das bereitgestellte `logger`-Objekt führen (`logger.info()`/`logger.warning()`/`logger.error()`); `print` oder eigene Logger sind in der Sandbox nicht vorgesehen
- **KANN [MAY]** über `hass.bus.fire("event_name", {...})` Events feuern und über `hass.services.call(domain, service, data, blocking)` Aktionen aufrufen — Letzteres mit `blocking=True, return_response=True`, wenn eine Service-Antwort eingesammelt werden soll

### Abgrenzung: Wann NICHT verwenden

- **SOLLTE NICHT [SHOULD NOT]** `python_script` für Logik einsetzen, die sich deklarativ in **Skript/Template/Automation** ausdrücken lässt — die Doku selbst positioniert es als Ausweg für den Rest; verzweigende Sequenzlogik gehört in `ha-automation/script` (`choose`/`if`/`repeat`), abgeleitete Werte in einen Template-Sensor (`ha-automation/template`), weil das deklarative Konstrukt versioniert, im UI editierbar und ohne Sandbox-Fallstricke ist
- **MUSS NICHT [MUST NOT]** `python_script` verwenden, wenn die Aufgabe einen **Import**, eine **Drittbibliothek** oder **Netzwerk-/HTTP-Zugriff** braucht — das ist in der Sandbox unmöglich; für HTTP ist `rest_command` (`ha-automation/rest-command`) zuständig, für alles Weitergehende eine echte **Custom-Integration**, weil nur sie Bibliotheken und einen langlebigen Client betreiben darf
- **SOLLTE NICHT [SHOULD NOT]** komplexe oder langlaufende Berechnungen in ein `python_script` legen — die Sandbox bietet keine Nebenläufigkeits-/Hintergrund-Primitiven; rechenintensive oder periodische Aufgaben gehören in eine **Custom-Integration** mit Coordinator (`ha/coordinator-patterns`), weil sie sauber im Event-Loop bzw. Executor laufen
- **SOLLTE NICHT [SHOULD NOT]** ein `python_script` schreiben, nur um einen Wert in eine State-Maschine zu zwingen, den ein **Template** direkt liefern könnte — `states('…')`, Filter und `is_state(…)` im Jinja-Template sind robuster und ohne Sandbox-Risiko
- **MUSS NICHT [MUST NOT]** unbeschränkten/ungeprüften Code aus fremder Quelle als `python_script` ablegen, weil er trotz Sandbox `hass`-Aktionen, States und Events manipulieren kann — die Sandbox begrenzt die API-Oberfläche, ersetzt aber kein Review

## Akzeptanzkriterien

- [ ] Die Integration ist über `python_script:` aktiviert; jede Datei liegt als snake_case-`.py` in `<config>/python_scripts/`
- [ ] Kein Skript enthält ein `import`; es nutzt ausschließlich `hass`/`data`/`logger`/`output` (plus erlaubte `time`/`datetime`/`dt_util`/Builtins)
- [ ] Eingaben werden über `data` gelesen, Rückgaben über `output` geliefert und per `response_variable` eingesammelt
- [ ] Logging läuft über das bereitgestellte `logger`-Objekt
- [ ] Skripte sind über `python_scripts/services.yaml` dokumentiert
- [ ] Kein `python_script` ersetzt deklarativ ausdrückbare Skript-/Template-/Automation-Logik
- [ ] Kein `python_script` versucht Imports, Drittbibliotheken oder Netzwerkzugriff (HTTP via `rest_command`, Weitergehendes via Custom-Integration)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Mehr-Datei-/Modulstruktur**: Die gelesene Doku-Seite verankert keinen Mechanismus, um ein `python_script` über mehrere Dateien zu strukturieren (kein Import zwischen Skripten). Soll diese Spec eine eigene Regel „ein Skript = eine Datei, keine Modul-Aufteilung" aufnehmen, oder bleibt das implizit über das Import-Verbot abgedeckt?
