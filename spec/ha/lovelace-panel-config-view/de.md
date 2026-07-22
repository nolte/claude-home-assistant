# HA-Integration: Custom-Panel Konfigurations- und Options-Ansicht

Status: draft

## Kontext

Ein Custom-Panel (`panel_custom`) ist eine vollflächige Frontend-Fläche. Über das reine Darstellen von Daten hinaus brauchen viele Panels eine **eigene Konfigurations- oder Options-Ansicht** — eine Einstellungs-Fläche, auf der der User (oder Admin) das Verhalten des Panels prüft und ändert und auf der diese Entscheidungen **persistiert** werden, sodass sie einen Reload überstehen. Das ist das Panel-Pendant zum Config-vs-Options-Flow einer Integration: manche Werte stehen zum Deploy-Zeitpunkt fest, andere sollen zur Laufzeit editierbar sein.

HA bietet keine einzelne „Panel-Options"-API. Stattdessen setzt ein Panel die Options-Ansicht aus vorhandenen Frontend-Bausteinen zusammen und wählt einen Persistenz-Pfad bewusst. Diese Spec deckt **diese Fläche** ab: wie die Konfigurations-/Options-Ansicht eines Panels aussehen kann, welche Eingaben sie lesen darf und — die tragende Entscheidung — **wo die geänderten Werte gespeichert werden**. Sie grenzt sich gegen die Schwester-Specs ab und referenziert sie per Slug, statt zu duplizieren:

- Panel-**Registrierung und Element-Contract** (`panel_custom`-YAML-Keys, `module_url`, `customElements.define`, die Properties `hass` / `narrow` / `route` / `panel`) — `ha/lovelace-views-panels`. Diese Spec setzt diesen Contract voraus und baut darauf auf.
- Die **WebSocket-Command-Definition** (`@websocket_api.websocket_command`, `async_register_command`) — `ha/frontend-websocket-commands`. Diese Spec ruft einen solchen Command als Persistenz-Pfad auf; sie dokumentiert nicht neu, wie man einen definiert.
- Der **`hass`-Objekt- und `hass.callWS`**-Datenkanal — `ha/frontend-data-api`.
- Das **`ha-form` / `ha-selector`**-Formular-Schema-Pattern — `ha/lovelace-card-editor` (hier für das Options-Formular eines Panels wiederverwendet).
- Das Backend-**Config-vs-Options**-Konzept-Pendant — `ha/config-flow-patterns`.
- Serverseitige **Autorisierungs-Durchsetzung** — `ha/security-hardening`.

**Evidenz-Tiers.** HA-interne Fakten müssen gegen die offizielle Doku verifiziert werden, nicht aus dem Gedächtnis behauptet (`ha/upstream-docs-verification`). Die Panel-Options-Fläche ist in der offiziellen Doku dünn — die Doku beschreibt Registrierung und `panel.config`, aber nicht Persistenz, nicht die `route`-Form und nicht den Per-User-Data-Store. Jede Regel unten ist getaggt:

- `[doc]` — in der offiziellen Doku angegeben (`developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/`, `.../custom-card/`, `.../frontend/data/`, `.../extending/websocket-api/`; `home-assistant.io` `panel_custom`-Integrationsseite); zitiert oder paraphrasiert.
- `[src]` — gegen den HA-Frontend-/Backend-Source (`github.com/home-assistant/frontend`, `github.com/home-assistant/core`) verifiziert, weil die Doku schweigt; der Source ist die Autorität für den exakten Identifier / das exakte Verhalten.
- `[unsupported]` — weder in der Doku noch als stabile öffentliche API angegeben; eine Schlussfolgerung aus dem Source oder aus Abwesenheit. **Muss** als Schlussfolgerung präsentiert werden, nie als dokumentierte Garantie.
- `[policy]` — eine nolte-Portfolio-Regel; **keine** HA-dokumentierte Anforderung, als solche gekennzeichnet.

Quality-Scale-Marker: Custom-Panels sind **nicht Teil der HA-Quality-Scale**; die Konfigurations-/Options-Ansicht eines Panels ist eine Frontend-Lieferform und steht außerhalb der Skala.

## Ziele

