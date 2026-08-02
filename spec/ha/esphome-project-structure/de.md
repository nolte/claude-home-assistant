# ESPHome-Projektstruktur (Repository-Layout und Wiederverwendung)

Status: draft

## Kontext

Eine ESPHome-Flotte ist nicht eine Config — es sind Dutzende. Das Portfolio-Fixture [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs) trägt derzeit rund zwei Dutzend Device-Dateien: sieben Kameras, sieben Smart-Plugs eines Modells, mehrere Grow-Boxen, zwei ESP32-S3-BOX-3-Geräte. In dieser Größenordnung ist nicht mehr interessant, „was in einer Device-Datei steht", sondern **was fünfundzwanzig Device-Dateien teilen und wie**.

Diese Spec beantwortet die zweite Frage. Sie ist das Repository-seitige Gegenstück zu [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md), die eine einzelne Device-YAML regelt — deren Pflichtblöcke, Secret-Handling und Naming. Hier ist der Gegenstand der Baum, in dem diese Dateien leben: welche Verzeichnisse existieren, wie gemeinsame Konfiguration in Packages zerlegt wird, wie ein Gerät parametrisiert, was es wiederverwendet, und wie ein neues Gerät ohne jedes Kopieren aufgenommen wird.

Der tragende Mechanismus ist ESPHomes **`packages:`**-Feature. Es merged nicht-destruktiv — „dictionaries are merged key-by-key, lists of components are merged by component ID (if specified), other lists are merged by concatenation" — und unterstützt parametrisierte Includes, Defaults, Remote-Quellen sowie chirurgische `!extend`-/`!remove`-Overrides `[doc]`. Fast jede Wiederverwendungs-Entscheidung dieser Spec ist eine Entscheidung darüber, wie man dieses eine Feature gut nutzt.

