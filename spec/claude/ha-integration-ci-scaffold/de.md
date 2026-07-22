# Skill: `ha-integration-ci-scaffold`

Status: draft

## Kontext

Eine hochwertige Custom Integration wird in CI durch zwei HA-Domänen-Gates validiert, die die generische Portfolio-CI nicht emittiert: **hassfest** (`home-assistant/actions/hassfest@master`), das Manifest, Strings und Service-Definitionen validiert (ein Bronze-Floor gemäß `ha/dev-workflow`), und die **HACS-Validierungs-Action** (`hacs/action@main` mit `category: integration`), die das Repository so validiert, wie HACS es zur Install-Zeit tut (`ha/hacs-release`). Daneben läuft eine **pytest-Matrix** auf `pytest-homeassistant-custom-component` (`ha/test-harness`). `ha-integration-scaffold` behauptet aktuell, hassfest-CI werde „vom project-structure-Scaffold gehandhabt", aber der generische `nolte-shared:project-structure`-Scaffold emittiert Lint-/Pre-commit-/Release-Wiring, nicht diese HA-spezifischen Validatoren — eine gescaffoldete Integration hat also kein hassfest- oder HACS-Gate.

Dieser Skill schließt die Lücke: Er scaffoldet die HA-Domänen-CI-Validierung für ein Custom-Integration-Repository — hassfest, die HACS-Action und die pytest-Matrix — als GitHub-Actions-Workflow im **Consumer**-Repo, ergänzend statt ersetzend zur generischen CI. Er ist die CI-Validierungs-Schwester von `ha-hacs-release` (das die HACS-Distributions-Schicht besitzt).

## Scope

Scaffolding eines HA-Domänen-CI-Validierungs-Workflows in ein Custom-Integration-Repository: eine `.github/workflows/validate.yml` mit einem `validate`-Job (`actions/checkout@v4` → `home-assistant/actions/hassfest@master` → `hacs/action@main` mit `category: integration`, wenn HACS-distribuiert) und einem `pytest`-Job über eine Python-Versions-Matrix, getriggert auf `push` / `pull_request` (+ optionaler nightly `schedule`). Der Skill liest `domain`, erkennt HACS-Distribution, entscheidet die Matrix und validiert offline; er emittiert keine Lint-/Release-Jobs, die die generische CI besitzt.

## Ziele

- Die HA-Domänen-CI-Validatoren (hassfest + HACS-Action + pytest-Matrix) emittieren, die die generische Portfolio-CI nicht liefert, und den `ha-integration-scaffold`-hassfest-CI-Anspruch auflösen
- Die kanonischen Action-Refs nutzen — `home-assistant/actions/hassfest@master` und `hacs/action@main` (`category: integration`)
- Eine pytest-Matrix auf `pytest-homeassistant-custom-component` fahren, abgestimmt auf `ha/test-harness`
- Ergänzen, nicht duplizieren, gegenüber der generischen Lint-/Release-CI, und `nolte/gh-plumbing`-Reusables referenzieren, wo das Portfolio sie bereits bereitstellt
- Alle generierte CI-YAML gemäß der Portfolio-Config-Sprach-Regel Englisch halten

## Nicht-Ziele

- Der generische Repo-Scaffold (Lint, Pre-commit, Release-Drafter-Wiring) — `nolte-shared:project-structure`
- Der Release-Publish-Flow (Draft → Published, Version-Alignment, ZIP-Asset) — `release-automation` / `ha-hacs-release`
- Die Python-Integration-Code-Generierung — `ha-integration-scaffold`
- Die pytest-Tests selbst — `ha-test-harness-augment`
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add hassfest and HACS validation to CI", „set up the integration CI workflow", „add a pytest matrix job for the integration"
  - „richte die Integration-CI ein", „füge hassfest/HACS-Validierung zur CI hinzu"
