# HA-Integration: Backup-Platform

Status: draft

## Kontext

Eine Integration kann ein **Backup-Plattform-Modul** (`backup.py`) bereitstellen, das zwei voneinander unabhängige Zwecke abdeckt. Erstens kann sie einen **Backup-Agent** registrieren, der Backups an einen lokalen oder entfernten Speicherort hochlädt. Zweitens kann sie **Pre-/Post-Operationen** einklinken, um Integrationsaktivität zu pausieren oder Daten vorzubereiten, bevor ein Backup erstellt wird, und nach Abschluss aufzuräumen.

Beide Mechanismen leben im selben Plattform-Modul `backup.py` im Integrations-Ordner — analog zu `diagnostics.py` ist `backup.py` ein per Konvention erkanntes Plattform-Modul, das HA automatisch lädt. Welcher der beiden Mechanismen (oder beide) gebraucht wird, hängt vom Integrationstyp ab: Cloud-Storage-Integrationen liefern Agents, DB-schreibende oder zustandsbehaftete Integrationen brauchen Pre-/Post-Hooks. Diese Spec überführt die HA-Backup-Plattform-Doku in eine generische Verpflichtung. Verwandte Specs: [`ha/integration-architecture`](../integration-architecture/de.md), [`ha/diagnostics`](../diagnostics/de.md) (Schwester-Plattform-Modul), [`ha/security-hardening`](../security-hardening/de.md) (Backup-Daten können Secrets enthalten).

## Ziele

- `backup.py` als Standard-Plattform-Modul für Integrationen etablieren, die einen Speicherort bereitstellen oder zustandsbehaftete Operationen schützen müssen
- Den `BackupAgent`-Vertrag (upload/download/list/delete) als vollständige Implementierung der abstrakten Basisklasse festschreiben
- Agent-Registrierung und Listener-Mechanismus (`async_get_backup_agents`, `async_register_backup_agents_listener`) als gekoppeltes Paar etablieren, damit stale Agents zuverlässig entfernt und neue hinzugefügt werden
- Pre-/Post-Backup-Hooks für DB-schreibende und zustandsbehaftete Integrationen verpflichten, damit Backups konsistent und restaurierbar bleiben

## Nicht-Ziele

- Backup-Verschlüsselung, Aufbewahrungs-Policy und Scheduling — gehören dem Backup-Manager, nicht dem Plattform-Modul
- Restore-Orchestrierung über den `BackupAgent`-Download hinaus — der eigentliche Restore-Flow liegt im HA-Core
- Das Scaffold-Werkzeug (`python3 -m script.scaffold backup`) selbst — es ist ein Komfort-Generator, kein Vertragsbestandteil
- Frontend-Darstellung der Upload-Progress-Events — die `UploadBackupEvent`-Verarbeitung liegt außerhalb der Integration

## Anforderungen

### Zweck

- **MUSS [MUST]** das Backup-Plattform-Modul in `custom_components/<domain>/backup.py` ablegen, sobald die Integration einen Backup-Agent bereitstellt oder Pre-/Post-Operationen einklinkt
- **MUSS [MUST]** entscheiden, welcher der beiden Zwecke gebraucht wird: einen Backup-Agent zum Hochladen von Backups an einen lokalen/entfernten Speicherort, und/oder Pre-/Post-Operationen zum Pausieren bzw. Vorbereiten von Integrationsaktivität rund um ein Backup
- **KANN [MAY]** beide Zwecke im selben `backup.py`-Modul kombinieren, wenn die Integration sowohl Speicherort als auch zustandsbehaftete Operationen führt

### Pre-/Post-Backup-Hooks (`backup.py`)

- **MUSS [MUST]** `async_pre_backup(hass: HomeAssistant) -> None` in `backup.py` exportieren, wenn die Integration vor dem Backup Operationen pausieren oder Daten dumpen muss, damit sie korrekt restauriert werden können
- **MUSS [MUST]** `async_post_backup(hass: HomeAssistant) -> None` exportieren, das die in `async_pre_backup` pausierten Operationen nach Abschluss des Backups wieder aufnimmt
- **SOLLTE [SHOULD]** zum schnellen Hinzufügen das eingebaute Scaffold-Template nutzen (`python3 -m script.scaffold backup`), statt das Modul von Hand anzulegen

### Backup-Agent (Storage-Location)

- **MUSS [MUST]** `async_get_backup_agents(hass: HomeAssistant) -> list[BackupAgent]` in `backup.py` exportieren, wenn die Integration einen Speicherort für Backups bereitstellt
- **MUSS [MUST]** eine leere Liste zurückgeben, wenn kein geladener ConfigEntry für die Domain existiert (`hass.config_entries.async_loaded_entries(DOMAIN)`) — ein Agent ohne geladenen Entry darf nicht angeboten werden
- **MUSS [MUST]** das abstrakte Interface der `BackupAgent`-Basisklasse aus `homeassistant.components.backup` vollständig implementieren und `domain`, `name` und `unique_id` als Agent-Identität setzen

### Agent-Methoden (upload/download/list/delete)

