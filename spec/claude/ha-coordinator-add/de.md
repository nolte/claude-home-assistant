# Skill: `ha-coordinator-add`

Status: draft

## Kontext

Eine reife Custom Integration startet selten mit ihrer endgültigen Coordinator-Topologie. Typischer Verlauf: Initial-Scaffold liefert einen `<Domain>Coordinator`, der für Plant-/Resource-Daten gut funktioniert; mit der Zeit zeigt sich, dass Alerts-/Notifications-Daten ein deutlich kürzeres Update-Intervall brauchen (`60 s` statt `300 s`), oder dass Stammdaten (Tenants, Locations) ein längeres Intervall verkraften, weil sie sich kaum ändern. Spätestens an dem Punkt wird ein Mega-Coordinator zur Reibung — er pollt entweder unnötig oft oder unnötig langsam für einzelne Datensätze.

Dieser Skill fügt einer existierenden Integration einen weiteren Coordinator hinzu, ohne den bestehenden zu zerstören. Er bündelt die Cross-File-Edits (Coordinator-Klasse, RuntimeData-Erweiterung, `__init__.py`-Setup, `const.py`-Konstanten, `config_flow.py`-Options-Schema, Tests) zu einem additiven Pattern.

## Scope

Der Skill fügt **einen** weiteren Coordinator pro Aufruf hinzu. Er entfernt keinen, mergt keinen und ändert das Update-Intervall eines bestehenden nicht. Bestehende Plattform-Module bleiben unverändert; die neue Coordinator-Bindung passiert nur für Plattform-Module, die der User explizit nennt — der Rest bleibt am alten Coordinator.

## Ziele

- Die Multi-Coordinator-Topologie aus `ha/coordinator-patterns` nachträglich einführbar machen
- `RuntimeData.coordinators`-Mapping als alleinigen Lookup-Pfad sicherstellen — der neue Coordinator wird nicht als separates `RuntimeData`-Feld geführt, sondern als zusätzlicher Schlüssel im Mapping
- Konfigurierbare Update-Intervalle für den neuen Coordinator von Anfang an mit Options-Flow-Eintrag plus Min-Cap
- Test-Coverage für den neuen Coordinator (Error-Mapping, Happy-Path) als Pflicht-Bestandteil der Auslieferung

## Nicht-Ziele

- Coordinator-Entfernung oder Coordinator-Konsolidierung — manuelle Aufgabe
- Mega-Coordinator-Aufspaltung in mehrere Stücke in einem Aufruf — Schritt-für-Schritt mit dem `add`-Skill
- Cross-Coordinator-Datenaggregation (Plattform liest aus zwei Coordinators) — eigene Folge-Spec, falls überhaupt nötig
- Push-basierte Coordinators (Webhook, MQTT, WebSocket) — eigene Folge-Spec

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a new coordinator for <role>"
  - „split the existing coordinator into <role> and <role>"
  - „add a faster polling coordinator for alerts"
  - „füge einen Coordinator für <Rolle> hinzu"
- **MUSS NICHT [MUST NOT]** aktivieren bei:
  - Greenfield-Setup (`ha-integration-scaffold`)
  - Coordinator-Entfernung (manueller Edit)
  - Push-Coordinator-Setup (eigene Spec geplant)

### Eingaben

- **MUSS [MUST]** erfassen:
  - `target_dir` — Repo-Root der Integration
  - `role` — der Coordinator-Rollen-Name in lowercase ASCII (`alerts`, `tenants`, `metrics`, …) — wird als Schlüssel im `RuntimeData.coordinators`-Mapping und Suffix in der Coordinator-Klasse (`<Domain><Role>Coordinator`) verwendet
  - `default_interval` — Default-Update-Intervall in Sekunden
  - `min_interval` — Mindest-Cap in Sekunden
  - `update_method` — der Name der API-Methode in `api.py`, die `_async_update_data` aufruft (z. B. `async_get_alerts`)
- **SOLLTE [SHOULD]** erfassen:
  - `setup_method` — der Name einer optionalen `_async_setup`-Methode für Stammdaten-Laden (Default: keine)
  - `data_type` — der Generic-Type für `DataUpdateCoordinator[<Type>]` (Default: `list[dict[str, Any]]`)

### Pre-Flight

