# HA-Integration: Dev-Environment

Status: draft

## Kontext

Eine Custom Integration ist Code, der innerhalb einer laufenden HA-Instanz lebt. Lokales Entwickeln ohne eine echte HA-Instanz im Loop führt zu Reibung — Pytest deckt strukturelle Tests ab (siehe `ha/test-harness`), aber Frontend-Verhalten, Lifecycle-Bugs, Setup-Race-Conditions und Lovelace-Card-Rendering brauchen die echte Instanz. Das nolte-Portfolio nutzt dafür einen **Kubernetes-basierten Dev-Loop**: ein lokaler Kind-Cluster mit dem `homeassistant`-Helm-Chart, in den Custom-Integration-Code per `kubectl cp` reingespiegelt wird.

`nolte/kamerplanter-ha` hat in Commit `f4c24fb (2026-04-24 "refactor(skills): extract HA deploy/verify steps into Taskfile")` die Deploy-Choreographie in `Taskfile.yml`-Targets extrahiert (`task deploy-ha`, `task verify-ha`). Die kritische Erkenntnis dahinter: **`kubectl exec ... -- kill 1` ist der korrekte Restart-Mechanismus, NICHT `kubectl delete pod`**. Beim `delete pod` läuft der InitContainer erneut und überschreibt die per `kubectl cp` kopierten Dateien — die Änderung verschwindet stillschweigend. `kill 1` startet nur das HA-Hauptprozess innerhalb des bestehenden Containers neu, sodass die kopierten Dateien erhalten bleiben.

Diese Spec überführt das Pattern in eine generische Verpflichtung. Sie definiert die Deploy-Choreographie, die Verify-Choreographie (Pod-Status-Check, Log-Scan, Error-Detection), die Pflicht-Cache-Bereinigung (`__pycache__`) und die Variablen, die ein Skill für `task deploy-ha`/`task verify-ha` standardmäßig erwartet.

Quality-Scale-Marker: **unscaled** (Dev-Environment ist nicht Teil der HA-Quality-Scale; das Pattern ist nolte-portfolio-spezifisch).

## Ziele

- Kind-Cluster + `homeassistant`-Helm-Chart als Standard-Dev-Stack festschreiben — schnelle Iteration ohne echtes HA-Restart-Trauma
- `kubectl cp` als Deployment-Mechanismus etablieren — Files landen direkt im Container, keine Image-Builds nötig
- `kill 1` statt `kubectl delete pod` als Pflicht-Restart-Mechanismus festschreiben — verhindert silent overwrite durch InitContainer
- Bytecode-Cache-Bereinigung (`__pycache__`) als Pflicht-Schritt vor jedem Restart, sodass Python keine veralteten `.pyc`-Dateien lädt
- Verify-Choreographie definieren, die Pod-Status, Log-Tail und Error-Detection nach jedem Deploy automatisch durchläuft
- Taskfile-basierte Choreographie als alleinigen Einstiegspunkt — keine ad-hoc `kubectl`-Kommandos in Onboarding-Docs

## Nicht-Ziele

- Container-Image-Build / Helm-Chart-Authoring — externe Bestandteile, nicht Skill-Output
- HA-Konfiguration der Test-Instanz selbst (`configuration.yaml`, integrations YAML, etc.) — User-spezifisch, jenseits der Custom-Integration
- Production-Deployment — die `kubectl cp`-Mechanik ist explizit für lokale Dev-Loops; Production läuft über reguläre HA-Add-on-Distribution oder HACS
- Lokale Python-venv-Setup für Pytest — siehe `ha/test-harness` und `nolte-shared:project-structure`
- Multi-Cluster-Workflows (Staging-Cluster, Cloud-Cluster) — eigene Folge-Spec, sobald die erste Integration es konkret braucht
- VS-Code-/IDE-Integrations — Tooling-Spezifikum

## Anforderungen

### Cluster-Voraussetzung

- **MUSS [MUST]** voraussetzen, dass ein lokaler Kind-Cluster (oder ein gleichwertiger lokaler K8s-Cluster) mit installiertem `homeassistant`-Helm-Chart läuft — die Spec adressiert nicht das Cluster-Setup, nur den Dev-Loop darauf
- **MUSS [MUST]** den HA-Pod via Label-Selector finden — typische Konvention: `app.kubernetes.io/name=homeassistant` oder ein vergleichbarer Helm-Chart-Standard-Selector
- **SOLLTE [SHOULD]** Cluster-, Namespace- und Pod-Selector-Werte als `Taskfile.yml`-Variablen exponieren, sodass User sie pro Cluster überschreiben können

