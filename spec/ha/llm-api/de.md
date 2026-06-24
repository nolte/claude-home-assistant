# HA-Integration: LLM-API (Tools für Conversation-Agents)

Status: draft

## Kontext

Home Assistant kann mit Large Language Models (LLMs) interagieren. Durch das Bereitstellen einer Home-Assistant-API für ein LLM kann das LLM Daten abrufen oder Home Assistant steuern, um den User besser zu unterstützen. Home Assistant bringt eine eingebaute LLM-API mit, aber Custom Integrations können eine eigene registrieren, um zusätzliche Funktionalität anzubieten.

Die LLM-Hilfs-API hat **zwei Konsumentenseiten**, die eine Integration sauber trennen muss: (a) eine Integration, die **Tools für LLMs anbietet**, indem sie eine `llm.API` über `llm.async_register_api(hass, api)` registriert und eine API-Klasse implementiert, die von `API` erbt und `async_get_api_instance(...) -> APIInstance` mit einer Liste von `Tool`-Objekten liefert; (b) eine LLM-bereitstellende Integration (Conversation-Entity), die eine API **konsumiert** — sie speichert die ausgewählten API-IDs in den Config-Entry-Options unter `CONF_LLM_HASS_API`, zieht die Tools des ausgewählten APIs aus dem `ChatLog` und übergibt sie zusammen mit dem `api_prompt` an das LLM.

Home Assistant bringt die eingebaute **Assist-API** mit, die die Assist-Fähigkeiten den LLMs zugänglich macht. Diese API erlaubt LLMs, über [Intents](../intents-conversation) mit Home Assistant zu interagieren, und kann durch das Registrieren von Intents erweitert werden. Die Assist-API ist äquivalent zu den Fähigkeiten und exposed Entities, die auch dem eingebauten Conversation-Agent zur Verfügung stehen; administrative Tasks sind nicht möglich.

Diese Spec überführt die Doku-Konvention in eine generische Verpflichtung. Conversation-Agents, die LLM-APIs konsumieren, sowie Intents gehören in `ha/intents-conversation`; die Abgrenzung Tools vs. Services gehört in `ha/services`; Translations für API- und Tool-bezogene Strings gehören in `ha/translations`.

## Ziele

- Die zwei Seiten der LLM-Hilfs-API (Tools anbieten vs. konsumieren) explizit trennen, damit eine Integration nicht versehentlich beide Rollen vermischt
- Eigene `llm.API` korrekt registrieren und beim Unload des Config-Entry wieder deregistrieren
- `Tool`-Definitionen mit Name, Beschreibung, voluptuous-Parameterschema und async `async_call` deklarieren, sodass das LLM weiß, wann und wie es das Tool aufruft
- Die eingebaute `assist`-API als Default-Konsum-Pfad nutzen, statt Intent-Funktionalität neu zu erfinden
- Den `LLMContext` als alleinige Quelle des Aufruf-Kontexts behandeln, statt Kontext über Seitenkanäle zu schmuggeln
- Tool-Fehler über `HomeAssistantError` signalisieren statt über In-Band-Error-Codes in der Response

## Nicht-Ziele

- Conversation-Agent-Implementierung, Intent-Handler und Intent-Registrierung — eigene Spec `ha/intents-conversation`
- Abgrenzung und Implementierung von HA-Services (benutzergesteuerte Aktionen) — eigene Spec `ha/services`
- Translations für API-Namen, Tool-Namen und Prompt-Texte — gehört zu `ha/translations`
- Die konkrete LLM-Anbindung (Streaming, Message-Formatierung, Provider-spezifische Tool-Serialisierung) — providerseitig und außerhalb dieser Spec
- Administrative Tasks über die Assist-API — die eingebaute API erlaubt keine administrativen Tasks

## Anforderungen

### Zweck & zwei Seiten (Tools anbieten vs. konsumieren)

- **MUSS [MUST]** explizit entscheiden, welche der zwei Rollen die Integration einnimmt: eine Integration, die **Tools anbietet** (registriert eine `llm.API`), oder eine LLM-bereitstellende Integration, die eine **API konsumiert** (zieht Tools aus dem `ChatLog`)
- **MUSS [MUST]** beim Konsumieren die ausgewählten API-IDs in den Config-Entry-Options unter `CONF_LLM_HASS_API` halten — als String oder Liste; ist keine API ausgewählt, **MUSS NICHT [MUST NOT]** der Key gesetzt sein
- **SOLLTE [SHOULD]** im Options-Flow einen Selector anbieten, der die verfügbaren APIs über `llm.async_get_apis(hass)` zur Auswahl stellt

### Eigene `llm.API` registrieren

- **MUSS [MUST]** für eine eigene API eine Klasse anlegen, die von `API` erbt, und `async_get_api_instance(self, llm_context: LLMContext) -> APIInstance` implementieren, die eine `APIInstance` mit `api`, `api_prompt`, `llm_context` und `tools` zurückgibt
- **MUSS [MUST]** die API über `llm.async_register_api(hass, MyAPI(...))` registrieren, wobei die `llm.API` ein eindeutiges `id` und einen `name` trägt
- **MUSS [MUST]** die API beim Entladen des Config-Entry wieder deregistrieren, wenn sie an einen Config-Entry gebunden ist — den Rückgabewert von `async_register_api` über `entry.async_on_unload(unreg)` registrieren
- **MUSS [MUST]** in der `APIInstance` einen `api_prompt` setzen, der dem LLM erklärt, wie es die Tools nutzen soll — `api_prompt` ist Pflichtfeld