Upstream existieren zwei Strukturmodelle, und diese Spec bezieht dazwischen Position: ESPHomes eigenes [`wake-word-voice-assistants`](https://github.com/esphome/wake-word-voice-assistants) gibt **jedem Gerät ein eigenes Verzeichnis** (`esp32-s3-box-3/`, `m5stack-atom-echo/`) mit geteilten Assets daneben, während das Portfolio-Fixture **flache Device-Dateien** über einem geteilten `common/`-Package-Verzeichnis hält. Das Modell des Fixtures skaliert besser für eine Flotte ähnlicher Geräte; das Upstream-Modell passt zu einer Handvoll unverwandter Referenz-Builds.

### Quellen-Tiers

- `[doc]` — die offizielle ESPHome-Dokumentation unter <https://esphome.io>: maßgeblich für `packages:`, Substitutions- und Merge-Semantik.
- `[fixture]` — das reale Repository des Portfolios [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs), inspiziert 2026-08: maßgeblich dafür, was dieses Portfolio heute tatsächlich tut, **nicht** automatisch dafür, was es tun sollte.
- `[upstream]` — ESPHomes eigene Multi-Device-Repositories (`esphome/firmware`, `esphome/wake-word-voice-assistants`): Vergleichspunkt, kein Auftrag.
- `[src]` — ESPHomes eigener Quellcode, wo Verhalten real, aber undokumentiert ist. Ein nur `[src]`-belegter Fakt trägt keine Kompatibilitätszusage und kann sich ohne Release-Notiz ändern. (Korpusweit als `[src]` geschrieben; diese Spec schrieb zuvor `[src]`.)
- `[policy]` — eine nolte-Portfolio-Regel, kein Upstream-Fakt.

Verifiziert 2026-08.

## Ziele

- Ein Repository-Layout für eine ESPHome-Flotte festlegen, sodass ein Leser jedes Gerät, jeden geteilten Block und jeden C++-Helfer ohne Suchen findet
- `packages:` zum einzigen Wiederverwendungs-Mechanismus machen und konkret sagen, wie Packages geschnitten, benannt, parametrisiert und komponiert werden
- Den Parameter-Kontrakt zwischen Device-Datei und den konsumierten Packages definieren, sodass eine Device-Datei eine kurze, deklarative Aussage über Identität plus Abweichungen bleibt
- Chirurgischen Overrides (`!extend`, `!remove`) einen Platz geben, damit ein abweichendes Gerät kein Package forkt
- Eine Credential-Strategie festlegen, die geteilte und Remote-Packages überlebt, wo `!secret` nachweislich nicht funktioniert
- Das Aufnehmen eines neuen und das Stilllegen eines alten Geräts zu mechanischen Schritten machen statt zu Copy-Paste-Archäologie
- Ehrlich festhalten, wo Fixture und bestehende Spec derzeit auseinanderlaufen, statt es zu übertünchen

## Nicht-Ziele

- Der Inhalt einer einzelnen Device-YAML — Pflicht-Kernblöcke, geräteweise Plattform-Konfiguration und die Naming-Regel auf Geräteebene gehören zu [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md)
- Gerätespezifisches Hardwarewissen — das lebt in Geräte-Specs wie [`ha/esp32-s3-box`](../esp32-s3-box/de.md)
- ESPHome-Custom-Components in C++/Python (`external_components`-Authoring) — eine zu konsumieren ist in Scope, eine zu schreiben ist eine eigene Achse
- Die Compile-/Flash-Toolchain selbst und OTA-Rollout-Orchestrierung über eine Flotte
- Home-Assistant-seitige Belange (Entity-Freigabe, Dashboards, Assist-Pipeline)
- Repository-Scaffolding, das nicht ESPHome-spezifisch ist — Taskfile, pre-commit, Renovate, Release-Automation und Docs sind portfolioweit durch die vererbten `project/`-Specs geregelt

## Anforderungen

### Repository-Layout

- Jede Geräte-Konfiguration **MUSS [MUST]** unter einem Config-Root liegen (Fixture: `src/`), mit **einer Datei je Gerät, benannt nach dem Gerät** (`<device-name>.yaml`, kebab-case) `[fixture]` `[policy]`
- Wiederverwendbares YAML **MUSS [MUST]** in einem `common/`-Verzeichnis innerhalb dieses Roots liegen, und Device-Dateien **DÜRFEN NICHT [MUST NOT]** dorthin — die Unterscheidung „wird das auf ein Gerät geflasht oder von einem eingebunden" ist das, was den Baum lesbar macht `[fixture]` `[policy]`
- Device-Dateien **SOLLTEN [SHOULD]** **flach** im Config-Root liegen, statt jedem Gerät ein eigenes Verzeichnis zu geben: Die Flotte besteht aus vielen ähnlichen Geräten, und ein Verzeichnis je Gerät vergräbt die eine Datei, auf die es ankommt. (ESPHomes eigene Referenz-Repos nutzen ein Verzeichnis je Gerät, was zu einer Handvoll unverwandter Builds passt, nicht zu einer Flotte) `[fixture]` `[upstream]` `[policy]`
- `common/` **SOLLTE [SHOULD]** **nach Konsument gruppiert werden, nicht nach Anzahl**: Packages, die ein Gerät direkt einbindet — die Basis, Board-Packages, Feature-Packages — bleiben flach, während Bausteine, die nur andere Packages einbinden, in ein ESPHome-Domänen-Unterverzeichnis wandern (`common/sensor/`, `common/binary_sensor/`, `common/text_sensor/`, wie das Fixture sie bereits führt). Die flache Ebene ist dann genau die Menge der Einstiegspunkte `[fixture]` `[policy]`
- Geräteeigene Assets (Bilder, Sounds) **SOLLTEN [SHOULD]** in einem eigenen, nach Gerät oder Gerätetyp geschlüsselten Baum liegen (`images/<device-type>/`), neben `common/` und `include/`, statt einem Gerät ein eigenes Verzeichnis zu geben — ESPHomes Referenz-Repo tut dasselbe mit `casita/` und `sounds/` neben seinen Geräteordnern `[upstream]` `[policy]`
- C++-Helfer-Header, die von Lambdas konsumiert werden, **MÜSSEN [MUST]** in einem separaten `include/`-Verzeichnis liegen, nicht vermischt mit `common/`: Sie werden vom Compiler `#include`d, nicht von ESPHome gemerged, und das Vermischen verdeckt diesen Unterschied `[fixture]` `[policy]`
- Die Datei eines stillgelegten Geräts **SOLLTE [SHOULD]** in einen `archive/`-Nachbarn wandern statt gelöscht zu werden, damit die Konfiguration als Pattern-Historie erhalten bleibt `[fixture]` `[policy]`
- Generierter oder werkzeug-eigener Zustand (`.esphome/`, Build-Verzeichnisse, `secrets.yaml`) **DARF NICHT [MUST NOT]** in die Versionskontrolle gelangen `[policy]`

### Package-Architektur

- `packages:` **MUSS [MUST]** der einzige Wiederverwendungs-Mechanismus für YAML sein; die Legacy-Merge-Key-Form (`<<: !include`) **DARF NICHT [MUST NOT]** in neuen Dateien eingeführt werden, da sie Listen nicht deep-merged und aus der Zeit vor packages stammt `[doc]` `[policy]`
- Packages **SOLLTEN [SHOULD]** in der **Mapping**-Form mit sprechendem Schlüssel deklariert werden (`packages: {plug: !include …, duration: !include …}`) statt als anonyme Liste, weil der Schlüssel dokumentiert, welchen Concern die Datei liefert. Mehr sollte man von ihm nicht erwarten: Die Dokumentation hält fest, dass bei Verwendung eines Mappings „the keys are for reference only and have no significance in themselves". Insbesondere ist ein Package-Schlüssel **nicht** das Ziel von `!extend` — `!extend` und `!remove` nehmen eine *Config-ID* einer Komponente, nie einen Package-Namen `[doc]` `[fixture]` `[policy]`
- Packages **MÜSSEN [MUST]** entlang **je eines Concerns** geschnitten werden — ein Board-Package (`common/gosund-sp111.yaml`, `common/esp32-s3-box-3.yaml`), ein Basis-Package (`common/base.yaml`) und Feature-Packages (`common/time.yaml`, `common/active-duration.yaml`, `common/timer-cancelable.yaml`) — sodass ein Gerät genau die Concerns komponiert, die es hat `[fixture]` `[policy]`
- Das **Board-Package** **SOLLTE [SHOULD]** das Basis-Package selbst hereinziehen, statt jedes Gerät beides einbinden zu lassen: Ein Gerät nennt dann ein Board und seine Extras, und eine Änderung an der Basis erreicht die ganze Flotte über eine Kante `[fixture]` `[policy]`
- Die Merge-Semantik **MUSS [MUST]** verstanden sein, bevor man sich darauf stützt — hier vollständig aus der Dokumentation zitiert, weil jede Teilaussage anders zubeißt: „Dictionaries are merged key-by-key. Lists of components are merged by component ID (if specified). Other lists are merged by concatenation. **All other configuration values are replaced with the later value.**" Die letzte Klausel wird am leichtesten vergessen — ein Skalar in der Device-Datei gewinnt stillschweigend gegen den des Packages `[doc]`
- Jede Komponente in einem Package, die ein Gerät später erweitern oder entfernen könnte, **MUSS [MUST]** eine `id:` tragen; ohne ID fällt der Merge auf Konkatenation zurück und das Gerät bekommt zwei Komponenten statt einer modifizierten `[doc]` `[policy]`
- Die Package-Verschachtelung **SOLLTE [SHOULD]** flach bleiben (Gerät → Board → Basis). Tiefere Ketten machen die effektive Konfiguration schwer vorhersagbar, und die Ausgabe von `esphome config` ist dann der einzige Weg zu wissen, was ein Gerät tatsächlich hat `[policy]`

### Parametrisierung

- Jede Device-Datei **MUSS [MUST]** mit einem `substitutions:`-Block beginnen, der die Identität des Geräts deklariert, nach der Drei-Teile-Konvention des Fixtures: `name` (kebab-case, entspricht dem Dateinamen), `id` (snake_case, gültig als C++-Bezeichner) und `comment` (menschenlesbar) `[fixture]` `[policy]`
- Diese Substitutions **MÜSSEN [MUST]** in Packages als `${name}` / `${id}` / `${comment}` konsumiert werden, statt Literale zu wiederholen, sodass eine Umbenennung eine Ein-Zeilen-Änderung bleibt `[fixture]` `[doc]`
- Die Override-Richtung **MUSS [MUST]** bekannt sein: Substitutions in der konsumierenden Konfiguration **überschreiben** gleichnamige Substitutions aus einem Package — genau das macht ein Package überhaupt parametrisierbar `[doc]`
- Ein Package, das je Gerät mehr als einmal instanziiert wird, **SOLLTE [SHOULD]** über `!include` mit `vars:` parametrisiert werden, wobei die Substitutions des Geräts hineingereicht werden — das Fixture tut genau das für sein Scheduling-Package (`file: common/active-duration.yaml`, `vars: {time_start: ${time_start}, time_end: ${time_end}}`). Die Dokumentation sagt ausdrücklich, dass dieselbe Datei mehrfach mit unterschiedlichen `vars:` gelistet werden darf — genau das macht daraus einen Template-Mechanismus statt eines Einmal-Includes `[fixture]` `[doc]`
- Jedes Package, das eine Variable liest, die nicht jeder Konsument setzt, **MUSS [MUST]** einen `defaults:`-Block deklarieren, damit ein fehlender Wert einen dokumentierten Fallback statt eines Substitutions-Fehlers erzeugt — das Basis-Package des Fixtures defaultet `project_name` und `project_version` auf diese Weise `[doc]` `[fixture]`
- Eine Package-Datei **KANN [MAY]** per Substitution ausgewählt werden (`!include device-${platform}.yaml`), **DARF** dies aber **NICHT [MUST NOT]** mit dem YAML-Merge-Key kombinieren, wo Dateinamen-Substitution nicht funktioniert `[doc]`
- Jede `${var}`, die ein Package liest, **SOLLTE [SHOULD]** als Teil seiner öffentlichen Schnittstelle behandelt werden: Eine hinzuzufügen ist für bestehende Konsumenten eine brechende Änderung, sofern sie keinen Default trägt `[policy]`

### Abweichen ohne Forken

- Ein Gerät, das eine Package-Komponente *leicht anders* braucht, **MUSS [MUST]** dies über `!extend` auf der Komponenten-ID lösen, nie durch Kopieren des Packages in eine gerätespezifische Variante `[doc]` `[policy]`
- Ein Gerät, das eine vom Package gelieferte Komponente nicht haben darf, **MUSS [MUST]** dies über `!remove` lösen — auf einer ID, auf einem ganzen Abschnitt (`captive_portal: !remove`) oder auf einem einzelnen Attribut `[doc]`
- `!extend` / `!remove` **KÖNNEN [MAY]** konditional aus Substitutions gesteuert werden, wo ein Package Varianten einer Gerätefamilie bedient `[doc]`
- Eine Ein-Geräte-Abweichung **DARF NICHT [MUST NOT]** durch ein beinahe-identisches Package beantwortet werden: Zwei Packages, die sich in einem Schlüssel unterscheiden, sind genau die Drift, gegen die diese Spec existiert `[policy]`
- Eine Abweichung **SOLLTE [SHOULD]** ins Package als defaultete Variable hochgezogen werden, sobald ein **zweites** Gerät denselben Override braucht — eine Abweichung ist eine Ausnahme, zwei sind ein Parameter `[policy]`

### Credentials

- In einem Package, das ein **Remote**-Package ist oder werden könnte, **DÜRFEN NICHT [MUST NOT]** `!secret`-Lookups stehen: Die Dokumentation stellt fest, dass Remote-Packages keine Secrets auflösen können, und verweist stattdessen auf Substitutions mit Defaults `[doc]`
- Jedes Credential **MUSS [MUST]** unabhängig vom Mechanismus aus der Versionskontrolle herausgehalten werden, und eine befüllte `secrets.yaml` **DARF NICHT [MUST NOT]** committet werden `[policy]`
- Für Credentials **MUSS [MUST]** `!env_var` verwendet werden, wie es das Fixture für WLAN-SSID, -Passwort, -Domain und Fallback-Hotspot-Passwort tut: Umgebungsvariablen erreichen sowohl einen lokalen als auch einen CI-Build ohne eine Datei, die niemals committet werden darf, und sie funktionieren in Packages, wo `!secret` es nachweislich nicht kann. Das ist der Credential-Mechanismus des Portfolios; [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md) trägt dieselbe Regel `[fixture]` `[src]` `[policy]`
- `!env_var` **MUSS [MUST]** als **undokumentierte API** behandelt werden: Es ist in ESPHomes `yaml_util.py` registriert und liest `os.environ`, optional mit Fallback (`!env_var NAME default`), erscheint aber weder in der FAQ noch in der Substitutions-Dokumentation — die stattdessen `!secret` empfehlen. Bei einem ESPHome-Upgrade erneut zu prüfen, und die Prüfung festzuhalten `[src]` `[doc]` `[policy]`
- In einem `!env_var`-Namen **DÜRFEN NICHT [MUST NOT]** Substitutions erwartet werden: Das Tag wird beim Parsen des YAML aufgelöst, bevor Substitutions angewendet werden, `!env_var KEY_${id}` funktioniert also nicht `[src]`
- Jede Umgebungsvariable, die ein Package liest, **MUSS [MUST]** dokumentiert sein, damit ein frischer Checkout baubar ist, ohne die Fehlermeldungen rückwärts zu interpretieren `[policy]`
- Die API-Verschlüsselungs-Anforderung aus [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md) **MUSS [MUST]** über Packages hinweg intakt bleiben: Ein Basis-Package mit nacktem `api:` lässt jedes konsumierende Gerät auf einen Schlag unverschlüsselt — genau der Wirkungsradius, den geteilte Packages erzeugen. Das Basis-Package des Fixtures tut dies derzeit und ist ein zu behebender Defekt, keine zu kodifizierende Variante `[fixture]` `[policy]`
- Der Flotte **DARF NICHT [MUST NOT]** **ein gemeinsamer** API-Encryption-Key gegeben werden: Eine einzige flottenweite Variable in einem geteilten Package bedeutet, dass ein kompromittiertes Gerät die API-Sitzung jedes anderen preisgibt — das Gegenteil dessen, wofür Verschlüsselung da ist. Jedes Gerät **MUSS [MUST]** seinen eigenen Key tragen, gesetzt als Substitution in seiner eigenen Device-Datei (`substitutions: {api_key: !env_var <DEVICE>_API_KEY}`) und vom Package als `${api_key}` konsumiert — die Indirektion ist nötig, weil `!env_var` den Gerätenamen nicht selbst interpolieren kann `[src]` `[policy]`

### Remote-Packages

- Ein Package **KANN [MAY]** aus einem Git-Repository konsumiert werden, über die Kurzform (`github://user/repo/file.yml@ref` — auch `gitlab://` und `codeberg://` werden unterstützt) oder die erweiterte Form mit `url`, `files`, `ref`, `refresh`, optionalen Credentials und `vars:` pro Datei `[doc]`
- Ein Remote-Package **MUSS [MUST]** auf einen hinreichend unveränderlichen `ref` gepinnt werden (ein Tag oder ein Commit, kein wandernder Branch) — ein ungepinntes Remote-Package bedeutet, dass sich der Inhalt eines Builds ohne einen Commit in diesem Repository ändert `[doc]` `[policy]`
- `refresh` **MUSS [MUST]** bewusst gesetzt werden, wenn ein `ref` ein Branch ist, und die daraus folgende Nicht-Reproduzierbarkeit ist als in Kauf genommener Preis zu behandeln `[doc]` `[policy]`
- Ein Drittanbieter-Package **SOLLTE [SHOULD]** eher nach `common/` **gevendort** als remote referenziert werden, im Einklang mit der in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) festgehaltenen Entscheidung: Ein gevendortes Package ist im Diff reviewbar, baut offline und ändert sich nur, wenn jemand es ändert `[policy]`
- Parameter **MÜSSEN [MUST]** über Substitutions mit Defaults in ein Remote-Package gereicht werden, statt zu erwarten, dass es in die Secrets des Konsumenten zurückgreift `[doc]`

