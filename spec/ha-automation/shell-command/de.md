# HA-Automation: Shell Command nutzen

Status: draft

## Kontext

Die `shell_command`-Integration macht aus benannten Kommandozeilen-Befehlen aufrufbare Aktionen. In der `configuration.yaml` wird unter dem Schlüssel `shell_command:` ein Alias auf einen Befehls-String abgebildet (z. B. `restart_pow: touch ~/.pow/restart.txt`); jeder Alias wird als Aktion `shell_command.<alias>` exponiert und ist aus Automationen und Skripten aufrufbar.

Der Befehls-String unterstützt **Templating**, läuft mit Templates aber in einer **abgesicherten Umgebung**: Die Doku stellt klar, dass dort keine Shell-Helfer erlaubt sind — kein Home-Verzeichnis-Kürzel `~`, keine Pipes `|`, keine Umleitungs-Operatoren — und dass **nur der Teil nach dem ersten Leerzeichen** aus einem Template stammen darf; der Befehlsname selbst muss literal stehen. Befehle laufen mit Arbeitsverzeichnis `/config`, werden nach **60 Sekunden** abgebrochen, und ihre `stdout`/`stderr` werden auf Log-Level `debug` protokolliert. Aufrufer können über `response_variable` ein Dictionary mit `stdout`, `stderr` und `returncode` einsammeln.

Reale Einordnung: `shell_command` ist eine **System-/Befehls-Integration** mit Integrations-Karte unter `/integrations/shell_command/`, aber ohne verbindbares Gerät. Sie ist sicherheitssensibel: Der Befehl läuft (auf HA OS) im `homeassistant`-Container als root. Im `ha-automation`-Korpus ist sie der Ausweg für genau die lokale Systeminteraktion, die keine Integration abdeckt.

