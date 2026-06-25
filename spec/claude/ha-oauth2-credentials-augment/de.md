# Skill: `ha-oauth2-credentials-augment`

Status: draft

## Kontext

`ha/application-credentials` definiert den verpflichtenden OAuth2-Pfad für Integrationen: User legen eigene Client-Credentials beim Provider an und tragen sie über die **Application-Credentials-UI** ein. Eine Integration aktiviert diesen Pfad, indem sie `application_credentials` als Manifest-Dependency deklariert (bei gesetztem `config_flow: true`) und ein `application_credentials.py`-Platform-Modul mitliefert, das mindestens `async_get_authorization_server(hass) -> AuthorizationServer` (Authorize-URL + Token-URL) bereitstellt — optional eine Custom-Implementierung (`async_get_auth_implementation`, ggf. `LocalOAuth2ImplementationWithPkce`) und `async_get_description_placeholders`. Der Config Flow läuft über `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` mit `domain=DOMAIN`, der Token-Refresh über die `OAuth2Session`-Helper. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt den OAuth2-/Application-Credentials-Flow in einer **bestehenden** Integration: das `application_credentials.py`-Modul, den `AbstractOAuth2FlowHandler`-Config-Flow inkl. Reauth, die Manifest-Dependency, die `OAuth2Session`-Token-Nutzung und die `application_credentials:`-Strings — spec-konform zu `ha/application-credentials`. Generische User-/Passwort- oder API-Key-Flows bleiben ausdrücklich außen vor.

## Scope

Ergänzung des OAuth2-Application-Credentials-Pfads in einer bestehenden `custom_components/<domain>/`-Integration: `application_credentials.py` (`async_get_authorization_server`, optional `async_get_auth_implementation` / `async_get_description_placeholders`), der `AbstractOAuth2FlowHandler`-Config-Flow mit `DOMAIN` und Logger, die Manifest-Dependency `application_credentials` (plus `config_flow: true`), der Token-Refresh über `OAuth2Session`, der Reauth-Pfad und die `application_credentials:`-Einträge in `strings.json`. Der Skill liest `ha/application-credentials` und validiert.

## Ziele

- Den Application-Credentials-Pfad als Standard für OAuth2 spec-konform verdrahten, sodass User eigene Client-Credentials eintragen können
- Die Manifest-Dependency `application_credentials` setzen und `config_flow: true` erzwingen
- `application_credentials.py` mit `async_get_authorization_server` (gültiger `AuthorizationServer(authorize_url=..., token_url=...)`) erzeugen; bei Bedarf `async_get_auth_implementation` (ggf. mit PKCE) und `async_get_description_placeholders`
- Den Config Flow als `AbstractOAuth2FlowHandler`-Subklasse (`domain = DOMAIN`, Logger) verdrahten, der `async_oauth_create_entry` nutzt und `unique_id` setzt — die generische Flow-Mechanik nicht duplizieren
- Token-Refresh über `OAuth2Session` führen, beim Setup einen Refresh-Aufruf machen und bei Auth-Fehler `ConfigEntryAuthFailed` raisen; den Reauth-Pfad implementieren
- Den Credentials-Dialog über `application_credentials:` in `strings.json` übersetzbar halten und sichere Credential-Behandlung anker

## Nicht-Ziele

- Generische User-/Passwort- oder API-Key-Config-Flows — `ha-config-flow-augment` / `ha/config-flow-patterns`
- Cloud Account Linking über Nabu Casa (zentral verwaltete Client-ID/Secret) — separater Pfad, hier nicht abgedeckt
- Aufbau einer OAuth2-fähigen API-Library (Token-Refresh-Struktur im Client) — eigene Folge-Spec
- Import von YAML-Credentials für Legacy-Integrationen (`async_import_client_credential`) — neue Integrationen akzeptieren keine YAML-Credentials
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`; Coordinator-Verdrahtung — `ha-coordinator-add`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add OAuth2 to my integration", „wire up application credentials", „set up the OAuth2 config flow"
  - „let the user enter their own client id and secret"
  - „füge OAuth2 / Application Credentials hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Provider-OAuth2-Endpunkte (`authorize_url`, `token_url`)
- **KANN [MAY]** erfassen: ob eine Custom-Implementierung (`async_get_auth_implementation`) bzw. PKCE (`LocalOAuth2ImplementationWithPkce`) nötig ist, die `unique_id`-Quelle nach Auth, und Description-Placeholders (z. B. `console_url`) für den Dialog

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** prüfen, dass die Integration einen OAuth2-Provider voraussetzt; deckt ein User-/Passwort- oder API-Key-Flow den Bedarf, **SOLLTE [SHOULD]** der Skill auf `ha-config-flow-augment` verweisen statt OAuth2 zu erzwingen
- **MUSS [MUST]** die `ha/application-credentials`-Spec lesen
- **MUSS NICHT [MUST NOT]** einen bestehenden Nicht-OAuth2-`ConfigFlow` oder ein bestehendes `application_credentials.py` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/application-credentials`)