### Naming- und Flotten-Konventionen

- Eine Device-Datei **MUSS [MUST]** nach dem Gerät benannt sein und das Gerät nach dem, was es ist, plus einer Ordnungszahl, wenn mehrere einer Art existieren — die `gosund-sp111-01` … `gosund-sp111-07` und `cam-01` … `cam-07` des Fixtures sind das Muster `[fixture]` `[policy]`
- `name` (kebab-case) und `id` (snake_case) **MÜSSEN [MUST]** aus derselben Zeichenkette abgeleitet bleiben, damit die Abbildung zwischen Dateiname, Netzwerkname und C++-Bezeichner mechanisch bleibt `[fixture]` `[policy]`
- Ein Board-Package **SOLLTE [SHOULD]** nach dem Board benannt werden (`gosund-sp111.yaml`, `nous-a1t.yaml`, `ulanzi-tc001.yaml`) und ein Feature-Package nach der Fähigkeit (`time.yaml`, `active-duration.yaml`, `pixel_art.yaml`), sodass sich die Import-Liste wie ein Satz über das Gerät liest `[fixture]` `[policy]`
- `esphome.project.name` / `.version` **SOLLTEN [SHOULD]** im Basis- oder Board-Package deklariert werden, damit ein geflashtes Gerät meldet, was es ist — so wie das Fixture es tut `[fixture]` `[doc]`
- Ort oder Zweck eines Geräts **DÜRFEN NICHT [MUST NOT]** in seinen `name` kodiert werden, wenn sie sich ändern können — das Fixture hält den Ort in `comment` und die Identität in `name`, weshalb ein umgestelltes Gerät keine Umbenennung braucht `[fixture]` `[policy]`

