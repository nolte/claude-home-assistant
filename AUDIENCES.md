# Zielgruppen — `claude-home-assistant`-Plugin (dieses Repository)

<!--
Erzeugt mit dem `audience-identify`-Skill, gemäß
spec/project/audience-identification/ (im nolte-shared-Plugin).
Keine Zielgruppen ergänzen, ohne zuerst den Bounded Context unten anzupassen.
-->

## Bounded Context

**Was dieser Kontext *ist***:

- Das Repository `nolte/claude-home-assistant`, veröffentlicht als Claude-Code-Plugin `claude-home-assistant` (Version 0.1.0) über den Plugin-Marketplace.
- Es bündelt wiederverwendbare **Skills** (`skills/<name>/SKILL.md`), **Agents** (`agents/<name>.md`) und **Specs** (`spec/`, DE-kanonisch, EN als Übersetzung) für vier Home-Assistant-Authoring-Oberflächen: **Custom Integrations (Python)**, **Lovelace Cards (TypeScript / JavaScript)**, **Blueprints & Automations (YAML)** und **ESPHome / Add-ons**.
- MkDocs-Doku (`docs/`, DE-only zum Start) und Taskfile-Automatisierung.

**Konkrete Anwendungs-Domänen, an denen die Skills geschärft werden**:

