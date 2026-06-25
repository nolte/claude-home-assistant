# HA-Automation: Legacy-Trigger-Helfer vermeiden

Status: draft

## Kontext

Unter der HA-Kategorie **Automation** liegt ein Cluster von Integrationen, die per Domänen-Slug auftreten — `door`, `garage_door`, `gate`, `window`, `humidity`, `illuminance`, `moisture`, `motion`, `occupancy`, `power`, `temperature` — sowie die älteren Automatisierungs-Helfer `flux`, `device_sun_light_trigger` und die Automation-Rolle von `hdmi_cec`. Diese Sammel-Spec ist eine **Abgrenzungs-Spec**: Sie lehrt keine Nutzung, sondern legt verbindlich fest, welche Teile dieses Clusters in neuen Artefakten **vermieden** werden und was stattdessen zu verwenden ist.

Die Verifikation gegen die offizielle Doku korrigiert eine verbreitete Annahme: Die geräteklassen-bezogenen Slugs (`door`, `motion`, `temperature`, …) sind **nicht** mehr die dünnen Pre-`device_automation`-Helfer von früher. Laut den aktuellen Integrations-Karten wurden sie **in Home Assistant 2026.4 eingeführt** und liefern „dedizierte Triggers und Conditions" für Entities einer bestimmten `device_class` — UI-konfigurierbar, ohne YAML-Konfiguration (`door`: „provides automation triggers and conditions for entities that represent doors"; `temperature`: „provides automation triggers and conditions for climate, water heater, and weather entities, as well as sensors with device class temperature", mit den Triggern „Temperature changed" / „Temperature crossed threshold"). Diese moderne Geräteklassen-Schicht ist **kein Vermeidungs-Ziel** — sie ist eine empfohlene Alternative.

Die tatsächlich zu vermeidenden Legacy-Bausteine in diesem Cluster sind die **alten YAML-Automatisierungs-Helfer**: `flux` (ein `switch`-Platform-Helfer mit `platform: flux`, der Lichtfarbtemperatur/Helligkeit nach Tageszeit „ähnlich wie f.lux" rechnet, IoT-Klasse „Calculated"), `device_sun_light_trigger` (ein präsenz-basierter Licht-Helfer: „Fade in the lights when the sun is setting and there are people home … Turn off the lights when all people leave the house", Kategorien Automation/Light/Presence detection) und die Automation-Rolle von `hdmi_cec` (auf der Karte als **„Legacy integration"** markiert). Diese Helfer stammen aus der Zeit vor Blueprints und vor der modernen Geräteklassen-Schicht; ihre Logik ist in `configuration.yaml` verdrahtet, nicht im UI editierbar und nicht als Blueprint teilbar.

Reale Einordnung / Kategorie-Ehrlichkeit: HA listet den gesamten Cluster unter der Kategorie **Automation**. Das ist jedoch keine homogene Einheit — er zerfällt in eine **moderne Geräteklassen-Trigger/Condition-Schicht (2026.4, empfohlen)** und einen **Rest echter Legacy-Automatisierungs-Helfer (zu vermeiden)**. Diese Spec macht die Trennung explizit, damit Autoren nicht versehentlich den Legacy-Pfad wählen.

Verifizierte Quellen: `/integrations/motion/`, `/integrations/door/`, `/integrations/garage_door/`, `/integrations/gate/`, `/integrations/window/`, `/integrations/occupancy/`, `/integrations/humidity/`, `/integrations/illuminance/`, `/integrations/moisture/`, `/integrations/power/`, `/integrations/temperature/`, `/integrations/flux/`, `/integrations/device_sun_light_trigger/`, `/integrations/hdmi_cec/` sowie `/docs/automation/trigger/` für `state`/`numeric_state`/`sun`.

## Wann verwenden

