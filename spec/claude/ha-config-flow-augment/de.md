# Skill: `ha-config-flow-augment`

Status: draft

## Kontext

Der initiale Scaffold (`ha-integration-scaffold`) liefert einen Config-Flow mit User- / Reauth- / Reconfigure- / Options-Step und optional Zeroconf-Discovery. Reale Integrationen brauchen aber regelmäßig nachträgliche Erweiterungen, die der Initial-Scaffold nicht generisch abdecken kann: einen zweiten Auth-Step für Tenant- oder Account-Auswahl, eine zweite Discovery-Quelle (DHCP, SSDP, MQTT, Bluetooth, USB), einen OAuth-Flow als Alternative zu API-Key, oder eine Migration von API-Key auf OAuth in einem laufenden Setup.

Dieser Skill ergänzt einen bestehenden `config_flow.py` um genau diese Patterns, **additiv** und **non-destruktiv** — bestehende Steps werden nicht überschrieben, sondern um neue Steps erweitert, die in den existierenden Flow eingehängt werden.

## Scope

Der Skill erweitert einen **bestehenden** `config_flow.py` einer Custom Integration. Er scaffolded keinen Greenfield-Flow (das macht `ha-integration-scaffold`) und löst keine bestehenden Steps aus dem Code (das wäre destruktive Refactoring-Arbeit, die manuelle User-Approval verlangt). Der Skill identifiziert das gewünschte Augmentations-Pattern aus der User-Anfrage und appendet die nötigen Steps plus Schema-Konstanten plus String-Einträge plus Tests.

## Ziele

- Nachrüstung einzelner Config-Flow-Patterns ohne dass der User den initial-Scaffold-Pfad noch einmal durchlaufen muss
- Non-destruktive Erweiterung: bestehende Steps bleiben unverändert; nur neue Steps und neue Schema-Konstanten landen im Code
- Cross-File-Konsistenz für jeden hinzugefügten Step: `config_flow.py`-Code, `strings.json`-Step-Strings, `translations/<lang>.json`-Spiegel, ggf. `manifest.json`-Discovery-Schlüssel, Tests in `tests/test_config_flow.py`
- Quality-Scale-Übergänge sichtbar machen: ein User → Reauth-Augment hebt Bronze auf Silver; ein User → Reconfigure-Augment hebt Silver auf Gold

## Nicht-Ziele

- Greenfield-Scaffold — `ha-integration-scaffold`
- Destruktive Refactorings (Step-Umbau, Step-Entfernung, Schema-Reduktion) — manuelle Aufgabe
- Backend-spezifische OAuth-Provider-Konfiguration (Token-Endpoint, Scopes, Client-ID-Auth) — der Skill scaffolded den OAuth-**Flow**-Skelett; konkrete Provider-Werte trägt der User
- Multi-Account-Architektur jenseits von Multi-Step-Auswahl (z. B. ein Account mit Sub-Accounts pro Service-Region) — eigene Folge-Spec, sobald konkret nötig

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a multi-step tenant selection to the config flow"
  - „add zeroconf discovery to the existing config flow"
  - „add a reauth flow" (sofern nicht initial scaffolded)
  - „add reconfigure flow" (sofern nicht initial scaffolded)
  - „add OAuth login as alternative to API key"
  - „erweitere den Config-Flow um <Pattern>"
- **MUSS NICHT [MUST NOT]** aktivieren bei:
  - Greenfield-Setup (`ha-integration-scaffold` ist zuständig)
  - Reine Schema-Änderungen (Feld umbenennen, Default ändern) — das ist Code-Edit, nicht Skill-Aufgabe
  - Schema-Migration (`async_migrate_entry`-Logik) — wenn nötig, eigener Skill (`ha-schema-migration`, geplant)

### Eingaben

- **MUSS [MUST]** den `target_dir` (Repository-Wurzel der Integration) erfassen
- **MUSS [MUST]** den `domain` aus `manifest.json` lesen, ohne den User zu fragen — der Domain-Wert ist Teil des bestehenden Codes und wird im Augment wieder verwendet
- **MUSS [MUST]** das gewünschte Augment-Pattern erfassen, aus dieser Liste:
  - `tenant-step` — zweiter Step nach erfolgreichem User-Auth, der eine Liste auswählbarer Tenants/Accounts rendert
  - `zeroconf` — Zeroconf-Discovery-Pre-Fill für den existierenden User-Step
  - `reauth` — Reauth-Flow nachrüsten (Reauth-Step + Confirm-Step)
  - `reconfigure` — Reconfigure-Flow nachrüsten
  - `oauth` — OAuth-Flow als zusätzlicher Auth-Pfad (parallel zum API-Key-Pfad)
