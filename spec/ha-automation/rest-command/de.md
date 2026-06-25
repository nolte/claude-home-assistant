# HA-Automation: REST Command nutzen

Status: draft

## Kontext

Die `rest_command`-Integration macht aus benannten HTTP-Anfragen aufrufbare Aktionen. In der `configuration.yaml` wird unter dem Schlüssel `rest_command:` ein Service-Name auf eine Anfrage-Definition abgebildet; jeder Name wird als Aktion `rest_command.<service_name>` exponiert und ist aus Automationen und Skripten aufrufbar. Damit ist `rest_command` das deklarative Werkzeug, um aus einer Automation heraus **einmalige** HTTP-Aufrufe (Webhooks, Trigger-Endpunkte, Push-APIs) abzusetzen.

Die Anfrage wird über dokumentierte Konfigurationsvariablen beschrieben: Pflicht ist `url` (Template), optional `method` (Default `get`; erlaubt sind `get`/`patch`/`post`/`put`/`delete`), `payload` (Template), `headers` (Map), `content_type`, `username`/`password` mit `authentication` (Default `basic`, alternativ `digest`), `timeout` (Default `10` Sekunden), `verify_ssl` (Default `true`) sowie `insecure_cipher` und `skip_url_encoding`. `url`, `payload` und `headers` unterstützen Templates. Aufrufer können über `response_variable` ein Dictionary mit `status` (HTTP-Code), `content` (Body) und `headers` (Antwort-Header) einsammeln.

Reale Einordnung: `rest_command` ist eine **Befehls-/Integrations-Integration** mit Karte unter `/integrations/rest_command/`, aber ohne verbindbares Gerät. Sie sendet, sie pollt nicht: Im `ha-automation`-Korpus ist sie der ausgehende, einmalige HTTP-Aufruf — das Gegenstück zum einlesenden `rest`-/`restful`-Sensor.