- **Deploy-Zeit-Config** (`panel.config`, bei Registrierung gesetzt) von **laufzeit-editierbaren Optionen** (persistiert über einen WebSocket-Command oder den Per-User-Data-Store) trennen, damit ein Panel nicht über den falschen Kanal zu persistieren versucht
- Die zwei dokumentierten/verifizierten Persistenz-Pfade etablieren — einen **Custom-WebSocket-Command** für Domain-/Shared-State und den **`frontend/*_user_data`**-Store für Per-User-UI-Präferenzen — und wann welcher gilt
- Die Options-Ansicht aus wiederverwendeten Frontend-Bausteinen (`ha-form` + `ha-selector`) zusammensetzen, statt Formular-Widgets selbst zu bauen
- Admin-only-Optionen sowohl in der UI (`require_admin` / `hass.user.is_admin`) als auch — entscheidend — **serverseitig** im Command-Handler absichern
- HA-Doku-Fakten, Frontend-/Backend-Source-Fakten, Schlussfolgerungen und Portfolio-Policy sauber trennen, sodass keine Regel auf einer undokumentierten Annahme ruht, die als dokumentiert präsentiert wird

## Nicht-Ziele

- Panel-Registrierung und Element-Property-Contract (`panel_custom`-YAML, `module_url`, `hass`/`narrow`/`route`/`panel`, ES5-Adapter, `embed_iframe`) — `ha/lovelace-views-panels`
- Einen WebSocket-Command im Backend definieren (Decorator, Schema, `async_register_command`, Subscription-Lifecycle) — `ha/frontend-websocket-commands`
- Das Detail-Schema der `hass`-Objekt-Datenkanäle — `ha/frontend-data-api`
- Der Card-Config-Editor (`getConfigElement` / `getConfigForm` / `config-changed`) — `ha/lovelace-card-editor` (diese Spec verwendet das `ha-form`-Pattern für ein Panel wieder, nicht den Card-Editor-Contract)
- Der Backend-Integration-Config-/Options-Flow (`config_flow.py`, `OptionsFlow`) — `ha/config-flow-patterns`
- Theming und Übersetzungen der Options-Ansicht — eigene Achsen

## Anforderungen

### Statische Registrierungs-Config (`panel.config`)

- **MUSS [MUST]** den bei der Registrierung übergebenen `config`-Block als **Deploy-Zeit-, Einmal-gesetzt**-Daten behandeln: er wird bei der Instanziierung in die Web-Komponente übergeben und zur Laufzeit als `panel.config` gelesen `[doc]` (die `panel_custom`-Seite: „Config is available as `panel.config`"; der `config:`-YAML-Key ist „Configuration to be passed into your web component when being instantiated")
- **MUSS NICHT [MUST NOT]** `panel.config` zur Laufzeit mutieren und erwarten, dass die Änderung persistiert — es gibt **keinen dokumentierten Write-Back-Pfad** vom Element zurück in die Registrierungs-Config `[unsupported]` (die Read-Only-Natur ist aus dem Source geschlossen: `config` ist ein Registrierungs-Zeit-Objekt ohne Persistenz-Hook; sie ist nicht als read-only dokumentiert, also als Schlussfolgerung präsentieren, nicht als Garantie)
- **KANN [MAY]** das Panel programmatisch via `async_register_built_in_panel(..., config=...)` aus einer Integration registrieren statt via `panel_custom`-YAML `[src]` (die Python-Registrierungs-API ist nicht in der Doku; nur die resultierende `panel.config`-Property ist `[doc]`)
- **SOLLTE [SHOULD]** `panel.config` für Werte nutzen, die legitim pro Deployment feststehen (eine API-Basis-URL, ein Feature-Flag, ein Modus), und alles, was der **User editiert**, an einen der Persistenz-Pfade unten leiten

### Die Options-Ansichts-Fläche (Routing & Formular-Komposition)

