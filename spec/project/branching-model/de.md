# Branching-Modell

Status: draft

## Kontext
Repositories in diesem Portfolio verwenden `main` als reinen Präsentations-Branch, der stets das zuletzt veröffentlichte GitHub Release widerspiegelt. Aktive Entwicklung findet auf `develop` statt; Feature-Branches zielen per Pull Request auf `develop`. Wenn ein GitHub Release veröffentlicht wird, führen wiederverwendbare Workflows aus [`nolte/gh-plumbing`](https://github.com/nolte/gh-plumbing) einen Fast-Forward von `main` auf den freigegebenen Tag durch, sodass `main` eine maschinell gepflegte, lesende Sicht auf das zuletzt ausgelieferte Artefakt bleibt. Menschen und KI-Agenten, die auf `main` schauen, sehen genau das, was ausgeliefert wurde — niemals einen Work-in-Progress-Stand.

## Ziele
- `main` entspricht immer dem zuletzt veröffentlichten GitHub Release, nichts anderem
- Keine manuellen Commits, Pushes oder Merges landen auf `main` — jede Änderung läuft über `develop` und ein Release
- Die Überführung von `develop` nach `main` ist automatisiert, auditierbar und nur durch ein veröffentlichtes Release ausgelöst
- Branch-Rollen sind für Menschen und KI-Agenten, die das Repository lesen, eindeutig

## Nicht-Ziele
- Tag-Namensschema (von der release-drafter-Konfiguration abgedeckt; die Portfolio-Konvention ist der `v`-präfixierte SemVer-Tag, zum Beispiel `v1.2.3`, zentral in `nolte/gh-plumbing:.github/commons-release-drafter.yml` gesetzt)
- Changelog-Erzeugung (von release-drafter abgedeckt)
- Veröffentlichung in externen Registries (HACS, PyPI, Container-Registries)
- Inhalt projektweiter Taskfile-/CI-Targets (durch die project-structure-Spec abgedeckt)

## Anforderungen

### Branch-Rollen
- **MUSS [MUST]** `develop` als Integrations-Branch festlegen, auf dem alle Feature-Arbeit per Pull Request landet
- **MUSS [MUST]** `main` als Release-Präsentations-Branch festlegen, der das zuletzt veröffentlichte GitHub Release widerspiegelt
- **MUSS NICHT [MUST NOT]** manuelle Commits, Pushes oder Merges direkt auf `main` zulassen; der Branch wird ausschließlich durch die Release-Automatisierung beschrieben
- **MUSS [MUST]** Feature-Branches mit einem der Präfixe `feat/`, `fix/`, `chore/`, `docs/` oder `exp/` benennen und in ihrem Pull Request auf `develop` zielen; diese Präfixe sind identisch mit den in PR-Titeln verwendeten Conventional-Commits-Types, sodass Branch-Name und Commit-Type ohne Übersetzung zueinander passen
- **SOLLTE [SHOULD]** den `exp/`-Präfix für experimentelle oder iterations-scoped Arbeit reservieren, die lose verwandte Exploration bündelt; ein `exp/`-Branch hat eine explizit begrenzte Lebensdauer, und sein Merge wird als Wegwerf-Integration behandelt, nicht als stabile Feature-, Fix-, Chore- oder Dokumentationsänderung
- **SOLLTE [SHOULD]** `exp/`-Branches entweder mit einem Kalenderwochen-Marker (`exp/YYYY-WW-<thema>`, zum Beispiel `exp/2026-W17-skill-agent-split`) oder einem monoton steigenden Zähler (`exp/NNN-<thema>`, zum Beispiel `exp/003-skill-agent-split`) benennen, damit Iterationen sich chronologisch sortieren; der Thema-Teil folgt derselben Kebab-Case-Regel wie jeder andere Branch-Präfix
- **SOLLTE [SHOULD]** `exp`-PR-Titel aus den benutzerseitigen Release Notes ausschließen — entweder durch Mapping auf eine versteckte Kategorie in `.github/release-drafter.yml` (direkt oder über die `nolte/gh-plumbing:.github/commons-release-drafter.yml`-Extension) oder indem der `exp`-Type komplett aus den konfigurierten Kategorien herausgehalten wird; experimentelle Arbeit ist kein ausgeliefertes Feature und darf nicht als solches erscheinen

### Branch-Protection
- **MUSS [MUST]** alle Branch-Protection-Regeln als Code in `.github/settings.yml` deklarieren (direkt oder über `_extends: nolte/gh-plumbing:.github/commons-settings.yml`) und über die [Probot-Settings-App](https://probot.github.io/apps/settings/) synchronisieren; Protection-Regeln **MUSS NICHT [MUST NOT]** ad-hoc über die GitHub-UI konfiguriert werden
- **MUSS [MUST]** `main` so schützen, dass direkte Pushes von Menschen blockiert werden und nur der Release-Workflow (via `GITHUB_TOKEN`) ihn aktualisieren kann
- **SOLLTE [SHOULD]** `develop` so schützen, dass Pull Requests vor dem Merge grüne CI voraussetzen
- **SOLLTE [SHOULD]** lineare Historie auf `main` erzwingen, damit der Fast-Forward von Release-Tags sauber bleibt

### Release-Flow
- **MUSS [MUST]** GitHub Releases aus Tags erzeugen, die auf dem `develop`-Branch entstehen — release-drafter hält den Entwurf aktuell, sobald PRs landen
- **MUSS [MUST]** den Entwurf über `release-publish.yml` als primären Draft → Published-Pfad zu einem veröffentlichten GitHub Release flippen, gegated durch die Pre-Publish-Verifikation des Release-Automation-Workflows; ein direktes `gh release edit <tag> --draft=false` ist nur als dokumentierter Fallback für Incident-Response zulässig, wenn `release-publish.yml` selbst defekt ist
- **KANN [MAY]** durch den Sprint-Abschluss ausgelöst werden: die Geschwister-Specs `release-artifact` §Dispatch-Grenze zur Release-Maschinerie und `release-skill-layer` definieren eine optionale, operator-opt-in-Kette, in der `sprint-review` die Skills `release-notes-curate` (Body-Curation) und `release-publish-trigger` (Dispatch des oben deklarierten Workflows) aufruft. Die Dispatch-Grenze ist einseitig — diese Spec regiert den Workflow selbst, die Sprint-Specs regieren die Trigger-Bedingungen — und die konsumierenden Specs **DÜRFEN NICHT [MUST NOT]** hier deklarierte Regeln neu definieren
- **MUSS [MUST]** `main` ausschließlich über den Release-Workflow auf `release: [published]` aktualisieren
- **MUSS [MUST]** den Inhalt von `main` mechanisch aus dem Release ableiten; direkte Datei-Änderungen auf `main` sind ein Fehler
- **SOLLTE [SHOULD]** die Default-Pull-Request-Basis auf `develop` lassen, nicht auf `main`

### Hotfix-Flow
- **MUSS [MUST]** einen Notfall-Hotfix als regulären `fix/`-Pull-Request gegen `develop` behandeln, gefolgt von einem neuen Patch-Release, das `main` über `release-cd-refresh-master.yml` wie jedes andere Release per Fast-Forward bringt
- **MUSS NICHT [MUST NOT]** ab `main` branchen oder einen Hotfix zurück nach `main` mergen; die Regel „keine manuellen Schreibzugriffe auf `main`“ aus §Branch-Rollen und §Release-Flow lässt keine Hotfix-Ausnahme zu
- **MUSS [MUST]** das resultierende Release als Out-of-Band-Artefakt unter `project/release-artifacts/out-of-band/<NNNN>-<slug>.md` nach der Out-of-Band-Konvention erfassen; Mid-Sprint-Hotfixes werden auf dieselbe Weise nachgehalten, und die Release-Automation delegiert den Hotfix-Flow an diesen Unterabschnitt

### Erforderliche GitHub-Workflows
Das Repository **MUSS [MUST]** die folgenden Workflows unter `.github/workflows/` enthalten, jeweils an den entsprechenden wiederverwendbaren Workflow aus `nolte/gh-plumbing` angeschlossen:

- **`release-drafter.yml`** — löst auf `push: [develop]` aus; nutzt `nolte/gh-plumbing/.github/workflows/reusable-release-drafter.yml`, um den GitHub-Release-Entwurf der nächsten Version aktuell zu halten
- **`release-publish.yml`** — löst ausschließlich auf `workflow_dispatch` aus; nutzt `nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml`, um den offenen Entwurf auf `draft: false` zu flippen, sobald die Pre-Publish-Gates des Release-Automation-Workflows allesamt grün sind; benötigt die Berechtigung `contents: write`
- **`release-cd-refresh-master.yml`** — löst auf `release: [published]` aus; nutzt `nolte/gh-plumbing/.github/workflows/reusable-release-cd-refresh-master.yml` mit `target_branch: main`, um `main` per Fast-Forward auf den veröffentlichten Commit zu bringen; benötigt die Berechtigung `contents: write`
- **`automerge.yaml`** — löst auf Pull-Request-/Review-/Check-Suite-Events aus; nutzt `nolte/gh-plumbing/.github/workflows/reusable-automerge.yaml`, damit freigegebene, grüne Pull Requests gegen `develop` automatisch gemergt werden

`target_branch` ist für jedes Repository `main`, einschließlich HACS-Integrationen; das `master`-Token im Dateinamen des wiederverwendbaren Workflows `reusable-release-cd-refresh-master.yml` ist ein `nolte/gh-plumbing`-Namens-Altlast und impliziert keinen `master`-Branch.

Das Repository **SOLLTE [SHOULD]** außerdem enthalten, wo anwendbar:

- **`release-cd-deliver-docs.yml`** — auf `release: [published]`; veröffentlicht die MkDocs-Ausgabe über `nolte/gh-plumbing/.github/workflows/reusable-mkdocs.yaml`
- Weitere `release: [published]`-Packaging-Workflows (zum Beispiel `release.yml` zur Erzeugung eines HACS-ZIP), die spezifisch für das Liefer-Artefakt des Repositories sind

### Workflow-Integrität
- **MUSS [MUST]** die vier Pflicht-Workflows (`release-drafter.yml`, `release-publish.yml`, `release-cd-refresh-master.yml`, `automerge.yaml`) in jedem Repository halten, das diesem Branching-Modell folgt
- **SOLLTE [SHOULD]** die Referenz auf die wiederverwendbaren `nolte/gh-plumbing`-Workflows auf einen Tag fixieren (zum Beispiel `@v1.1.12`) statt auf einen wandernden Branch, damit das Refresh-Verhalten von `main` reproduzierbar bleibt
- Die Bump-Kadenz für den fixierten Tag wird durch die Workflow-Health-Disziplin (§Upstream-Drift) geregelt (Kandidaten-Bump über einen einzelnen gegateten PR, wobei Renovate-Automerge für `nolte/gh-plumbing`-Tag-Bumps verboten ist); jedes Repository fixiert den zuletzt validierten Tag, und portfolioweit ist keine einzelne feste Version vorgeschrieben

## Akzeptanzkriterien
- [ ] `develop` existiert und ist die Default-Basis für Pull Requests
- [ ] `main` existiert und ist per Branch-Protection so geschützt, dass Menschen nicht direkt pushen können
- [ ] Branch-Protection-Regeln für `main` und `develop` sind in `.github/settings.yml` deklariert (direkt oder über die `nolte/gh-plumbing`-commons-Erweiterung), nicht ausschließlich über die GitHub-UI
- [ ] `.github/workflows/release-drafter.yml` ist vorhanden und löst auf `push: [develop]` aus
- [ ] `.github/workflows/release-publish.yml` ist vorhanden, deklariert ausschließlich `workflow_dispatch` als Trigger, fordert `contents: write` an und ruft `nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml` auf
- [ ] `.github/workflows/release-cd-refresh-master.yml` ist vorhanden, löst auf `release: [published]` aus und setzt `target_branch: main`
- [ ] `.github/workflows/automerge.yaml` ist vorhanden und ruft den wiederverwendbaren Automerge-Workflow aus `nolte/gh-plumbing` auf
- [ ] Der HEAD von `main` entspricht einem veröffentlichten GitHub-Release-Tag (`git tag --points-at main` liefert einen Release-Tag zurück)
- [ ] Zwischen zwei aufeinanderfolgenden Releases gibt es keine menschlich erzeugten Commits auf `main` — nur Commits, die der Refresh-Workflow eingebracht hat
- [ ] Feature-Branches im Repository verwenden einen der Präfixe `feat/`, `fix/`, `chore/`, `docs/`, `exp/`
- [ ] Wenn `.github/release-drafter.yml` vorhanden ist, landet der `exp`-Type entweder in einer nicht benutzerseitigen Kategorie oder ist aus den konfigurierten Kategorien ausgeschlossen, sodass experimentelle PRs nicht als ausgelieferte Features erscheinen
- [ ] Wenn MkDocs verwendet wird **und** `.github/workflows/release-cd-deliver-docs.yml` ausgeliefert ist, löst der Workflow auf `release: [published]` aus (der Workflow selbst ist SHOULD, gemäß Anforderungen §Erforderliche GitHub-Workflows; dieses AK prüft den Trigger im Vorhandenseinsfall, nicht das Vorhandensein selbst)

## Offene Fragen
_Derzeit keine._
