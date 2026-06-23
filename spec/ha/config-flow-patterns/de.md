# HA-Integration: Config-Flow-Patterns

Status: draft

## Kontext

Eine moderne Custom Integration in Home Assistant wird ausschließlich über den UI-getriebenen **Config Flow** konfiguriert; YAML-basierte Konfiguration ist seit HA 2024 für neue Integrationen abgekündigt. Eine vollständige Custom Integration deckt vier Flows ab: den **User-Flow** für die Ersteinrichtung, den **Reauth-Flow**, der ausgelöst wird, wenn ein Coordinator `ConfigEntryAuthFailed` raised (siehe `ha/coordinator-patterns`), den **Reconfigure-Flow** für nachträgliche URL- oder Endpoint-Wechsel, und den **Options-Flow** für laufzeit­konfigurierbare Verhaltens-Schalter (typisch: Polling-Intervalle).

`nolte/kamerplanter-ha` validiert dieses Quartett mit zusätzlichem Multi-Step-Pattern (Tenant-Auswahl nach erfolgreicher Auth) und Zeroconf-Discovery, die den User-Flow mit Pre-Fill-Daten startet. Diese Spec überführt das Quartett in eine generische Verpflichtung und legt fest, wie `entry.data` (unveränderliche Setup-Daten) sauber von `entry.options` (Verhaltens-Schalter) getrennt wird.

Quality-Scale-Marker:
- **Bronze**: Basis-Config-Flow (`async_step_user` + `manifest.json:config_flow: true`).
- **Silver**: Reauth-Flow für Auth-basierte Integrationen.
- **Gold**: Reconfigure-Flow.

## Ziele

- Config Flow als alleinigen Konfigurationspfad festschreiben — kein YAML-config-Block, keine Imperative Imports
- Die vier Flows (User / Reauth / Reconfigure / Options) als Standard-Suite definieren, sodass Skill-Output reauth-fähig und reconfigure-fähig ohne Nachrüsten startet
- `unique_id`-Setzung am ConfigEntry zur Pflicht machen, damit Mehrfach-Setups desselben Endpunkts automatisch abgewehrt werden
- Trennung zwischen `entry.data` (immutable Setup-State) und `entry.options` (laufzeit-änderbar) als Vertrag etablieren
- Discovery-Integration (Zeroconf, DHCP, SSDP, …) als Pre-Fill-Quelle für `async_step_user` vorsehen, ohne dass Discovery den User-Bestätigungs-Schritt umgeht
- Schema-Validierung + API-Test-Validierung pro User-Eingabe verlangen, damit fehlerhafte Daten nicht erst in der Coordinator-Schleife auffallen

## Nicht-Ziele

- YAML-basierte Konfiguration (`async_setup` im klassischen Sinne) — verboten für neue Custom Integrations
- Discovery-Mechanik selbst (Zeroconf-TXT-Format, DHCP-MAC-Match, SSDP-Service-Type) — eigene Folge-Specs (`ha/zeroconf-discovery`, `ha/dhcp-discovery`, …)
- Reauth-Trigger im Coordinator — das gehört in `ha/coordinator-patterns` (Mapping `AuthError → ConfigEntryAuthFailed`)
- Multi-Account-/Multi-Tenant-Sharing-Strategien (ein Account-Token für mehrere Entries) — eigene Spec, sobald konkret nötig
- Frontend-Customization des Config-Flow-Renderings — HA gibt das Frontend vor; Skills greifen nicht in das Rendering ein

## Anforderungen

### Manifest-Voraussetzung

- **MUSS [MUST]** `manifest.json:config_flow: true` setzen — siehe `ha/integration-architecture`
- **MUSS NICHT [MUST NOT]** `async_setup`-basierte YAML-Konfiguration als alternativen Konfigurationspfad anbieten; YAML-Config wird in HA 2024 für neue Integrationen abgewiesen und stört das hassfest-Audit

### `ConfigFlow`-Klasse