- **SOLLTE [SHOULD]** Pattern-spezifische Optionen erfassen:
  - Für `zeroconf`: Service-Type-String (Default `_<domain>._tcp.local.`), Pflicht-TXT-Records (Default: `instance_id`, `version`, `api_path`, `scheme`)
  - Für `tenant-step`: Backend-API-Methode für Tenant-Listing (z. B. `async_get_tenants`)
  - Für `oauth`: Backend-Token-Endpoint, Default-Scopes (User füllt die Werte)

### Pre-Flight

- **MUSS [MUST]** in dieser Reihenfolge prüfen und bei Fehlschlag abbrechen:
  1. `target_dir` ist git-Repo, sauberer Working tree
  2. `target_dir/custom_components/<domain>/config_flow.py` existiert
  3. Das gewünschte Augment-Pattern existiert noch nicht im bestehenden Code (z. B. kein bestehendes `async_step_zeroconf`, wenn der User Zeroconf nachrüsten will) — auf Treffer abbrechen mit Hinweis „pattern already present"
- **MUSS NICHT [MUST NOT]** existierenden Step-Code überschreiben — nur additiv neue Methoden anhängen

### Augment-Patterns

#### `tenant-step`

- **MUSS [MUST]** einen zweiten Flow-Step `async_step_tenant(self, user_input=None)` einfügen, der nach erfolgreichem User-Auth aufgerufen wird
- **MUSS [MUST]** den User-Step so anpassen, dass er bei Erfolg `return await self.async_step_tenant()` zurückgibt statt direkt `async_create_entry` zu rufen
- **MUSS [MUST]** im Tenant-Step die Backend-Tenant-Liste abrufen (`api.<list-method>()`), als `vol.In(tenant_choices)`-Schema rendern, und nach User-Auswahl in `async_create_entry(title=..., data={..., CONF_TENANT_SLUG: tenant_slug})` einmünden
- **MUSS [MUST]** die `unique_id` aus User-Input plus Tenant-Slug ableiten (typisch `f"{base_url}_{tenant_slug}"`)
- **MUSS [MUST]** `strings.json` um `config.step.tenant.{title,data,description}` und ggf. `config.error.no_tenants` erweitern
- **MUSS [MUST]** Tests in `tests/test_config_flow.py` für Single-Tenant-Auswahl und Multi-Tenant-Auswahl ergänzen

#### `zeroconf`

- **MUSS [MUST]** `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo)` einfügen
- **MUSS [MUST]** `manifest.json:zeroconf` auf `[<service_type>]` setzen
- **MUSS [MUST]** Discovery-Daten als Instanz-Attribute (`self._discovered_url`, `self._discovered_instance_id`, `self._discovered_api_path`) zwischen Steps speichern
- **MUSS [MUST]** in den User-Step einen Pre-Fill-Pfad einfügen, der `add_suggested_values_to_schema(SCHEMA, self._discovered_payload)` verwendet, wenn die Instanz-Attribute gesetzt sind
- **MUSS [MUST]** den Re-Discovery-mit-IP-Wechsel-Pfad implementieren: `_abort_if_unique_id_configured(updates={CONF_HOST: ..., CONF_PORT: ..., CONF_API_PATH: ...})`
- **MUSS [MUST]** Tests für Greenfield-Discovery und Re-Discovery-mit-IP-Wechsel ergänzen, plus `_make_zeroconf_info(...)`-Helper in `tests/conftest.py` oder `tests/helpers.py`

#### `reauth`

- **MUSS [MUST]** `async_step_reauth(self, entry_data: Mapping[str, Any])` und `async_step_reauth_confirm(self, user_input=None)` einfügen
- **MUSS [MUST]** den Coordinator-Pfad (`ha/coordinator-patterns`) prüfen — die Coordinator müssen `ConfigEntryAuthFailed` raisen, sonst springt der Reauth-Flow nicht; falls noch nicht vorhanden, dem User den Hinweis ausgeben (kein Auto-Edit)
- **MUSS [MUST]** `strings.json` um `config.step.reauth_confirm.{title,data,description}` und `config.abort.reauth_successful` erweitern
- **MUSS [MUST]** Tests für Happy-Path-Reauth und Sad-Path-Reauth (invalid_auth) ergänzen

#### `reconfigure`

- **MUSS [MUST]** `async_step_reconfigure(self, user_input=None)` einfügen
- **MUSS [MUST]** bestehende `entry.data` als Suggested-Values laden (`self.add_suggested_values_to_schema(SCHEMA, self._get_reconfigure_entry().data)`)
- **MUSS [MUST]** dieselbe Echt-Validierung wie der User-Step verwenden — typisch über einen geteilten `_validate_input(hass, data)`-Helper
- **MUSS [MUST]** auf `async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates={...})` enden
- **MUSS [MUST]** `strings.json` um `config.step.reconfigure.{title,data,description}` erweitern