### `Tool`-Definition (`async_call`)

- **MUSS [MUST]** jedes Tool von `llm.Tool` ableiten und ein `name`-Attribut tragen — `name` ist Pflicht
- **MUSS [MUST]** `async_call` als async-Methode implementieren; die Argumente sind `hass`, eine `llm.ToolInput`-Instanz und der `llm_context`
- **MUSS [MUST]** Tool-Fehler als `HomeAssistantError` (oder Subklassen) raisen — die Response-Daten **MUSS NICHT [MUST NOT]** Error-Codes zur Fehlerbehandlung enthalten
- **SOLLTE [SHOULD]** ein `description`-Attribut setzen, das dem LLM hilft zu verstehen, wann und wie das Tool aufgerufen werden soll — optional, aber empfohlen
- **SOLLTE [SHOULD]** die Eingabe-Parameter über ein voluptuous-`parameters`-Schema deklarieren; HA konvertiert und validiert `tool_args` über dieses Schema (Default: `vol.Schema({})`)
- **MUSS [MUST]** als Response-Daten ein JSON-serialisierbares Resultat (`JsonObjectType`) zurückgeben

### Built-in `assist`-API konsumieren

- **SOLLTE [SHOULD]** die eingebaute Assist-API als Default-Konsum-Pfad nutzen, statt Intent-Funktionalität neu zu erfinden — sie exposed Entities und Intents äquivalent zum eingebauten Conversation-Agent
- **KANN [MAY]** die Assist-API durch das Registrieren zusätzlicher Intents erweitern
- **MUSS NICHT [MUST NOT]** administrative Tasks über die Assist-API erwarten oder voraussetzen — die eingebaute API erlaubt keine administrativen Tasks

### `LLMContext`

- **MUSS [MUST]** den `LLMContext` als Eingabe an `async_get_api_instance(...)` und `async_call(...)` durchreichen, statt Aufruf-Kontext über globale Variablen oder Seitenkanäle zu transportieren
- **MUSS [MUST]** beim Konsumieren die LLM-API über `llm.async_get_api(hass, api_id, llm_context)` mit dem aktuellen `llm_context` auflösen
- **SOLLTE [SHOULD]** die in `ToolInput` gelieferten Felder (`tool_name`, `tool_args`, `platform`, `context`, `user_prompt`, `language`, `assistant`, `device_id`) für die Tool-Logik nutzen, statt diese Werte selbst zu rekonstruieren

### Abgrenzung zu Conversation/Intents

- **MUSS NICHT [MUST NOT]** in dieser Spec Conversation-Entity-Logik, Intent-Handler oder Intent-Registrierung definieren — diese gehören in `ha/intents-conversation`
- **MUSS NICHT [MUST NOT]** LLM-Tools mit HA-Services vermischen — Tools werden vom LLM aufgerufen, Services sind benutzergesteuerte Aktionen; die Abgrenzung gehört in `ha/services`
- **SOLLTE [SHOULD]** API-Namen, Tool-Namen und Prompt-Texte, sofern sie übersetzbar sind, über die Translations-Mechanik aus `ha/translations` führen

## Akzeptanzkriterien

- [ ] Die Integration legt explizit eine der zwei Rollen fest (Tools anbieten oder API konsumieren)
- [ ] Beim Konsumieren werden die ausgewählten API-IDs unter `CONF_LLM_HASS_API` in den Options gehalten; ohne Auswahl ist der Key weggelassen
- [ ] Eine eigene API erbt von `API` und implementiert `async_get_api_instance(...) -> APIInstance`
- [ ] Die API wird über `llm.async_register_api(hass, api)` registriert und beim Unload über `entry.async_on_unload(unreg)` deregistriert
- [ ] Jedes `Tool` trägt ein `name`-Attribut und implementiert async `async_call(self, hass, tool_input, llm_context)`
- [ ] Tool-Fehler werden als `HomeAssistantError` geraised; die Response enthält keine Error-Codes
- [ ] `async_call` gibt ein JSON-serialisierbares `JsonObjectType`-Resultat zurück
- [ ] Beim Konsumieren wird die API über `llm.async_get_api(hass, api_id, llm_context)` aufgelöst
- [ ] Conversation/Intent-Logik und Service-Logik werden nicht in dieser Spec definiert, sondern an `ha/intents-conversation` bzw. `ha/services` delegiert

## Offene Fragen

- **`api_prompt`-Granularität**: Die Doku verlangt einen `api_prompt` pro `APIInstance`. Soll die Spec eine Mindeststruktur für diesen Prompt vorschreiben (z. B. „nenne die verfügbaren Tools explizit"), oder bleibt er frei?
- **Tool-Naming-Konvention**: Die Doku nennt `name` als Pflicht, gibt aber kein Naming-Schema vor. Soll die Spec eine Konvention (CamelCase, Verb-Objekt) festlegen, damit Skill-Output deterministisch ist?
- **Mehrfach-API-Auswahl**: Der Selector erlaubt `multiple=True`. Soll die Spec adressieren, wie Tool-Namenskollisionen über mehrere ausgewählte APIs hinweg aufgelöst werden?
- **Streaming/Message-Formatierung**: Die Doku zeigt provider-spezifische `_format_tool`/`_convert_content`-Stubs. Soll die Spec diese providerseitige Anbindung explizit als außerhalb des Scopes markieren oder eine Mindest-Schleifenstruktur empfehlen?