- **MUSS [MUST]** in `config_flow.py` eine Subklasse von `homeassistant.config_entries.ConfigFlow` definieren
- **MUSS [MUST]** die Klasse als `domain=DOMAIN` annotieren (Class-Attribut)
- **MUSS [MUST]** `VERSION` als Class-Attribut setzen — beginnend bei `1`; jede Schema-Änderung an `entry.data` (z. B. neue Pflicht-Felder) erhöht `VERSION` und triggert `async_migrate_entry`
- **SOLLTE [SHOULD]** den Discovery-Datenträger (z. B. Zeroconf-Properties) als Instanz-Attribute zwischen Steps speichern statt als Klassen-Attribute, damit parallele Flow-Instanzen sich nicht gegenseitig stören

### User-Flow (Pflicht)

- **MUSS [MUST]** `async_step_user(self, user_input=None) -> ConfigFlowResult` implementieren — der primäre Einstiegspunkt für die manuelle Einrichtung
- **MUSS [MUST]** bei `user_input is None` ein Form mit dem Eingabe-Schema rendern (`return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)`)
- **MUSS [MUST]** bei vorhandenem `user_input` zwei Validierungs­stufen ausführen, in dieser Reihenfolge:
  1. Schema-Validierung über `vol.Schema(...)` (passiert implizit beim Rendern, falls fehlerhafte Daten ankommen, aber sicherheitshalber explizit prüfen)
  2. **Echt-Validierung** gegen die API: einen Test-Aufruf (z. B. Health-Endpoint, Token-Validation) ausführen und API-spezifische Exceptions abfangen
- **MUSS [MUST]** bei erfolgreicher Validierung `await self.async_set_unique_id(<unique_id>)` aufrufen, wobei `<unique_id>` den Konfigurations-Ziel-Endpunkt eindeutig identifiziert (typisch `f"{base_url}_{tenant_slug}"` oder `f"{instance_id}"` aus Discovery)
- **MUSS [MUST]** direkt nach `async_set_unique_id` `self._abort_if_unique_id_configured()` aufrufen — verhindert Duplikat-Setups
- **MUSS [MUST]** bei Erfolg `return self.async_create_entry(title=<title>, data=<entry_data>)` zurückgeben; `<title>` ist menschenlesbar und in `strings.json` übersetzt
- **KANN [MAY]** als Multi-Step-Flow strukturiert sein — typisch: Step 1 sammelt Auth-Credentials, Step 2 lässt aus den authentisierten Tenants/Accounts auswählen
- **MUSS NICHT [MUST NOT]** Credentials oder API-Keys ohne explizite User-Bestätigung in `entry.data` schreiben

### Reauth-Flow

- **SOLLTE [SHOULD]** `async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult` implementieren, wenn die Integration Auth-basiert ist (API-Key, OAuth-Token, Username/Passwort)
- **SOLLTE [SHOULD]** den Reauth-Einstieg in einen `async_step_reauth_confirm`-Step weiterleiten, der ein Schema mit dem zu erneuernden Credential rendert
- **MUSS [MUST]** bei fehlgeschlagener Re-Validierung Fehlermeldungen anzeigen, ohne den Entry zu zerstören oder den Reauth-Flow abzubrechen
- **MUSS [MUST]** bei erfolgreicher Re-Validierung `return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates={CONF_<KEY>: user_input[CONF_<KEY>]})` zurückgeben — das aktualisiert `entry.data` mit dem neuen Credential und reloadet den Entry
- **MUSS NICHT [MUST NOT]** Reauth-spezifische Credentials in `entry.options` ablegen — Credentials gehören in `entry.data`

### Reconfigure-Flow

- **SOLLTE [SHOULD]** `async_step_reconfigure(self, user_input=None) -> ConfigFlowResult` implementieren, wenn der API-Endpoint nachträglich änderbar sein soll (z. B. Server-Umzug auf neue IP / neuen Hostname)
- **MUSS [MUST]** bestehende `entry.data`-Werte als Suggested-Values im Schema vorausfüllen, damit der User nur das tatsächlich Geänderte bestätigt: `self.add_suggested_values_to_schema(SCHEMA, self._get_reconfigure_entry().data)`
- **MUSS [MUST]** dieselbe Echt-Validierung wie der User-Flow ausführen, bevor die Daten geschrieben werden
- **MUSS [MUST]** bei Erfolg `return self.async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates={...})` zurückgeben

