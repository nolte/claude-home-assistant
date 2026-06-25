# HA-Artefakte: Verifikation gegen offizielle Docs

Status: draft

## Kontext

Die Skills, Agents und Specs dieses Plugins erzeugen Home-Assistant-Artefakte — Custom Integrations (Python), Lovelace-Cards (TypeScript/JavaScript), Blueprints und Automationen (YAML) sowie ESPHome-/Add-on-Arbeit. HA-interne APIs, Namenskonventionen, Quality-Scale-Kriterien und Frontend-Verträge ändern sich über Releases hinweg; aus dem Gedächtnis reproduzierte Annahmen veralten still und propagieren dann in generierten Code, Specs und Antworten.

Home Assistant pflegt zwei maßgebliche, öffentlich versionierte Doku-Quellen:

- **Developer-Doku** — [`home-assistant/developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) (gerendert unter `developers.home-assistant.io`): Integration-Internals, Config-Flow, Entities, Coordinators, Quality-Scale, Frontend-/WebSocket-Verträge.
- **User-/Architektur-Doku** — [`home-assistant/home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (gerendert unter `www.home-assistant.io`): Architektur, Blueprints, YAML-Schemata, Endnutzer-zugewandtes Verhalten.

Diese Spec hebt die Verifikation gegen diese beiden Quellen von einer Ad-hoc-Gewohnheit zu einer querschnittlichen Pflicht für jedes HA-Artefakt, das dieses Plugin produziert. Sie ergänzt die bestehende `Adaptionsquelle`-Konvention in `spec/README.md`, die festhält, dass jede `ha/`-Spec an einer konkreten Doc-Datei verankert ist.

## Ziele

- Jede unsichere Aussage über HA-Internals gegen die offizielle Doku prüfen, bevor sie behauptet, in Code gegossen oder in eine Spec geschrieben wird
- Die beiden maßgeblichen Quellen eindeutig benennen und ihren jeweiligen Zuständigkeitsbereich abgrenzen
- Verifizierte Aussagen an einer konkreten Doc-Datei verankern, damit Drift später nachvollziehbar bleibt
- Die Pflicht so formulieren, dass sie sowohl Antworten an den Nutzer als auch generierte Artefakte abdeckt

## Nicht-Ziele

- Den Doku-Inhalt hier spiegeln oder zusammenfassen — diese Spec verlangt das Nachschlagen, sie ersetzt es nicht
- Eine erschöpfende Quellenliste pro Themengebiet pflegen — die `Adaptionsquelle`-Konvention in `spec/README.md` deckt die Themen-zu-Doc-Zuordnung ab
- Externe Drittquellen (Foren, Blogposts, Drittanbieter-Integrationen) zu maßgeblichen Quellen erheben — sie sind allenfalls ergänzend, nie ersetzend
- Eine automatisierte Drift-Prüfung gegen Upstream definieren — das bleibt einer späteren Spec vorbehalten

## Anforderungen

### Geltungsbereich

- **MUSS [MUST]** für jedes HA-Artefakt gelten, das dieses Plugin erzeugt oder verändert: Integrations-Code, Lovelace-Cards, Blueprints, Automationen, Service-Definitionen, Translations, Tests und die `ha/`-Specs selbst
- **MUSS [MUST]** sowohl für an den Nutzer gerichtete Antworten als auch für auf Platte geschriebene Inhalte gelten

### Verifikationspflicht

- **MUSS [MUST]** jede unsichere Aussage über HA-Internals (API-Signaturen, Lifecycle-Hooks, Konventionen, Quality-Scale-Kriterien, Frontend-/WebSocket-Verträge, YAML-Schemata) gegen die offizielle Doku prüfen, bevor die Aussage in eine Antwort, generierten Code oder eine Spec eingeht
- **MUSS [MUST]** im Zweifel die Quelle konsultieren, statt aus dem Gedächtnis zu antworten — Unsicherheit ist der Auslöser, nicht eine spätere Korrektur
- **SOLLTE [SHOULD]** die `raw.githubusercontent.com`-Fassung der relevanten Datei abrufen, wenn der konkrete Wortlaut oder Stand zählt

### Quellenwahl

- **MUSS [MUST]** Integration-Internals, Config-Flow, Entities, Coordinators, Quality-Scale und Frontend-/WebSocket-Verträge gegen [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) prüfen
- **MUSS [MUST]** Architektur, Blueprints, YAML-Schemata und endnutzer-zugewandtes Verhalten gegen [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) prüfen
- **MUSS NICHT [MUST NOT]** Foren, Blogposts oder Drittanbieter-Repos als maßgebliche Quelle behandeln — sie ergänzen die offizielle Doku, ersetzen sie nie

### Verankerung

- **SOLLTE [SHOULD]** eine verifizierte, nicht-offensichtliche Aussage an der konkreten Doc-Datei verankern (Pfad relativ zum jeweiligen Repo), damit spätere Drift nachvollziehbar bleibt
- **SOLLTE [SHOULD]** den Stand (Jahr/Release) notieren, wenn eine Aussage versionsabhängig ist

## Akzeptanzkriterien

- [ ] Die beiden maßgeblichen Quellen sind benannt und ihr Zuständigkeitsbereich ist abgegrenzt
- [ ] Die Pflicht gilt ausdrücklich für Antworten an den Nutzer **und** für generierte Artefakte
- [ ] Unsicherheit über HA-Internals löst eine Doku-Konsultation aus, bevor die Aussage verwendet wird
- [ ] Integration-Internals werden gegen `developers.home-assistant`, Architektur/Blueprints/YAML gegen `home-assistant.io` geprüft
- [ ] Foren-/Blog-/Drittquellen sind explizit als nicht-maßgeblich markiert
- [ ] Nicht-offensichtliche verifizierte Aussagen sind an einer konkreten Doc-Datei verankert

## Offene Fragen

- **Automatisierte Drift-Prüfung**: Soll eine spätere Spec einen mechanischen Abgleich generierter Annahmen gegen den Upstream-HEAD definieren (analog zur Spec-Drift-Prüfung zwischen DE und EN)?
- **Pinning auf Release-Stände**: Soll die Verankerung auf ein konkretes HA-Release gepinnt werden, oder genügt der Verweis auf den `dev`-Branch der Doku-Repos?
- **Verifikations-Cache**: Lohnt sich ein wiederverwendbarer Cache häufig nachgeschlagener Doc-Fakten, oder konterkariert das die Aktualitäts-Garantie der Live-Konsultation?