- **SOLLTE [SHOULD]** die Options-/Einstellungs-Ansicht als eigene Region oder Sub-Route des Panels rendern statt als separate Registrierung — ein Panel ist ein vollflächiges Element, und die Options-Ansicht ist Teil davon
- **KANN [MAY]** eine Panel-interne Sub-Route aus dem `route`-Property (`{ prefix, path }`) treiben, das HA dem Element setzt `[src]` (das `route`-Property und seine `{ prefix, path }`-Form erscheinen im Panel-Beispiel, sind aber **nicht** in der dokumentierten Property-Tabelle; `route` als source-verifiziert behandeln, konsistent zu `ha/lovelace-views-panels`)
- **SOLLTE [SHOULD]** das Options-Formular aus `ha-form`, gebunden an ein Schema aus `ha-selector`-Selector-Configs, zusammensetzen — der dokumentierte öffentliche Weg ist ein Formular-Schema aus Selectors `[doc]` (der `getConfigForm`-Selector-Ansatz verlinkt auf den `/docs/blueprint/selectors/`-Selector-Katalog), während die **direkt** in einem Panel verwendeten `ha-form` / `ha-selector`-Elemente frontend-intern sind `[src]` (es gibt kein dokumentiertes `getConfigForm`-Pendant für ein eigenständiges Panel, also bindet ein Panel `ha-form` direkt)
- **SOLLTE [SHOULD]** HA-Selectors (Entity, Area, Boolean, Number, Select) wiederverwenden statt roher Inputs, damit die Options-Ansicht HAs Validierung, Theming und Mobile-Verhalten erbt `[policy]`

### Persistenz-Pfad A — Custom-WebSocket-Command (Domain-/Shared-State)