- Erstklassiges Anwendungsbeispiel: [`nolte/kamerplanter-ha`](https://github.com/nolte/kamerplanter-ha) — eine HA Custom Integration mit aiohttp-API-Wrapper, Multi-Coordinator (5 Coordinators mit konfigurierbaren Intervallen), Zeroconf-Discovery, `runtime_data`-Pattern, EntityDescription-basierten Sensoren, Vanilla-JS-Lovelace-Cards und Kind-basiertem Dev-Loop. Ihre `spec/ha-integration/`- und `spec/style-guides/HA-INTEGRATION.md`-Dokumente (~11k LOC) sind die Quelle, aus der die Specs unter `spec/ha/` adaptiert werden.
- Zweite Erweiterungsachse: Lovelace Cards, Blueprints/Automations, ESPHome — werden iterativ durch Folge-Skills abgedeckt.

**Wo die Grenzen verlaufen**:

- Externe Oberflächen: Plugin-Manifest + Marketplace-Eintrag (Install-Pfad), Slash-Commands (`/claude-home-assistant:<skill>`), Agent-Definitionen, veröffentlichte MkDocs-Seite.
- Repo selbst, Branches `develop`/`main`, CI-Workflows.

**Was explizit *außerhalb* liegt**:

- Konkrete Konsumenten-Artefakte (HA-Integrationen, Cards, Blueprints, ESPHome-Configs), die mit Hilfe der Skills gebaut werden — leben in separaten Repos / HACS-Listings (z. B. `kamerplanter-ha` selbst, `homeassistant-fertilizer-helper`, `esphome-configs`).
- **Home Assistant Core** selbst — externes System, gegen dessen API/Konventionen die Skills produzieren.
- **HACS** — externes Distributionsmodell, gegen das Custom-Integration-/Card-Skills produzieren.
- **ESPHome Core** und **Add-on-Supervisor / s6** — externe Tools.
- **Claude Code** selbst (CLI/IDE-Integration) — Plugin baut darauf auf, betreibt es nicht.
- Inhaltliche Themen einzelner Skills — jeder Skill hat seinen eigenen, schmaleren Kontext, falls separat auditiert.

## Zielgruppen

Jeder Eintrag: Label, Beziehungs-Kategorie, Interaktions-Oberfläche, Erwartung, offene Fragen, `confirmed` oder `assumed`, Kritikalität (primary / secondary / peripheral), Doku-Track (`user-docs` / `developer-docs`). Eine ganze Kategorie wird mit `none — <Grund>` markiert, wenn sie nicht zutrifft.

> **Doku-Track-Zuordnung**: Dieses Repository ist ein **Entwickler-Plugin** — es bedient ausschließlich den `developer-docs`-Track. Der Portfolio-Default (`spec/project/docs-audience-tracks/` §Audience-to-track mapping: `contributor` / `operator` / `release-manager` → `developer-docs`) greift für praktisch alle Einträge; direkte Konsumenten sind hier durchweg Entwickler (Plugin-Autor, Skill-Konsumenten, die HA-Artefakte bauen) und mappen ebenfalls auf `developer-docs`.
>
> **No audience maps to `user-docs`**: Dieses Plugin hat keine End-User-Oberfläche. Die einzigen „End-User" sind die *indirekten* Smart-Home-Bewohner, die nicht das Plugin, sondern nur die mit den Skills gebauten Artefakte (Integration, Card, Automation) erleben — sie lesen keine Doku aus diesem Repo. Daher bleibt der `user-docs`-Track bewusst unbesetzt (Omission-Form gemäß `spec/project/mkdocs-structure/` §Audience targeting).

### Direkte Konsumenten

- **Plugin-Autor beim Dogfooding in diesem Repo (nolte)** — _Kategorie_: direct-consumer · _Oberfläche_: `claude --plugin-dir .`, `/reload-plugins`, lokales Skill-Invokation während der Skill-/Agent-/Spec-Entwicklung · _erwartet_: Änderungen sind sofort aufrufbar; Skills funktionieren auch gegen dieses Repo selbst (z. B. `/nolte-shared:project-structure-apply`) · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: keine

- **Plugin-Autor beim Refactoring/Weiterbau von `kamerplanter-ha` (nolte)** — _Kategorie_: direct-consumer · _Oberfläche_: Slash-Commands wie `/claude-home-assistant:ha-integration-scaffold`, `/claude-home-assistant:ha-config-flow-generator`, `/claude-home-assistant:ha-coordinator-pattern` und der Agent `ha-integration-deploy`, eingesetzt im `kamerplanter-ha`-Repo · _erwartet_: Skills reflektieren die Patterns, die in `kamerplanter-ha` bereits validiert sind; generierter Code matched die existierenden Konventionen (`runtime_data`, `EntityDescription`, `has_entity_name`); Deploy-Agent passt zum vorhandenen Kind-/`kubectl`-Workflow · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: Sollen Skills explizit gegen den `kamerplanter-ha`-Stand validiert werden (Round-Trip-Test: Skill regeneriert eine `kamerplanter-ha`-Datei, Diff sollte minimal sein)?

- **Plugin-Autor beim Bau einer neuen HA Custom Integration / Card / Blueprint / ESPHome-Komponente (nolte)** — _Kategorie_: direct-consumer · _Oberfläche_: Slash-Commands beim Greenfield-Scaffold in einem neuen Repo · _erwartet_: Scaffold liefert HA-2024.1+-konformen Boilerplate ohne Insider-Wissen aus `kamerplanter-ha`; aktuelle HA-Konventionen (`translation_key`, `has_entity_name`, `runtime_data`); funktionierender Test-Harness ab Tag 1 · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: An welche minimal unterstützte HA-Version pinnen wir die Skills? (`hacs.json` von `kamerplanter-ha` sagt `2024.1.0` — übernehmen?)

- **Spätere öffentliche Nutzer (HA-Custom-Integration- und Card-Autoren-Community)** — _Kategorie_: direct-consumer · _Oberfläche_: Plugin-Installation aus dem Marketplace, dieselben Slash-Commands · _erwartet_: belastbare Patterns auch ohne Insider-Wissen über das nolte-Portfolio; klare Trennung zwischen domänen-agnostischen HA-Patterns und nolte-spezifischen Konventionen; Versionierung kommuniziert Breaking-Changes · _Status_: `assumed` · _Kritikalität_: peripheral (heute hypothetisch — erst relevant, wenn das Plugin geteilt wird) · _Track_: developer-docs
  - Offene Fragen: Wann wird das Plugin tatsächlich öffentlich beworben? Welche Mindest-Reife (Anzahl Skills, Test-Coverage, gegen welche HA-Versionen verifiziert) muss vorher erreicht sein?

### Betreiber

- **GitHub Actions CI für dieses Repo** — _Kategorie_: operator · _Oberfläche_: Workflows unter `.github/workflows/` (insbesondere `ci.yml` mit `lint`/`test`/`docs` als Required-Checks auf `develop`), plus Release-/Automerge-/`main`-Fast-Forward-Infrastruktur über `nolte/gh-plumbing@v1.1.15` · _erwartet_: reproduzierbare Läufe; stabile Task-Targets (`task lint`/`test`/`docs`); keine flaky Checks, die `develop` blockieren · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: keine

- **GitHub Pages als Hosting der Plugin-Doku** — _Kategorie_: operator · _Oberfläche_: `release-cd-deliver-docs.yml`, MkDocs-Site veröffentlicht unter `nolte.github.io/claude-home-assistant` · _erwartet_: jeder Release liefert eine reproduzierbare Doku aus; sobald Skills/Agents existieren und der Skill-Agent-Catalog-Generator (`mkdocs-gen-files`) eingebunden ist, bricht der Build bei kaputter Frontmatter ab statt stillen Lücken · _Status_: `assumed` · _Kritikalität_: secondary · _Track_: developer-docs
  - Offene Fragen: keine

- **Claude-Code-Plugin-Marketplace (Distributionsinfrastruktur)** — _Kategorie_: operator · _Oberfläche_: `.claude-plugin/marketplace.json`, Install-Pfad über den Plugin-Marketplace-Mechanismus · _erwartet_: Plugin-Manifest ist marketplace-valid; Versionsbumps in `plugin.json` + `marketplace.json` synchron; Skills/Agents bleiben rückwärtskompatibel innerhalb einer Major-Version · _Status_: `assumed` · _Kritikalität_: peripheral (heute, solange das Plugin nicht öffentlich gelistet ist) · _Track_: developer-docs
  - Offene Fragen: Folgt das Plugin schon der `claude-shared`-Versions-Konvention? Wie kommunizieren wir Breaking-Changes an Skill-Konsumenten?

### Beitragende / Maintainer

- **Repo-Maintainer (nolte)** — _Kategorie_: contributor · _Oberfläche_: direkter Commit-Zugriff auf alle Branches, Review-Autorität, Release-Autorität, Spec-Evolutions-Autorität · _erwartet_: Specs, Skills und Plugin-Manifest bleiben konsistent; `CLAUDE.md` reflektiert den Repo-Stand; Konventionen (DE-kanonische Specs, Conventional Commits, PR-Workflow via `/nolte-shared:pull-request-create`) werden eingehalten · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: keine

- **Claude Code als Co-Autor** — _Kategorie_: contributor · _Oberfläche_: Skills aus `nolte-shared` (`/nolte-shared:skill-management`, `/nolte-shared:spec`, `/nolte-shared:project-structure-apply`, `/nolte-shared:pull-request-create`, `/nolte-shared:audience-identify`) — Claude scaffolded und editiert Files unter `skills/`, `agents/`, `spec/` und erzeugt Commits/PRs · _erwartet_: Skills folgen ihren eigenen Specs (Meta-Konsistenz: `claude-home-assistant`-Skills lesen `claude-home-assistant`-Specs); Änderungen bleiben review-fähig; Hard Rules werden respektiert (z. B. keine Plugin-Skills nach `.claude/skills/` kopieren); generierter Code für HA-Patterns matched die kanonisierten Specs · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: keine

- **`kamerplanter-ha`-Repo als Wissens-Quelle und Round-Trip-Validierer** — _Kategorie_: contributor · _Oberfläche_: `spec/ha-integration/` und `spec/style-guides/HA-INTEGRATION.md` in `nolte/kamerplanter-ha` sind die Quell-Texte, die in `claude-home-assistant/spec/ha/` adaptiert werden; `custom_components/kamerplanter/` ist das Fixture, gegen das die Skills round-trip-getestet werden können (Skill regeneriert eine Datei, Diff sollte minimal bleiben) · _erwartet_: Drift zwischen `kamerplanter-ha`-Specs und unseren Specs wird sichtbar; eine Spec-Änderung hier triggert eine Skill-Update-Welle, nicht eine stille Divergenz; wenn `kamerplanter-ha` sein Pattern weiterentwickelt (z. B. neuer HA-Release zwingt zu API-Änderung), zieht unser Spec nach · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: Wer pflegt die Sync-Richtung — wir hier (pull) oder `kamerplanter-ha` (push, indem es selbst diese Skills konsumiert und Drift meldet)? Soll es einen `spec-drift-audit`-Lauf zwischen den beiden Repos geben?

- **Externe Contributors via Pull Request** — _Kategorie_: contributor · _Oberfläche_: GitHub-Forks, PRs gegen `develop`, Issue-Tracker · _erwartet_: klare Einstiegspunkte (README, `CLAUDE.md`, Spec-Layout); PR-Workflow via `/nolte-shared:pull-request-create` ist ohne Insider-Wissen befolgbar; Skill-vs-Plugin-Architektur ist nachvollziehbar dokumentiert · _Status_: `assumed` · _Kritikalität_: peripheral (heute kein offener Beitragspfad — keine `CONTRIBUTING.md`) · _Track_: developer-docs
  - Offene Fragen: Soll dieses Repo aktiv für externe Beiträge geöffnet werden? Ab welchem Reifegrad ist das sinnvoll?

### Steuernde Parteien

- **Home-Assistant-Projekt als API- und Konventions-Steward** — _Kategorie_: governing-party · _Oberfläche_: HA-Developer-Docs, `manifest.json`-Schema, Lifecycle-Verträge (`async_setup_entry` / `async_unload_entry`), Helper-Module (`config_entries`, `helpers.update_coordinator`, `helpers.device_registry`, …), Quality-Scale-Stufen, hassfest-Validator · _erwartet_: Skills/Specs spiegeln die offiziellen Patterns wider und nicht eine private Fork-Realität; Skills benennen explizit, gegen welche HA-Mindest-Version sie verifiziert wurden (Kandidat: `2024.1.0`, analog `kamerplanter-ha/hacs.json`); Änderungen am HA-Core (z. B. neue Quality-Scale-Anforderungen, Deprecation einer Helper-API) werden in den Specs nachgezogen · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: Welche HA-Mindest-Version pinnen wir portfolioweit? Wie verfolgen wir HA-Breaking-Changes (Release-Notes, hassfest-Updates)?

- **HACS (Home Assistant Community Store) als Distributions- und Validations-Steward** — _Kategorie_: governing-party · _Oberfläche_: `hacs.json`-Schema, HACS-Action (`hacs/action@main` mit Category `Integration` / `Plugin` für Cards), Repo-Layout-Erwartungen (Domain-Folder, README-Rendering, `content_in_root`-Flag) · _erwartet_: Skills für Custom Integrations und Lovelace Cards produzieren HACS-konformes Layout out-of-the-box; CI-Templates enthalten den HACS-Validator; Skills weisen darauf hin, wenn ein Pattern (z. B. Multi-Card-Repo) HACS-spezifische Bedingungen verletzen würde · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: Sollen Skills nur HACS-konforme Strukturen erzeugen oder auch native Custom-Integration-Layouts ohne HACS unterstützen?

- **Anthropic / Claude Code als Plugin-Schnittstellen-Steward** — _Kategorie_: governing-party · _Oberfläche_: Plugin-Manifest-Schema (`.claude-plugin/plugin.json`), Marketplace-Schema (`marketplace.json`), Skill-Frontmatter-Format, Slash-Command-Namespacing (`/<plugin>:<skill>`), Agent-Definition-Format · _erwartet_: dieses Plugin folgt der jeweils aktuellen Plugin-Spezifikation; Skills nutzen offiziell unterstützte Frontmatter-Felder; Breaking-Changes seitens Claude Code werden via `nolte-shared`-Specs propagiert · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: keine

- **Portfolio-Konsistenz-Anker (`nolte/gh-plumbing`, `nolte/taskfiles`, `nolte/claude-shared` als Spec-Quelle)** — _Kategorie_: governing-party · _Oberfläche_: `_extends`-Pointer in `.github/{settings,release-drafter,boring-cyborg,stale}.yml`, gepinnter `gh-plumbing`-Tag (aktuell `v1.1.15`), `TASK_COLLECTION_BASE`-Referenzen, Specs aus `nolte-shared` (project-structure, audience-identification, skill-management, …) · _erwartet_: dieses Repo divergiert nicht von den Portfolio-Standards; Upstream-Änderungen werden nachgezogen (Renovate-PRs für `gh-plumbing`-Releases, Spec-Drift via `project-structure-apply`); Plugin-Konventionen aus `claude-shared` (Skill-vs-Agent, Frontmatter-Form, Hard-Rules-Block) werden eingehalten · _Status_: `assumed` · _Kritikalität_: primary · _Track_: developer-docs
  - Offene Fragen: keine

- **ESPHome-Projekt als API-Steward für die ESPHome-/Add-on-Skills** — _Kategorie_: governing-party · _Oberfläche_: ESPHome-Component-API (C++/Python-Schnittstelle), ESPHome-YAML-Schema, HA-Add-on-Spezifikation (Supervisor, s6-Init, `config.yaml`-Schema) · _erwartet_: Skills/Specs für ESPHome-Components und HA-Add-ons spiegeln die offiziellen Schemas; Skills benennen die ESPHome-Mindest-Version · _Status_: `assumed` · _Kritikalität_: secondary (heute — wird primary, sobald die ersten ESPHome-/Add-on-Skills entstehen) · _Track_: developer-docs
  - Offene Fragen: Sind ESPHome-Custom-Components und HA-Add-ons zwei getrennte Spec-Achsen oder eine? `kamerplanter-ha` deckt diesen Bereich nicht ab — wir haben dort kein Round-Trip-Repo.

### Indirekte Zielgruppen

- **End-User der mit den Skills gebauten HA-Integrationen / Cards / Blueprints / ESPHome-Komponenten (Bewohner des Smart Homes)** — _Kategorie_: indirect · _Oberfläche_: keine direkt — sie sehen nur die laufende Integration in HA, das Card im Dashboard, die Automation, die ihr Licht schaltet. Einfluss läuft mediated, weil die Skills die Qualität der Integration formen, die diese End-User dann erleben (z. B. ob `unique_id`/`translation_key` korrekt gesetzt sind und Entitäten dadurch ihren Namen behalten, ob `via_device` zur sinnvollen Geräte-Hierarchie führt, ob Config-Flow-Strings übersetzt sind) · _erwartet_: nichts direkt vom Plugin. Das Plugin übernimmt explizit keine Verantwortung für End-User-Outcomes; Skills sind Tooling, keine Garantien — verantwortlich ist die Integration, die mit ihnen gebaut wird · _Status_: `assumed` · _Kritikalität_: peripheral · _Track_: kein Track — indirekt, liest keine Doku aus diesem Repo; Beleg für die `user-docs`-Omission oben (Override-Rationale gemäß `spec/project/docs-audience-tracks/` §Audience-to-track mapping)
  - Offene Fragen: keine

- **Weitere HA-bezogene Repos im `nolte`-Portfolio (`ha-fertiliser`, `homeassistant-fertilizer-helper`, `homeassistant-config`, `kamerplanter`, `esphome-configs`)** — _Kategorie_: indirect · _Oberfläche_: keine direkt — diese Repos sind keine Konsumenten des Plugins per Install, könnten aber von der Spec-Konsolidierung profitieren (z. B. `homeassistant-fertilizer-helper` ist ebenfalls eine HA Custom Integration; `esphome-configs` ist ein Konsument der ESPHome-Skill-Achse) · _erwartet_: dass die Specs/Skills generisch genug bleiben, um auch dort anwendbar zu sein, statt ausschließlich auf `kamerplanter-ha`-Patterns zugeschnitten; dass eine Skill-Anwendung in einem dieser Repos nicht stille Drift erzeugt · _Status_: `assumed` · _Kritikalität_: peripheral (wird secondary, sobald eines dieser Repos die Skills aktiv konsumiert) · _Track_: developer-docs
  - Offene Fragen: Sollen wir explizit gegen `homeassistant-fertilizer-helper` als zweites Round-Trip-Repo testen, um Pattern-Generalität sicherzustellen?

- **Andere domänen-spezifische Claude-Code-Plugins im Portfolio, die `claude-home-assistant` als Vorbild für ein „Plugin pro Tech-Domäne"-Muster betrachten (analog `claude-reachy-mini`)** — _Kategorie_: indirect · _Oberfläche_: keine direkt — sie installieren das Plugin nicht, schauen aber auf die hier kodifizierten Patterns (wie ein domänen-spezifisches Plugin gegen das nolte-shared-Skelett aussieht, wie Specs aus einem Konsumenten-Repo destilliert werden) · _erwartet_: dass das Plugin als sauberes Beispiel taugt — also Specs, Skill-Layout und der `kamerplanter-ha → spec → skill`-Destillationsweg reproduzierbar dokumentiert sind · _Status_: `assumed` · _Kritikalität_: peripheral · _Track_: developer-docs
  - Offene Fragen: keine

- **HA-Custom-Integration-Reviewer (HA-Quality-Scale-Prozess)** — _Kategorie_: indirect · _Oberfläche_: keine direkt — sie reviewen Custom Integrations, die ggf. mit Hilfe dieser Skills gebaut wurden, gegen die HA-Quality-Scale-Kriterien (`bronze` / `silver` / `gold` / `platinum`). Einfluss läuft mediated, weil Skill-generierter Code unmittelbar auf bestimmten Quality-Scale-Stufen landet (oder eben nicht) · _erwartet_: nichts direkt; aber Skills sollten Quality-Scale-bewusst sein (z. B. `runtime_data` ist ein Silver-Kriterium, `unique_id`-Strategie ist ein Bronze-Kriterium) und das in Specs sichtbar machen · _Status_: `assumed` · _Kritikalität_: peripheral (heute — solange wir keine Integration zur HA-Core-Aufnahme einreichen) · _Track_: kein Track — indirekt, reviewt fremde Integrationen statt Doku aus diesem Repo zu lesen (Override-Rationale gemäß `spec/project/docs-audience-tracks/` §Audience-to-track mapping)
  - Offene Fragen: Sollen Specs explizit Quality-Scale-Stufen pro Pattern markieren?

## Offene Fragen (übergreifend)

- Keine Zielgruppe ist heute `confirmed` — keine wurde gegen einen echten Repräsentanten oder eine autoritative Quelle validiert. Alle Einträge bleiben `assumed`, bis eine solche Validierung passiert (z. B. erste tatsächliche Nutzung des Plugins gegen `kamerplanter-ha` oder ein anderes HA-Repo, erste öffentliche Veröffentlichung).
- **HA-Mindest-Version** ist portfolioweit ungeklärt: Übernehmen wir `2024.1.0` aus `kamerplanter-ha/hacs.json`, oder pinnen wir konservativer/aggressiver? Wie kommunizieren wir Breaking-Changes von HA upstream an Skill-Konsumenten?
- **Round-Trip-Validierung**: Sollen Skills explizit gegen `kamerplanter-ha` (und ggf. `homeassistant-fertilizer-helper` als zweites Repo) Round-Trip-getestet werden — Skill regeneriert eine Datei, Diff sollte minimal sein? Welcher Mechanismus (CI-Job, manueller Audit per `spec-drift-audit`)?
- **Spec-Sync-Richtung** zwischen `kamerplanter-ha/spec/ha-integration/` und `claude-home-assistant/spec/ha/`: Pull (wir adaptieren von dort) oder Push (`kamerplanter-ha` konsumiert unsere Specs und meldet Drift)? Beide Wege müssen koexistieren — der Initial-Pull ist klar, der laufende Sync nicht.
- **Veröffentlichungs-Schwelle**: Ab welchem Skill-/Reifegrad gibt das Plugin den Nicht-Owner-Konsumenten überhaupt einen Mehrwert, der eine Marketplace-Listung rechtfertigt?
- **HACS-Layout-Pflicht**: Sollen Skills nur HACS-konforme Strukturen erzeugen oder auch native Custom-Integration-Layouts ohne HACS unterstützen?
- **Quality-Scale-Markierung**: Sollen Specs pro Pattern explizit eine HA-Quality-Scale-Stufe markieren (Bronze/Silver/Gold/Platinum), damit Skill-Konsumenten wissen, auf welcher Stufe ihr Output landet?
- **ESPHome-Achse**: Sind ESPHome-Custom-Components und HA-Add-ons zwei getrennte Skill-Achsen oder eine? Welches Repo dient als Round-Trip-Fixture (`esphome-configs`)?

## Anlässe für Re-Identifikation

- **`kamerplanter-ha` beginnt, dieses Plugin als Konsument einzusetzen** — der direct-consumer-Status „Plugin-Autor beim Refactoring von kamerplanter-ha" flippt potenziell von `assumed` auf `confirmed`.
- **Ein zweites HA-Repo wird aktiver Konsument der Skills** (z. B. `homeassistant-fertilizer-helper`) — die Patterns-Generalität wird empirisch validiert; betroffene Indirect-Einträge werden secondary.
- **Das Plugin wird erstmals öffentlich gelistet** — „Spätere öffentliche Nutzer" und „Externe Contributors" werden von peripheral mindestens secondary.
- **Home Assistant veröffentlicht einen Breaking-Change am Custom-Integration-Lifecycle** (z. B. neue Quality-Scale-Stufen, Deprecation einer Helper-API, neue Pflicht-Felder im `manifest.json`-Schema) — die governing-party-Erwartungen ändern sich.
- **HACS ändert Validator-Verhalten oder Repo-Layout-Anforderungen** — analog.
- **Die ersten ESPHome-/Add-on-Skills entstehen** — der ESPHome-Steward wird von secondary auf primary.
- **Anthropic ändert das Plugin-Manifest- oder Skill-Frontmatter-Schema** — Plugin-Schnittstellen-Steward-Erwartungen ändern sich.
- **Das `nolte-shared`-Plugin verschärft die Spec für `audience-identification`** (z. B. neue Pflicht-Kategorien) — diese Datei muss nachgezogen werden.
- **Ein zweiter HA-orientierter Skill-/Agent-Katalog entsteht in einem anderen Repo**, der dieses hier ablöst oder mit ihm konkurriert — Anlass, die indirect-Kategorie ernsthaft zu prüfen.
