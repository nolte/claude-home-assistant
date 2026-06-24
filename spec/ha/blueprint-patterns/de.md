# HA-Blueprint: Authoring-Patterns

Status: draft

## Kontext

Ein Home-Assistant-**Blueprint** ist eine Automation-, Script- oder Template-Entity-Konfiguration, in der einzelne Stellen bewusst leer gelassen sind, damit der Nutzer sie ohne Code befüllen kann ([HA-Doku: Blueprints](https://www.home-assistant.io/docs/blueprint/)). Genau drei Domains werden unterstützt: `automation`, `script` und `template`. Anders als eine Custom Integration (Python, Coordinator, Config-Flow) ist ein Blueprint ein reines **YAML-Artefakt** ohne Laufzeit-Code — die gesamte Qualität entscheidet sich an der Schema-Korrektheit, der UX der Eingabefelder (Selectors) und der Template-Robustheit.

Ein Blueprint lebt als `.yaml`-Datei unter `<config>/blueprints/<domain>/<author>/<file>.yaml` ([HA-Doku: Tutorial](https://www.home-assistant.io/docs/blueprint/tutorial/), [Using Blueprints](https://www.home-assistant.io/docs/automation/using_blueprints/)). Der Top-Level-Schlüssel `blueprint:` verlangt nur `name` und `domain`; alles andere (`description`, `author`, `homeassistant.min_version`, `input`, `source_url`) ist optional ([HA-Doku: Schema](https://www.home-assistant.io/docs/blueprint/schema/)). Konkrete Werte werden über den Custom-YAML-Tag `!input <name>` referenzierbar gemacht; jeder so referenzierte Eingang muss in der `input:`-Map deklariert sein.

Der zentrale Hebel für Wiederverwendbarkeit sind **Selectors**: Sie definieren sowohl die akzeptierten Werte eines Eingangs als auch dessen Darstellung in der HA-UI — „gute Selectors machen ein Blueprint aus der UI heraus benutzbar" ([HA-Doku: Selectors](https://www.home-assistant.io/docs/blueprint/selectors/)). Importierte Blueprints merken sich ihre `source_url`, sodass HA sie später erneut von der Quelle aktualisieren kann.

Diese Spec destilliert die offizielle HA-Blueprint-Doku (Stand 2024–2026) in eine verbindliche Authoring-Konvention für jeden Blueprint, den Skills oder Agents dieses Plugins generieren. Da Blueprints kein Quality-Scale-Pendant haben (der Quality-Scale gilt für Integrationen), ist der Qualitätsmaßstab hier die offizielle Doku plus die etablierten Forum-Konventionen aus „Share your Blueprints".

## Ziele

- Den `blueprint:`-Header und das Datei-Layout (`blueprints/<domain>/<author>/<file>.yaml`) als verbindliche Struktur festschreiben
- Selectors als primäre UX-Oberfläche erzwingen: jeder Eingang trägt einen typgerechten Selector statt eines nackten Freitextfeldes
- `target`/`entity`-Selectors gegenüber `device`-Selectors bevorzugen, damit Blueprints geräte-übergreifend funktionieren
- Den Templating-Pfad korrekt verdrahten: `!input` niemals direkt in Templates, sondern über `variables:` bzw. `trigger_variables:` brücken
- Einen bewussten `mode` (mit `max` bei `queued`/`parallel`) statt des stillen `single`-Defaults verlangen, wo die Automation es braucht
- Robustheit gegen `unavailable`/`unknown`-Zustände und sinnvolle Defaults als Pflicht etablieren
- Versions- und Distributions-Disziplin festschreiben (`source_url`, rückwärtskompatible Updates, My-Home-Assistant-Import-Link)

## Nicht-Ziele

- Custom-Integration-Patterns (Coordinator, Config-Flow, Entity-Architektur) — abgedeckt durch die übrigen `ha/`-Specs
- HACS-Distribution von Blueprints als Repository — eigene Folge-Spec, sobald ein konkreter Bedarf entsteht
- Vollständige Selector-Referenz — diese Spec verlangt korrekten Selector-Einsatz, repliziert aber nicht die erschöpfende [Selector-Tabelle der HA-Doku](https://www.home-assistant.io/docs/blueprint/selectors/)
- Authoring von Jinja-Templates jenseits der Blueprint-spezifischen `!input`-Brücke — generelles Template-Hardening ist HA-weites Wissen, nicht Blueprint-spezifisch
- Übersetzung/Lokalisierung von Blueprint-Texten — HA-Blueprints tragen ihre Texte inline; ein i18n-Mechanismus existiert (noch) nicht

## Anforderungen

### Blueprint-Header und Datei-Layout

- **MUSS [MUST]** den Top-Level-Schlüssel `blueprint:` mit mindestens `name` und `domain` führen; `domain` ist genau einer aus `automation`, `script`, `template`
- **MUSS [MUST]** die Datei mit `.yaml`-Endung unter `<config>/blueprints/<domain>/<author>/<file>.yaml` ablegen — `<author>` ist der Autor-/Namespace-Ordner, `<domain>` matched den `domain`-Schlüssel
- **MUSS [MUST]** eine `description` setzen, die in vollständigen Sätzen erklärt, was das Blueprint tut und welche Eingaben es erwartet — sie ist die einzige Doku, die der Nutzer beim Import sieht
- **SOLLTE [SHOULD]** `description` als Markdown-Mehrzeiler (YAML `>` oder `|`) formulieren und für **nicht-technische Nutzer** verständlich halten (kein internes Jargon, keine Entity-IDs im Fließtext)
- **SOLLTE [SHOULD]** `source_url` auf die kanonische Quelle (Forum-Post oder GitHub-Raw-URL) setzen, sobald das Blueprint geteilt wird — HA speichert sie für spätere Updates
- **SOLLTE [SHOULD]** `homeassistant: { min_version: <YYYY.M.0> }` setzen, wenn das Blueprint Features verwendet, die eine Mindest-HA-Version verlangen (siehe Sections: `2024.6.0`)
- **KANN [MAY]** `author` setzen; fehlt er, dient der Namespace-Ordner als faktischer Autor-Marker
- **MUSS NICHT [MUST NOT]** ausführbare Konfiguration (Trigger, Conditions, Actions, Sequence) in den `blueprint:`-Block schachteln — die liegen auf der Top-Level-Ebene der Datei neben `blueprint:`

### Inputs

- **MUSS [MUST]** jeden über `!input <name>` referenzierten Wert in `blueprint.input.<name>` deklarieren — ein `!input` ohne passende Deklaration bricht den Import
- **MUSS [MUST]** pro Input mindestens `name` (UI-Label) und einen `selector` führen; `description` ist dringend empfohlen
- **MUSS [MUST]** einen Input ohne `default` als **Pflichtfeld** behandeln; ein gesetzter `default` macht ihn optional (der Nutzer kann ihn leer lassen)
- **SOLLTE [SHOULD]** für optionale Verhaltens-Erweiterungen (z. B. „zusätzliche Aktion") einen sinnvollen `default` setzen — typisch `default: []` für Action-/Entity-Listen, sodass das Blueprint ohne Befüllung lauffähig bleibt
- **SOLLTE [SHOULD]** zusammengehörige Inputs in **Sections** gruppieren: eine Section ist ein Input-Eintrag, der selbst einen verschachtelten `input:`-Schlüssel enthält, und unterstützt `collapsed: true` zum Einklappen per Default
- **MUSS [MUST]** bei Verwendung von Sections `homeassistant.min_version: 2024.6.0` (oder höher) setzen — Sections sind erst ab dieser Version verfügbar
- **MUSS NICHT [MUST NOT]** dieselbe Input-Bezeichnung doppelt vergeben oder einen Input deklarieren, der nirgends per `!input` referenziert wird (toter Eingang)

### Selectors

- **MUSS [MUST]** jedem Input einen domänen-gerechten Selector geben (`entity`, `target`, `device`, `area`, `number`, `boolean`, `time`, `action`, `text`, `select`, `object`, …) statt eines nackten Freitext-Felds
- **SOLLTE [SHOULD]** für die Auswahl von zu steuernden Geräten/Entitäten einen `target`- oder `entity`-Selector gegenüber einem `device`-Selector **bevorzugen** — `target`/`entity` funktionieren entity-übergreifend und brechen nicht, wenn der Nutzer ein anderes Gerätemodell verwendet
- **MUSS [MUST]** Selectors filtern, wo sinnvoll: `entity`-Selectors per `domain`, `device_class`, `integration` oder `supported_features` einengen, damit der Nutzer nur passende Werte angeboten bekommt (z. B. `domain: binary_sensor`, `device_class: motion`)
- **SOLLTE [SHOULD]** `multiple: true` setzen, wenn der Input fachlich mehrere Werte aufnehmen soll — der gelieferte Wert ist dann eine **Liste** statt eines Einzel-Strings; Actions/Templates müssen das berücksichtigen
- **SOLLTE [SHOULD]** bei `number`-Selectors `min`, `max`, `step` und — wo sinnvoll — `unit_of_measurement` und `mode` (`slider`/`box`) setzen, damit die UI sinnvolle Grenzen rendert
- **MUSS NICHT [MUST NOT]** einen `device`-Selector verwenden, nur um anschließend per Template die zugehörigen Entitäten aufzulösen, wenn ein direkter `entity`/`target`-Selector dasselbe ohne Template-Fragilität leistet

### Templating-Brücke (`variables` / `trigger_variables`)

- **MUSS [MUST]** einen `!input`-Wert, der in einem **Template** (Jinja) gebraucht wird, zuerst über einen `variables:`-Block (Script-Level) auf einen benannten Variablen-Namen mappen — `!input` ist außerhalb der Blueprint-Metadaten referenzierbar, steht aber **nicht** direkt als Template-Variable zur Verfügung
- **MUSS [MUST]** für `!input`-Werte, die in **Trigger-Konfiguration** (z. B. templated `value_template`, `for`) gebraucht werden, den Automation-Level-Block `trigger_variables:` verwenden — er existiert genau zu diesem Zweck (Blueprint-Inputs in Triggern verfügbar machen)
- **MUSS [MUST]** akzeptieren, dass `trigger_variables` nur **limitierte Templates** zulassen und sich **nicht** neu anwenden, wenn sich der Template-Wert ändert — keine Logik dort platzieren, die auf Laufzeit-Reevaluation angewiesen ist
- **SOLLTE [SHOULD]** `variables` (per-Trigger/Action, reagiert auf Trigger-Match) und `trigger_variables` (Automation-Level, einmal zur Setup-Zeit) bewusst auseinanderhalten — beide sind eigene Variablen-Typen mit unterschiedlichem Lebenszyklus
- **MUSS NICHT [MUST NOT]** `!input` direkt in einen Jinja-Ausdruck schreiben (`{{ !input foo }}`) — das ist syntaktisch ungültig und der häufigste Import-Bruch

### Automation-spezifisch: Mode, Trace, ID

- **MUSS [MUST]** den `mode` bewusst wählen — `single` (Default), `restart`, `queued` oder `parallel`; die Wahl wird über das erwartete Trigger-Verhalten begründet, nicht dem stillen Default überlassen
- **MUSS [MUST]** bei `mode: queued` oder `mode: parallel` `max` explizit setzen oder den Default `10` bewusst akzeptieren — `max` deckelt gleichzeitig laufende und/oder eingereihte Läufe
- **SOLLTE [SHOULD]** `restart` für „neuester Trigger gewinnt"-Logik (z. B. Bewegungs-Licht mit Nachlaufzeit) und `single` für nicht-reentrante Abläufe wählen
- **KANN [MAY]** die generierte Automation eine stabile `id` tragen, damit Trace und UI-Referenzen über Reimporte stabil bleiben
- **SOLLTE [SHOULD]** so strukturiert sein, dass die HA-**Trace**-Ansicht aussagekräftig bleibt (benannte Steps, keine monolithische Template-Action, in der jede Logik verschwindet)

### Script- und Template-Blueprints

- **MUSS [MUST]** für `domain: script` die ausführbare Logik unter `sequence:` führen (statt `trigger`/`action`) — Script-Blueprints haben keine Trigger
- **MUSS [MUST]** für `domain: template` die Template-Entity-Konfiguration gemäß der jeweiligen Template-Plattform strukturieren (z. B. `sensor:`, `binary_sensor:`) — Template-Blueprints definieren Entitäten, keine Automationen
- **MUSS NICHT [MUST NOT]** automation-spezifische Schlüssel (`mode`, `trigger`, `trigger_variables`) in Script- oder Template-Blueprints verwenden, wo die Domain sie nicht kennt
- **KANN [MAY]** dieselben Input-/Selector-/`variables`-Patterns wie ein Automation-Blueprint nutzen — die Eingabe-Schicht ist domain-übergreifend identisch

### Robustheit und UX

- **MUSS [MUST]** Templates gegen `unavailable`/`unknown`/`None`-Zustände absichern (z. B. `states('sensor.x') not in ['unavailable','unknown']` prüfen, `default`-Filter in Jinja verwenden), bevor auf den Wert zugegriffen wird
- **MUSS NICHT [MUST NOT]** Entity-IDs, Bereichs-Namen oder andere installationsspezifische Werte hart kodieren — alles Konfigurierbare läuft über `!input` mit Selector
- **SOLLTE [SHOULD]** sinnvolle Defaults so wählen, dass das Blueprint mit minimaler Befüllung (nur Pflichtfelder) sofort lauffähig ist
- **SOLLTE [SHOULD]** Conditions defensiv formulieren, sodass wiederholte Trigger-Auslösungen idempotent bleiben (kein Doppel-Schalten, kein Aufschaukeln)
- **MUSS [MUST]** gültiges YAML produzieren, das HAs Blueprint-Schema-Validierung besteht — ein Blueprint, das beim Import scheitert, ist wertlos

### Distribution und Versionierung

- **SOLLTE [SHOULD]** beim Teilen einen **My-Home-Assistant-Import-Link** (`https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=<url>`) bereitstellen — er öffnet den Import-Dialog mit vorausgefülltem Blueprint per einzelner URL
- **MUSS [MUST]** beim Aktualisieren eines bereits veröffentlichten Blueprints **rückwärtskompatibel** bleiben: bestehende Selectors und Input-Namen **nicht** umbenennen oder entfernen; **neu** hinzugefügte Inputs/Selectors **müssen** einen `default` tragen, damit bestehende Automationen weiterlaufen
- **SOLLTE [SHOULD]** bei substanziellen, nicht rückwärtskompatiblen Änderungen ein **neues** Blueprint anlegen statt das bestehende brechend zu ändern
- **KANN [MAY]** eine Versionsangabe in `description` oder als Kommentar führen — HA hat kein eigenes Blueprint-Versionsfeld
- **SOLLTE [SHOULD]** wissen, dass ein erneuter Import zwar Inhalte (z. B. `description`) aktualisiert, die gespeicherte `source_url` aber bei einer im YAML geänderten Quelle **nicht** mit-aktualisiert wird (bekanntes Core-Verhalten, [core#123025](https://github.com/home-assistant/core/issues/123025)) — die kanonische `source_url` daher von Anfang an stabil wählen

## Akzeptanzkriterien

- [ ] `blueprint:` enthält `name` und `domain`; `domain` ∈ {`automation`, `script`, `template`}
- [ ] Datei liegt unter `blueprints/<domain>/<author>/<file>.yaml` mit `.yaml`-Endung
- [ ] `description` erklärt Zweck und Eingaben in vollständigen, nicht-technischen Sätzen
- [ ] Jeder `!input`-Verweis hat eine korrespondierende `blueprint.input.<name>`-Deklaration; kein toter oder doppelter Input
- [ ] Jeder Input trägt einen typgerechten `selector`; kein nacktes Freitextfeld für strukturierte Werte
- [ ] Geräte-/Entity-Auswahl nutzt `target`/`entity` statt `device`, wo entity-übergreifende Funktion gefragt ist
- [ ] Selectors sind gefiltert (`domain`/`device_class`/`integration`), wo es die Auswahl sinnvoll einengt
- [ ] `multiple: true`-Inputs werden in Actions/Templates als Liste behandelt
- [ ] Kein `!input` steht direkt in einem Jinja-Template; Templating läuft über `variables` bzw. `trigger_variables`
- [ ] Sections (falls verwendet) gehen mit `homeassistant.min_version: 2024.6.0` einher
- [ ] `mode` ist bewusst gesetzt; bei `queued`/`parallel` ist `max` explizit oder bewusst auf Default belassen
- [ ] Templates sind gegen `unavailable`/`unknown` abgesichert; keine hart kodierten installationsspezifischen Werte
- [ ] Neu hinzugefügte Inputs (bei Updates) tragen `default`; bestehende Input-Namen/Selectors sind unverändert
- [ ] Das Blueprint besteht HAs Schema-Validierung (Import bzw. `hass --script check_config` lokal)

## Offene Fragen

- **Validierungs-Toolchain**: Welcher lokal ausführbare Check verifiziert ein Blueprint ohne laufende HA-Instanz am verlässlichsten? Kandidaten: ein YAML-Schema-Lint, `hass --script check_config` in einem Container, oder ein dedizierter Blueprint-Schema-Validator. Bis geklärt, ist der Import in eine HA-Instanz der maßgebliche Gate.
- **Referenz-Blueprint im Portfolio**: Anders als die Integration-Specs (geerdet in `nolte/kamerplanter-ha`) hat diese Spec noch kein Portfolio-internes Referenz-Blueprint. Sobald eines existiert, sollten dessen konkrete Patterns hier als Beispiel verankert werden.
- **Template-Blueprint-Tiefe**: Die Template-Domain ist hier nur grob abgegrenzt. Sobald ein realer Template-Blueprint entsteht, braucht es ggf. eine eigene `ha/template-blueprint`-Spec mit Plattform-spezifischen Anforderungen.
- **Sections-Mindestversion vs. Zielgruppe**: Sections verlangen `2024.6.0`. Soll die Spec Sections generell empfehlen (UX-Gewinn) oder konservativ bleiben, damit Blueprints auch ältere HA-Installationen bedienen?
- **Idempotenz-Heuristik**: „Idempotent bei wiederholten Triggern" ist als SOLLTE formuliert. Eine prüfbare Heuristik (welche Condition-Muster gelten als ausreichend) fehlt noch.
