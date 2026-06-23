# HA-Integration: Zeroconf-Discovery

Status: draft

## Kontext

Lokale Integrationen (mit `iot_class: local_polling` oder `local_push` aus `ha/integration-architecture`) sollten den User nicht zwingen, IP, Port und Endpunkt-Pfad ihres Backends manuell einzutippen — wenn das Backend per **mDNS / Zeroconf** announciert, kann HA das Setup automatisch vorschlagen, sobald der User die Integration im Frontend hinzufügt. Das ist nicht nur eine UX-Verbesserung, sondern auch eine Quality-Scale-Erwartung: HA Silver verlangt, dass eine Integration Discovery unterstützt, sofern das Backend einen lokalen Discovery-Mechanismus anbietet.

`nolte/kamerplanter-ha` validiert dieses Pattern mit dem Service-Type `_kamerplanter._tcp.local.` und TXT-Records, die `version`, `api_path`, `instance_id`, `tenant` und `scheme` mit­liefern. Der Config-Flow nutzt diese Records als Pre-Fill für die User-Bestätigungs­seite und setzt die `unique_id` aus der `instance_id`, sodass Re-Discovery (z. B. nach IP-Wechsel) nicht zu einem zweiten Entry führt, sondern den existierenden Entry mit der neuen IP aktualisiert.

Diese Spec überführt das Pattern in eine generische Verpflichtung. DHCP-, SSDP-, MQTT-, Bluetooth- und USB-Discovery folgen demselben Muster, leben aber in eigenen Folge-Specs (`ha/dhcp-discovery`, `ha/ssdp-discovery`, …); diese Spec adressiert ausschließlich Zeroconf.

Quality-Scale-Marker: **Silver** (Discovery für lokale Integrationen ist Silver-Pflicht, sofern das Backend einen Discovery-Mechanismus anbietet).

## Ziele

- Zeroconf als Standard-Discovery-Mechanismus für `iot_class: local_*`-Integrationen festschreiben, sofern das Backend mDNS announciert
- TXT-Record-Schema definieren, das Skill-Output aus dem Backend-Discovery-Code ableiten kann
- `async_step_zeroconf` als Pre-Fill-Quelle für den User-Step etablieren — Discovery umgeht den User-Bestätigungs-Schritt nicht
- Re-Discovery mit IP-/Port-Wechsel sauber behandeln: `unique_id` bleibt stabil, IP/Port werden in `entry.data` aktualisiert
- Discovery-Konflikte bei Multi-Instance (zwei Backend-Instanzen im selben Netz) klar auflösen

## Nicht-Ziele

- Backend-seitige mDNS-Announce-Implementation — das Backend ist nicht Teil dieses Plugins; die Spec adressiert nur das HA-seitige Verhalten
- DHCP-, SSDP-, MQTT-, Bluetooth-, USB-Discovery — eigene Folge-Specs
- Service-Type-Reservierung beim IANA — Backend-Authoring-Aufgabe, nicht Plugin-Aufgabe
- Discovery-Cache-Verhalten von HA selbst — HA-internes Detail; das Plugin verlässt sich auf die HA-Garantien

## Anforderungen

### `manifest.json:zeroconf`-Schlüssel

- **MUSS [MUST]** `manifest.json:zeroconf` als Liste von mDNS-Service-Types setzen, sobald die Integration Zeroconf-Discovery unterstützt — typisch `["_<domain>._tcp.local."]`
- **MUSS [MUST]** den Service-Type-String mit `_<name>._tcp.local.` formatieren — der trailing-Punkt ist Pflicht (mDNS-Konvention)
- **KANN [MAY]** mehrere Service-Types listen, wenn das Backend mehrere Announces produziert (z. B. eines für Auth, eines für API) — selten gerechtfertigt
- **MUSS NICHT [MUST NOT]** `_<name>._udp.local.` ohne expliziten Grund verwenden — die meisten REST-/HTTP-APIs nutzen TCP

### TXT-Record-Schema

- **SOLLTE [SHOULD]** im TXT-Record mindestens diese Schlüssel announciert werden:
  - `instance_id` — eine eindeutige, stabile Backend-Instanz-ID; wird zur `unique_id` des ConfigEntries
  - `version` — die Backend-Version; nützlich für Kompatibilitäts-Prüfungen im Skill
  - `api_path` — der API-Pfad-Prefix (z. B. `/api`); zusammen mit IP/Port ergibt sich die volle URL
  - `scheme` — `http` oder `https`; Default `http` wenn nicht gesetzt
- **KANN [MAY]** weitere Schlüssel announciert werden (z. B. `tenant`, `mode`, `region`), wenn die Integration sie für Multi-Tenant- oder Multi-Mode-Auflösung braucht
- **MUSS NICHT [MUST NOT]** `api_key` oder andere Secrets im TXT-Record erwartet — TXT-Records sind im LAN unverschlüsselt sichtbar; Secrets gehören in den User-Eingabe-Step

### `async_step_zeroconf`