### Lebenszyklus

- Ein neues Gerät einer bestehenden Art **MUSS [MUST]** durch Anlegen **nur** einer Device-Datei aufgenommen werden: Substitutions plus Board-Package plus etwaige Feature-Packages. Erfordert die Aufnahme das Anfassen eines Packages, war das Package falsch geschnitten `[fixture]` `[policy]`
- Eine neue *Art* von Gerät **MUSS [MUST]** durch Hinzufügen eines Board-Packages und anschließend der Device-Datei aufgenommen werden, statt durch Schreiben einer in sich geschlossenen Device-Config `[policy]`
- Ein Gerät **SOLLTE [SHOULD]** durch Verschieben seiner Datei nach `archive/` stillgelegt werden, was es aus dem Build nimmt und das Muster erhält `[fixture]` `[policy]`
- Legacy-Artefakte in `archive/` (das Fixture hält dort `include-*.yaml.snipped`-Merge-Key-Snippets) **SOLLTEN [SHOULD]** als schreibgeschützte Historie behandelt werden, nie als Vorlage für neue Arbeit `[fixture]` `[policy]`

### Validierung

- Jede Geräte-Konfiguration **MUSS [MUST]** vor dem Commit mit `esphome config <file>` validiert werden; die aufgelöste Ausgabe ist zugleich die einzig verlässliche Antwort auf „was hat dieses Gerät tatsächlich, nachdem alle Packages gemerged sind" `[doc]` `[policy]`
- `esphome config` **MUSS [MUST]** in CI bei jeder Änderung für **jede** Device-Datei laufen, nicht nur für die Dateien im Diff: Eine Package-Änderung kann ein Gerät brechen, dessen Datei niemand angefasst hat — der charakteristische Fehlermodus eines Repositories mit geteilten Packages — und Schema-Validierung ist schnell genug, um sie flottenweit zu leisten `[policy]`
- Das vollständige `esphome compile` **SOLLTE [SHOULD]** einem Nightly- oder Vor-Release-Lauf vorbehalten bleiben statt jedem Pull Request — die Compile-Zeit wächst mit der Flotte, während der flottenweite `config`-Lauf den Fall „Package bricht unberührtes Gerät" bereits fängt `[policy]`
- Die statischen Prüfungen des Repositories **SOLLTEN [SHOULD]** als Gate neben der ESPHome-Validierung bestehen bleiben. Dabei ist genau zu benennen, was das Fixture tatsächlich liefert, denn es ist dünner als es aussieht: `build-static-tests.yaml` fährt pre-commit, Trivy und chain-bench; die pre-commit-Konfiguration trägt nur `end-of-file-fixer` und `trailing-whitespace`; die Rechtschreibprüfung für Prosa ist Vale über `.vale.ini` und einen `spelling.yaml`-Workflow. Einen YAML-Linter gibt es **nicht**, und eine ESPHome-Validierung findet in dieser Pipeline nirgends statt `[fixture]` `[policy]`
- Ist die ESPHome-Toolchain nicht verfügbar, **MUSS [MUST]** die Validierung als offener Caller-Schritt gemeldet werden, statt sie stillschweigend zu überspringen `[policy]`