Ziehe `ha-automation/legacy-trigger-helpers` immer dann heran, wenn du im **Automation**-Cluster eine Trigger-/Licht-/Präsenz-Logik bauen willst und entscheiden musst, ob der moderne oder der Legacy-Pfad greift — diese Spec sagt dir verbindlich, was zu meiden ist und welche moderne Alternative stattdessen zu verwenden ist. Typische Entscheidungssituationen:

- **Geräteklassen-Trigger ansetzen** — du willst auf Bewegung, Tür/Fenster oder einen Temperatur-Schwellwert reagieren; diese Spec weist auf die moderne 2026.4-Geräteklassen-Schicht (`door`, `motion`, `temperature`, …) statt eines handgebauten `platform:`-Helfers hin
- **f.lux-artige Lichtsteuerung erwägen** — du denkst an `flux` für Circadian-/Farbtemperatur-Steuerung; diese Spec verweist stattdessen auf eine `sun`-getriggerte Automation mit `light.turn_on` (`color_temp_kelvin`/`brightness`) oder eine Adaptive-Lighting-Lösung
- **Präsenz-Lichtlogik erwägen** — du denkst an `device_sun_light_trigger` für „Licht an, wenn Leute da sind und die Sonne untergeht"; diese Spec verweist auf eine explizite `sun`-getriggerte Automation mit Personen-/`device_tracker`-Bedingung
- **Modern von Legacy unterscheiden** — du siehst eine Integration unter der Kategorie **Automation** und musst die moderne Geräteklassen-Schicht von echtem Legacy (`flux`, `device_sun_light_trigger`, `hdmi_cec`-Automation-Rolle) trennen
- **`hdmi_cec`-Automation prüfen** — du erwägst die Automation-Rolle von `hdmi_cec`; diese Spec markiert sie als „Legacy integration" und verweist auf die `media_player`-Entities/-Dienste der Geräte
- **Fehlende Geräteklassen-Quelle überbrücken** — du willst einen abgeleiteten Wert in einen `input_number`/`input_text` schreiben; diese Spec verweist auf einen `template`-Sensor mit gesetzter `device_class`

Konsultiere diese Spec also, bevor du ein neues Artefakt im Automation-Cluster erstellst — die negativen Verbote und ihre Begründungen stehen in `### Abgrenzung: Wann NICHT verwenden`.

## Ziele

- Eine einzige autoritative „Nicht verwenden — nimm stattdessen X"-Referenz für diesen Cluster bereitstellen
- Die Kategorie-Ehrlichkeit herstellen: trennen, was modern (Geräteklassen-Schicht 2026.4) und was echtes Legacy (alte YAML-Helfer) ist
- Für jeden Legacy-Baustein die moderne Alternative **und** die Begründung (nicht UI-konfigurierbar, intransparent, abgelöst, nicht portabel) benennen
- Verhindern, dass generierte Artefakte versehentlich `flux`, `device_sun_light_trigger` oder die `hdmi_cec`-Automation-Rolle einführen
- Die moderne Geräteklassen-Schicht ausdrücklich als zulässige Alternative absichern, statt sie pauschal mit zu verwerfen

## Nicht-Ziele

- Die detaillierte Nutzung der modernen Geräteklassen-Trigger/Conditions — dafür ist die jeweilige Integration bzw. `ha-automation/automation` zuständig
- Das vollständige Trigger-/Bedingungs-/Aktions-Modell — `ha-automation/automation`
- Geräte-zentrierte Trigger/Conditions/Actions (Backend-Vertrag, `device_automation`-Plattform) — `ha/device-automations`
- Template-Sensoren und `template`-Trigger im Detail — `ha-automation/template`
- Die Namens-Dimension (snake_case-`id`, englischer `alias`, ≤50 Zeichen) — `ha/naming-conventions`, hier nur referenziert
- Migration bestehender produktiver `flux`/`device_sun_light_trigger`-Setups (Bestandspflege bleibt erlaubt) — diese Spec regelt **neue** Artefakte

## Anforderungen

### Was diese Integrationen sind