- **MUSS [MUST]** `async_upload_backup(*, open_stream, backup, on_progress, **kwargs) -> None` implementieren, das den über `open_stream` gelieferten Byte-Stream zum Speicherort hochlädt
- **MUSS [MUST]** `async_download_backup(backup_id, **kwargs) -> AsyncIterator[bytes]` implementieren, das die Backup-Datei zur übergebenen `backup_id` als Async-Iterator über Bytes zurückgibt
- **MUSS [MUST]** `async_list_backups(**kwargs) -> list[AgentBackup]` und `async_get_backup(backup_id, **kwargs) -> AgentBackup` implementieren, damit der Backup-Manager Backups auflisten und einzeln abfragen kann
- **MUSS [MUST]** `async_delete_backup(backup_id, **kwargs) -> None` implementieren, das die Backup-Datei zur übergebenen `backup_id` am Speicherort löscht
- **MUSS [MUST]** bei Fehlern eine `BackupAgentError` (oder eine Subklasse davon) werfen — andere Exceptions sollen den Backup-Agent nicht verlassen
- **MUSS [MUST]** bei fehlendem Backup in `async_download_backup`, `async_delete_backup` und `async_get_backup` `BackupNotFound` werfen
- **SOLLTE [SHOULD]** in `async_upload_backup` den `on_progress`-Callback periodisch (z. B. nach jedem gesendeten Chunk) mit der bis dahin hochgeladenen Byte-Gesamtzahl aufrufen (`on_progress(bytes_uploaded=bytes_sent)`), damit der Backup-Manager `UploadBackupEvent`-Events feuert

### Registrierung & Listener

- **MUSS [MUST]** `async_register_backup_agents_listener(hass, *, listener, **kwargs) -> Callable[[], None]` als `@callback` exportieren, das den Listener registriert und eine Unregister-Funktion zurückgibt
- **MUSS [MUST]** den registrierten Listener jedes Mal aufrufen, wenn Backup-Agents neu geladen werden müssen — stale Agents entfernen, neue hinzufügen
- **SOLLTE [SHOULD]** die Listener während `async_setup_entry` benachrichtigen (z. B. via `entry.async_on_state_change`), damit Agent-Änderungen bei ConfigEntry-Zustandswechseln propagiert werden

### Wann implementieren

- **MUSS [MUST]** Pre-/Post-Backup-Hooks implementieren, wenn die Integration während eines Backups Operationen pausieren oder Daten dumpen muss (typisch: DB-schreibende oder anderweitig zustandsbehaftete Integrationen), damit das Backup konsistent und restaurierbar ist
- **MUSS [MUST]** einen Backup-Agent implementieren, wenn die Integration einen Speicherort für Backups bereitstellt (typisch: Cloud-Storage-Integrationen)
- **KANN [MAY]** das Plattform-Modul weglassen, wenn die Integration weder einen Speicherort bereitstellt noch zustandsbehaftete Operationen rund um ein Backup schützen muss

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/backup.py` existiert, sobald die Integration einen Agent bereitstellt oder Pre-/Post-Hooks einklinkt
- [ ] Für Pre-/Post-Operationen sind `async_pre_backup(hass)` und `async_post_backup(hass)` als Top-Level-Async-Funktionen exportiert
- [ ] Für einen Speicherort sind `async_get_backup_agents(hass)` und `async_register_backup_agents_listener(hass, *, listener)` exportiert
- [ ] `async_get_backup_agents` gibt `[]` zurück, wenn kein geladener ConfigEntry für die Domain existiert
- [ ] Die `BackupAgent`-Subklasse setzt `domain`, `name` und `unique_id` und implementiert `async_upload_backup`, `async_download_backup`, `async_list_backups`, `async_get_backup` und `async_delete_backup`
- [ ] Fehler im Agent werfen `BackupAgentError` (oder eine Subklasse); fehlende Backups werfen `BackupNotFound`
- [ ] `async_upload_backup` ruft den `on_progress`-Callback während des Uploads auf
- [ ] Der Listener wird während `async_setup_entry` benachrichtigt, damit Agent-Änderungen propagiert werden

## Offene Fragen

- **Hook-vs.-Agent-Trennung**: Die Doku führt beide Mechanismen im selben `backup.py`. Soll die Spec eine Integration verpflichten, beide bewusst gegeneinander abzuwägen, oder reicht der bedarfsgetriebene Trigger?
- **Pre-Backup-Pausierdauer**: Wie lange darf `async_pre_backup` Operationen pausieren, bevor es das Backup-Fenster blockiert? Die Doku nennt keine Obergrenze.
- **Progress-Granularität**: „Periodisch, z. B. nach jedem Chunk" ist als SHOULD formuliert; eine konkrete Aufruf-Frequenz (z. B. alle N Bytes oder N Millisekunden) ist nicht standardisiert.
- **Secret-Behandlung im Agent**: Backup-Daten können Secrets enthalten ([`ha/security-hardening`](../security-hardening/de.md)). Ob der Agent serverseitige Verschlüsselung erzwingen muss, deckt diese Doku nicht ab.
