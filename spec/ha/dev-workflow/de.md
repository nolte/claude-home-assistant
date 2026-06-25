# HA-Integration: Dev-Workflow (Guidelines, Typing, Validation)

Status: draft

## Kontext

Eine Custom Integration für Home Assistant ist Python-Code, der mit dem HA-Core-Codestil mitlaufen muss: HA erzwingt strikte [PEP8](https://peps.python.org/pep-0008/)- und [PEP 257](https://peps.python.org/pep-0257/)-Konformität auf jeglichem eingereichten Code, formatiert mit [Ruff](https://docs.astral.sh/ruff/), und prüft Typannotationen statisch im CI. Die HA-Dokumentation (`development_guidelines.md`, `development_typing.md`, `development_validation.md`, `development_checklist.md`) definiert diese Coding-Konventionen — sie sind aber über mehrere Seiten verteilt und nicht als operationalisierbare Verpflichtung formuliert.

Diese Spec bündelt den **Coding-Workflow** einer Custom Integration in eine durchsetzbare Form: Code-Style (Zeilenlänge, Import-Reihenfolge, f-strings, Ruff/Pylint), strikte Typisierung (`from __future__ import annotations`, der `.strict-typing`-Opt-in, mypy) sowie Validierung (`hassfest`, Manifest-/Strings-/Services-Validierung). Sie schreibt die HA-Originalregeln so fest, dass ein Skill sie automatisch anwenden und ein Reviewer sie abhaken kann.

Abgegrenzt wird strikt: das devcontainer-/Kind-Setup gehört zu `ha/dev-environment`, das Pytest-Harness zu `ha/test-harness`. Diese Spec adressiert ausschließlich, **wie der Code geschrieben, typisiert und validiert** wird, bevor er eingereicht wird.

Quality-Scale-Marker: **bronze→platinum** (Code-Style und `hassfest` sind ein Bronze-Floor; die strikte Typisierung via `.strict-typing` ist die Platinum-`strict-typing`-Regel, siehe `ha/quality-scale`).

## Ziele

- HA-Code-Style (PEP8/PEP257, Ruff-Formatierung, geordnete Imports, alphabetische Konstanten/Listen, f-strings) als durchsetzbare Verpflichtung festschreiben
- Strikte Typisierung etablieren — vollständige Annotationen, `from __future__ import annotations`, Aufnahme in `.strict-typing`, mypy-Lauf — als Brücke zur Platinum-`strict-typing`-Regel
- `hassfest` (`python3 -m script.hassfest`) als Pflicht-Validierung vor dem Einreichen festschreiben — Manifest, Strings, Services
- Voluptuous-basierte Config-Validierung (`config_validation.py`-Helper, `const.py`-Konstanten, required-vor-optional) für YAML-konfigurierbare Plattformen festschreiben
- Die Pre-Submit-Checkliste aus `development_checklist.md` in eine abhakbare Liste überführen
- Klar gegen `ha/dev-environment` (Setup) und `ha/test-harness` (Pytest) abgrenzen, ohne sie zu duplizieren

## Nicht-Ziele

- Devcontainer-/Kind-Cluster-Setup, `script/setup`, venv-Bootstrap — gehört zu `ha/dev-environment`
- Pytest-Harness, Snapshot-Tests, Fixtures, Coverage-Reports — gehört zu `ha/test-harness`
- Async-/Event-Loop-Patterns (`async def`, Executor-Jobs, Blocking-I/O) — gehört zu `ha/async-patterns`
- Manifest-Schema-Authoring im Detail (`manifest.json`-Felder, Versionierung) — gehört zu `ha/integration-manifest`; diese Spec verlangt nur, dass `hassfest` es validiert
- Quality-Scale-Regelkatalog selbst — gehört zu `ha/quality-scale`; diese Spec verweist nur auf die `strict-typing`-Regel
- MonkeyType-gestützte Migrations-Workflows für Altcode — optional, kein Pflicht-Bestandteil des Skill-Outputs

## Anforderungen

### Code-Style & Guidelines

- **MUSS [MUST]** PEP8- und PEP257-konformen Code erzeugen und mit Ruff formatieren (`ruff format`) — HA merged keine Einreichungen, die davon abweichen
- **MUSS [MUST]** Imports ordnen ([PEP8 Imports](https://peps.python.org/pep-0008/#imports)) und Konstanten sowie den Inhalt von Listen und Dictionaries alphabetisch sortieren
- **MUSS [MUST]** [f-strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings) gegenüber `%`- oder `str.format`-Formatierung bevorzugen — einzige Ausnahme: Logging, das prozentuale Formatierung nutzt, um die Nachricht nur bei Bedarf zu rendern (`_LOGGER.info("... %s ...", value)`)
- **MUSS [MUST]** im Datei-Header einen Docstring führen, der beschreibt, worum es in der Datei geht (z. B. `"""Support for MQTT lights."""`)
- **SOLLTE [SHOULD]** Kommentare als vollständige Sätze mit Punkt am Ende schreiben
- **SOLLTE [SHOULD]** keine Plattform-/Komponenten-Namen oder abschließende Punkte in Log-Nachrichten setzen (wird automatisch ergänzt), niemals API-Keys, Tokens, Usernames oder Passwörter loggen und `_LOGGER.info` restriktiv einsetzen — alles Nicht-User-Gerichtete via `_LOGGER.debug`
- **KANN [MAY]** [Google-Style](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods)-Docstrings für erweiterte Parameter-/Return-/Raises-Dokumentation verwenden; Typinformationen gehören dabei in die Annotationen und werden aus dem Docstring weggelassen

### Typing (strict)

- **MUSS [MUST]** Code vollständig typannotieren — HA prüft Typannotationen statisch im CI und nimmt an, dass alles typgeprüft ist, sofern nicht explizit ausgeschlossen
- **MUSS [MUST]** das Modul in die `.strict-typing`-Datei im Root des HA-Core-Projekts eintragen, sobald es vollständig typisiert ist — dies aktiviert die strikten Checks und erfüllt zugleich die Platinum-`strict-typing`-Regel (siehe `ha/quality-scale`)
- **SOLLTE [SHOULD]** `from __future__ import annotations` am Modulkopf führen, damit Annotationen als Strings ausgewertet werden und Forward-References ohne Quote-Strings funktionieren
- **SOLLTE [SHOULD]** mypy gegen das Modul laufen lassen, bevor es eingereicht wird — der CI-Typecheck spiegelt diesen Lauf
- **KANN [MAY]** `assert`-Statements zur Typverengung verwenden, jedoch **ausschließlich** innerhalb eines `if TYPE_CHECKING:`-Blocks, sodass sie nur für den Typechecker existieren und das Laufzeitverhalten nicht beeinflussen
- **KANN [MAY]** [MonkeyType](https://pypi.org/project/MonkeyType/) (`script/monkeytype`) zur Erstinstrumentierung gänzlich untypisierter Module nutzen; der generierte Stub wird stets manuell nachkorrigiert

### Validation (`hassfest`)

- **MUSS [MUST]** `python3 -m script.hassfest` vor dem Einreichen ausführen — der Lauf validiert die Integration und aktualisiert generierte Artefakte (u. a. `CODEOWNERS`)
- **MUSS [MUST]** die Integration so gestalten, dass `hassfest` ohne Fehler durchläuft — das umfasst die Validierung des Manifests (siehe `ha/integration-manifest`), der Übersetzungs-/Strings-Dateien und der Service-Definitionen
- **MUSS [MUST]** voluptuous für die Validierung jeglicher YAML-Konfiguration verwenden, die der User bereitstellt, sofern die Plattform YAML-konfigurierbar ist
- **SOLLTE [SHOULD]** beim Schema-Bau die Konstanten aus `const.py` nutzen, `PLATFORM_SCHEMA` der Ziel-Integration importieren und erweitern, `required`-Keys vor `optional`-Keys ordnen und für optionale Keys gültige Defaults setzen (kein `default=None` für `cv.string`; stattdessen `default=''`)
- **KANN [MAY]** die HA-Custom-Validatoren aus [`config_validation.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/config_validation.py) (`cv.port`, `cv.ensure_list`, `vol.In([...])`, `entity_id`, `slug`, …) statt roher voluptuous-Typen verwenden

### Pre-Submit-Checklist

- **MUSS [MUST]** jegliche Kommunikation mit externen Geräten oder Diensten in eine externe, auf [PyPI](https://pypi.org/) gehostete Python-Library kapseln — mit verfügbarer Source-Distribution (keine reinen Binary-Distributionen) und aktiviertem Issue-Tracker
- **MUSS [MUST]** neue Dependencies via `python3 -m script.gen_requirements_all` zu `requirements_all.txt` hinzufügen (sofern zutreffend)
- **MUSS [MUST]** neue Codeowners via `python3 -m script.hassfest` in `CODEOWNERS` eintragen (sofern zutreffend)
- **MUSS [MUST]** den Code mit Ruff formatieren (`ruff format`) und die `.strict-typing`-Datei aktualisieren, sofern der Code vollständig typannotiert ist
- **SOLLTE [SHOULD]** Dokumentation für [home-assistant.io](https://home-assistant.io/) entwickeln, sofern die Integration user-sichtbares Verhalten einführt
- **KANN [MAY]** unvermeidbare Pylint-Warnungen zeilenweise mit `# pylint: disable=YOUR-ERROR-NAME` unterdrücken — nur, wenn die Warnung nachweislich falsch ist (z. B. fehlgemeldetes fehlendes Member)

### Abgrenzung (Dev-Environment / Test-Harness)

- **MUSS NICHT [MUST NOT]** Setup-Mechanik (devcontainer, Kind-Cluster, `script/setup`, venv, `kubectl cp`/`kill 1`) hier definieren — das gehört zu `ha/dev-environment`
- **MUSS NICHT [MUST NOT]** das Pytest-Harness (Fixtures, `MockConfigEntry`, Snapshot-Tests, Coverage) hier definieren — das gehört zu `ha/test-harness`; diese Spec deckt nur Style/Typing/Validation des einzureichenden Codes
- **SOLLTE [SHOULD]** Geschwister-Specs per Slug referenzieren statt zu duplizieren: `ha/dev-environment`, `ha/test-harness`, `ha/async-patterns`, `ha/quality-scale`, `ha/integration-manifest`

## Akzeptanzkriterien

- [ ] Code ist PEP8/PEP257-konform und mit `ruff format` formatiert
- [ ] Imports sind geordnet; Konstanten, Listen- und Dictionary-Inhalte sind alphabetisch sortiert
- [ ] String-Formatierung nutzt f-strings (Ausnahme: Logging via Prozent-Formatierung)
- [ ] Code ist vollständig typannotiert und das Modul ist in `.strict-typing` eingetragen
- [ ] `from __future__ import annotations` steht am Modulkopf; mypy läuft fehlerfrei
- [ ] `assert`-Typverengungen stehen ausschließlich in `if TYPE_CHECKING:`-Blöcken
- [ ] `python3 -m script.hassfest` läuft fehlerfrei (Manifest, Strings, Services)
- [ ] YAML-konfigurierbare Plattformen validieren Input via voluptuous mit `const.py`-Konstanten
- [ ] Externe Kommunikation ist in eine PyPI-Library mit Source-Distribution und aktivem Issue-Tracker gekapselt
- [ ] Neue Dependencies via `python3 -m script.gen_requirements_all`, neue Codeowners via `hassfest` ergänzt
- [ ] Quality-Scale-Marker: **bronze→platinum** (`hassfest`/Style = Bronze-Floor, `.strict-typing` = Platinum-Regel)

## Offene Fragen

- **`.strict-typing`-Anwendbarkeit für Custom Integrations**: Die `.strict-typing`-Datei lebt im HA-Core-Repo. Für eine eigenständige Custom Integration (außerhalb von Core) braucht es ein äquivalentes lokales mypy-Strict-Profil. Soll die Spec ein `pyproject.toml`-`[tool.mypy]`-Strict-Snippet als Custom-Integration-Pendant festlegen?
- **`hassfest` außerhalb von Core**: `python3 -m script.hassfest` setzt das Core-`script`-Paket voraus. Custom Integrations brauchen entweder ein vendored `hassfest` oder einen Pre-Commit-Hook (`home-assistant/actions`). Welche Variante wird im Portfolio bevorzugt?
- **Ruff-vs-Pylint-Konfiguration**: HA-Core liefert eine kuratierte Ruff-/Pylint-Config. Soll die Spec eine konkrete `ruff.toml`/`.pylintrc`-Baseline für Custom Integrations vorgeben oder auf die Core-Config verweisen?
- **Voluptuous-Relevanz bei Config-Flow-only-Integrationen**: Moderne Integrationen sind config-flow-basiert und nicht YAML-konfigurierbar. Soll die voluptuous-Anforderung als „nur bei YAML-Konfiguration zutreffend" markiert bleiben oder auf Config-Flow-Voluptuous-Schemata ausgeweitet werden?