### Taskfile-Variablen

- **MUSS [MUST]** die folgenden Variablen in `Taskfile.yml` (oder einer eingebundenen Tasks-Datei) standardmäßig setzen:
  - `NAMESPACE` — typisch `default`
  - `POD_SELECTOR` — typisch `app.kubernetes.io/name=homeassistant`
  - `LOCAL_PATH` — der lokale Custom-Integration-Pfad, typisch `custom_components/<domain>/`
  - `REMOTE_PATH` — der HA-`/config`-Pfad, typisch `/config/custom_components/<domain>`
- **SOLLTE [SHOULD]** den Pod-Namen aus dem Selector dynamisch auflösen (`kubectl get pod -n {{.NAMESPACE}} -l {{.POD_SELECTOR}} -o jsonpath='{.items[0].metadata.name}'`) — hartkodierte Pod-Namen brechen, sobald der Pod neu gestartet wurde
- **KANN [MAY]** weitere Variablen für Konvention-Erweiterungen einführen (z. B. `CONTEXT` für Multi-Cluster-Setup, `LOG_TAIL_LINES` für Verify-Variante)

### Deploy-Choreographie (`task deploy-ha`)

- **MUSS [MUST]** den Deploy-Lauf in dieser Reihenfolge durchführen:
  1. **Pre-Lint**: `task lint` — verhindert Deploy von kaputtem Code
  2. **Cache-Bereinigung lokal**: lokales `__pycache__` löschen, falls vorhanden — sonst landet veralteter Bytecode beim Copy
  3. **Datei-Kopie**: `kubectl cp <LOCAL_PATH> <NAMESPACE>/<POD>:<REMOTE_PATH>` — die Files landen direkt im laufenden Container
  4. **Cache-Bereinigung remote**: `kubectl exec <POD> -n <NAMESPACE> -- rm -rf <REMOTE_PATH>/__pycache__` — Pflicht-Schritt, sonst lädt Python beim Restart veralteten Bytecode
  5. **HA-Prozess-Restart**: `kubectl exec <POD> -n <NAMESPACE> -- kill 1` — startet nur den HA-Hauptprozess neu, ohne den Container zu zerstören
  6. **Wait-on-ready**: kurze Wartezeit, bis HA wieder antwortet (typisch 5–15 s; via Health-Endpoint oder einfacher Sleep)
  7. **Log-Tail**: `kubectl logs <POD> -n <NAMESPACE> --tail=200` — direkt nach dem Restart, damit Setup-Errors sofort sichtbar werden
- **MUSS NICHT [MUST NOT]** `kubectl delete pod` als Restart-Mechanismus verwenden — der InitContainer würde erneut laufen und die per `kubectl cp` kopierten Dateien überschreiben; die Änderung verschwände stillschweigend
- **MUSS NICHT [MUST NOT]** den Cache-Bereinigungs-Schritt überspringen — Python-Bytecode-Caching kann veraltete `.pyc`-Dateien laden, was zu falschen False-Positives bei Bug-Suche führt

### Verify-Choreographie (`task verify-ha`)

- **MUSS [MUST]** ein separates Taskfile-Target `task verify-ha` führen, das ohne Deploy nur den Status diagnostiziert
- **MUSS [MUST]** in dieser Reihenfolge durchlaufen:
  1. **Pod-Status**: `kubectl get pod <POD> -n <NAMESPACE> -o wide` — zeigt Phase, Restarts, Age
  2. **Log-Tail (jüngste 5 min)**: `kubectl logs <POD> -n <NAMESPACE> --since=5m` — frischer Output ohne Boilerplate
  3. **Error-Scan**: das Log nach `ERROR`, `Traceback`, `Exception`, `Failed to set up` filtern und nur Treffer ausgeben — typisch via `kubectl logs ... | grep -E "ERROR|Traceback|Exception|Failed to set up"`
  4. **Installierte Files**: `kubectl exec <POD> -n <NAMESPACE> -- ls -la <REMOTE_PATH>` — bestätigt, dass der letzte `kubectl cp` die richtigen Files am richtigen Ort hat
- **SOLLTE [SHOULD]** zusätzlich einen Health-Endpoint-Check ausführen, sofern HA einen exponiert (`/api/`, `/`, `/auth/providers`)

### Bytecode-Cache-Disziplin