Verifizierte Quelle: [`/integrations/shell_command/`](https://www.home-assistant.io/integrations/shell_command/) (Konfigurations-Mapping, Aufruf `shell_command.<alias>`, Template-Einschränkungen, `~`/`|`/Redirect-Verbot mit Templates, „only content after the first space", `response_variable` mit `stdout`/`stderr`/`returncode`, 60-Sekunden-Timeout, Arbeitsverzeichnis `/config`, Debug-Logging).

## Wann verwenden

Verwende `shell_command` für eine **lokale, kurzlebige Systeminteraktion**, die keine native Integration abdeckt und als benannter Befehl mit kontrollierten Werten ausgeführt wird. Typische Anwendungsfälle:

- **Lokales CLI-Tool auslösen** — ein in HA verfügbares Kommandozeilen-Werkzeug aus einer Automation aufrufen, das kein passendes Integrations-Pendant hat
- **Datei im `/config`-Verzeichnis berühren** — eine Datei anlegen/aktualisieren (z. B. ein Trigger-/Flag-File), wobei der Befehl im Arbeitsverzeichnis `/config` läuft
- **Exit-Code-gesteuerte Verzweigung** — einen Befehl ausführen und über `response_variable` auf `returncode`/`stdout`/`stderr` verzweigen, statt Erfolg blind anzunehmen
- **Parametrisierter Befehl mit kontrollierten Daten** — Aktions-Daten über die dokumentierte Template-Variable (nur der Teil nach dem ersten Leerzeichen) in den literalen Befehl einsetzen
- **Kurze, nicht-interaktive Aufgabe** — ein in unter 60 Sekunden abgeschlossener, nicht-interaktiver Befehl ohne Pipes/Redirects/`~` im Template

Ein `shell_command` ist nur das richtige Werkzeug für **lokale, kurzlebige Befehle mit vollständig kontrollierten Werten**. Geht es um einen HTTP-Aufruf, einen langlaufenden/interaktiven Prozess, untrusted Input oder eine bereits vorhandene native Aktion, ist ein anderer Baustein richtig (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Konfigurations-Mapping (`shell_command:`-Alias → Befehl) und Aufruf-Vertrag (`shell_command.<alias>`) verbindlich festschreiben
- Die **Sicherheitsregel gegen Shell-Injection** (kein ungeprüftes Template/Untrusted-Input in den Befehls-String) als Kern-Anforderung fixieren
- Die dokumentierten Template-Einschränkungen (kein `~`/`|`/Redirect, nur nach erstem Leerzeichen, literaler Befehlsname) verankern
- Den Rückgabe-/Exit-Code-Pfad über `response_variable` (`stdout`/`stderr`/`returncode`) festschreiben
- Klar abgrenzen, wann **kein** `shell_command` das richtige Werkzeug ist

## Nicht-Ziele

- Die deklarative Skript-/Aktions-Syntax, in der der Aufruf eingebettet wird — `ha-automation/script`
- Das Trigger-/Bedingungs-Modell der Regel-Engine — `ha-automation/automation`
- HTTP-Aufrufe an externe Dienste — `ha-automation/rest-command`
- In-Sandbox-Python ohne Subprozess — `ha-automation/python-script`
- Die Namens-Dimension (Alias, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration und Aufruf

- **MUSS [MUST]** jeden Befehl unter `shell_command:` als Mapping `<alias>: <befehls-string>` definieren; der Alias wird zur Aktion `shell_command.<alias>`
- **MUSS [MUST]** den Alias als Kleinbuchstaben-snake_case vergeben — die Doku verbietet Camel-Case ausdrücklich („Use lowercase names and separate words with underscores"); Namens-Mechanik in `ha/naming-conventions`
- **MUSS [MUST]** den **Befehlsnamen literal** im String belassen — laut Doku darf nur der Teil **nach dem ersten Leerzeichen** aus einem Template stammen, der Befehlsname selbst nicht
- **SOLLTE [SHOULD]** voraussetzen, dass der Befehl im Arbeitsverzeichnis `/config` läuft, und Pfade entsprechend relativ oder absolut wählen
- **MUSS [MUST]** beachten, dass Befehle nach **60 Sekunden** abgebrochen werden — länger laufende Arbeit gehört nicht in ein `shell_command`

### Templating, Sicherheit und Rückgabe

- **MUSS NICHT [MUST NOT]** ungeprüften/untrusted Input (Benutzereingaben, Entitäts-Attribute aus Fremdquellen, frei editierbare Helfer) ungequotet in den Befehls-String interpolieren — das ist der klassische **Shell-Injection-Pfad**; nur kontrollierte, validierte Werte einsetzen
- **MUSS [MUST]** beim Einsatz von Templates die dokumentierten Einschränkungen der abgesicherten Umgebung respektieren: **kein** `~` (Home-Expansion), **keine** Pipes `|`, **keine** Umleitungs-Operatoren — diese Helfer sind mit Templates nicht verfügbar
- **MUSS [MUST]** Aktions-Daten ausschließlich über die dokumentierte Bridge in den Befehl bringen: die an die Aktion übergebenen Daten stehen „as a variable within the template" zur Verfügung — keine String-Verkettung im YAML außerhalb dieses Mechanismus
- **SOLLTE [SHOULD]** Erfolg/Misserfolg über `response_variable` auswerten und auf den `returncode` verzweigen (`response_variable` liefert ein Dictionary mit `stdout`, `stderr`, `returncode`) — ein Nicht-Null-Exit darf nicht stillschweigend ignoriert werden
- **KANN [MAY]** für Diagnose das Debug-Logging nutzen: `stdout` und `stderr` werden auf Log-Level `debug` protokolliert

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** untrusted oder template-erzeugten Input in den Befehls-String einbauen, ohne ihn strikt zu kontrollieren — Shell-Injection erlaubt beliebige Befehlsausführung (auf HA OS als root im `homeassistant`-Container); wenn der Wert nicht vollständig kontrolliert ist, ist `shell_command` das falsche Werkzeug, und die Aufgabe gehört in eine **Integration** mit typisierten Parametern
- **SOLLTE NICHT [SHOULD NOT]** `shell_command` für einen **HTTP-Aufruf** (`curl`/`wget`) an einen externen Dienst missbrauchen — dafür ist `rest_command` (`ha-automation/rest-command`) gedacht, das `method`/`url`/`payload`/`headers`/`verify_ssl`/`timeout` deklarativ und ohne Shell-Risiko abbildet und die Antwort strukturiert zurückgibt
- **SOLLTE NICHT [SHOULD NOT]** lang laufende oder interaktive Prozesse (Daemons, Watcher, Prozesse mit Eingabeerwartung) per `shell_command` starten — der **60-Sekunden-Timeout** bricht sie ab; solche Bedürfnisse gehören in eine **Add-on-/Integration**, die einen langlebigen Prozess sauber verwaltet
- **SOLLTE NICHT [SHOULD NOT]** ein `shell_command` einsetzen, wo es bereits eine **native Integration oder Aktion** für das Zielsystem gibt — die native Aktion ist portabler, getestet und ohne Subprozess-/Pfad-Annahmen (`/config`-Arbeitsverzeichnis) als die Shell-Auslagerung
- **SOLLTE NICHT [SHOULD NOT]** Pipes/Redirects/`~` in einem getemplateten Befehl erwarten — die abgesicherte Umgebung erlaubt sie nicht; wer eine Pipeline braucht, kapselt sie in ein versioniertes Skript-File (literaler Befehlsname) statt im Template, oder wechselt das Werkzeug

## Akzeptanzkriterien

- [ ] Jeder Befehl ist als `shell_command:`-Alias (Kleinbuchstaben-snake_case) → Befehls-String definiert; der Befehlsname steht literal
- [ ] Kein untrusted/template-erzeugter Input wird ungeprüft in den Befehls-String interpoliert (Injection-Schutz)
- [ ] Getemplatete Befehle verwenden kein `~`, keine Pipes `|`, keine Redirects (Einschränkungen der abgesicherten Umgebung)
- [ ] Aktions-Daten gelangen nur über die dokumentierte Template-Variable in den Befehl
- [ ] Erfolg/Misserfolg wird über `response_variable` (`returncode`) ausgewertet; Nicht-Null-Exit wird nicht stillschweigend ignoriert
- [ ] Kein Befehl läuft konzeptionell länger als 60 Sekunden bzw. interaktiv
- [ ] HTTP-Aufrufe nutzen `rest_command`, nicht `shell_command`; vorhandene native Aktionen werden bevorzugt
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Quoting-Hilfe für Templates**: Die gelesene Doku-Seite nennt das Injection-Risiko, verankert aber keinen konkreten Quoting-/Escaping-Filter für den Template-Teil. Soll diese Spec eine eigene Regel zu sicherem Quoting (oder zur Pflicht, dynamische Werte über die Daten-Variable statt String-Konkatenation zu führen) verbindlich machen, oder bleibt es bei der „nur kontrollierte Werte"-Regel?
