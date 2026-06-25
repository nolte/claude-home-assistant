# Skill: `ha-backup-platform-add`

Status: draft

## Kontext

`ha/backup-platform` definiert das Backup-Plattform-Modul `backup.py` einer Integration, das zwei voneinander unabhängige Zwecke abdeckt. Erstens **Pre-/Post-Backup-Hooks**: die Top-Level-Async-Funktionen `async_pre_backup(hass)` und `async_post_backup(hass)`, die Integrationsaktivität rund um ein Backup pausieren bzw. wieder aufnehmen — typisch für DB-schreibende oder anderweitig zustandsbehaftete Integrationen, damit das Backup konsistent und restaurierbar bleibt. Zweitens **Backup-Agents**: `async_get_backup_agents(hass)` liefert `BackupAgent`-Subklassen, die Backups an einen lokalen/entfernten Speicherort hochladen — typisch für Cloud-Storage-Integrationen, gekoppelt mit `async_register_backup_agents_listener`. Analog zu `diagnostics.py` ist `backup.py` ein per Konvention erkanntes Plattform-Modul, das HA automatisch lädt. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt **eine** der beiden Backup-Plattform-Oberflächen (Pre-/Post-Hooks oder einen Backup-Agent) in einer **bestehenden** Integration: das `backup.py`-Modul mit den passenden Exports — spec-konform zu `ha/backup-platform`. Vor der Generierung disambiguiert er mit dem User, welcher der beiden Zwecke (oder beide) zum Integrationstyp passt.

## Scope

Ergänzung genau einer Backup-Oberfläche pro Lauf (`hooks` oder `agent`) in einer bestehenden `custom_components/<domain>/`-Integration: das Plattform-Modul `backup.py`. Für `hooks` die Top-Level-Funktionen `async_pre_backup(hass)` und `async_post_backup(hass)`. Für `agent` die `async_get_backup_agents(hass)`-Funktion (mit Leer-Liste ohne geladenen ConfigEntry), die `async_register_backup_agents_listener`-`@callback` und eine `BackupAgent`-Subklasse mit dem vollständigen upload/download/list/get/delete-Vertrag samt `BackupAgentError`/`BackupNotFound`-Fehlerbehandlung. Der Skill liest `ha/backup-platform` und validiert.

## Ziele

- Aus dem beschriebenen Integrationstyp die richtige Oberfläche (Pre-/Post-Hooks vs. Backup-Agent) wählen und spec-konform ergänzen
- Für Hooks `async_pre_backup`/`async_post_backup` als Top-Level-Async-Funktionen erzwingen, deren Pausieren in `async_pre_backup` symmetrisch in `async_post_backup` wieder aufgenommen wird
- Für Agents den vollständigen `BackupAgent`-Vertrag erzwingen (upload/download/list/get/delete), die Agent-Identität (`domain`, `name`, `unique_id`) setzen und Agents nur bei geladenem ConfigEntry anbieten
- Die Fehler-Semantik erzwingen: `BackupAgentError` (oder Subklasse) verlässt den Agent, fehlende Backups werfen `BackupNotFound`
- Registrierung und Listener als gekoppeltes Paar etablieren, damit stale Agents zuverlässig entfernt und neue hinzugefügt werden

## Nicht-Ziele