- **MUSS [MUST]** `application_credentials` ins `dependencies`-Array der `manifest.json` aufnehmen und `config_flow: true` sicherstellen (siehe `ha/integration-manifest`)
- **MUSS [MUST]** `application_credentials.py` anlegen, das `async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer` implementiert und `AuthorizationServer` aus `homeassistant.components.application_credentials` importiert; `authorize_url` und `token_url` sind Pflichtfelder
- **SOLLTE [SHOULD]** `authorize_url` und `token_url` als HTTPS-Endpunkte angeben, nicht als hartkodierte Klartext-HTTP-URLs (siehe `ha/security-hardening`)
- **KANN [MAY]** stattdessen `async def async_get_auth_implementation(hass, auth_domain, credential) -> config_entry_oauth2_flow.AbstractOAuth2Implementation` implementieren, wenn abweichendes Token-Handling nötig ist; für PKCE (RFC 7636) eine `LocalOAuth2ImplementationWithPkce` zurückgeben, die `credential.client_id` und optional `credential.client_secret` übernimmt
- **MUSS [MUST]** den Config Flow als Subklasse von `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` mit `domain = DOMAIN` und einem `logger`-Property definieren; die generische Flow-Mechanik aus `ha/config-flow-patterns` nicht duplizieren
- **MUSS [MUST]** `async_oauth_create_entry(self, data)` nutzen, um den Config Entry mit den OAuth-Token-Daten zu erstellen bzw. (Reauth) zu aktualisieren; **SOLLTE [SHOULD]** dabei `async_set_unique_id` setzen und bei Erstanlage `self._abort_if_unique_id_configured()` aufrufen
- **MUSS [MUST]** den Token-Refresh über die `OAuth2Session`-Helper aus `config_entry_oauth2_flow` laufen lassen statt Tokens selbst zu erneuern; beim Setup einen Refresh-Aufruf ausführen und bei Auth-Fehler `ConfigEntryAuthFailed` raisen, damit HA Reauth startet
- **SOLLTE [SHOULD]** `async_step_reauth` / `async_step_reauth_confirm` implementieren; im Reauth-Fall (`self.source == SOURCE_REAUTH`) `self._abort_if_unique_id_mismatch()` aufrufen und mit `async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)` abschließen
- **MUSS [MUST]** Texte für den Credentials-Dialog unter dem Schlüssel `application_credentials` in `strings.json` definieren (siehe `ha/translations`); **KANN [MAY]** `async_get_description_placeholders(hass) -> dict[str, str]` ergänzen, um z. B. `console_url` einzusetzen
- **MUSS NICHT [MUST NOT]** OAuth2-Client-Credentials in `configuration.yaml` annehmen
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `manifest.json:dependencies` enthält `application_credentials` und `config_flow` ist `true`; `application_credentials.py` existiert und implementiert `async_get_authorization_server` mit gültigem `AuthorizationServer`; der `AbstractOAuth2FlowHandler`-Config-Flow trägt `domain = DOMAIN`, nutzt `async_oauth_create_entry` und setzt `unique_id`; Token-Refresh läuft über `OAuth2Session`; das Setup raised `ConfigEntryAuthFailed`; der Reauth-Pfad ist implementiert; der Dialog ist über `application_credentials:` übersetzt; keine YAML-Credentials werden angenommen
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/application-credentials` liefern, plus die geänderten Datei-Pfade

### Verbote

- **MUSS NICHT [MUST NOT]** einen generischen Nicht-OAuth2-Config-Flow erzeugen oder ersetzen
- **MUSS NICHT [MUST NOT]** Tokens selbst erneuern statt über `OAuth2Session`
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] `manifest.json:dependencies` enthält `application_credentials` und `manifest.json:config_flow` ist `true`
- [ ] `application_credentials.py` existiert und implementiert `async_get_authorization_server` mit gültigem `AuthorizationServer(authorize_url=..., token_url=...)`
- [ ] Wenn nötig: `async_get_auth_implementation` ist implementiert (ggf. mit `LocalOAuth2ImplementationWithPkce` für PKCE)
- [ ] `config_flow.py` enthält eine `AbstractOAuth2FlowHandler`-Subklasse mit `domain = DOMAIN` und Logger, die `async_oauth_create_entry` nutzt und `unique_id` setzt
- [ ] Token-Refresh läuft über `OAuth2Session`; das Setup raised `ConfigEntryAuthFailed` bei Auth-Fehler
- [ ] Reauth ist implementiert: `async_step_reauth` / `async_step_reauth_confirm` plus `_abort_if_unique_id_mismatch` und `async_update_reload_and_abort` im Reauth-Pfad
- [ ] Der Credentials-Dialog ist über den `application_credentials`-Schlüssel in `strings.json` übersetzt; optionale Placeholders kommen aus `async_get_description_placeholders`
- [ ] Keine OAuth2-Client-Credentials werden über `configuration.yaml` angenommen; Bericht nennt die geänderten Datei-Pfade

## Offene Fragen

- **PKCE als Standard vs. Opt-in**: Soll der Skill `LocalOAuth2ImplementationWithPkce` für Provider mit PKCE-Support aktiv empfehlen oder als reine KANN-Option pro Provider-Fähigkeit belassen? Aktuell fragt der Skill nach.
- **`unique_id`-Quelle bei OAuth2**: Die `unique_id` stammt typischerweise aus einer erst nach Auth verfügbaren User-ID. Wie geht der Skill mit Providern ohne stabile User-ID um? Aktuell fall-zu-fall mit Rückfrage.
- **Reauth SHOULD vs. MUST**: `ha/application-credentials` listet den Reauth-Pfad als SHOULD; die Reauth-Quality-Scale-Regel macht ihn faktisch verpflichtend. Soll der Skill ihn als Default immer generieren?
