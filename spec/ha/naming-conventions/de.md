# HA-Artefakte: Namenskonventionen

Status: draft

## Kontext

Die Skills und Agents dieses Plugins erzeugen Artefakte über vier sehr unterschiedliche Welten hinweg: Custom-Integration-Code (Python), Blueprints und Automationen (YAML), Lovelace-Cards (TypeScript/JavaScript) und das Datei-/Verzeichnis-Layout, in dem all das liegt. Jede dieser Welten hat ihre eigenen, von Home Assistant vorgegebenen Namensmechaniken — eine `unique_id` folgt anderen Regeln als ein Custom-Element-Tag, ein `translation_key` anderen als ein Blueprint-Dateiname. Ohne eine gemeinsame, verbindliche Konvention driften die Skill-Outputs auseinander: mal `snake_case`, mal `camelCase`, mal deutsche, mal englische Anzeigenamen, mal mit Bereichspräfix, mal ohne.

Diese Spec ist die **einzige autoritative Quelle für die Namens­dimension** über alle generierten Artefakte. Sie schreibt fest, welche Schreibweise (Casing), welche Sprache und welche Struktur ein Bezeichner trägt — abhängig von seiner Rolle, nicht von der Laune des jeweiligen Skills. Die zugrunde liegenden *Mechaniken* (wie eine `unique_id` technisch gebildet wird, wie das `EntityDescription`-Pattern funktioniert, wie eine Card registriert wird) bleiben in den jeweiligen Fach-Specs und werden hier **nicht wiederholt**, sondern referenziert: `ha/entity-architecture`, `ha/entity-platform-types`, `ha/device-registry`, `ha/integration-manifest`, `ha/services`, `ha/translations`, `ha/blueprint-patterns`, `ha/lovelace-card-patterns`.

Die zwei Leitentscheidungen dieser Spec: **(1)** Menschenlesbare Anzeigenamen sind durchgängig **englisch**; Lokalisierung erfolgt sauber über `translation_key`/`translations`, niemals über fest verdrahtete fremdsprachige Namen. **(2)** Entity- und Device-Namen folgen der **HA-Konvention** (`_attr_has_entity_name = True` + `translation_key`, von HA zur Laufzeit abgeleitete `entity_id`) — es wird **kein** erzwungenes Präfix-Muster wie `<bereich>_<gerät>_<funktion>` vorgeschrieben.

Quality-Scale-Marker: **Bronze** — eine stabile, nicht-zufällige `unique_id` ist eine Bronze-Pflicht; diese Spec konsolidiert die Namens­regel, die `ha/entity-architecture` als Mechanik trägt.

## Ziele

- Eine geschlossene Casing-Matrix festschreiben: welche Bezeichner-Rolle `snake_case`, `kebab-case` bzw. `PascalCase` trägt
- Englisch als verbindliche Sprache für alle menschenlesbaren Anzeigenamen etablieren und Lokalisierung an `translation_key`/`translations` binden
- Die HA-Konvention für Entity-/Device-Namen (`has_entity_name` + `translation_key`, abgeleitete `entity_id`) als verbindlich erklären und manuelles `entity_id`-Setzen verbieten
- Die Namens­regeln pro Artefaktwelt (Integration-Code, Blueprint/Automation, Lovelace-Card, Datei-Layout) atomar und prüfbar machen
- Identifier-Stabilität sichern: keine volatilen Daten (IP, Hostname, Token, Zeitstempel) in `unique_id`, `identifiers` oder Datei-/Element-Namen
- Klar gegen die Fach-Specs abgrenzen: diese Spec definiert *Namen*, die Fach-Specs definieren *Mechanik*

## Nicht-Ziele

- Mechanik der `unique_id`-Bildung, des `EntityDescription`-Patterns oder der Coordinator-Anbindung — abgedeckt durch `ha/entity-architecture` und `ha/entity-platform-types`
- Aufbau der `DeviceInfo`-/Hub-Hierarchie und `via_device`-Verkettung — abgedeckt durch `ha/device-registry`
- Manifest-Feldsemantik jenseits des `domain`-Namens — abgedeckt durch `ha/integration-manifest`
- Übersetzungs-Workflow und `strings.json`-Struktur — abgedeckt durch `ha/translations`
- Blueprint-Schema, Selektoren und Templating-Brücke — abgedeckt durch `ha/blueprint-patterns`
- Card-Registrierung, Lifecycle-Callbacks und Rendering — abgedeckt durch `ha/lovelace-card-patterns`
- Vorschreiben eines bereichs-/raumbasierten Präfix-Schemas für Entity-IDs (bewusst der HA-Ableitung überlassen)
- Benennung von Artefakten in der privaten HA-Config des Nutzers (`home-assistant-config`) — diese Spec bindet ausschließlich die vom Plugin generierten Artefakte

## Anforderungen

### Übergreifende Regeln

