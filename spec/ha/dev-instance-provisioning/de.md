# HA-Integration: Dev-Instanz-Provisioning

Status: draft

## Kontext

`ha/dev-environment` regelt den Dev-Loop (Deploy via `kubectl cp`, `kill 1`-Restart, Verify), **setzt aber eine laufende HA-Instanz voraus** — Cluster-Setup und das Bereitstellen der Instanz sind dort ausdrücklich Nicht-Ziel. In der Praxis fehlt diese Instanz aber regelmäßig: ein frischer Kind-Cluster hat keinen HA-Pod, und nicht jedes Setup bringt einen vorinstallierten `homeassistant`-Helm-Chart mit. Ohne Instanz scheitert die gesamte Deploy-Choreographie an der ersten Vorbedingung.

`nolte/kamerplanter-ha` löste das zunächst projektspezifisch über einen lokalen Skill plus ein rohes StatefulSet-Manifest. Diese Spec hebt das Pattern auf die Plugin-Ebene: das **Bereitstellen einer wegwerfbaren Dev-HA-Instanz** per rohem Kubernetes-Manifest, generisch über beliebige HA-Integrationen, als Voraussetzung für `ha/dev-environment`.

Quality-Scale-Marker: **unscaled** (Dev-Tooling ist nicht Teil der HA-Quality-Scale; das Pattern ist nolte-portfolio-spezifisch).

## Ziele

- Eine wegwerfbare HA-Dev-Instanz im lokalen Cluster bereitstellen, **ohne** vorinstallierten Helm-Chart vorauszusetzen — rohes Manifest als Standard
- Die Instanz so formen, dass die Deploy-/Verify-Choreographie aus `ha/dev-environment` ohne weitere Anpassung darauf läuft (gleicher Label-Selektor, stabiler Pod-Name, `/config`-Layout)
- Den `kubectl cp`-Zielpfad vorbereiten, sodass der erste Deploy nicht an einem fehlenden Verzeichnis scheitert
- Idempotentes Bereitstellen und einen sauberen Teardown definieren

## Nicht-Ziele

- Der Dev-Loop selbst (Deploy, `kill 1`-Restart, Verify) — geregelt in `ha/dev-environment`
- Helm-Chart-Authoring und Production-Deployment — die rohe Manifest-Mechanik ist explizit für lokale Dev-Loops
- Cluster-Setup (Kind installieren/konfigurieren) — Voraussetzung, nicht Output
- HA-Konfigurationsinhalte (`configuration.yaml`, Integrations-YAML) jenseits des Erststart-Bootstraps — User-spezifisch
- Reverse-Proxy / Ingress / TLS für die Dev-Instanz — Zugang läuft über `kubectl port-forward`

## Anforderungen

### Workload-Form

- **MUSS [MUST]** die Instanz als **StatefulSet** mit stabilem Pod-Namen (`<name>-0`) bereitstellen — der stabile Name macht `kubectl cp`/`kubectl exec` ohne dynamische Pod-Auflösung möglich und überlebt `kill 1`-Restarts
- **MUSS [MUST]** das Label `app.kubernetes.io/name=homeassistant` (oder den im Portfolio konventionierten Selektor) setzen, damit die Deploy-/Verify-Choreographie aus `ha/dev-environment` den Pod findet
- **MUSS [MUST]** `/config` über ein `volumeClaimTemplate` persistieren, sodass Onboarding-Zustand und kopierte Integration über Restarts erhalten bleiben
- **MUSS [MUST]** einen ClusterIP-Service auf Port 8123 bereitstellen — Zugang zur UI via `kubectl port-forward`
- **SOLLTE [SHOULD]** das offizielle Image `ghcr.io/home-assistant/home-assistant:stable` verwenden, überschreibbar per Eingabe
- **SOLLTE [SHOULD]** die `storageClassName` zur Laufzeit aus der Default-StorageClass des Clusters ableiten, überschreibbar per Eingabe

### Minimale Konfiguration

- **MUSS NICHT [MUST NOT]** eine `configuration.yaml` vorbefüllen — HA generiert beim Erststart eine Default-Konfiguration mit `default_config:`, die für Config-Flow und Entitäten ausreicht
- **MUSS NICHT [MUST NOT]** Ingress, Auth-Provider oder TLS einrichten — der Dev-Zugang läuft über `kubectl port-forward`
- **KANN [MAY]** Komfort-Env setzen (z. B. `TZ`)

### Bootstrap für den Deploy-Loop

- **MUSS [MUST]** nach erreichter Bereitschaft das Verzeichnis `/config/custom_components` anlegen (`mkdir -p`) — sonst scheitert der erste `kubectl cp <…>:/config/custom_components/<domain>` der Deploy-Choreographie am fehlenden Elternverzeichnis
- **SOLLTE [SHOULD]** nach dem Bereitstellen den `port-forward`-Befehl und den Folgeschritt (Deploy-Choreographie aus `ha/dev-environment`) als Hinweis ausgeben

### Idempotenz und Teardown

- **MUSS [MUST]** das Bereitstellen idempotent halten (`kubectl apply`) — ein erneuter Lauf lässt eine bereits laufende Instanz samt `/config`-PVC unberührt
- **MUSS [MUST]** einen Teardown-Pfad bieten, der StatefulSet, Service **und** das `/config`-PVC entfernt — das PVC wird beim StatefulSet-Löschen nicht automatisch mitgelöscht
- **MUSS NICHT [MUST NOT]** zum bloßen Code-Refresh den Pod löschen — das ist `kill 1` aus `ha/dev-environment`; `kubectl delete` ist dem vollständigen Teardown vorbehalten

### Restart-Kompatibilität

- **MUSS [MUST]** ein Image voraussetzen, dessen PID 1 (s6-overlay beim offiziellen Image) auf `SIGTERM` den HA-Prozess sauber neu startet — Voraussetzung dafür, dass `kubectl exec <pod> -- kill 1` aus `ha/dev-environment` als Restart funktioniert, ohne Pod und PVC zu verlieren

## Akzeptanzkriterien

- [ ] Provision erzeugt ein StatefulSet `<name>` (Pod `<name>-0`), einen Service und ein `/config`-PVC
- [ ] Der Pod trägt das Label `app.kubernetes.io/name=homeassistant`
- [ ] `/config` bleibt über `kill 1`-Restarts erhalten
- [ ] `/config/custom_components` existiert nach dem Provision
- [ ] Ein erneuter Provision-Lauf ist idempotent (kein Datenverlust)
- [ ] Teardown entfernt StatefulSet, Service und PVC
- [ ] Kein Helm-Chart vorausgesetzt
- [ ] Quality-Scale-Marker: **unscaled** (portfolio-spezifisch)

## Offene Fragen

- **Helm-Variante**: Soll neben dem rohen Manifest eine Helm-basierte Variante adressiert werden, sobald ein Portfolio-Standard-Chart feststeht (siehe offene Frage in `ha/dev-environment`)?
- **Mehrere parallele Instanzen**: Wie werden mehrere Dev-Loops nebeneinander betrieben — über Namespace-Trennung oder Name-Suffix? Aktuell als Single-Instance angenommen.
- **Readiness-Robustheit**: Die HTTP-Readiness-Probe auf `/` ist HA-versionsabhängig; ein stabilerer Endpoint-Vertrag ist offen.