### Options-Flow

- **SOLLTE [SHOULD]** für HA 2024.2+ `OptionsFlowWithReload` als Basisklasse verwenden — die Klasse ruft beim Speichern automatisch `entry.async_reload()` auf, sodass die Coordinators mit den neuen Intervallen neu gestartet werden
- **KANN [MAY]** für HA-Mindest-Versionen vor 2024.2 den klassischen `OptionsFlow` mit manuellem `await self.hass.config_entries.async_reload(entry.entry_id)` verwenden
- **MUSS [MUST]** in der `ConfigFlow`-Klasse einen `@staticmethod async_get_options_flow(config_entry)` oder das `@callback def async_get_options_flow(config_entry)`-Pendant exportieren, der eine Instanz des Options-Flows zurückgibt
- **MUSS [MUST]** den Options-Flow auf `async_create_entry(data=user_input)` enden lassen — `title` ist hier nicht zulässig
- **SOLLTE [SHOULD]** `add_suggested_values_to_schema(OPTIONS_SCHEMA, self.config_entry.options)` verwenden, damit aktuelle Werte vorausgewählt sind
- **MUSS [MUST]** alle Verhaltens-Optionen, die in `OPTIONS_SCHEMA` ausgewiesen sind, mit einem Default versehen — der Coordinator liest mit `entry.options.get(CONF_<KEY>, DEFAULT_<KEY>)` (siehe `ha/coordinator-patterns`)

### Discovery-Integration

- **KANN [MAY]** Discovery-Steps implementieren (`async_step_zeroconf`, `async_step_dhcp`, `async_step_ssdp`, `async_step_mqtt`, `async_step_bluetooth`, `async_step_usb`); jeder Step hat eine eigene Folge-Spec
- **MUSS [MUST]** bei Discovery die `unique_id` so setzen, dass sie das vom Discovery-Mechanismus identifizierte Gerät eindeutig identifiziert (typisch: `instance_id` aus den Zeroconf-TXT-Records)
- **SOLLTE [SHOULD]** Discovery-Daten als Pre-Fill an `async_step_user` (oder einen Discovery-spezifischen Bestätigungs-Step) weiterreichen, statt den User-Bestätigungs-Schritt zu umgehen — der User soll wissen, was hinzugefügt wird
- **MUSS [MUST]** bei bereits konfiguriertem `unique_id` den Discovery-Flow mit `_abort_if_unique_id_configured(updates={...})` abbrechen — die `updates`-Map kann genutzt werden, um geänderte Discovery-Daten (z. B. neue IP) ohne Reauth in `entry.data` nachzuziehen

### Validierung und Fehlermeldungen

- **MUSS [MUST]** alle User-Eingaben über `voluptuous`-Schemas (`vol.Schema`) deklarativ validieren — keine ad-hoc String-Manipulation
- **MUSS [MUST]** API-Test-Validierung als Echt-Validierungs­schritt durchführen — Schema-Validierung allein reicht nicht
- **MUSS [MUST]** Validierungs-Fehler dem User über das `errors`-Dict in `async_show_form(..., errors=errors)` anzeigen
- **MUSS [MUST]** Fehler-Keys (`"cannot_connect"`, `"invalid_auth"`, `"unknown"`) verwenden, die in `strings.json` als `config.error.<key>` übersetzt sind (siehe `ha/translations`)
- **SOLLTE [SHOULD]** einen gemeinsamen Validierungs-Helper (z. B. `async def _validate_input(hass, data) -> dict`) zwischen User-, Reauth- und Reconfigure-Flow teilen, damit das API-Test-Verhalten konsistent ist

### `entry.data` vs. `entry.options`