#### `oauth`

- **MUSS [MUST]** den OAuth-Flow als parallelen Pfad zum bestehenden API-Key-Pfad einführen — der User-Step bekommt eine Auswahl zwischen „API Key" und „OAuth"
- **MUSS [MUST]** `homeassistant.helpers.config_entry_oauth2_flow.AbstractOAuth2FlowHandler` als zweite Basisklasse einbinden (oder die ConfigFlow-Klasse über Multiple Inheritance erweitern, je nach OAuth-Provider)
- **MUSS [MUST]** den OAuth-Setup-Block in `__init__.py` (`hass.helpers.config_entry_oauth2_flow.async_register_implementation(...)`) ergänzen
- **MUSS [MUST]** dem User in der Skill-Output-Doku eine Liste der manuell nachzutragenden Werte ausgeben (Token-Endpoint, Authorize-Endpoint, Scopes, Client-ID, Client-Secret)
- **SOLLTE [SHOULD]** den Skill-Output mit einem deutlichen „provider-spezifische Werte musst du selbst eintragen"-Hinweis abschließen

### Cross-File-Konsistenz

- **MUSS [MUST]** für jeden hinzugefügten Step gleichzeitig: Code in `config_flow.py`, Strings in `strings.json` und allen `translations/<lang>.json`, ggf. Schlüssel in `manifest.json`, Tests in `tests/test_config_flow.py`
- **MUSS [MUST]** den Augment in einem einzigen Commit-fähigen Zustand hinterlassen — keine Halb-Augments, bei denen Code da ist, aber Strings fehlen

### Quality-Scale-Marker im Output

- **SOLLTE [SHOULD]** in der Skill-Output-Zusammenfassung explizit nennen, welcher Quality-Scale-Tier durch den Augment erreicht wurde (`tenant-step` allein hebt nichts; `reauth` hebt Bronze auf Silver; `reconfigure` hebt Silver auf Gold; `zeroconf` hebt für lokale Integrationen Bronze auf Silver — unter der Annahme, dass die ha/coordinator-patterns-Konformität gegeben ist)

## Akzeptanzkriterien

- [ ] Der Skill modifiziert nur `config_flow.py`, `strings.json`, `translations/<lang>.json`, ggf. `manifest.json` und `tests/test_config_flow.py` — keine Änderungen an `coordinator.py`, `entity.py`, Plattform-Modulen oder `__init__.py` außer für `oauth`
- [ ] Bestehende Steps in `config_flow.py` bleiben unverändert
- [ ] Der hinzugefügte Step erfüllt die jeweilige `ha/config-flow-patterns` (oder `ha/zeroconf-discovery`)-Pflicht
- [ ] Translation-Strings sind in `strings.json` und allen `translations/<lang>.json` synchron
- [ ] Tests für den neuen Step laufen direkt nach Augment fehlerfrei
- [ ] Bei `oauth`: der Skill-Output enthält eine explizite Liste der provider-spezifischen Werte, die der User selbst eintragen muss
- [ ] Quality-Scale-Tier-Übergang ist im Output benannt

## Offene Fragen

- **OAuth-Provider-Catalogue**: Soll der Skill einen kleinen Katalog häufiger OAuth-Provider (Google, GitHub, generic OAuth2) als Templates mit­bringen, oder bleibt jeder Provider User-Aufgabe?
- **Reauth-Trigger-Verifikation**: Aktuell weist der Skill nur darauf hin, dass die Coordinator `ConfigEntryAuthFailed` raisen müssen. Soll er den `coordinator.py`-Code auch lesen und prüfen, oder bleibt das User-Aufgabe?
- **Tenant-Listing-API-Methode**: Aktuell muss der User die Methode benennen (`async_get_tenants`). Soll der Skill den `api.py`-Code lesen und Methoden-Vorschläge generieren, oder bleibt das User-Eingabe?
- **Multi-Augment in einem Aufruf**: Soll der Skill mehrere Augment-Patterns in einem Lauf hintereinander ausführen können (z. B. `tenant-step` + `zeroconf`), oder bleibt jeder Augment ein eigener Aufruf?
- **Migration API-Key → OAuth**: Wenn der User einen bestehenden API-Key-Flow auf OAuth migrieren will, ist das ein destruktiver Eingriff in `entry.data`. Soll dieser Skill das adressieren oder eine eigene `ha-auth-migration`-Spec eröffnen?