- **MUSS [MUST]** für alle technischen Bezeichner (Domain, `object_id`, `translation_key`, Service-Name, Input-Key, Automation-`id`, Blueprint-Dateiname) `snake_case` aus `[a-z0-9_]` verwenden, ohne führende Ziffer
- **MUSS [MUST]** für Web-Custom-Element-Tags und Card-Quelldateinamen `kebab-case` aus `[a-z0-9-]` verwenden
- **MUSS [MUST]** für TypeScript-/JavaScript-Klassennamen `PascalCase` verwenden
- **MUSS [MUST]** alle menschenlesbaren Anzeigenamen (friendly name, `blueprint.name`, Automation-`alias`, Card-`name`/Label) auf **Englisch** verfassen
- **MUSS [MUST]** menschenlesbare Anzeigenamen auf höchstens **50 Zeichen** begrenzen, damit UI-Listen und Picker schlank bleiben
- **MUSS [MUST]** jeden Bezeichner auf ASCII beschränken — keine Umlaute, Akzente oder Nicht-ASCII-Zeichen in Bezeichnern
- **MUSS NICHT [MUST NOT]** volatile oder umgebungsabhängige Daten (IP-Adresse, Hostname, Port, Token, Seriennummer-Rohwert ohne Stabilitätsgarantie, Zeitstempel) in `unique_id`, Device-`identifiers`, Datei- oder Element-Namen einbetten
- **MUSS NICHT [MUST NOT]** personenbezogene Daten oder Geheimnisse (Benutzername, E-Mail, API-Key) in irgendeinen Bezeichner oder Anzeigenamen aufnehmen
- **SOLLTE [SHOULD]** Anzeigenamen knapp und gerätebezogen halten und Lokalisierung dem `translation_key`-Pfad überlassen, statt mehrsprachige Namen hart zu kodieren

### Custom-Integration-Code

- **MUSS [MUST]** die Integration-`domain` als `snake_case` führen, global eindeutig, identisch zum Ordnernamen `custom_components/<domain>/` und zum `domain`-Schlüssel im `manifest.json` (Mechanik: `ha/integration-manifest`)
- **MUSS [MUST]** jede Entity über `_attr_has_entity_name = True` plus `translation_key` benennen und die `entity_id` von HA ableiten lassen (Mechanik: `ha/entity-architecture`)
- **MUSS NICHT [MUST NOT]** `self.entity_id` manuell setzen oder einen festen Anzeigenamen hart kodieren, wo ein `translation_key` greift — das umgeht die HA-Slug-Logik und friert eine sprach-/installationsabhängige ID ein
- **MUSS [MUST]** den `translation_key` als `snake_case` führen, passend zu einem Schlüssel unter `entity.<platform>.<translation_key>.name` in den Übersetzungen (Mechanik: `ha/translations`)
- **MUSS [MUST]** die `unique_id` stabil und kollisionsfrei innerhalb der Integration bilden und sie niemals mit der `entity_id` gleichsetzen (Mechanik: `ha/entity-architecture`)
- **MUSS [MUST]** Device-`identifiers` als `{(DOMAIN, <stabiler_string>)}` bilden und bei Multi-Instance-Fähigkeit mit `entry.entry_id` präfigieren (Mechanik: `ha/device-registry`)
- **SOLLTE [SHOULD]** den Device-Anzeigenamen (`DeviceInfo.name`) englisch und gerätebezogen wählen oder weglassen, wenn Hersteller/Modell den Namen sinnvoller tragen
- **SOLLTE [SHOULD]** den Config-Entry-Titel englisch und instanz-identifizierend wählen (z. B. Account-Name oder Standort), nicht den Domain-Namen wiederholen
- **MUSS [MUST]** Service-Namen als `snake_case` registrieren, unterhalb der Integration-`domain`, mit passendem Schlüssel in `services.yaml`/Übersetzungen (Mechanik: `ha/services`)
- **SOLLTE [SHOULD]** Plattform-, Coordinator- und Entity-Description-Bezeichner im Code (`snake_case`-Variablen, `PascalCase`-Klassen) sprechend nach ihrer Rolle benennen (z. B. `<Domain>DataUpdateCoordinator`, `<Platform>EntityDescription`)

### Blueprints und Automationen

- **MUSS [MUST]** den Blueprint-Dateinamen als `snake_case` mit `.yaml`-Endung führen, sprechend für den Zweck (z. B. `motion_light.yaml`), abgelegt unter `blueprints/<domain>/<author>/<file>.yaml` (Mechanik: `ha/blueprint-patterns`)
- **MUSS [MUST]** `blueprint.name` als knappen, englischen, menschenlesbaren Titel führen
- **MUSS [MUST]** jeden Input-Schlüssel (die per `!input <key>` referenzierte Bezeichnung) als `snake_case` führen und das menschenlesbare `name:`-Label des Inputs englisch verfassen
- **MUSS NICHT [MUST NOT]** denselben Input-Schlüssel doppelt vergeben oder einen Schlüssel verwenden, der mit der HA-`!input`-Tag-Syntax kollidiert
- **MUSS [MUST]** die `id` einer generierten Automation/eines Scripts als stabilen `snake_case`-Slug führen (nicht den volatilen UI-Zeitstempel nachbilden) und den `alias` englisch und menschenlesbar
- **SOLLTE [SHOULD]** den `alias` so wählen, dass er die Automation in der UI-Liste eindeutig identifiziert, ohne interne Bezeichner oder Entity-IDs im Klartext zu führen