- **MUSS [MUST]** unveränderliche Setup-Konfiguration (URL, API-Key, Tenant-Slug, instance_id, andere identifizierende Daten) in `entry.data` ablegen
- **MUSS [MUST]** laufzeit-änderbare Verhaltens-Schalter (Polling-Intervalle, Feature-Toggles, Sprach-Override) in `entry.options` ablegen
- **MUSS NICHT [MUST NOT]** `entry.data` außerhalb von Reauth, Reconfigure oder `async_migrate_entry` ändern — die einzigen erlaubten Wege, `entry.data` zu mutieren, sind diese drei
- **MUSS NICHT [MUST NOT]** Credentials oder andere Auth-Materialien in `entry.options` ablegen — `entry.options` ist als laufzeit-konfigurierbar gedacht und nicht als Credential-Store

## Akzeptanzkriterien

- [ ] `manifest.json:config_flow` ist `true`
- [ ] `config_flow.py` enthält eine `ConfigFlow`-Subklasse mit `domain = DOMAIN` und `VERSION = N`
- [ ] `async_step_user` ist implementiert, validiert das Schema, führt einen API-Test-Call aus und ruft `async_set_unique_id` + `_abort_if_unique_id_configured`
- [ ] Wenn die Integration Auth-basiert ist: `async_step_reauth` und `async_step_reauth_confirm` sind implementiert; bei Erfolg wird `async_update_reload_and_abort` mit `data_updates` aufgerufen
- [ ] Wenn der Endpoint nachträglich änderbar sein soll: `async_step_reconfigure` ist implementiert und füllt bestehende `entry.data` als Suggested-Values
- [ ] Options-Flow ist als `OptionsFlowWithReload`-Subklasse (oder klassischer `OptionsFlow` mit manuellem Reload) implementiert
- [ ] `async_get_options_flow(config_entry)` ist auf der `ConfigFlow`-Klasse exportiert
- [ ] Validierungs-Fehler werden über `errors`-Dict angezeigt; Fehler-Keys sind in `strings.json` als `config.error.<key>` übersetzt
- [ ] `entry.data` und `entry.options` sind sauber getrennt — keine Auth-Daten in `entry.options`, keine Verhaltens-Schalter in `entry.data`
- [ ] Quality-Scale-Marker: **Bronze** für den User-Flow, **Silver** zusätzlich für den Reauth-Flow, **Gold** zusätzlich für den Reconfigure-Flow

## Offene Fragen

- **HA-Mindest-Versions-Implikation für `OptionsFlowWithReload`**: Die Klasse existiert ab HA 2024.2. Wenn die portfolioweite HA-Mindest-Version (siehe Open Question in `ha/integration-architecture`) auf 2024.1 pinnt, müssen Skills den klassischen `OptionsFlow` plus manuellen `async_reload` scaffolden — die Spec-Anforderung würde dann von SHOULD auf MUSS für 2024.2+ konditioniert.
- **Multi-Step-User-Flow als Pflicht**: `kamerplanter-ha` nutzt zwei Steps (Auth → Tenant-Auswahl), weil Multi-Tenant-Setup das nötig macht. Soll die Spec den Multi-Step-Flow grundsätzlich erlauben, oder soll sie eine Konvention für Multi-Tenant-Auswahl definieren?
- **Reauth-Trigger jenseits von `ConfigEntryAuthFailed`**: Reicht der Trigger durch den Coordinator (siehe `ha/coordinator-patterns`), oder gibt es Fälle, in denen Reauth manuell durch den User initiiert wird (z. B. nach freiwilligem Token-Reset im Backend)?
- **Reconfigure ohne Reload**: Gibt es Reconfigure-Fälle, die den Entry **nicht** neu laden sollten (z. B. nur Topic-Hint-Änderung in MQTT-basierter Integration)? `async_update_reload_and_abort` reloadet immer; eine Variante ohne Reload würde `async_update_entry` + `async_abort` voraussetzen.
- **Validierungs-Helper-Stil**: Gemeinsamer freier Helper (`_validate_input`) vs. Methoden auf der Flow-Klasse vs. Methoden auf einer separaten Validator-Klasse — gibt es eine Konvention, oder bleibt das pro Integration entscheidbar?
