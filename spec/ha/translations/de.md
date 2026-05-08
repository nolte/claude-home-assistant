# HA-Integration: Translations

Status: draft

## Kontext

Eine Custom Integration übersetzt zwei Klassen von Strings: **Config-Flow-Strings** (Step-Titel, Feld-Labels, Fehlermeldungen, Abort-Gründe) und **Entity-/Service-Strings** (Anzeige­namen, State-Übersetzungen, Service-Beschreibungen). HA gibt das Format vor: eine `strings.json` als kanonische Quelle (per Konvention Englisch) und `translations/<lang>.json`-Dateien pro ausgelieferter Sprache. Die Übersetzungs-Keys sind hierarchisch, sodass HA gezielte Lookups (`entity.sensor.<key>.name`, `config.error.<key>`, `services.<name>.fields.<field>.name`) auflösen kann.

`nolte/kamerplanter-ha` validiert dieses Schema mit Englisch (`strings.json` + `translations/en.json`) und Deutsch (`translations/de.json`) und kodifiziert in `spec/style-guides/HA-INTEGRATION.md` zwei nicht-offensichtliche Regeln: (1) **Englisch als HA-System-Sprache** ist Pflicht für stabile `entity_id`-Slugs — der Slug wird aus dem System-Sprach-Display-Namen gebildet, also einmal beim Erstregistrieren festgeschrieben; ein deutscher System-Sprach-Slug bricht bei späterem Sprachwechsel; (2) `state:`-Maps unter `entity.<platform>.<translation_key>.state.<value>` übersetzen Enum-State-Werte (z. B. Phase-Stadien) statt sie als Roh-Strings in der UI zu rendern.

Diese Spec überführt die Konvention in eine generische Verpflichtung. Icons (`icons.json`) leben in der parallelen Spec `ha/icons`.

Quality-Scale-Marker: **Bronze** (`strings.json` mit englischer Quelle ist Bronze-Pflicht; multi-language `translations/<lang>.json` pro ausgelieferter Sprache erweitert die Bronze-Konformität, ohne formal Silver zu sein).

## Ziele

- Englisch als kanonische Quelle in `strings.json` festschreiben — HA-System-Sprache `en` ist die Voraussetzung für stabile, sprach­unabhängige `entity_id`-Slugs
- Hierarchische Übersetzungs-Keys nach HA-Konvention erzwingen, damit Skills generierbar gegen das Schema arbeiten
- Sync zwischen `strings.json` und allen `translations/<lang>.json`-Dateien zur Pflicht machen — strukturelle Drift (fehlender Key in einer Sprache, andere Reihenfolge) wird via Drift-Check erkannt
- `state:`-Maps für Enum-Sensoren als Default-Pattern etablieren, statt rohe Backend-Strings ans Frontend durchzureichen

## Nicht-Ziele

- Translation-Engine selbst (HA übersetzt zur Laufzeit; das Plugin liefert nur die Strings) — nicht in dieser Spec
- Übersetzungs-Workflow / Tooling (z. B. crowdin, Lokalise) — Werkzeug-Frage; Skills generieren Roh-JSON-Dateien
- Icons — eigene Spec `ha/icons`
- Service-Translation-Pflicht-Tiefe (alle Felder vs. nur top-level) — gehört zu `ha/services`; diese Spec definiert nur das Format
- Sprach-Auswahl-Mechanismus für End-User — der lebt in der HA-Frontend-UI und nicht im Plugin

## Anforderungen

### `strings.json` als kanonische Quelle

- **MUSS [MUST]** im `custom_components/<domain>/`-Ordner eine `strings.json` enthalten — sie ist die englische Quelle der Wahrheit für alle Übersetzungs-Keys
- **MUSS [MUST]** englische Strings als Werte führen — HA verlangt das implizit, weil es `strings.json` als Fallback nutzt, wenn eine `translations/<lang>.json` fehlt oder einen Key nicht enthält
- **MUSS NICHT [MUST NOT]** lokalisierte Strings (Deutsch, Französisch, …) direkt in `strings.json` ablegen — diese gehören in `translations/<lang>.json`

### `translations/<lang>.json`-Dateien

