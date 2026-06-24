# HA-Integration: Application Credentials (OAuth2)

Status: draft

## Kontext

Integrationen, die [Konfiguration via OAuth2](https://developers.home-assistant.io/docs/core/integration/config_flow#configuration-via-oauth2) anbieten, lassen User ihre Accounts verknüpfen. OAuth2 erfordert Credentials (Client-ID / Client-Secret), die zwischen Anwendung und Provider geteilt werden. Home Assistant stellt diese integrationsspezifischen OAuth2-Credentials über die **Application-Credentials-Platform** bereit: Der User legt eigene Credentials beim Cloud-Provider an — oft als App-Entwickler — und registriert sie über die Application-Credentials-UI bei Home Assistant. Dieser Pfad (*Local OAuth with Application Credentials Component*) ist laut HA-Docs für **alle** OAuth2-Integrationen verpflichtend; das alternative *Cloud Account Linking* über Nabu Casa ist empfohlen, aber nicht Gegenstand dieser Spec.

Die Integration aktiviert diesen Pfad, indem sie `application_credentials` als Manifest-Dependency deklariert und ein `application_credentials.py`-Platform-Modul mitliefert. Dieses Modul stellt mindestens einen `AuthorizationServer` (Authorize-URL + Token-URL) bereit; optional eigene OAuth2-Implementierungen, PKCE-Unterstützung und Beschreibungs-Placeholders für die UI. Der eigentliche Config Flow läuft dann über `config_entry_oauth2_flow.AbstractOAuth2FlowHandler`, und der Token-Refresh über die `OAuth2Session`-Helper.

Abgrenzung: Diese Spec deckt **ausschließlich** den OAuth2-Application-Credentials-Pfad ab. Generische User-/Passwort- oder API-Key-Config-Flows bleiben in `ha/config-flow-patterns`; der OAuth2-Flow ist eine Variante davon und wird hier nur dort beschrieben, wo er sich vom generischen Quartett unterscheidet.

## Ziele

- Die Application-Credentials-Platform als Standard-Pfad für OAuth2-Integrationen festschreiben, sodass User eigene Client-Credentials eintragen können
- Die Manifest-Dependency `application_credentials` als Pflicht für jede OAuth2-Integration etablieren
- Den Vertrag für `application_credentials.py` definieren — mindestens `async_get_authorization_server`, optional Custom-Implementierung und Beschreibungs-Placeholders
- Die Kopplung an den OAuth2-Config-Flow (`AbstractOAuth2FlowHandler`) und den Token-Refresh (`OAuth2Session`) festhalten, ohne die generische Flow-Mechanik aus `ha/config-flow-patterns` zu duplizieren
- Sichere Behandlung der User-eingegebenen Credentials (`client_id` / `client_secret`) als Vertrag verankern (siehe `ha/security-hardening`)
- Übersetzbare Anweisungs-Texte für den Credentials-Dialog über `strings.json` und optionale Placeholders sicherstellen (siehe `ha/translations`)

## Nicht-Ziele

- Generische User-/Passwort- oder API-Key-Config-Flows — die bleiben in `ha/config-flow-patterns`
- Cloud Account Linking über Nabu Casa (zentral verwaltete Client-ID/Secret) — separater Pfad, hier nicht abgedeckt
- Aufbau einer OAuth2-fähigen API-Library (Token-Refresh-Struktur im Client) — eigene Folge-Spec / API-Library-Guide
- Import von YAML-Credentials für Legacy-Integrationen (`async_import_client_credential`) — nur als Migrationspfad relevant, keine Neu-Integration darf YAML-Credentials akzeptieren
- Frontend-Rendering des Application-Credentials-Dialogs — HA gibt das Frontend vor

## Anforderungen

### Voraussetzungen (manifest dependency)

- **MUSS [MUST]** `application_credentials` im `dependencies`-Array der `manifest.json` listen — siehe `ha/integration-manifest`
- **MUSS [MUST]** zusätzlich `manifest.json:config_flow: true` gesetzt haben — die Application-Credentials-Platform wird über einen Config Flow konsumiert (siehe `ha/config-flow-patterns`)

### `application_credentials.py`-Platform

- **MUSS [MUST]** im Integrations-Ordner eine Datei `application_credentials.py` anlegen, die die Platform-Funktionen implementiert
- **MUSS [MUST]** `async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer` implementieren und einen gültigen `AuthorizationServer` zurückgeben
- **KANN [MAY]** stattdessen `async def async_get_auth_implementation(hass, auth_domain, credential) -> config_entry_oauth2_flow.AbstractOAuth2Implementation` implementieren, wenn eine Custom-OAuth2-Implementierung (z. B. abweichendes Token-Handling) benötigt wird
- **KANN [MAY]** für PKCE-Unterstützung in `async_get_auth_implementation` eine `LocalOAuth2ImplementationWithPkce` zurückgeben (RFC 7636), die `credential.client_id` und optional `credential.client_secret` übernimmt
- **MUSS NICHT [MUST NOT]** OAuth2-Client-Credentials in `configuration.yaml` annehmen — neue Integrationen lassen den User die Credentials über die Application-Credentials-UI eintragen

### Authorization Server

- **MUSS [MUST]** den `AuthorizationServer` aus `homeassistant.components.application_credentials` importieren
- **MUSS [MUST]** `authorize_url` setzen — die OAuth-Authorize-URL, auf die der User während des Config Flows umgeleitet wird (Pflichtfeld)
- **MUSS [MUST]** `token_url` setzen — die URL zum Beziehen eines Access-Tokens (Pflichtfeld)
- **SOLLTE [SHOULD]** `authorize_url` und `token_url` als HTTPS-Endpunkte des Providers angeben, nicht als hartkodierte Klartext-HTTP-URLs (siehe `ha/security-hardening`)

### Config-Flow-Integration (OAuth2)

- **MUSS [MUST]** den Config Flow als Subklasse von `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` mit `domain=DOMAIN` definieren — die generische Flow-Mechanik (Schema-Validierung, `unique_id`, `entry.data` vs. `entry.options`) ist in `ha/config-flow-patterns` festgelegt
- **MUSS [MUST]** den von HA aufgerufenen `async_oauth_create_entry(self, data)` nutzen, um den Config Entry mit den OAuth-Token-Daten zu erstellen bzw. (im Reauth-Fall) zu aktualisieren
- **SOLLTE [SHOULD]** in `async_oauth_create_entry` `async_set_unique_id` setzen und bei Erstanlage `self._abort_if_unique_id_configured()` aufrufen, um Duplikat-Setups desselben Accounts zu verhindern

### Token-Refresh & Reauth

- **MUSS [MUST]** den Token-Refresh über die HA-bereitgestellten `OAuth2Session`-Helper aus `config_entry_oauth2_flow` laufen lassen, statt Tokens selbst zu erneuern — die API-Library muss so strukturiert sein, dass HA den Refresh verantwortet
- **MUSS [MUST]** beim Setup einen Token-Validierungs-/Refresh-Aufruf ausführen und bei Auth-Fehler `ConfigEntryAuthFailed` raisen, damit HA den Reauth-Flow startet (siehe `ha/config-flow-patterns` und die Reauth-Quality-Scale-Regel)
- **SOLLTE [SHOULD]** `async_step_reauth` / `async_step_reauth_confirm` implementieren, die den Reauth-Dialog anzeigen und dann via `async_step_user` zurück in den OAuth2-Flow leiten
- **MUSS [MUST]** im Reauth-Fall (`self.source == SOURCE_REAUTH`) `self._abort_if_unique_id_mismatch()` aufrufen und mit `async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)` abschließen — so wird derselbe Account erzwungen und der Entry mit neuen Tokens neu geladen

### Beschreibungs-Placeholders/Übersetzungen

- **MUSS [MUST]** Texte für den Application-Credentials-Dialog unter dem Schlüssel `application_credentials` in `strings.json` definieren (siehe `ha/translations`)
- **KANN [MAY]** `async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]` in `application_credentials.py` implementieren, um Platzhalter (z. B. `console_url`) in den Dialog-Text einzusetzen
- **SOLLTE [SHOULD]** dem User im `description`-Text einen Hinweis geben, wo (z. B. in welcher Developer-Console) die Credentials anzulegen sind, idealerweise als verlinkter Placeholder

## Akzeptanzkriterien

- [ ] `manifest.json:dependencies` enthält `application_credentials` und `manifest.json:config_flow` ist `true`
- [ ] `application_credentials.py` existiert und implementiert `async_get_authorization_server` mit gültigem `AuthorizationServer(authorize_url=..., token_url=...)`
- [ ] Wenn eine Custom-Implementierung nötig ist: `async_get_auth_implementation` ist implementiert (ggf. mit `LocalOAuth2ImplementationWithPkce` für PKCE)
- [ ] `config_flow.py` enthält eine `AbstractOAuth2FlowHandler`-Subklasse mit `domain = DOMAIN`, die `async_oauth_create_entry` nutzt und `unique_id` setzt
- [ ] Der Token-Refresh läuft über `OAuth2Session`; das Setup raised `ConfigEntryAuthFailed` bei Auth-Fehler
- [ ] Reauth ist implementiert: `async_step_reauth` / `async_step_reauth_confirm` plus `_abort_if_unique_id_mismatch` und `async_update_reload_and_abort` im Reauth-Pfad
- [ ] Der Credentials-Dialog ist über den `application_credentials`-Schlüssel in `strings.json` übersetzt; optionale Placeholders kommen aus `async_get_description_placeholders`
- [ ] Keine OAuth2-Client-Credentials werden über `configuration.yaml` angenommen

## Offene Fragen

- **PKCE als Standard vs. Opt-in**: Soll die Spec `LocalOAuth2ImplementationWithPkce` für neue Integrationen empfehlen (SHOULD), wo der Provider PKCE unterstützt, oder bleibt PKCE eine reine KANN-Option pro Provider-Fähigkeit?
- **Cloud Account Linking als Folge-Spec**: Das *Cloud Account Linking* über Nabu Casa ist von HA empfohlen, aber hier als Nicht-Ziel gesetzt. Soll dafür eine eigene Spec (`ha/cloud-account-linking`) angelegt werden, sobald eine Portfolio-Integration den Partner-Pfad geht?
- **YAML-Credential-Import**: `async_import_client_credential` existiert für Legacy-Migrationen. Soll die Spec einen expliziten Migrationsabschnitt erhalten, oder bleibt der Import außerhalb des Scopes, da neue Integrationen ihn nicht brauchen?
- **`unique_id`-Quelle bei OAuth2**: Im OAuth2-Flow stammt die `unique_id` typischerweise aus einer User-ID, die erst nach erfolgreicher Auth verfügbar ist. Gibt es Provider ohne stabile User-ID, bei denen eine alternative `unique_id`-Strategie nötig wird?