- **MUSS [MUST]** vor jedem Deploy lokales `<LOCAL_PATH>/__pycache__` und `<LOCAL_PATH>/**/__pycache__` löschen — sonst landen veraltete `.pyc`-Dateien im Container
- **MUSS [MUST]** nach `kubectl cp` und vor `kill 1` remote `<REMOTE_PATH>/__pycache__` löschen — Python-Importmaschine cached aggressiv und lädt sonst alte Bytecodes
- **KANN [MAY]** statt `rm -rf __pycache__` ein gezieltes Mtime-Check-basiertes Cleanup verwenden, falls die Bereinigungs-Aktion langsam wird; der einfache `rm -rf` reicht für die Größenordnungen einer Custom Integration

### Restart-Mechanismus

- **MUSS [MUST]** `kubectl exec <POD> -n <NAMESPACE> -- kill 1` als alleinigen Restart-Befehl im Deploy-Loop verwenden
- **MUSS NICHT [MUST NOT]** `kubectl delete pod`, `kubectl rollout restart`, oder Helm-`upgrade --force` verwenden — alle drei zerstören den laufenden Container und triggern den InitContainer, der typischerweise `/config` aus einem anderen Mount neu befüllt und die per `kubectl cp` kopierten Custom-Integration-Dateien dabei verliert
- **SOLLTE [SHOULD]** in der Skill-Output-Doku (z. B. `CLAUDE.md` der konsumierenden Integration) den `kill 1`-vs.-`delete pod`-Unterschied explizit dokumentieren — neue Contributor stolpern sonst regelmäßig in dieselbe Falle

### CI-Abgrenzung

- **MUSS NICHT [MUST NOT]** den Kind-Cluster-Loop in CI laufen lassen — CI nutzt das Pytest-basierte Test-Harness (siehe `ha/test-harness`); der Kind-Loop ist für interaktives Dev gedacht
- **KANN [MAY]** einen separaten CI-Job für E2E-Tests gegen einen ephemeren Kind-Cluster führen — eigene Folge-Spec

## Akzeptanzkriterien

- [ ] `Taskfile.yml` (oder eingebundene Tasks-Datei) enthält ein `deploy-ha`-Target
- [ ] `Taskfile.yml` enthält ein `verify-ha`-Target
- [ ] Variablen `NAMESPACE`, `POD_SELECTOR`, `LOCAL_PATH`, `REMOTE_PATH` sind als Top-Level-`vars:` definiert
- [ ] `deploy-ha` führt in dieser Reihenfolge aus: Lint → lokale Cache-Bereinigung → `kubectl cp` → remote Cache-Bereinigung → `kill 1` → Wait → Log-Tail
- [ ] `deploy-ha` enthält **keinen** `kubectl delete pod`-Aufruf
- [ ] `verify-ha` führt aus: Pod-Status → Log-Tail (`--since=5m`) → Error-Scan → Installierte-Files-Check
- [ ] `CLAUDE.md` (oder gleichwertige Dev-Doku) der konsumierenden Integration dokumentiert die `kill 1`-vs.-`delete pod`-Regel
- [ ] CI-Pipeline ruft den Kind-Cluster-Loop **nicht** auf — Pytest-Test-Harness läuft separat
- [ ] Quality-Scale-Marker: **unscaled** (portfolio-spezifisch)

## Offene Fragen

- **Helm-Chart-Konvention**: Welcher konkrete `homeassistant`-Helm-Chart wird im Portfolio bevorzugt? Aktuell als „der Helm-Chart" referenziert; eine konkrete Quelle (z. B. `bjw-s/app-template` mit values-yaml-Snippet) würde die Spec konkreter machen.
- **Wait-on-ready-Mechanik**: `sleep 10` ist primitiv, aber zuverlässig; ein Health-Endpoint-Polling wäre eleganter, aber ist HA-Version-abhängig. Soll die Spec eine Variante festlegen?
- **Multi-Pod-Setups**: Was passiert, wenn der HA-Pod ein StatefulSet mit mehreren Replicas ist? Aktuell als Single-Pod angenommen; in der Praxis selten, aber konzeptionell offen.
- **Linux/Mac/Windows-Plattform-Abhängigkeit**: `kubectl cp` und `kubectl exec ... -- kill 1` funktionieren plattformübergreifend, aber die Wait-Mechanik (z. B. `sleep`) variiert. Aktuell nicht adressiert.
- **`docker compose`-Variante**: Manche User entwickeln gegen ein `docker-compose`-basiertes HA statt Kind. Soll die Spec eine zweite Variante adressieren oder bleibt sie Kind-only?