Verifizierte Quelle: [`/integrations/rest_command/`](https://www.home-assistant.io/integrations/rest_command/) (Konfigurations-Mapping, Aufruf `rest_command.<service_name>`, Variablen `url`/`method`/`payload`/`headers`/`content_type`/`authentication`/`username`/`password`/`timeout`/`verify_ssl`/`insecure_cipher`/`skip_url_encoding` samt Defaults, Template-Unterstützung in `url`/`payload`/`headers`, `response_variable` mit `status`/`content`/`headers`).

## Wann verwenden

Verwende `rest_command` für einen **einmaligen, ausgehenden HTTP-Aufruf** aus einer Automation heraus — deklarativ über `url`/`method`/`payload`/`headers`, ohne State und ohne Polling. Typische Anwendungsfälle:

- **Webhook auslösen** — einen Push-/Trigger-Endpunkt eines externen Dienstes per `post` aufrufen, sobald eine Automation feuert
- **Zustand an eine Fremd-API senden** — mit `method` (`put`/`patch`/`post`) und einem getemplateten `payload` einen Wert aus einem Entitäts-Zustand an eine API übergeben
- **Dynamische Anfrage aus Entitäts-Daten** — `url`, `payload` und `headers` per Template aus aktuellen Zuständen zusammensetzen
- **Status-abhängige Verzweigung** — die Antwort über `response_variable` einsammeln und auf `status`/`content`/`headers` reagieren, statt einen Fehlerstatus zu ignorieren
- **Authentifizierter Einmal-Aufruf** — eine Anfrage mit `username`/`password` und `authentication` (`basic`/`digest`) sowie bewusstem `timeout` und `verify_ssl: true` absetzen

Ein `rest_command` ist nur das richtige Werkzeug für den **einmaligen ausgehenden Aufruf**. Geht es um periodisches Einlesen als Sensor, einen mehrstufigen Auth-Flow, einen bereits nativ abgedeckten Dienst oder eine lokale Systeminteraktion, ist ein anderer Baustein richtig (siehe `### Abgrenzung: Wann NICHT verwenden`).

## Ziele

- Konfigurations-Mapping (`rest_command:`-Name → Anfrage) und Aufruf-Vertrag (`rest_command.<name>`) verbindlich festschreiben
- Die dokumentierten Variablen und ihre **Defaults** (`method=get`, `timeout=10`, `verify_ssl=true`, `authentication=basic`) als verbindliche Basis fixieren
- Das Template-Modell in `url`/`payload`/`headers` und den korrekten `content_type` verankern
- Den Antwort-Pfad über `response_variable` (`status`/`content`/`headers`) und sauberes Status-Handling festschreiben
- Klar abgrenzen, dass `rest_command` ein **einmaliger ausgehender** Aufruf ist und **wann es NICHT** gewählt wird

## Nicht-Ziele

- Das **Einlesen** einer REST-API als Sensor (Polling) — `rest`/`restful`-Sensor-Integration (eigene Specs), hier nur als Abgrenzung referenziert
- Die deklarative Skript-/Aktions-Syntax, in der der Aufruf eingebettet wird — `ha-automation/script`
- Das Trigger-/Bedingungs-Modell der Regel-Engine — `ha-automation/automation`
- Lokale Subprozess-/Shell-Interaktion — `ha-automation/shell-command`
- Die Namens-Dimension (Service-Name, snake_case, Englisch, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert

## Anforderungen

### Konfiguration und Aufruf

- **MUSS [MUST]** jede Anfrage unter `rest_command:` als Mapping `<service_name>: { url: …, … }` definieren; der Name wird zur Aktion `rest_command.<service_name>`
- **MUSS [MUST]** `url` als Pflichtfeld setzen (Template erlaubt); fehlt es, ist die Definition unvollständig
- **MUSS [MUST]** den Service-Namen als snake_case-Slug vergeben; Namens-Mechanik in `ha/naming-conventions`
- **MUSS [MUST]** `method` bewusst aus `{get, patch, post, put, delete}` wählen, wenn der Default `get` nicht zur Operation passt — ein zustandsändernder Aufruf darf nicht versehentlich als `get` laufen
- **SOLLTE [SHOULD]** `timeout` bewusst setzen, wenn der Default `10` (Sekunden) für den Ziel-Endpunkt zu kurz oder zu lang ist
- **MUSS NICHT [MUST NOT]** `verify_ssl: false` setzen, ohne den Grund zu dokumentieren — der Default `true` ist sicherheitskritisch; `false`/`insecure_cipher: true` nur als bewusste Ausnahme für Altgeräte

### Templating, Payload und Antwort

- **KANN [MAY]** Templates in `url`, `payload` und `headers` verwenden, um dynamische Werte aus Entitäts-Zuständen einzusetzen
- **SOLLTE [SHOULD]** bei strukturiertem `payload` einen passenden `content_type` setzen (z. B. `application/json`), damit der Ziel-Dienst den Body korrekt interpretiert
- **SOLLTE [SHOULD]** Anmeldedaten über `username`/`password` mit dem passenden `authentication` (`basic`/`digest`) übergeben, statt sie in die `url` zu kodieren
- **SOLLTE [SHOULD]** die Antwort über `response_variable` einsammeln und auf `status` (HTTP-Code) verzweigen; `content` (Body) und `headers` (Antwort-Header) stehen ebenfalls zur Verfügung — ein Fehlerstatus darf nicht stillschweigend ignoriert werden
- **KANN [MAY]** `skip_url_encoding: true` setzen, wenn der Endpunkt eine bereits kodierte/kanonisierte URL erwartet — sonst beim Default belassen

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** `rest_command` verwenden, um eine REST-API **periodisch abzufragen** und ihren Wert als Zustand verfügbar zu machen — dafür ist der **`rest`-/`restful`-Sensor** zuständig, weil er ein Poll-Intervall, Wert-Templates und eine Entität mit Historie/Verfügbarkeit bietet; `rest_command` ist ein einmaliger, ausgehender Feuer-Aufruf ohne State
- **SOLLTE NICHT [SHOULD NOT]** `rest_command` für **mehrstufige Auth-Flows** (OAuth-Token holen, Refresh, Session-Cookies verwalten) einsetzen — das gehört in eine **Custom-Integration** mit `application_credentials`/Config-Flow (`ha/config-flow-patterns`, `ha/application-credentials`), die Tokens sicher speichert und erneuert; `rest_command` kennt nur `basic`/`digest` und hält keinen Sitzungszustand
- **SOLLTE NICHT [SHOULD NOT]** `rest_command` als Dauerlösung für einen Dienst nutzen, für den es bereits eine **native Integration** gibt — die Integration ist typisiert, fehler- und auth-robuster und liefert Entitäten statt rohem `content`, das im Template geparst werden muss
- **SOLLTE NICHT [SHOULD NOT]** lokale Systembefehle als HTTP verkleiden — wenn kein Netzwerk-Endpunkt beteiligt ist, ist `shell_command` (`ha-automation/shell-command`) oder eine native Aktion das richtige Werkzeug, nicht ein REST-Aufruf an `localhost`
- **MUSS NICHT [MUST NOT]** `verify_ssl: false` als Standard nutzen, um ein Zertifikatsproblem zu umgehen — das öffnet Man-in-the-Middle; die Ursache (CA/Hostname) gehört behoben, `verify_ssl: false`/`insecure_cipher` bleibt die dokumentierte, begründete Ausnahme

## Akzeptanzkriterien

- [ ] Jede Anfrage ist als `rest_command:`-Service-Name (snake_case) → Definition mit Pflicht-`url` gesetzt
- [ ] `method` ist bewusst gewählt (nicht versehentlich `get` bei zustandsändernden Aufrufen)
- [ ] `timeout` ist bewusst gesetzt, wenn der Default `10`s nicht passt
- [ ] `verify_ssl` bleibt `true`, außer eine dokumentierte Ausnahme rechtfertigt `false`/`insecure_cipher`
- [ ] Strukturierter `payload` trägt einen passenden `content_type`; Auth läuft über `username`/`password`/`authentication`, nicht über die URL
- [ ] Die Antwort wird über `response_variable` (`status`/`content`/`headers`) ausgewertet; ein Fehlerstatus wird nicht ignoriert
- [ ] Kein `rest_command` pollt eine API als Sensor (dafür `rest`/`restful`-Sensor) und keiner implementiert einen mehrstufigen Auth-Flow (dafür Custom-Integration)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Retry-/Fehler-Strategie**: Die gelesene Doku-Seite beschreibt `timeout`, aber keinen eingebauten Retry- oder Backoff-Mechanismus. Soll diese Spec eine eigene Regel verankern, wie Aufrufer auf einen Fehlerstatus reagieren (Wiederholung über die Skript-Syntax `repeat`/`until` vs. einfaches Verwerfen), oder bleibt das dem aufrufenden Skript überlassen?