- **MUSS [MUST]** einen **Custom-WebSocket-Command** als Persistenz-Pfad nutzen, wenn die Optionen **Domain- oder Shared-State** sind (Konfiguration, die für die Installation gilt, nicht nur den aktuellen User) — ihn gemäß `ha/frontend-websocket-commands` definieren und aus dem Panel mit `hass.callWS({ type: "<domain>/options/set", ... })` aufrufen `[doc]` (`hass.callWS` ist dokumentiert als „Call a WebSocket command on the backend"; `@websocket_api.websocket_command` + `async_register_command` sind unter Extending the WebSocket API dokumentiert)
- **SOLLTE [SHOULD]** einen passenden Read-Command (`hass.callWS({ type: "<domain>/options/get" })`) bereitstellen, den die Options-Ansicht beim Laden aufruft, und — wo sich die Optionen anderswo ändern können — einen Subscription-Command, damit die Ansicht live aktualisiert `[doc]`
- **MUSS NICHT [MUST NOT]** einen Ad-hoc-HTTP-Endpoint erfinden oder aus dem Frontend in eine Datei schreiben, um Optionen zu persistieren, wenn ein WebSocket-Command der dokumentierte Mechanismus ist `[policy]`

### Persistenz-Pfad B — Per-User-Data-Store (`frontend/*_user_data`)

- **KANN [MAY]** **Per-User-UI-Präferenzen** (ein gewählter Tab, eine eingeklappte Sektion, eine Sortierreihenfolge — State, der zum aktuellen User gehört, nicht zur Installation) über den Frontend-User-Data-Store persistieren: `frontend/get_user_data`, `frontend/set_user_data`, `frontend/subscribe_user_data` `[src]` (diese Commands sind in **keinem** offiziellen Doku-Repo dokumentiert; sie sind nur im Frontend-Source `src/data/frontend.ts` und der Backend-`frontend`-Komponente verifiziert — als source-verifiziert behandeln und als undokumentiert kennzeichnen)
- **MUSS NICHT [MUST NOT]** den Per-User-Data-Store für **installationsweite** Konfiguration nutzen — er ist pro User gekeyt, sodass admin-gesetzte Shared-Optionen dort für andere User nicht sichtbar wären `[src]`
- **SOLLTE [SHOULD]** Pfad A vs. Pfad B nach **Ownership** wählen: Shared-/Domain-State → WebSocket-Command (Pfad A); Per-User-Präferenz → User-Data-Store (Pfad B) `[policy]`

### Admin-Gating & serverseitige Durchsetzung

- **KANN [MAY]** `require_admin: true` an der `panel_custom`-Registrierung setzen, sodass das Panel für Nicht-Admin-User in der Sidebar verborgen wird `[doc]` (die `panel_custom`-Seite: „If admin access is required to see this panel")
- **SOLLTE [SHOULD]** zusätzlich Admin-only-Controls **innerhalb** der Options-Ansicht auf `hass.user.is_admin` gaten, damit ein Nicht-Admin, der die Ansicht erreicht, keine Admin-only-Optionen sieht `[doc]` (`hass.user` exponiert `is_admin`)
- **MUSS [MUST]** Admin-only-Writes **serverseitig** im WebSocket-Command-Handler durchsetzen — `require_admin` verbirgt das Panel nur im Frontend und `hass.user.is_admin` ist ein Frontend-Check; keiner verhindert einen präparierten WebSocket-Call `[src]`/`[policy]` (die serverseitige Durchsetzung von `require_admin` ist nicht dokumentiert; der Command-Handler ist die echte Trust-Boundary, gemäß `ha/security-hardening`)

### Config-vs-Options-Trennung

- **MUSS [MUST]** jeden konfigurierbaren Wert als **Deploy-Zeit-Config** (pro Deployment fest → `panel.config`) oder **Laufzeit-Option** (user- oder admin-editierbar → Persistenz-Pfad A oder B) klassifizieren, analog zur Integration-Config-vs-Options-Trennung in `ha/config-flow-patterns` `[policy]`
- **MUSS NICHT [MUST NOT]** für einen Wert, den der User zur Laufzeit ändern soll, eine `configuration.yaml`-Bearbeitung und einen HA-Neustart verlangen — dieser Wert ist eine Laufzeit-Option und gehört in einen Persistenz-Pfad, nicht in `panel.config` `[policy]`

## Akzeptanzkriterien

- [ ] Jeder konfigurierbare Wert ist als Deploy-Zeit-`panel.config` oder als Laufzeit-Option klassifiziert; Laufzeit-Optionen verlangen keine YAML-Bearbeitung + Neustart
- [ ] `panel.config` wird zur Laufzeit als `panel.config` gelesen und im Element nie mutiert, um State zu persistieren
- [ ] Domain-/Shared-Optionen persistieren über einen Custom-WebSocket-Command (`hass.callWS`), mit passendem Read- (und wo relevant Subscription-) Command
- [ ] Per-User-UI-Präferenzen persistieren über den `frontend/*_user_data`-Store und werden nicht für installationsweite Config genutzt
- [ ] Das Options-Formular ist aus `ha-form` + `ha-selector`-Selectors zusammengesetzt, nicht aus rohen Inputs
- [ ] Admin-only-Optionen sind in der UI gegatet (`require_admin` / `hass.user.is_admin`) **und** serverseitig im Command-Handler durchgesetzt
- [ ] Jede Regel ist `[doc]` / `[src]` / `[unsupported]` / `[policy]` getaggt; source-verifizierte, geschlossene und Policy-Fakten werden nicht als dokumentierte HA-Fakten präsentiert
- [ ] Quality-Scale-Marker: nicht Teil der HA-Quality-Scale (Frontend-Lieferform)

## Offene Fragen

- **`route`-getriebene Sub-Routing-Tiefe**: die `route`-`{ prefix, path }`-Form ist source-verifiziert, nicht dokumentiert. Ist Panel-internes Sub-Routing für eine Einstellungs-Ansicht ein stabiles Pattern, oder sollte die Options-Ansicht eine Same-Page-Region bleiben, um nicht von undokumentierten `route`-Internas abzuhängen?
- **`ha-form` als Panel-API**: `getConfigForm` (Schema aus Selectors) ist für Cards dokumentiert, aber es existiert kein Pendant für Panels, sodass ein Panel `ha-form` / `ha-selector` direkt bindet (`[src]`). Gibt es eine unterstützte Panel-Level-Formular-API, oder ist das direkte `ha-form`-Binden der einzige Weg?
- **`frontend/*_user_data`-Stabilität**: die Per-User-Data-Commands sind undokumentiert (`[src]`). Gibt es einen dokumentierten Per-User-Präferenz-Store für Panels, oder ist dies trotz der Doku-Lücke der De-facto-Store?
- **Serverseitige `require_admin`-Semantik**: die Doku sagt, `require_admin` steuert die Panel-Sichtbarkeit, sagt aber nicht, dass es serverseitig etwas durchsetzt. Gatet `require_admin` zur Registrierungszeit irgendeinen Backend-Zugriff, oder ist der WebSocket-Command-Handler der einzige Durchsetzungspunkt (aktuelle Annahme)?
- **Config-Write-Back**: gibt es einen unterstützten Weg, in die Registrierungs-`config` zurückzuschreiben, oder ist `panel.config` in der Praxis strikt read-only (`[unsupported]`)? Falls ein Write-Back-Pfad existiert, müsste die Deploy-Zeit-vs-Laufzeit-Trennung überdacht werden.