- **MUSS [MUST]** für jede ausgelieferte Sprache (typisch mindestens `en` und `de` im nolte-Portfolio) eine `translations/<lang>.json` enthalten, die die Schlüssel von `strings.json` 1:1 mit übersetzten Werten spiegelt
- **MUSS [MUST]** alle Keys aus `strings.json` in jeder `translations/<lang>.json` enthalten — fehlende Keys führen zu Mixed-Language-UI (englischer Fallback einzelner Strings inmitten deutscher UI)
- **SOLLTE [SHOULD]** `translations/en.json` zusätzlich zu `strings.json` ausliefern, auch wenn die Werte identisch sind — manche HA-Versionen lesen explizit aus `translations/en.json` statt aus `strings.json` zurückzufallen
- **MUSS NICHT [MUST NOT]** eine `translations/<lang>.json` mit nur einer Teilmenge der Keys ausliefern — das Schema ist all-or-nothing pro Sprache

### Schema der Übersetzungs-Keys

Der Schlüssel-Baum ist durch HA vorgegeben. Skill-Output muss diese Top-Level-Sektionen unterstützen:

- **`config`** — Config-Flow-Strings:
  - `config.flow_title` — der Titel, der im Config-Flow oben steht (typisch `<Integration> ({url})` oder ähnlich)
  - `config.step.<step_id>.title` — der Titel pro Step (`user`, `reauth_confirm`, `reconfigure`, `tenant`, …)
  - `config.step.<step_id>.description` — die optionale erläuternde Beschreibung
  - `config.step.<step_id>.data.<field>` — Feld-Label pro Form-Feld
  - `config.error.<key>` — Fehler-Strings, die der Flow im `errors`-Dict raised (`cannot_connect`, `invalid_auth`, …)
  - `config.abort.<key>` — Abort-Gründe (`already_configured`, `reauth_successful`, …)
- **`options`** — Options-Flow-Strings (parallel zu `config.step.*` aber unter `options.step.<step_id>`)
- **`entity`** — Entity-Anzeigenamen, gegliedert pro Plattform:
  - `entity.<platform>.<translation_key>.name` — der Anzeigename, der hinter `_attr_translation_key` aufgelöst wird
  - `entity.<platform>.<translation_key>.state.<value>` — Übersetzung von Enum-States (siehe nächster Abschnitt)
- **`services`** — Service-Strings:
  - `services.<service>.name` — der Service-Anzeigename
  - `services.<service>.description` — die Service-Beschreibung
  - `services.<service>.fields.<field>.name` — der Feld-Anzeigename pro Service-Feld
  - `services.<service>.fields.<field>.description` — die Feld-Beschreibung

- **MUSS [MUST]** jeden Key in `strings.json` über genau diesen hierarchischen Pfad führen — flache Keys oder umstrukturierte Hierarchien werden von HA nicht aufgelöst
- **MUSS [MUST]** Keys lowercase und mit Unterstrichen (`snake_case`) führen — HA-Konvention; gemischte Schreibweisen sind nicht erlaubt
- **MUSS NICHT [MUST NOT]** Format-Strings mit `{var}`-Platzhaltern in HTML, sondern in plain text führen — HA rendert die Übersetzungen als Text, kein Markup

### Enum-State-Übersetzung

- **SOLLTE [SHOULD]** für Sensoren mit Enum-State (Status-Werte aus einer festen Menge — z. B. Phase-Stadien, Modi, Gerätezustände) eine `state:`-Map unter `entity.<platform>.<translation_key>.state.<value>` führen, sodass die UI die übersetzten Labels statt der Roh-Backend-Strings rendert
- **MUSS [MUST]** alle möglichen `state.<value>`-Werte abdecken, die der Sensor zurückgeben kann — fehlende Werte rendert HA als Roh-String
- **MUSS [MUST]** beim Hinzufügen eines neuen Backend-Werts `state.<value>` in `strings.json` und allen `translations/<lang>.json` nachziehen — sonst stille Lücken in der UI
- **KANN [MAY]** für Sensoren mit `device_class` (z. B. `device_class: enum` mit deklarierten `options:`) den `state:`-Block weglassen, wenn HAs Default-Übersetzungen ausreichen — meistens reichen sie nicht

### Sprach-Konvention