- Backup-Verschlüsselung, Aufbewahrungs-Policy und Scheduling — gehören dem Backup-Manager, nicht dem Plattform-Modul
- Restore-Orchestrierung über den `BackupAgent`-Download hinaus — der eigentliche Restore-Flow liegt im HA-Core
- Frontend-Darstellung der Upload-Progress-Events (`UploadBackupEvent`) — liegt außerhalb der Integration
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`
- Das Schwester-Plattform-Modul `diagnostics.py` — `ha/diagnostics`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add backup hooks", „make my integration backup-aware", „provide a backup agent"
  - „pause my integration before a backup / upload backups to my storage"
  - „füge Backup-Platform-Hooks hinzu", „mach meine Integration backup-fähig"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und den Integrationstyp/Bedarf (Prosa), aus dem der Skill die Oberfläche (Hooks vs. Agent) ableitet
- **KANN [MAY]** erfassen: `surface` (`hooks`/`agent`), den Agent-`name`/`unique_id`, und die Storage-Anbindung (lokal/entfernt) bzw. die zu pausierenden Operationen

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** die Oberfläche disambiguieren: zustandsbehaftete/DB-schreibende Integration → Pre-/Post-Hooks; Speicherort-bereitstellende (Cloud-Storage-)Integration → Backup-Agent; bei beidem den User wählen lassen, welche Oberfläche dieser Lauf ergänzt
- **MUSS [MUST]** die `ha/backup-platform`-Spec lesen
- **MUSS NICHT [MUST NOT]** bereits vorhandene Exports in `backup.py` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (pro Oberfläche, aus `ha/backup-platform`)

- **MUSS [MUST]** das Modul nach `custom_components/<domain>/backup.py` schreiben; **SOLLTE [SHOULD]** das eingebaute Scaffold-Template (`python3 -m script.scaffold backup`) als schnellen Einstieg nennen, statt zwingend von Hand zu beginnen
- **MUSS [MUST]** für Hooks `async_pre_backup(hass: HomeAssistant) -> None` und `async_post_backup(hass: HomeAssistant) -> None` als Top-Level-Async-Funktionen exportieren; `async_post_backup` nimmt die in `async_pre_backup` pausierten Operationen wieder auf
- **MUSS [MUST]** für einen Agent `async_get_backup_agents(hass: HomeAssistant) -> list[BackupAgent]` exportieren und eine leere Liste zurückgeben, wenn kein geladener ConfigEntry für die Domain existiert (`hass.config_entries.async_loaded_entries(DOMAIN)`)
- **MUSS [MUST]** für einen Agent die `BackupAgent`-Basisklasse aus `homeassistant.components.backup` vollständig implementieren, `domain`/`name`/`unique_id` setzen und `async_upload_backup`, `async_download_backup`, `async_list_backups`, `async_get_backup` und `async_delete_backup` implementieren
- **MUSS [MUST]** für einen Agent `async_register_backup_agents_listener(hass, *, listener, **kwargs) -> Callable[[], None]` als `@callback` exportieren, das den Listener registriert, eine Unregister-Funktion zurückgibt und bei nötigem Reload aufgerufen wird; **SOLLTE [SHOULD]** die Listener während `async_setup_entry` benachrichtigen
- **MUSS [MUST]** für einen Agent bei Fehlern `BackupAgentError` (oder eine Subklasse) werfen und bei fehlendem Backup in `async_download_backup`/`async_delete_backup`/`async_get_backup` `BackupNotFound` werfen
- **SOLLTE [SHOULD]** in `async_upload_backup` den `on_progress`-Callback periodisch (z. B. nach jedem Chunk) mit der bis dahin hochgeladenen Byte-Gesamtzahl aufrufen (`on_progress(bytes_uploaded=bytes_sent)`)
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `backup.py` existiert; für Hooks sind `async_pre_backup(hass)` und `async_post_backup(hass)` als Top-Level-Async-Funktionen exportiert; für einen Agent sind `async_get_backup_agents(hass)` und `async_register_backup_agents_listener(hass, *, listener)` exportiert, `async_get_backup_agents` gibt `[]` ohne geladenen ConfigEntry zurück, die `BackupAgent`-Subklasse setzt `domain`/`name`/`unique_id` und implementiert die fünf Agent-Methoden, Fehler werfen `BackupAgentError`/`BackupNotFound`
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/backup-platform` liefern, plus die geänderten Datei-Pfade und die gewählte Oberfläche

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Oberfläche pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** Verschlüsselung, Aufbewahrung, Scheduling oder Restore-Orchestrierung implementieren — die gehören dem Backup-Manager bzw. dem Core
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet die Oberfläche ab (oder erfragt sie) und disambiguiert Hooks vs. Agent am Integrationstyp
- [ ] `custom_components/<domain>/backup.py` existiert nach dem Lauf
- [ ] Für Hooks sind `async_pre_backup(hass)` und `async_post_backup(hass)` als Top-Level-Async-Funktionen exportiert (symmetrisches Pausieren/Aufnehmen)
- [ ] Für einen Agent sind `async_get_backup_agents(hass)` und `async_register_backup_agents_listener(hass, *, listener)` exportiert; `async_get_backup_agents` gibt `[]` ohne geladenen ConfigEntry zurück
- [ ] Die `BackupAgent`-Subklasse setzt `domain`/`name`/`unique_id` und implementiert `async_upload_backup`/`async_download_backup`/`async_list_backups`/`async_get_backup`/`async_delete_backup`
- [ ] Fehler werfen `BackupAgentError` (oder Subklasse); fehlende Backups werfen `BackupNotFound`
- [ ] Bericht nennt Datei-Pfade und die gewählte Oberfläche

## Offene Fragen

- **Hook-vs.-Agent-Trennung**: Die Doku führt beide Mechanismen im selben `backup.py`. Soll der Skill eine Integration verpflichten, beide bewusst abzuwägen, oder reicht der bedarfsgetriebene Trigger? Aktuell ergänzt er genau eine Oberfläche pro Lauf.
- **Scaffold-Template**: Soll der Skill `python3 -m script.scaffold backup` verbindlich aufrufen, oder das Modul selbst schreiben? Aktuell nennt er das Template als SHOULD und generiert offline.
- **Progress-Granularität**: „Periodisch, z. B. nach jedem Chunk" ist als SHOULD formuliert; eine konkrete Aufruf-Frequenz ist nicht standardisiert — der Skill folgt dem Doc-Muster und fragt im Zweifel nach.