- **MUSS [MUST]** prüfen und bei Fehlschlag abbrechen:
  1. `target_dir` ist git-Repo, sauberer Working tree
  2. `target_dir/custom_components/<domain>/coordinator.py` existiert
  3. Eine Coordinator-Klasse mit dem Namen `<Domain><Role>Coordinator` existiert noch nicht
  4. Der Mapping-Schlüssel `role` existiert noch nicht in `RuntimeData.coordinators`
  5. `target_dir/custom_components/<domain>/api.py` enthält die unter `update_method` benannte API-Methode (oder der User wird darauf hingewiesen, sie selbst zu ergänzen)

### Generator-Choreographie

- **MUSS [MUST]** in `coordinator.py` eine neue `<Domain><Role>Coordinator(DataUpdateCoordinator[<DataType>])`-Klasse anhängen, die `ha/coordinator-patterns` erfüllt: `config_entry`, `name=f"{DOMAIN}_<role>"`, `update_interval` aus `entry.options` mit Min-Cap, `always_update=False`, Error-Mapping (`ConfigEntryAuthFailed` / `UpdateFailed`), `async_timeout.timeout(...)`-Wrap
- **MUSS [MUST]** in `const.py` Konstanten ergänzen: `CONF_POLL_<ROLE>`, `DEFAULT_POLL_<ROLE>`, `MIN_POLL_<ROLE>`
- **MUSS [MUST]** in `__init__.py` (`async_setup_entry`) den neuen Coordinator instanziieren, `async_config_entry_first_refresh()` aufrufen, und das `runtime_data.coordinators`-Mapping erweitern (`{"<existing_role>": existing, "<role>": new}`) — die `RuntimeData`-Dataclass selbst bleibt unverändert, weil das Mapping bereits existiert
- **MUSS [MUST]** in `config_flow.py` (Options-Flow) den neuen `CONF_POLL_<ROLE>`-Eintrag in `OPTIONS_SCHEMA` ergänzen mit `vol.All(int, vol.Range(min=MIN_POLL_<ROLE>))`, Default `DEFAULT_POLL_<ROLE>`
- **MUSS [MUST]** in `strings.json` und allen `translations/<lang>.json` den `options.step.init.data.poll_interval_<role>`-String ergänzen
- **MUSS [MUST]** in `tests/test_coordinator.py` Tests ergänzen: Auth-Error → `ConfigEntryAuthFailed`, Connection-Error → `UpdateFailed`, Happy-Path mit JSON-Fixture
- **KANN [MAY]** ein neues Fixture-File in `tests/fixtures/<role>.json` anlegen, falls die API-Methode strukturierte Antworten liefert

### Verbote

- **MUSS NICHT [MUST NOT]** den bestehenden Coordinator umbenennen oder ändern
- **MUSS NICHT [MUST NOT]** Plattform-Module umverdrahten — Coordinator-Bindung in den Plattformen bleibt User-Aufgabe (Zwei Plattformen mit derselben Rolle könnten den neuen Coordinator nutzen, das entscheidet der User)
- **MUSS NICHT [MUST NOT]** den Mindest-Cap auf weniger als `30 s` setzen ohne expliziten User-Hinweis — der Skill warnt, falls der User unter `30 s` setzen will

## Akzeptanzkriterien

- [ ] Eine neue Coordinator-Klasse erscheint in `coordinator.py`
- [ ] `const.py` enthält `CONF_POLL_<ROLE>`, `DEFAULT_POLL_<ROLE>`, `MIN_POLL_<ROLE>`
- [ ] `__init__.py` instanziiert den neuen Coordinator, ruft `async_config_entry_first_refresh()`, und erweitert das `runtime_data.coordinators`-Mapping
- [ ] `config_flow.py:OPTIONS_SCHEMA` enthält den neuen `CONF_POLL_<ROLE>`-Eintrag
- [ ] `strings.json` und `translations/<lang>.json` enthalten den neuen Options-String
- [ ] `tests/test_coordinator.py` enthält die drei neuen Tests (Auth-Error, Connection-Error, Happy-Path)
- [ ] `pytest tests/test_coordinator.py` läuft fehlerfrei
- [ ] `ruff check custom_components/<domain>/` läuft fehlerfrei

## Offene Fragen

- **API-Methoden-Lookup**: Soll der Skill `api.py` lesen und Methoden vorschlagen, oder muss der User die Methode benennen?
- **Push-Coordinator-Variante**: Wann verlangt eine Folge-Spec den Webhook-/MQTT-Coordinator-Pfad?
- **Cross-Coordinator-Plattformen**: Wie behandelt der Skill den Fall, dass eine Plattform Daten aus zwei Coordinators kombiniert? Aktuell als Nicht-Ziel ausgeschlossen.