- **MUSS NICHT [MUST NOT]** für den generischen Repo-Scaffold (`nolte-shared:project-structure`) oder den Release-Publish-Flow (`release-automation` / `ha-hacs-release`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Integration-Repo-Root)
- **KANN [MAY]** erfassen: `hacs_distributed` (sonst aus `hacs.json`-Präsenz abgeleitet), `python_matrix` (sonst die aktuell HA-unterstützten Versionen) und `nightly` (Default `true`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo ist und `custom_components/<domain>/manifest.json` existiert; `domain` lesen und `hacs.json` erkennen
- **MUSS NICHT [MUST NOT]** eine bestehende `validate.yml`, die bereits hassfest/HACS-Steps trägt, überschreiben — stattdessen Erweiterung anbieten

### Generierungs-Regeln

- **MUSS [MUST]** `.github/workflows/validate.yml` auf Englisch generieren mit einem `validate`-Job, der `actions/checkout@v4` dann `home-assistant/actions/hassfest@master` ausführt
- **MUSS [MUST]** einen `hacs/action@main`-Step mit `category: integration` ergänzen, wenn das Repo HACS-distribuiert ist
- **MUSS [MUST]** einen `pytest`-Job über eine Python-Versions-Matrix ergänzen, der die Test-Deps der Integration installiert und `pytest` (mit Coverage) ausführt, abgestimmt auf `ha/test-harness`
- **MUSS [MUST]** auf `push` und `pull_request` triggern; **KANN [MAY]** einen nightly `schedule` (`cron: "0 0 * * *"`) ergänzen
- **MUSS NICHT [MUST NOT]** Lint-/Pre-commit-/Release-Jobs re-emittieren, die die generische CI besitzt; **SOLLTE [SHOULD]** `nolte/gh-plumbing`-Reusable-Workflows referenzieren, wo einer existiert
- **MUSS [MUST]** die aktuellen Action-Refs und die unterstützte Python-Matrix gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`; hassfest gemäß `ha/dev-workflow`, HACS-Gate gemäß `ha/hacs-release`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: die YAML parst; der hassfest-Step ist vorhanden; der HACS-Step ist mit `category: integration` vorhanden, wenn anwendbar; der pytest-Matrix-Job ist vorhanden; keine Lint-/Release-Duplikation
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an diese Akzeptanzkriterien plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**bronze** — hassfest ist ein Bronze-Validierungs-Gate) anknüpft

### Verbote

- **MUSS NICHT [MUST NOT]** einen bestehenden HA-CI-Workflow überschreiben
- **MUSS NICHT [MUST NOT]** die generische Lint-/Release-CI duplizieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] `.github/workflows/validate.yml` ist auf Englisch auf `push` / `pull_request` generiert
- [ ] Der hassfest-Step nutzt `home-assistant/actions/hassfest@master`
- [ ] Der HACS-Step nutzt `hacs/action@main` mit `category: integration`, wenn HACS-distribuiert
- [ ] Ein pytest-Matrix-Job läuft auf `pytest-homeassistant-custom-component`
- [ ] Kein generischer Lint-/Release-Job wird dupliziert; Reusables werden referenziert, wo vorhanden
- [ ] Der Bericht benennt die geänderten Datei-Pfade und den Quality-Scale-Marker **bronze**

## Offene Fragen

- **Reusable vs. Inline**: Liefert `nolte/gh-plumbing` bereits einen Reusable-HA-Validate-Workflow zum Aufrufen statt Inline-hassfest/HACS/pytest? Falls ja, verdrahtet dieser Skill den Reusable.
- **Python-Matrix-Quelle**: Die Matrix sollte HAs aktuell unterstützte Python-Versionen tracken. Ist der Versions-Satz in einer Portfolio-Config gepinnt oder pro Lauf gegen die Doku aufgelöst?
- **hassfest für HACS-only-Repos**: hassfest validiert Core-stil-Integrationen; eine rein-HACS-Integration braucht ggf. eine engere Config. Welche hassfest-Checks sind immer anwendbar?