### Verifikation

- `packages:`-, Substitutions- und Merge-Verhalten **MÜSSEN [MUST]** gegen die offizielle ESPHome-Dokumentation verifiziert werden, bevor man sich darauf stützt, gemäß [`ha/upstream-docs-verification`](../upstream-docs-verification/de.md) `[policy]`
- Das Fixture **DARF NICHT [MUST NOT]** für sich als normativ behandelt werden: Es ist Beleg gelebter Praxis und trägt bekannte Abweichungen von den eigenen Specs des Portfolios (siehe Credentials und Offene Fragen) `[policy]`
- Die Merge- und Override-Regeln **SOLLTEN [SHOULD]** neu verifiziert werden, wenn ESPHome neue Package-Features einführt, da `!extend`, `!remove` und konditionale Einbindung jeweils verändert haben, was „Wiederverwendung" bedeuten kann `[policy]`

## Akzeptanzkriterien

- [ ] Jedes Gerät hat genau eine Datei, benannt nach ihm, flach im Config-Root; nichts unter `common/` ist flashbar
- [ ] Geteiltes YAML liegt in `common/`, C++-Helfer in `include/`, stillgelegte Geräte in `archive/`
- [ ] Wiederverwendung läuft über `packages:` in Mapping-Form mit sprechenden Schlüsseln; es existieren keine neuen `<<: !include`-Merge-Keys
- [ ] Jedes Package deckt einen Concern ab; ein Gerät komponiert ein Board-Package plus Feature-Packages, und das Board-Package zieht die Basis herein
- [ ] Jede Device-Datei beginnt mit `name`- / `id`- / `comment`-Substitutions, und Packages referenzieren sie statt Literale
- [ ] Jedes Package, das eine nicht von allen Konsumenten gesetzte Variable liest, deklariert einen `defaults:`-Fallback
- [ ] Komponenten, die Geräte überschreiben könnten, tragen eine explizite `id:`
- [ ] Abweichungen nutzen `!extend` / `!remove`; es existiert kein beinahe-identisches Package, das sich von einem anderen in einem Schlüssel unterscheidet
- [ ] Kein Credential ist committet, und kein Package, das remote werden könnte, enthält einen `!secret`-Lookup
- [ ] Jedes Remote-Package ist auf ein Tag oder einen Commit gepinnt, oder ein bewusstes `refresh` ist dokumentiert
- [ ] Die Aufnahme eines Geräts bestehender Art hat nur eine neue Datei berührt
- [ ] `esphome config` besteht für jede Device-Datei, und CI validiert alle statt nur die geänderten