- **MUSS [MUST]** sicherstellen, dass `strings.json` in Englisch geschrieben ist — der HA-System-Sprach-Default ist `en`, und der `entity_id`-Slug wird aus dem System-Sprach-Display-Namen bei Erstregistrierung gebildet
- **MUSS NICHT [MUST NOT]** `entity_id`-Stabilität von der HA-System-Sprache der Konsumenten-Installation abhängig machen — eine deutsche System-Sprache produziert deutsche Slugs (`sensor.tomate_1_tage_bis_giessen`), die bei Sprachwechsel oder Re-Registry instabil werden
- **SOLLTE [SHOULD]** in der Konsumenten-Doku (z. B. README) dokumentieren, dass HA mit `language: en` betrieben werden sollte, falls der User auf Deutsch oder einer anderen Sprache laufen will — die End-User-UI bleibt deutsch (über die persönliche Profil-Sprache); nur der `entity_id`-Slug bleibt englisch

### Sync-Strategie

- **MUSS [MUST]** bei jeder Änderung an `strings.json` (neuer Key, geänderter englischer Wert, gelöschter Key) jede `translations/<lang>.json` synchron nachziehen — strukturelle Drift ist ein Fehlerzustand
- **SOLLTE [SHOULD]** ein Drift-Check-Mechanismus existieren (z. B. CI-Job, der die Key-Bäume vergleicht) — ein konkreter Mechanismus ist Skill-Job, nicht Spec-Job
- **MUSS NICHT [MUST NOT]** `translations/<lang>.json`-Werte autogenerieren ohne Review — maschinelle Übersetzung erzeugt wörtliche Falschübertragungen; jede Änderung sollte review-fähig sein

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/strings.json` existiert und enthält englische Strings
- [ ] `custom_components/<domain>/translations/en.json` existiert (auch wenn die Werte identisch zu `strings.json` sind)
- [ ] Für jede zusätzlich ausgelieferte Sprache existiert `custom_components/<domain>/translations/<lang>.json`
- [ ] Jede `translations/<lang>.json` spiegelt die Key-Struktur von `strings.json` 1:1
- [ ] Top-Level-Sektionen sind auf `config`, `options`, `entity`, `services` beschränkt (plus optional `selector`, falls Skill-Sets sie ergänzen)
- [ ] Alle Keys sind `snake_case`, lowercase
- [ ] Sensoren mit Enum-State haben einen `state:`-Block, der alle möglichen Backend-Werte abdeckt
- [ ] Eine `grep`-Suche nach `_attr_name = "<hard-coded-string>"` in den Plattform-Modulen liefert keine Treffer (siehe `ha/entity-architecture`)
- [ ] Quality-Scale-Marker: **Bronze**

## Offene Fragen

- **Drift-Check-Mechanismus**: Welcher konkrete CI-Job oder Skill prüft die Key-Parität zwischen `strings.json` und allen `translations/<lang>.json`? Aktuell als „existieren sollte" formuliert.
- **Sprach-Liste-Pflicht**: Welche Sprachen liefert das Plugin standardmäßig? `en` ist Pflicht; `de` ist im nolte-Portfolio Standard. Soll die Spec eine zusätzliche Sprach-Liste vorschreiben (Französisch, Spanisch, …) oder bleibt das pro Integration offen?
- **`selector`-Übersetzungen**: HA hat zusätzliche Selector-Übersetzungs-Keys (`selector.<key>.options.<value>`) für `select:`-Selectors mit Wert-Listen. Soll die Spec diese Sektion explizit als Pflicht­bereich aufnehmen oder bleibt sie als KANN, weil sie nur bei spezifischen Selector-Typen anfällt?
- **Roh-Englische-Backend-Werte**: Wenn das Backend bereits englische Strings liefert (z. B. `"germination"`), sollen sie wörtlich in den `state:`-Block übernommen werden, oder soll die Integration sie zusätzlich kapitalisieren / formatieren?
- **HA-System-Sprach-Lockdown**: Sollte die Skill-Output-README explizit verlangen, dass `configuration.yaml: language: en` gesetzt ist? Aktuell als SOLLTE in der Konsumenten-Doku formuliert; ein „MUSS" wäre denkbar, aber das greift in die User-Konfiguration ein.