### Lovelace-Cards

- **MUSS [MUST]** das Custom-Element-Tag als `kebab-case` führen und — gemäß Web-Components-Pflicht — **mindestens einen Bindestrich** enthalten (z. B. `<domain>-card`)
- **SOLLTE [SHOULD]** das Element-Tag mit der Integration-`domain` namespacen (z. B. `<domain>-card`), um Kollisionen mit anderen Cards zu vermeiden; ein zusätzliches portfolio-weites Vendor-Präfix ist nicht erforderlich
- **MUSS [MUST]** den Card-Typ in der Lovelace-Konfiguration als `custom:<tag>` referenzieren, wobei `<tag>` exakt dem registrierten Element-Tag entspricht
- **MUSS [MUST]** das zugehörige Editor-Element-Tag als `<tag>-editor` führen (Mechanik: `ha/lovelace-card-editor`)
- **MUSS [MUST]** den Card-Klassennamen als `PascalCase` führen, endend auf `Card` bzw. `CardEditor` (z. B. `FooCard`, `FooCardEditor`)
- **MUSS [MUST]** den Card-`name` (Picker-Label) und die `description` englisch und menschenlesbar verfassen
- **SOLLTE [SHOULD]** die Card-Quelldatei `kebab-case` und passend zum Element-Tag benennen (z. B. `foo-card.ts`)

### Datei- und Verzeichnis-Layout

- **MUSS [MUST]** Integration-Code unter `custom_components/<domain>/` ablegen, wobei `<domain>` exakt der Integration-`domain` entspricht
- **MUSS [MUST]** Card-Assets, die mit der Integration ausgeliefert werden, unter `custom_components/<domain>/www/` ablegen (Mechanik: `ha/lovelace-card-patterns`)
- **MUSS [MUST]** Blueprints unter `blueprints/<domain>/<author>/<file>.yaml` ablegen, wobei `<domain>` genau einer aus `automation`, `script`, `template` ist (Mechanik: `ha/blueprint-patterns`)
- **MUSS [MUST]** Python-Modul- und -Paketnamen als `snake_case` führen (HA-/PEP-8-Konvention)
- **SOLLTE [SHOULD]** Datei- und Ordnernamen sprechend nach ihrer Rolle wählen und nicht nach Bereich/Raum/Instanz, damit dasselbe Artefakt installations­übergreifend wiederverwendbar bleibt

## Akzeptanzkriterien

- [ ] Jeder vom Plugin generierte technische Bezeichner ist `snake_case` (Code/YAML) bzw. `kebab-case` (Web-Element/Card-Datei) bzw. `PascalCase` (TS-Klasse) gemäß Casing-Matrix
- [ ] Kein menschenlesbarer Anzeigename in einem generierten Artefakt ist fremdsprachig; alle sind englisch
- [ ] Kein Anzeigename in einem generierten Artefakt überschreitet 50 Zeichen
- [ ] Keine generierte Entity setzt `self.entity_id` manuell; jede benennt sich über `has_entity_name` + `translation_key`
- [ ] Keine `unique_id`, kein Device-`identifiers`-Eintrag und kein Datei-/Element-Name enthält IP, Hostname, Token, Zeitstempel oder personenbezogene Daten
- [ ] Die Integration-`domain` ist identisch in Ordnername, `manifest.json` und allen Service-/Entity-Registrierungen
- [ ] Jedes Custom-Element-Tag enthält mindestens einen Bindestrich; der Card-Typ wird als `custom:<tag>` referenziert; das Editor-Tag ist `<tag>-editor`
- [ ] Jeder Blueprint liegt unter `blueprints/<domain>/<author>/<file>.yaml` mit `snake_case`-Dateinamen; jeder Input-Schlüssel ist `snake_case`
- [ ] Die Spec wiederholt keine Mechanik, sondern referenziert für jede Regel die zuständige Fach-Spec

## Offene Fragen

Die ursprünglichen drei Fragen sind entschieden und in die Anforderungen eingearbeitet:

- Custom-Element-Tags nutzen die Integration-`domain` als Namespace; ein portfolio-weites Vendor-Präfix ist nicht erforderlich.
- Anzeigenamen sind auf höchstens 50 Zeichen begrenzt.
- Der Blueprint-`author`-Ordner bleibt pro Projekt frei konfigurierbar.

Aktuell keine offenen Fragen.