- **MUSS [MUST]** in `config_flow.py` `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult` implementieren, wenn `manifest.json:zeroconf` gesetzt ist
- **MUSS [MUST]** die `unique_id` aus dem TXT-Record-`instance_id` ableiten und über `await self.async_set_unique_id(<instance_id>)` setzen
- **MUSS [MUST]** `self._abort_if_unique_id_configured(updates={...})` direkt nach `async_set_unique_id` aufrufen — die `updates`-Map enthält `host`/`port`/`api_path`-Aktualisierungen, sodass eine bestehende Konfiguration auf die neue IP nachgezogen wird
- **MUSS [MUST]** Discovery-Daten als Instanz-Attribute zwischen Steps speichern (`self._discovered_url`, `self._discovered_instance_id`), damit der nachgelagerte User-Bestätigungs-Step sie pre-fillt
- **MUSS [MUST]** in einen Bestätigungs-Step weiterleiten — typisch `async_step_user` mit Pre-Fill, oder ein eigener `async_step_zeroconf_confirm` — niemals direkt `async_create_entry` aufrufen, ohne dass der User die Discovery-Daten gesehen hat
- **SOLLTE [SHOULD]** Backend-Validierung (Test-Connection) erst im Bestätigungs-Step ausführen, nachdem der User die Discovery-Daten bestätigt hat — Validation während des Discovery-Empfangs würde unbestätigte Calls auslösen

### Pre-Fill-Pattern

- **MUSS [MUST]** Discovery-Daten als Suggested-Values in das Schema des nachgelagerten User-Steps einsetzen (`add_suggested_values_to_schema(SCHEMA, discovery_payload)`); der User sieht IP, Port, API-Pfad und Instance-ID, kann aber jedes Feld überschreiben
- **MUSS [MUST]** einen separaten Schritt für Auth-Credentials vorsehen, falls das Backend Authentifizierung verlangt — Discovery liefert keine Credentials
- **SOLLTE [SHOULD]** Multi-Step-Flows nutzen, wenn Discovery-Pre-Fill plus Auth plus Multi-Tenant-Auswahl alle nötig sind — siehe `ha/config-flow-patterns` für Multi-Step-Konvention

### Re-Discovery mit IP-Wechsel

- **MUSS [MUST]** beim Re-Discovery (gleicher `instance_id`, neue IP/Port) den existierenden Entry über `_abort_if_unique_id_configured(updates={CONF_HOST: discovery.host, CONF_PORT: discovery.port, CONF_API_PATH: discovery.properties["api_path"]})` aktualisieren — der Entry erhält die neuen Endpoint-Daten ohne User-Interaktion
- **MUSS NICHT [MUST NOT]** bei Re-Discovery einen zweiten Entry mit derselben `instance_id` anlegen — das ist die Aufgabe von `_abort_if_unique_id_configured`
- **SOLLTE [SHOULD]** dem User in der HA-Notifications einen Hinweis liefern, wenn die IP-/Port-Änderung übernommen wurde — typisch über einen `entry.async_create_issue`-Aufruf

### Multi-Instance-Behandlung

- **MUSS [MUST]** bei mehreren Backend-Instanzen im LAN (jede mit eigener `instance_id`) jede Instanz als separaten ConfigEntry zulassen — die `unique_id`-Disambiguierung passiert automatisch über die unterschiedlichen `instance_id`s
- **MUSS NICHT [MUST NOT]** Discovery-Resultate über mehrere Instanzen mergen — jede Discovery ist ein eigener Flow; der User klickt sich durch zwei separate Setup-Wizards

## Akzeptanzkriterien

- [ ] `manifest.json:zeroconf` ist als Liste von Service-Types gesetzt (Format `_<name>._tcp.local.`)
- [ ] `config_flow.py` enthält `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo)`
- [ ] `async_step_zeroconf` setzt `unique_id` aus dem TXT-Record-`instance_id` und ruft `_abort_if_unique_id_configured(updates={...})` mit IP-/Port-/API-Path-Updates
- [ ] `async_step_zeroconf` leitet in einen Bestätigungs-Step weiter — niemals direkter `async_create_entry`
- [ ] Der Bestätigungs-Step nutzt `add_suggested_values_to_schema(...)` mit den Discovery-Daten
- [ ] TXT-Records mit `instance_id`, `version`, `api_path`, `scheme` werden gelesen
- [ ] Bei Re-Discovery mit gleicher `instance_id` und geänderten Endpoint-Daten wird der bestehende Entry aktualisiert, kein neuer angelegt
- [ ] Quality-Scale-Marker: **Silver**

## Offene Fragen

- **Backend-Authoring-Vorgabe**: Soll das Plugin eine separate Spec für die Backend-Seite (mDNS-Announce mit empfohlenem TXT-Schema) führen, oder bleibt das ausschließlich Backend-Aufgabe? `kamerplanter-ha` hat Mock-Discovery in der Test-Suite, aber keine Backend-Spec.
- **TXT-Record-Pflicht-Mindestmenge**: `instance_id` ist klar Pflicht; sollten `version`, `api_path`, `scheme` ebenfalls auf MUSS hochgezogen werden, oder bleibt das SHOULD?
- **Issue-Erstellung bei IP-Wechsel**: Soll die Spec `entry.async_create_issue` verlangen oder bleibt das KANN? Aktuell SOLLTE — das User-Feedback-Verhalten ist nicht standardisiert.
- **Service-Type-Konflikte**: Was passiert, wenn zwei verschiedene Backends denselben Service-Type announciert (z. B. zwei Hersteller mit `_apex._tcp.local.`)? Aktuell nicht adressiert; in der Praxis ein Kommunikations-Problem zwischen Backend-Authors.
- **Combined-Discovery (Zeroconf + DHCP)**: Sollten Skills, die beide Mechanismen unterstützen, in einer kombinierten Spec zusammengefasst werden, oder bleiben sie separat? `kamerplanter-ha` deckt nur Zeroconf ab; die Frage öffnet sich, sobald der erste DHCP-fähige Skill anlegt.