## Offene Fragen

- **Fixture-Behebung**: Diese Spec und die angepasste [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md) beschreiben nun einen Zustand, den das Fixture noch nicht erfüllt — sein Basis-Package deklariert ein nacktes `api:` ohne `encryption:`. Wer behebt das, und braucht die Flotte ein koordiniertes Neu-Flashen, sobald der Schlüssel eingeführt wird (jedes Gerät verliert seine Home-Assistant-Verbindung, bis der Schlüssel auf HA-Seite eingetragen ist)? Am 2026-08-02 upstream gemeldet als [nolte/esphome-configs#15](https://github.com/nolte/esphome-configs/issues/15), zusammen mit [#14](https://github.com/nolte/esphome-configs/issues/14) für einen nicht auflösbaren Include, den die fehlende CI-Validierung hätte fangen müssen.

Per Entscheidung erledigt (hier festgehalten, damit die Begründung auffindbar bleibt, nicht als offene Arbeit): Credentials nutzen **`!env_var`**, und `ha/esphome-config-patterns` wurde entsprechend angepasst statt umgekehrt, weil Remote-Packages `!secret` nachweislich nicht auflösen können. Die API-Verschlüsselung bleibt **Anforderung**, das nackte `api:` des Fixtures ist also ein Defekt und keine akzeptierte Variante. Device-Dateien bleiben **flach**, geräteeigene Assets liegen in einem eigenen geschlüsselten Baum. `common/` gruppiert **nach Konsument** — Einstiegspunkte flach, Bausteine in Domänen-Unterverzeichnissen. CI führt `esphome config` **flottenweit** bei jeder Änderung aus, `compile` bleibt dem Nightly vorbehalten. Board-Packages tragen **keine** Versions-Substitution; die flottenweite Validierung fängt eine inkompatible Änderung im selben Pull Request.
