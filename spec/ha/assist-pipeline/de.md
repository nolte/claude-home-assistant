# HA-Voice: Assist-Pipeline (Konfiguration und Betrieb)

Status: draft

## Kontext

Die **Assist-Pipeline** ist die Home-Assistant-Seite der Sprachsteuerung: die geordnete Kette, die eine gesprochene Äußerung in eine ausgeführte Aktion und eine gesprochene Antwort verwandelt. Sie läuft in vier Stufen — **Wake-Word → Speech-to-Text → Intent → Text-to-Speech** — und wird von der internen Integration `assist_pipeline` bereitgestellt, eingeführt in Home Assistant **2023.5** und Teil von `default_config` `[doc:user]` `[doc:dev]`.

An der Pipeline entscheidet sich, ob Sprachsteuerung gelingt. Ein Sprachsatellit wie die ESP32-S3-BOX liefert Mikrofone, ein Wake-Word-Modell und einen Lautsprecher; alles, was darüber entscheidet, ob ein Befehl *verstanden* wird — welche Spracherkennung läuft, welche Entitäten der Agent anfassen darf, welche Sätze greifen, wie die Antwort gesprochen wird — lebt in Home Assistant. Ein perfekt konfigurierter Satellit vor einer unkonfigurierten Pipeline ist ein stummes Gerät.

Diese Spec ist bewusst die **Betreiber**-Sicht auf diese Maschinerie: wie eine Pipeline komponiert wird, welche Engine-Entscheidungen existieren und was sie kosten, wie Entitäten ihr gegenüber freigegeben werden, wie Satelliten daran gebunden werden und wie eine scheiternde Pipeline debuggt wird. Sie ergänzt drei bestehende entwicklerseitige Specs und überschneidet sich mit keiner:

- [`ha/intents-conversation`](../intents-conversation/de.md) — die Entwickler-API (`IntentHandler`, Slots, `ConversationEntity`). Jene Spec schließt „End-User-Assist-Konfiguration (Entitäten im UI freigeben, Voice-Pipeline-Setup)" ausdrücklich aus — genau die Lücke, die diese hier füllt.
- [`ha/entity-platforms-voice`](../entity-platforms-voice/de.md) — die Entity-Basisklassen, die eine Integration implementiert, um *selbst* STT-, TTS-, Wake-Word- oder Satelliten-Anbieter zu werden.
- [`ha/llm-api`](../llm-api/de.md) — Registrieren und Konsumieren von LLM-Tool-APIs für Conversation-Agents.

Die Geräteseite eines Satelliten — Mikrofone, Codecs, Wake-Word-Komponente, Display-Rückmeldung — gehört zu [`ha/esp32-s3-box`](../esp32-s3-box/de.md) und wird hier referenziert, nicht wiederholt.

### Quellen-Tiers

Jede nicht offensichtliche Aussage trägt ein Evidenz-Tier:

- `[doc:user]` — die offizielle Nutzer-Dokumentation, [`home-assistant/home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (`/voice_control/*`, `/integrations/*`): maßgeblich für Setup-Abläufe, UI-Pfade und Endnutzer-Verhalten.
- `[doc:dev]` — die offizielle Entwickler-Dokumentation, [`home-assistant/developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) (`/docs/voice/*`): maßgeblich für Pipeline-Stufen, Events und den WebSocket-Kontrakt.
- `[policy]` — eine nolte-Portfolio-Regel, kein Upstream-Fakt.

Verifiziert 2026-08.

## Ziele

- Die Pipeline als geordneten, beobachtbaren Kontrakt beschreiben — Stufen, Events und die Parameter, die eine Teilmenge davon auswählen — statt als undurchsichtigen UI-Schalter
- Die Engine-Entscheidungen (Speech-to-Text, Text-to-Speech, Wake-Word, Conversation-Agent) zu expliziten Entscheidungen mit ihren dokumentierten Kosten machen, statt zu Defaults, die niemand mehr angesehen hat
- Festlegen, wo die Wake-Word-Erkennung läuft und was diese Platzierung für Hardwarelast, Sprachabdeckung und Offline-Verhalten bedeutet
- Entity-Freigabe als Sicherheitsgrenze mit festgelegtem Minimum behandeln, nicht als Bequemlichkeitsschalter
- Satelliten über das aktuelle Entity-Modell (`assist_satellite`) an Pipelines binden und die Deprecation benennen, von der ältere Konfigurationen migrieren müssen
- Einer scheiternden Pipeline einen deterministischen Debugging-Pfad geben — welches Werkzeug welche Frage beantwortet — statt Ausprobieren
- Die Datenschutz-Konsequenzen der pipeline-eigenen Diagnose benennen, insbesondere der Audio-Aufzeichnung

## Nicht-Ziele

- Die Entwickler-API für Intents, Conversation-Agents und Voice-Entity-Plattformen — gehört `ha/intents-conversation`, `ha/entity-platforms-voice` und `ha/llm-api`
- Satelliten-Hardware und ihre ESPHome-Bindung — gehört `ha/esp32-s3-box`; diese Spec behandelt einen Satelliten als Pipeline-Client
- Add-on-Installationsmechanik und Home-Assistant-OS-Administration über die Feststellung hinaus, wo eine Supervisor-Anforderung besteht
- Auswahl oder Betrieb eines konkreten LLM-Anbieters (Modellwahl, Prompt-Engineering, Kosten) — die Spec behandelt, *dass* ein Agent gewählt wird und was sich ändert, nicht welcher Anbieter
- Sprachmodell-Training über den Hinweis hinaus, dass eigenes Wake-Word-Training existiert
- Home-Assistant-Cloud-Abonnement und Abrechnungsfragen — Cloud erscheint nur als eine dokumentierte Engine-Option
- Multiroom-Audio, Medien-Routing und Ansage-Planung über die Actions hinaus, die der Satellit exponiert

## Anforderungen

### Aufbau der Pipeline

- Eine Pipeline **MUSS [MUST]** als geordnete Kette aus genau vier Stufen behandelt werden — **Wake-Word**, **Speech-to-Text**, **Intent-Erkennung**, **Text-to-Speech** — in dieser Reihenfolge ausgeführt `[doc:dev]` `[doc:user]`
- Es **MUSS [MUST]** verstanden werden, dass ein Lauf eine **Teilmenge** der Kette abdecken kann: Die Parameter `start_stage` und `end_stage` der WebSocket-API wählen den Bereich, sodass ein reiner Textlauf (`intent` → `intent`) und ein vollständiger Sprachlauf dieselbe Pipeline-Definition teilen `[doc:dev]`
- Die **Events** eines Laufs **SOLLTEN [SHOULD]** als beobachtbarer Kontrakt für Integration und Debugging behandelt werden: `run-start`, `wake_word-start`/`wake_word-end`, `stt-start`, `stt-vad-start`/`stt-vad-end`, `stt-end`, `intent-start`/`intent-progress`/`intent-end`, `tts-start`/`tts-end`, `run-end` sowie `error` mit konkretem Fehlercode `[doc:dev]`
- Es **SOLLTE [SHOULD]** bekannt sein, dass ein Lauf optional `pipeline` (ID), `conversation_id`, `device_id` und Timeout-Parameter annimmt — die `conversation_id` ist das, was eine Folgeäußerung zum Teil derselben Konversation macht `[doc:dev]`
- Es **KANN [MAY]** darauf gebaut werden, dass `assist_pipeline` über `default_config` vorhanden ist; ein `assist_pipeline:` in der `configuration.yaml` ist nur nötig, wo die Default-Konfiguration entfernt wurde `[doc:user]`
- Es **DARF NICHT [MUST NOT]** angenommen werden, dass eine Pipeline gerätespezifisch ist: Pipelines sind benannte Konfigurationen, die viele Satelliten teilen können, und ein Satellit ist genau einer Pipeline zugeordnet `[doc:user]`

### Engine-Auswahl

- **Lokal gegenüber Cloud** **MUSS [MUST]** bewusst entschieden und die Entscheidung festgehalten werden — Home Assistant Cloud liefert Speech-to-Text und Text-to-Speech als Abo-Dienst, während eine vollständig lokale Pipeline aus Add-ons zusammengesetzt wird `[doc:user]`
- Die Speech-to-Text-Engine **MUSS [MUST]** gegen die tatsächliche Kapazität des Hosts gewählt werden: **Speech-to-Phrase** liefert „extremely fast transcription even on a Home Assistant Green or Raspberry Pi 4", erkennt aber einen begrenzten Phrasensatz, während **Whisper** freiere Sprache verarbeitet — mit dokumentierten ~8 Sekunden auf einem Pi 4 gegenüber unter 1 Sekunde auf einem Intel NUC `[doc:user]`
- Als lokale Text-to-Speech-Engine **SOLLTE [SHOULD]** **Piper** verwendet werden; sie ist die dokumentierte lokale Option, „optimized for the Raspberry Pi 4" `[doc:user]`
- Es **MUSS [MUST]** verstanden werden, dass diese Engines über die **Wyoming**-Protokoll-Integration andocken, die externe Speech-to-Text-, Text-to-Speech- und Wake-Word-Dienste anbindet und laufende Instanzen automatisch entdeckt (manuelle Host-/Port-Eingabe bleibt verfügbar) `[doc:user]`
- Die **Supervisor-Anforderung** **MUSS [MUST]** eingeplant werden: Die Engines werden als Home-Assistant-Apps (früher Add-ons) ausgeliefert, was Home Assistant OS oder Supervised voraussetzt — Home Assistant Core kann sie nicht installieren und benötigt stattdessen extern gehostete Wyoming-Dienste `[doc:user]` `[policy]`
- Die Pipeline **SOLLTE [SHOULD]** in der dokumentierten Reihenfolge zusammengesetzt werden — Speech-to-Text- und Text-to-Speech-Dienste installieren und starten, unter *Einstellungen → Geräte & Dienste* einbinden, dann den Assistenten unter *Einstellungen → Sprachassistenten → Assistent hinzufügen* anlegen und Sprache sowie Engines wählen `[doc:user]`
- Es **SOLLTE [SHOULD]** **eine Pipeline je Sprache oder Zweck** angelegt werden, statt eine einzelne Pipeline zu überladen, da Sprache und Engine-Auswahl Einstellungen je Pipeline sind `[doc:user]` `[policy]`

### Platzierung des Wake-Words

- Es **MUSS [MUST]** entschieden werden, **wo** die Wake-Word-Erkennung läuft, weil die beiden Platzierungen unterschiedliche Kosten haben — das ist eine architektonische Entscheidung, keine Vorliebe `[doc:user]`
- Für batterie- oder netzbeschränkte Satelliten **SOLLTE [SHOULD]** die **On-Device**-Erkennung (`microWakeWord`) bevorzugt werden: Nur Audio nach der Erkennung wird gesendet, sie funktioniert ohne Netzwerkverbindung und liefert die vortrainierten Modelle „okay nabu", „hey jarvis" und „alexa" — zum Preis kleinerer Modelle mit weniger Genauigkeitsspielraum `[doc:user]`
- Die **serverseitige** Erkennung (`openWakeWord`) **SOLLTE [SHOULD]** gewählt werden, wenn jedes Audio-streamende Gerät unabhängig von seiner Rechenleistung zum Satelliten werden soll — unter Inkaufnahme dessen, dass Satelliten dann dauerhaft streamen `[doc:user]`
- Serverseitige Erkennung **MUSS [MUST]** gegen den Host budgetiert werden: Die Dokumentation nennt für einen Raspberry Pi 4 etwa **fünf gleichzeitige** Audio-Streams, bevor er überfordert ist `[doc:user]`
- Vor der Wahl serverseitiger Erkennung **MUSS [MUST]** die Sprachabdeckung berücksichtigt werden: openWakeWord unterstützt derzeit **nur Englisch**, wegen begrenzter Multi-Speaker-Modelle in anderen Sprachen; die Alternative **Porcupine (v1)** bietet 29 Wake-Words in Englisch, Französisch, Spanisch und Deutsch `[doc:user]`
- Beim Betrieb des Wake-Words in Home Assistant **MÜSSEN [MUST]** die genannten Voraussetzungen erfüllt sein: Version **2023.10 oder neuer** auf Home Assistant OS plus Cloud oder eine konfigurierte lokale Pipeline; das Wake-Word wird dem Assistenten anschließend über *Add streaming wake word* zugewiesen `[doc:user]`
- Ein eigenes Wake-Word **KANN [MAY]** trainiert werden — das openWakeWord-Tooling synthetisiert Trainingsdaten per Text-to-Speech über Sprecher-, Raumakustik- und Rauschvariationen, sodass keine manuelle Aufnahmekampagne nötig ist `[doc:user]`

### Entity-Freigabe

- Die Freigabe **MUSS [MUST]** als **Sicherheitsgrenze** behandelt werden: Entitäten werden unter *Einstellungen → Sprachassistenten → Freigeben* bewusst zugelassen, ausdrücklich „to avoid that sensitive devices, such as locks and garage doors, can inadvertently be controlled by voice commands" `[doc:user]`
- Es **MUSS [MUST]** die **minimale** Menge freigegeben werden, die ein Assistent wirklich braucht, und diese bei jedem neuen Gerät erneut geprüft werden — eine freigegebene Entität ist für jeden in Hörweite eines Satelliten erreichbar `[doc:user]` `[policy]`
- Schlösser, Garagentore, Alarmanlagen oder andere folgenreiche Aktoren **DÜRFEN NICHT [MUST NOT]** ohne ausdrückliche, festgehaltene Entscheidung für einen Sprachassistenten freigegeben werden `[policy]`
- Entitäten, deren registrierter Name nicht dem entspricht, was ein Mensch laut sagen würde, **SOLLTEN [SHOULD]** **Aliase** erhalten, statt die Entität umzubenennen und bestehende Automationen zu brechen `[doc:user]` `[policy]`
- Die Freigabe je Assistent **SOLLTE [SHOULD]** bewusst bleiben: Das Freigabe-UI wählt, welche Assistenten (Assist, Google Assistant, Alexa) jede Entität erhalten, und das sind unabhängige Entscheidungen `[doc:user]`
- Freigabe-Änderungen **SOLLTEN [SHOULD]** mit dem Satz-Parser statt per Sprache verifiziert werden, damit ein fehlender Treffer von einem falsch verstandenen Wort unterscheidbar bleibt `[doc:user]` `[policy]`

### Conversation-Agent und Sätze

- Es **MUSS [MUST]** bekannt sein, dass der **Default-Agent** von der Community beigetragene Sätze in Dutzenden Sprachen matcht und für gängige Befehle keine Konfiguration braucht — Geräte per Name oder Bereich ein- und auszuschalten funktioniert sofort `[doc:user]`
- Vor dem Schreiben eigener Sätze **SOLLTE [SHOULD]** die eingebaute Abdeckung geprüft werden: Licht (an/aus, Helligkeit, Farbe), Abdeckungen, Szenen und Skripte, Media-Player, Staubsauger, generisches Ein/Aus, Einkaufs- und To-do-Listen sowie Datums-, Zeit- und Zustandsfragen werden von eingebauten Intents behandelt `[doc:user]`
- Die eingebauten **Timer-Intents** **SOLLTEN [SHOULD]** genutzt werden, statt Timer separat zu modellieren — Anlegen („stell einen Timer auf 5 Minuten"), Abbrechen, Zeit hinzufügen oder abziehen, Restzeit abfragen und verzögerte Aktionen („schalte das Licht in 5 Minuten aus") sind abgedeckt `[doc:user]`
- Eine eigene Phrase **SOLLTE [SHOULD]** über den **Satz-Trigger** in einer Automation ergänzt werden (*Einstellungen → Automationen & Szenen → Automation erstellen*, Trigger-Typ *Satz*, Phrasen ohne Satzzeichen), wenn eine Phrase genau eine Automation auslösen soll — das ist der dokumentierte einfachste Weg `[doc:user]`
- Wiederverwendbare eigene Intents **KÖNNEN [MAY]** als YAML unter `custom_sentences/<language>/` im Config-Verzeichnis definiert werden, mit `language:` und einer `intents:`-Zuordnung Intent-Name → `data:` → `sentences:`, behandelt über `intent_script` `[doc:user]`
- Ein **bestehender** Intent **KANN [MAY]** um zusätzliche Satzvarianten erweitert und die gesprochene Antwort eines bestehenden Intents angepasst werden, statt einen neuen Intent anzulegen `[doc:user]`
- Variable Teile **SOLLTEN [SHOULD]** über Wildcards (`{album}`) erfasst und in Antwort oder Aktion per `trigger.slots`-Templating konsumiert werden, statt jede Formulierung aufzuzählen `[doc:user]`
- Der Default-Agent **KANN [MAY]** durch einen eigenen oder LLM-gestützten Conversation-Agent ersetzt werden; die dem Modell exponierte Tool-Fläche unterliegt dann [`ha/llm-api`](../llm-api/de.md), und die obigen Freigaberegeln gelten weiter `[doc:user]` `[policy]`
- Die Pipeline **KANN [MAY]** aus Automationen mit der Action `conversation.process` angesprochen und die Satz-Konfiguration mit `conversation.reload` neu geladen werden `[doc:user]`

### Sprachausgabe

- Text außerhalb eines Pipeline-Laufs **SOLLTE [SHOULD]** mit der Action `tts.speak` gesprochen werden, gerichtet an eine `media_player_entity_id` mit `message` und optional `language`, `cache` und `options` `[doc:user]`
- Das erzeugte Audio **KANN [MAY]** über `options` eingeschränkt werden — `preferred_format` (`wav`, `mp3`, `ogg`), `preferred_sample_rate`, `preferred_sample_channels` und `preferred_sample_bytes` (`2` für 16 Bit) — wenn das Zielgerät wählerisch ist `[doc:user]`
- `cache` **SOLLTE [SHOULD]** für wiederkehrende Phrasen auf dem Default (`True`) bleiben: Home Assistant hält einen langlebigen Dateisystem-Cache plus einen kurzlebigen In-Memory-Cache, der automatisch aufgeräumt wird `[doc:user]`
- In neuen Konfigurationen **SOLLTE [SHOULD]** `tts.speak` den Legacy-Diensten `tts.<platform>_say` vorgezogen werden `[doc:user]` `[policy]`
- Die Pipeline-Antwort eines Satelliten **DARF NICHT [MUST NOT]** zusätzlich über einen manuellen `tts.speak`-Aufruf geleitet werden — die Text-to-Speech-Stufe der Pipeline liefert die Antwort bereits an den Satelliten, und ein zweiter Pfad erzeugt doppelte oder überlappende Audioausgabe `[doc:dev]` `[policy]`

### Satelliten-Bindung

- Ein Sprachsatellit **MUSS [MUST]** über die **`assist_satellite`-Entität** repräsentiert werden, die Building-Block-Integration, eingeführt in Home Assistant **2024.10** `[doc:user]`
- Konfigurationen, die noch die älteren ESPHome-Voice-Binary-Sensoren konsumieren, **MÜSSEN [MUST]** migriert werden: Sie sind seit 2024.10 deprecated, und Home Assistant erzeugt ein Repair-Issue, das auf die entsprechende `assist_satellite`-Entität zeigt `[doc:user]`
- Automatisiert **SOLLTE [SHOULD]** gegen das dokumentierte Zustandsmodell des Satelliten werden — die Trigger *wurde idle*, *begann zuzuhören*, *begann zu verarbeiten* und *begann zu antworten* samt der passenden Bedingungen — statt den Pipeline-Zustand aus Media-Player- oder Mikrofon-Entitäten abzuleiten `[doc:user]`
- Sprache **KANN [MAY]** über die dokumentierten Actions an einen Satelliten gepusht werden: **Ansage**, **Frage stellen** und **Konversation starten** `[doc:user]`
- Jedem Satelliten **MUSS [MUST]** explizit eine Pipeline zugewiesen und die Zuweisung nach dem Hinzufügen des Geräts verifiziert werden, statt anzunehmen, der Standard-Assistent greife `[doc:user]` `[policy]`
- Der geräteseitige Kontrakt eines ESPHome-Satelliten — Mikrofon, Wake-Word, Media-Player, Mute-Steuerung, Bildschirm-Rückmeldung — **SOLLTE [SHOULD]** aus [`ha/esp32-s3-box`](../esp32-s3-box/de.md) bezogen werden `[policy]`

### Audioqualität

- Schlechte Erkennung **SOLLTE [SHOULD]** zuerst als **Audio**-Problem und erst danach als Engine-Problem behandelt werden: Die Erkennungsqualität hängt vom aufgenommenen Signal ab, und Geräte mit nur einem Mikrofon brauchen kompensierende Nachbearbeitung in Home Assistant `[doc:user]`
- Für leise Mikrofone **SOLLTEN [SHOULD]** die dokumentierten Startwerte angewandt werden — `noise_suppression_level: 2`, `auto_gain: 31dBFS`, `volume_multiplier: 2.0` — exakt die Werte, die die ESPHome-Referenzkonfiguration ausliefert `[doc:dev]`
- Der Pipeline **MUSS [MUST]** Audio in der erwarteten Rate zugeführt werden (der dokumentierte Lauf-Input nutzt `sample_rate: 16000`), und die Aufnahmerate des Satelliten ist daran auszurichten `[doc:dev]`
- Die Verstärkung **SOLLTE [SHOULD]** **einmal** in der Kette eingestellt werden — am Audio-ADC des Geräts oder über die Gain-Einstellungen der Pipeline, nicht an beiden — damit ein leiser Sprecher nicht doppelt bis ins Clipping kompensiert wird `[policy]`

### Debugging

- Debuggt **MUSS [MUST]** in dieser Reihenfolge werden — jedes Werkzeug beantwortet eine andere Frage, und eine falsche Reihenfolge kostet die meiste Zeit `[doc:user]` `[policy]`:
  1. **Satz-Parser** (*Entwicklerwerkzeuge*) — trifft die Phrase überhaupt einen Intent? Er meldet den ausgelösten Intent, die anvisierten Entitäten und welche davon getroffen wurden, **ohne** den Befehl auszuführen
  2. **Pipeline-Debug** (*Einstellungen → Sprachassistenten → \<Assistent\> → Debug*) — eine Phrase real ausführen und vergangene Läufe aus dem Dropdown inspizieren
  3. **Debug-Aufzeichnung** — `assist_pipeline: {debug_recording_dir: /share/assist_pipeline}` in der `configuration.yaml` setzen, um pro Befehl eine `.wav` zu erhalten und das Audio selbst zu beurteilen
- Das Symptom **SOLLTE [SHOULD]** vor jeder Änderung einer Stufe zugeordnet werden: gar keine Reaktion deutet auf das Wake-Word, ein falsches Transkript auf Speech-to-Text, „Entschuldigung, das verstehe ich nicht" auf Intent-Matching oder Freigabe und eine stumme Antwort auf Text-to-Speech `[doc:user]` `[policy]`
- Wird ein Gerät nicht gefunden, **SOLLTE [SHOULD]** zuerst die **Freigabe** geprüft werden — der dokumentierte Fehlermodus für unbeantwortete Fragen ist eine nie freigegebene Entität, kein falsch geparster Satz `[doc:user]`
- `debug_recording_dir` **MUSS [MUST]** nach Abschluss einer Untersuchung entfernt werden: Es schreibt jeden gesprochenen Befehl als Audio auf die Platte — das sensibelste Artefakt, das die Pipeline erzeugt `[doc:user]` `[policy]`

### Datenschutz und Betriebsgrenzen

- Je Pipeline **MUSS [MUST]** festgehalten werden, ob Audio das Netzwerk verlässt: Eine Cloud-gestützte Speech-to-Text- oder Text-to-Speech-Stufe sendet Sprache nach außen, während eine Wyoming-basierte lokale Pipeline sie lokal verarbeitet `[doc:user]` `[policy]`
- Dauerhaftes Streaming **MUSS [MUST]** als datenschutzrelevante Konsequenz serverseitiger Wake-Word-Erkennung behandelt werden: Mit `openWakeWord` streamen Satelliten permanent Audio an Home Assistant, während On-Device-Erkennung erst nach dem Wake-Word streamt `[doc:user]` `[policy]`
- Der Host **SOLLTE [SHOULD]** gegen die Zahl streamender Satelliten dimensioniert werden, bevor weitere hinzukommen — mit der dokumentierten Fünf-Stream-Angabe für einen Raspberry Pi 4 als Bezugspunkt `[doc:user]`
- Jeder Satellit **SOLLTE [SHOULD]** ein auffindbares **Mute** bieten, dessen Fehlen als Defekt zu werten ist — die geräteseitige Anforderung lebt in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) `[policy]`
- Die freigegebene Entity-Menge und die Engine-Wahl der Pipeline **MÜSSEN [MUST]** als Teil normaler Wartung unter Beobachtung bleiben, da sich beide mit jedem neuen Gerät und Add-on stillschweigend ausweiten `[policy]`

### Verifikation

- Pipeline-Stufen, Lauf-Events und der WebSocket-Kontrakt **MÜSSEN [MUST]** gegen die Entwickler-Dokumentation verifiziert werden, Setup-Abläufe, UI-Pfade und Engine-Verhalten gegen die Nutzer-Dokumentation, gemäß [`ha/upstream-docs-verification`](../upstream-docs-verification/de.md) `[policy]`
- Versionsabhängige Aussagen **MÜSSEN [MUST]** am genannten Release verankert werden — `assist_pipeline` ab 2023.5, Wake-Word in Home Assistant ab 2023.10, der browserbasierte Satelliten-Installer ab 2023.12, `assist_satellite` ab 2024.10 — weil jede davon eine harte Schranke für ein gegebenes Setup ist `[doc:user]` `[policy]`
- Performance-Aussagen zu Engines (Transkriptionslatenz, gleichzeitige Streams) **SOLLTEN [SHOULD]** neu verifiziert werden, wenn die Host-Hardware von den dokumentierten Referenzgeräten abweicht; die publizierten Zahlen sind Kalibrierungspunkte, keine Zusagen `[doc:user]` `[policy]`
- Community-Forenbeiträge **DÜRFEN NICHT [MUST NOT]** als maßgeblich für Pipeline-Verhalten behandelt werden; sie ergänzen die beiden offiziellen Quellen, ersetzen sie nie `[policy]`

## Akzeptanzkriterien

- [ ] Die vier Stufen der Pipeline und ihre Reihenfolge sind verstanden, und der Stufenbereich eines Laufs ist bewusst gewählt, wo eine Teilmenge genutzt wird
- [ ] Lokal-gegenüber-Cloud ist eine festgehaltene Entscheidung, und die Speech-to-Text-Engine passt zur dokumentierten Kapazität des Hosts
- [ ] Wo lokale Engines genutzt werden, ist die Supervisor-Anforderung erfüllt oder es sind stattdessen extern gehostete Wyoming-Dienste bereitgestellt
- [ ] Die Wake-Word-Platzierung (On-Device gegenüber serverseitig) ist gegen Sprachabdeckung, Offline-Verhalten und Hostlast entschieden, mit angewandter Fünf-Stream-Angabe für streamende Satelliten
- [ ] Die Freigabe ist minimal und geprüft; keine Schloss-, Garagentor- oder Alarm-Entität ist ohne festgehaltene Entscheidung freigegeben; Aliase werden statt Umbenennungen genutzt
- [ ] Eingebaute Intents (inklusive Timer) werden genutzt, bevor eigene Sätze geschrieben werden; eigene Phrasen nutzen den Satz-Trigger oder `custom_sentences/<language>/` mit `intent_script`
- [ ] Jeder Satellit ist an eine explizite Pipeline gebunden, durch eine `assist_satellite`-Entität repräsentiert, und etwaige deprecated Voice-Binary-Sensoren sind migriert
- [ ] Automationen setzen an den dokumentierten Zustands-Triggern des Satelliten an statt an abgeleiteten Entity-Zuständen
- [ ] Die Sprachausgabe nutzt `tts.speak` mit bewusstem `cache` und, wo nötig, `options`; kein manueller TTS-Aufruf dupliziert eine Pipeline-Antwort
- [ ] Die Audio-Abstimmung erfolgt einmal in der Kette, mit den dokumentierten Startwerten für leise Mikrofone und einer zur Pipeline passenden Aufnahmerate
- [ ] Eine scheiternde Pipeline wird mit Satz-Parser, dann Pipeline-Debug, dann Debug-Aufzeichnung diagnostiziert — in dieser Reihenfolge — und das Symptom wird zuerst einer Stufe zugeordnet
- [ ] `debug_recording_dir` ist nach der Untersuchung entfernt und bleibt in einer laufenden Konfiguration nicht aktiviert
- [ ] Für jede Pipeline ist festgehalten, ob Audio das Netzwerk verlässt, und jeder Satellit bietet ein auffindbares Mute
- [ ] Die Versionsschranken (2023.5 / 2023.10 / 2023.12 / 2024.10) sind gegen die laufende Home-Assistant-Version geprüft, bevor eine Fähigkeit zugesagt wird

## Offene Fragen

- **Agent-Fallback**: Gibt es bei konfiguriertem LLM-Conversation-Agent ein Local-First- oder Fallback-Verhalten für Befehle, die die eingebauten Intents ohnehin beherrschen? Erneut geprüft 2026-08 gegen die Seite der `conversation`-Integration und einen repräsentativen LLM-Agenten (`openai_conversation`) — **keine von beiden dokumentiert eine solche Option**, die Frage bleibt also mangels Dokumentation offen, nicht mangels Nachschauens. Empirisch zu klären (beobachten, ob ein eingebauter Intent bei ausgewähltem LLM-Agenten noch feuert), bevor ein LLM-Agent portfolioweit übernommen wird.
- **Speech-to-Phrase gegenüber Whisper**: Reicht der begrenzte Phrasensatz von Speech-to-Phrase für das Befehlsvokabular dieses Portfolios, oder erzwingt freie Diktatnutzung (Einkaufslisten-Einträge, Notizen) Whisper und damit stärkere Host-Hardware?
- **Pipeline je Sprache**: Ist bei zweisprachigem Haushalt eine Pipeline je Sprache plus Zuweisung je Satellit das richtige Modell, oder tragen Satelliten in Gemeinschaftsräumen nur die Mehrheitssprache?
- **Eigenes Wake-Word**: Lohnt ein portfolio-spezifisches Wake-Word (Unterscheidbarkeit, weniger Fehlauslösungen), wo die On-Device-Erkennung auf ihre drei vortrainierten Modelle begrenzt ist — was die Erkennung serverseitig verschieben und das Streaming-Profil ändern würde?
- **Debug-Recording-Regel**: Soll das Portfolio `debug_recording_dir` außerhalb einer zeitlich begrenzten Untersuchung untersagen, und wenn ja, wie wird das durchgesetzt statt nur dokumentiert?
- **Satellitenzahl**: Ab welcher Zahl von Satelliten muss der Host dieses Portfolios neu dimensioniert werden, und sollte diese Schwelle gemessen statt aus der dokumentierten Raspberry-Pi-4-Referenz übernommen werden?
- **Prüfrhythmus der Freigabe**: Soll die Entity-Freigabe planmäßig auditiert werden (und durch welchen Skill), da sie sich beim Onboarding neuer Geräte stillschweigend ausweitet?