- **MUSS [MUST]** die Geräteklassen-Slugs (`door`, `garage_door`, `gate`, `window`, `humidity`, `illuminance`, `moisture`, `motion`, `occupancy`, `power`, `temperature`) als **moderne, in 2026.4 eingeführte** Trigger-/Condition-Schicht über einer `device_class` verstehen — sie haben laut Doku **keine Konfigurationsoptionen** und werden automatisch verfügbar, sobald eine andere Integration passende Entities liefert
- **MUSS [MUST]** `flux` als alten `switch`-Platform-Helfer (`platform: flux`, YAML in `configuration.yaml`, IoT-Klasse „Calculated") einordnen, der Lichtfarbtemperatur/Helligkeit nach Tageszeit berechnet
- **MUSS [MUST]** `device_sun_light_trigger` als präsenz-basierten Licht-Helfer einordnen, der Lichter anhand von `device_group`/Personen und Sonnenstand schaltet (Schlüssel u. a. `light_group`, `device_group`, `light_profile`, `disable_turn_off`)
- **MUSS [MUST]** die Automation-Rolle von `hdmi_cec` als auf der Integrations-Karte ausgewiesene **„Legacy integration"** behandeln
- **SOLLTE [SHOULD]** nicht aus dem gemeinsamen Kategorie-Label „Automation" schließen, dass alle Cluster-Mitglieder gleichwertig oder gleich modern sind

### Moderne Alternativen

- **SOLLTE [SHOULD]** für reaktive Logik die moderne **Geräteklassen-Trigger/Condition-Schicht** des Clusters nutzen, wo sie passt (z. B. „Motion detected"/„Motion cleared", „Temperature crossed threshold") — sie ist UI-konfigurierbar und an die `device_class` gebunden statt an eine konkrete Entity-ID
- **MUSS [MUST]** dort, wo die Geräteklassen-Schicht nicht greift, einen dokumentierten Kern-Trigger verwenden: `state` für diskrete Zustände, `numeric_state` (mit `above`/`below`/`for`) für Schwellwerte, `sun` (`event: sunset`/`sunrise`, `offset`) für Sonnenstands-Logik (`ha-automation/automation`)
- **SOLLTE [SHOULD]** wiederverwendbare, parametrisierte Trigger-Logik als **Blueprint** kapseln (`ha/blueprint-patterns`) statt als integriertem YAML-Helfer
- **SOLLTE [SHOULD]** abgeleitete numerische Größen über einen **Template-Sensor** mit gesetzter `device_class` modellieren (`ha-automation/template`), wenn keine native Geräteklassen-Quelle existiert
- **SOLLTE [SHOULD]** für f.lux-artige Lichtsteuerung moderne Mittel verwenden: eine explizite Automation mit `sun`-Trigger, die `light.turn_on` mit `color_temp_kelvin`/`brightness` aufruft, oder eine etablierte Adaptive-Lighting-Lösung — nicht den `flux`-Switch

### Abgrenzung: Wann NICHT verwenden

- **MUSS NICHT [MUST NOT]** in neuem YAML einen alten `platform:`-/`switch`-Helfer von Hand bauen, der nachbildet, was die moderne Geräteklassen-Schicht (`door`, `motion`, `temperature`, …) oder ein `state`/`numeric_state`-Trigger bereits leistet — **weil** ein solcher Helfer nicht UI-konfigurierbar, an eine konkrete Entity verdrahtet und nicht als Blueprint teilbar ist; nutze stattdessen die Geräteklassen-Trigger/Conditions, einen `state`/`numeric_state`-Trigger oder einen `template`-Binary-Sensor mit `device_class`
- **MUSS NICHT [MUST NOT]** `flux` (`platform: flux`) in neuen Setups einführen — **weil** es seine gesamte Circadian-Logik intransparent in `configuration.yaml` verdrahtet, nicht im UI editierbar ist und durch deklarative Mittel abgelöst wurde; nutze stattdessen eine Adaptive-Lighting-Lösung oder eine `sun`-getriggerte Automation, die `light.turn_on` mit `color_temp_kelvin`/`brightness` aufruft (moderne `light`-Farbtemperatur-Steuerung)
- **MUSS NICHT [MUST NOT]** `device_sun_light_trigger` in neuen Setups einführen — **weil** seine Präsenz-und-Sonnen-Licht-Logik fest verdrahtet, nicht parametrisierbar und nicht portabel ist; nutze stattdessen eine **explizite Automation** mit einem `sun`-Trigger (und ggf. einer Personen-/`device_tracker`-Bedingung), die die gewünschten `light`-Aktionen ausführt — sichtbar, editierbar und als Blueprint teilbar
- **SOLLTE NICHT [SHOULD NOT]** die Automation-Rolle von `hdmi_cec` als bevorzugten Automatisierungspfad wählen — **weil** die Integration auf ihrer eigenen Karte als „Legacy integration" markiert ist; bevorzuge, wo möglich, die `media_player`-Entities/-Dienste der Geräte und kapsele Sonderfälle in einer expliziten Automation
- **SOLLTE NICHT [SHOULD NOT]** den gemeinsamen Kategorie-Slug als Empfehlung missdeuten und die alten YAML-Helfer (`flux`, `device_sun_light_trigger`) mit der modernen Geräteklassen-Schicht gleichsetzen — **weil** beide zwar unter „Automation" stehen, aber unterschiedliche Generationen sind; verwende die 2026.4-Geräteklassen-Schicht als modernen Pfad
- **SOLLTE NICHT [SHOULD NOT]** eine Automation einen abgeleiteten Wert in einen `input_number`/`input_text` schreiben lassen, um eine fehlende Geräteklassen-Quelle nachzubauen — **weil** das die Messquelle verliert; definiere stattdessen einen `template`-Sensor mit passender `device_class` (`ha-automation/template`)

## Akzeptanzkriterien

- [ ] Kein generiertes Artefakt führt `flux` (`platform: flux`) ein
- [ ] Kein generiertes Artefakt führt `device_sun_light_trigger` ein; präsenz-/sonnenbasierte Lichtlogik ist als explizite `sun`-getriggerte Automation umgesetzt
- [ ] f.lux-artige Farbtemperatur-Steuerung nutzt `light.turn_on` mit `color_temp_kelvin`/`brightness` oder eine Adaptive-Lighting-Lösung, nicht den `flux`-Switch
- [ ] Die Automation-Rolle von `hdmi_cec` wird nur als bewusst begründeter Legacy-Pfad gewählt, sonst über `media_player`-Mittel ersetzt
- [ ] Reaktive Geräteklassen-Logik nutzt die moderne 2026.4-Trigger/Condition-Schicht oder einen `state`/`numeric_state`/`sun`-Trigger statt eines handgebauten `platform:`-Helfers
- [ ] Abgeleitete Größen ohne native Quelle sind als `template`-Sensor mit `device_class` modelliert, nicht in `input_*` geschrieben
- [ ] Die Spec setzt die moderne Geräteklassen-Schicht nicht fälschlich mit den alten YAML-Helfern gleich (Kategorie-Ehrlichkeit gewahrt)
- [ ] Die Spec wiederholt keine Namens-Mechanik, sondern referenziert `ha/naming-conventions`

## Offene Fragen

- **Adaptive-Lighting-Empfehlung**: Die offiziellen HA-Docs benennen keine konkrete Adaptive-Lighting-Custom-Integration als Nachfolger von `flux`. Soll diese Spec eine konkrete (Drittanbieter-)Lösung empfehlen oder bei der generischen „`sun`-getriggerte Automation + `light.turn_on color_temp_kelvin`"-Formulierung bleiben, die voll doc-verankert ist?
- **Bestands-Migration**: Soll eine Folge-Regel/Spec den Migrationspfad von bestehenden `flux`/`device_sun_light_trigger`-Setups hin zu expliziten Automationen/Blueprints normieren, oder bleibt diese Spec auf das Verbot in **neuen** Artefakten beschränkt?
