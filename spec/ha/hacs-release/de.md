# HA-Integration: HACS-Release und Distribution

Status: draft

## Kontext

Eine Home-Assistant **Custom Integration** wird in aller Regel über [HACS](https://www.hacs.xyz/) (Home Assistant Community Store) verteilt. HACS installiert und aktualisiert die Integration direkt aus ihrem GitHub-Repository. Diese Spec definiert den vollständigen, durch CI abgedeckten Release- und Distributionsprozess: welche Artefakte das Repository tragen muss (`hacs.json`, `manifest.json`, Verzeichnis-Layout), wie GitHub-Releases und die in HACS angezeigte Version zusammenhängen, wie die Versionsnummer konsequent synchron gehalten wird und welche wiederverwendbaren Workflows in [`nolte/gh-plumbing`](https://github.com/nolte/gh-plumbing) den Prozess tragen.

**Die zentrale Mechanik — Quelle der Wahrheit für die Version:** HACS setzt die angezeigte und installierbare Version aus dem **Tag-Namen des zuletzt veröffentlichten GitHub-Release**, nicht aus dem `version`-Feld der `manifest.json` ([hacs.xyz/docs/publish/start](https://www.hacs.xyz/docs/publish/start/): „If the repository uses GitHub releases, the tag name from the latest release is used to set the remote version. Just publishing tags is not enough, you need to publish releases."). Ein bloßer Git-Tag genügt nicht — es muss ein echtes GitHub-Release-Objekt existieren. Das `version`-Feld der `manifest.json` ist für Custom Integrations dennoch verpflichtend (HA-Loader, hassfest, Selbstauskunft der installierten Version) und **muss** mit dem Release-Tag übereinstimmen; es ist aber nicht der Hebel, den HACS für die Versionsauswahl liest.

**Verhältnis zum bestehenden Release-System:** Dieses Portfolio betreibt einen etablierten, durch `release-automation` (in `claude-shared`) normierten Flow: `release-drafter` leitet auf `develop`-Push die nächste Version ab und pflegt einen Draft-Release; ein `chore(release): <tag>`-Alignment-Commit setzt die versionstragenden Dateien; `reusable-release-publish.yml` verifiziert vor `draft=false` den Abgleich und veröffentlicht das Release; `reusable-release-cd-refresh-master.yml` aktualisiert den Präsentations-Branch. Der generische „versionstragende Dateien"-Mechanismus erkennt HACS-Integrationen bereits (`custom_components/<domain>/manifest.json` → `$.version`). Diese Spec ergänzt die HACS-spezifische Schicht (`hacs.json`, HACS-/hassfest-Validierung, ZIP-Distribution, `brands`) und schreibt den Versions-Abgleich für den HACS-Fall verbindlich fest, ohne die generischen Regeln neu zu definieren.

**Geltungsbereich:** Custom Integrations (Python) unter `custom_components/<domain>/`. Zwei Distributions-Stufen werden unterschieden: **Custom-Repository** (Nutzer fügt die Repo-URL manuell in HACS hinzu — Baseline) und **Default-Store** (Aufnahme in den offiziellen `hacs/default`-Index — zusätzliche, strengere Stufe).

## Ziele

- Den vollständigen Release-Prozess durch CI abdecken, sodass jeder veröffentlichte HACS-Release reproduzierbar und ohne manuelle Datei-Edits entsteht
- Sicherstellen, dass GitHub-Release-Tag, `manifest.json`-`version` und die in HACS angezeigte Version stets dieselbe Versionsnummer tragen und immer ein passender Tag zu jedem Release existiert
- Die Pflicht-Artefakte (`hacs.json`, `manifest.json`, Verzeichnis-Layout) verbindlich festschreiben
- Die HACS- und hassfest-Validierung als CI-Gate auf Push und Pull-Request verankern
- ZIP-Release als empfohlenes Distributions-Modell normieren und die daraus folgende CD-Pflicht (Asset bauen und anhängen) definieren
- Den Pre-Release-Mechanismus als Beta-Channel und das `brands`-Handling klar abgrenzen
- Die Default-Store-Aufnahme als optionale, klar umrissene Zusatzstufe beschreiben
- Die tragenden wiederverwendbaren Workflows in `nolte/gh-plumbing` benennen, statt CI-Logik je Integration zu duplizieren

## Nicht-Ziele

- Die generischen Regeln aus `release-automation` (Draft → Published, versionstragende Dateien, `chore(release)`-Alignment, Berechtigungen) — diese Spec referenziert sie, definiert sie nicht neu
- Die inhaltliche Definition der `manifest.json`-Felder jenseits des Release-Bezugs — fällt in `ha/integration-manifest`
- Lovelace-Cards, Themes, Python-Scripts, AppDaemon-Apps und andere HACS-Kategorien — diese Spec deckt ausschließlich die Kategorie `integration` ab
- Der inhaltliche Aufbau der Release-Notes — fällt in `release-skill-layer` (Skill `release-notes-curate`)
- Die konkrete Implementierung der gh-plumbing-Reusables (YAML-Details) — die Spec definiert deren Kontrakt, der Code lebt in `nolte/gh-plumbing`
- Verteilung über das offizielle Home-Assistant-Add-on-Repository oder als Core-Integration

## Anforderungen

### Repository-Struktur und Pflicht-Artefakte

- **MUSS [MUST]** alle Integrations-Dateien in genau einem Unterverzeichnis `custom_components/<domain>/` ablegen; pro Repository ist genau **eine** Integration zulässig — bei mehreren Unterverzeichnissen verwaltet HACS nur das erste (stille Fehlerquelle) ([publish/integration](https://www.hacs.xyz/docs/publish/integration/))
- **MUSS [MUST]** eine `manifest.json` unter `custom_components/<domain>/` führen, die mindestens `domain`, `documentation`, `issue_tracker`, `codeowners`, `name` und `version` setzt — die übrigen Manifest-Regeln regelt `ha/integration-manifest`
- **MUSS [MUST]** eine `hacs.json` im Repository-Wurzelverzeichnis führen (siehe `### hacs.json`)
- **MUSS [MUST]** für jeden Release ein echtes GitHub-Release-Objekt erzeugen (nicht nur einen Tag); andernfalls fällt HACS auf die Dateien des Default-Branch zurück und ignoriert die Release-basierte Versionsauswahl ([publish/start](https://www.hacs.xyz/docs/publish/start/), [publish/integration](https://www.hacs.xyz/docs/publish/integration/))

### `hacs.json`

Die `hacs.json` im Repo-Root steuert, wie HACS das Repository behandelt. Nur `name` ist verpflichtend; die übrigen Felder sind optional und bilden eine offene Menge.

- **MUSS [MUST]** `name` setzen — der Anzeigename der Integration in der HACS-Oberfläche
- **MUSS [MUST]** das Standard-Layout `custom_components/<domain>/` verwenden und daher `content_in_root` **nicht** setzen (Default `false`); `content_in_root: true` ist Repositories vorbehalten, deren Inhalt direkt im Wurzelverzeichnis liegt — für Integrations untypisch
- **MUSS [MUST]** `zip_release: true` setzen und dazu `filename: <domain>.zip` angeben — das gewählte Distributions-Modell (siehe `### ZIP-Release-Distribution`); `zip_release` ist laut HACS nur für Integrations unterstützt ([publish/include](https://www.hacs.xyz/docs/publish/include/))
- **SOLLTE [SHOULD]** `homeassistant` auf die minimal benötigte Home-Assistant-Version setzen, damit HACS Installationen auf zu alten Kernen blockiert
- **SOLLTE [SHOULD]** `hide_default_branch: true` setzen, sobald ausschließlich über Releases verteilt wird — so bietet HACS nicht zusätzlich den Default-Branch zur Installation an
- **KANN [MAY]** `hacs` auf die minimal benötigte HACS-Version, `render_readme: true` (README statt `info.md` rendern), `country` und `persistent_directory` setzen
- **MUSS [MUST]** valides JSON sein und im Repo-Root liegen — die `hacsjson`-Prüfung der HACS-Action verifiziert die Existenz

### Versionsquelle: GitHub-Release und Tag

- **MUSS [MUST]** akzeptieren, dass HACS die Remote-Version aus dem **Tag-Namen** des zuletzt veröffentlichten Release ableitet; HACS bietet dem Nutzer eine Auswahl der **fünf neuesten** Releases plus den Default-Branch ([publish/integration](https://www.hacs.xyz/docs/publish/integration/))
- **MUSS [MUST]** das Tag-Schema `v<MAJOR>.<MINOR>.<PATCH>` (z. B. `v0.1.2`) verwenden, wie vom portfolioweiten `release-drafter` (`tag-template: v$NEXT_PATCH_VERSION`) erzeugt
- **MUSS NICHT [MUST NOT]** sich darauf verlassen, dass HACS bei fehlendem Release die `manifest.json`-Version gegen die Commit-SHA prüft — ein solcher Vergleich existiert nicht; die alleinige Versionsquelle ist der Release-Tag
- **SOLLTE [SHOULD]** beachten, dass Custom-Repositories ihre Metadaten live über die GitHub-REST-API beziehen (nicht aus den vorgenerierten HACS-Daten) — Release-Aktualität propagiert dort sofort, GitHub-Rate-Limits wirken direkt ([faq/data_sources](https://www.hacs.xyz/docs/faq/data_sources/))

### Versions-Synchronisation der `manifest.json`

Die Versionsnummer wird über den bestehenden, in `release-automation` normierten Mechanismus synchron gehalten. Diese Spec bestätigt ihn für den HACS-Fall und stellt klar, dass der Abgleich verpflichtend bleibt, obwohl HACS den Tag liest.

- **MUSS [MUST]** `custom_components/<domain>/manifest.json` → `$.version` als versionstragende Datei behandeln; der Wert ergibt sich aus dem Release-Tag unter der Transformation `strip-leading-v` (Tag `v0.1.2` → `version` `0.1.2`, sofern die Datei die `v`-Konvention nicht selbst führt)
- **MUSS [MUST]** den Abgleich über einen `chore(release): <tag>`-Commit auf `develop` herstellen, bevor `reusable-release-publish.yml` `draft=false` aufruft — Primärpfad (workflow-getrieben über den Portfolio-App-Token) oder Fallback-Pfad (Maintainer-PR), wie in `release-automation` definiert
- **MUSS [MUST]** den Publish verweigern, wenn `$.version` am Ziel-SHA des Drafts nicht dem Tag entspricht; `reusable-release-publish.yml` erkennt die HACS-Integration (Quelle `hacs`) bereits und verifiziert dies vor der Veröffentlichung
- **MUSS NICHT [MUST NOT]** das `version`-Feld in Feature-Pull-Requests verändern; die einzige zulässige Quelle eines Version-Bumps ist der `chore(release): <tag>`-Pfad
- **SOLLTE [SHOULD]** klarstellen, dass der Abgleich der Korrektheit dient (HA-Loader-Warnung vermeiden, hassfest, korrekte Selbstauskunft im Geräte-Info-Dialog), nicht der HACS-Versionsauswahl — HACS würde auch bei Abweichung die Tag-Version anzeigen und installieren

### CI-Validierung (HACS-Action + hassfest)

Die Validierung läuft als CI-Gate über die beiden offiziellen GitHub-Actions; in diesem Portfolio gebündelt im Reusable `reusable-hacs-validate.yml` (siehe `### Wiederverwendbare Workflows`).

- **MUSS [MUST]** die HACS-Action (`hacs/action`) mit `category: integration` auf `push` und `pull_request` ausführen — sie nutzt denselben Code wie HACS zur Repository-Validierung ([publish/action](https://www.hacs.xyz/docs/publish/action/), [hacs/action](https://github.com/hacs/action))
- **MUSS [MUST]** die hassfest-Action (`home-assistant/actions/hassfest@master`) ausführen — das offizielle HA-Werkzeug zur Validierung (auch eigenständiger/Custom-) Integrationen ([HA-Devs hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/))
- **SOLLTE [SHOULD]** beide Actions zusätzlich auf `release: published` ausführen, damit ein veröffentlichter Release nachweislich validiert ist
- **KANN [MAY]** für ein reines Custom-Repository einzelne der acht HACS-Action-Checks per `ignore`-Input deaktivieren (`archived`, `brands`, `description`, `hacsjson`, `images`, `information`, `issues`, `topics`, leerzeichengetrennt) — jeder Ignore reduziert jedoch die Validierungs-Abdeckung
- **MUSS NICHT [MUST NOT]** für eine Default-Store-Aufnahme irgendeinen Check ignorieren (siehe `### Default-Store-Aufnahme`)
- **SOLLTE [SHOULD]** `hacs/action` auf eine Version oder einen Commit-SHA pinnen; `home-assistant/actions/hassfest` wird laut HA-Doku kanonisch als `@master` referenziert — ein SHA-Pin ist eine eigene Härtungsentscheidung

### ZIP-Release-Distribution

Mit `zip_release: true` lädt HACS ausschließlich das benannte Release-Asset statt das Repository zu klonen — schneller und zuverlässiger, da nur die Integrations-Dateien ausgeliefert werden ([publish/include](https://www.hacs.xyz/docs/publish/include/): „Use zip releases instead of git clone (recommended)").

- **MUSS [MUST]** in der CD ein ZIP-Asset mit exakt dem in `hacs.json` als `filename` angegebenen Namen (`<domain>.zip`) erzeugen und an den Release anhängen; fehlt oder verfehlt das Asset den Namen, schlägt der HACS-Download fehl
- **KANN [MAY]** den *Build*-Namen über den `asset-filename`-Input des Reusables (`reusable-release-publish.yml`) von `hacs.json` entkoppeln; ist er gesetzt, hat er Vorrang, andernfalls fällt das Reusable auf `hacs.json` `filename` und schließlich `<domain>.zip` zurück. Der Input ersetzt die `hacs.json`-Schlüssel `filename`/`zip_release` **nicht** — HACS liest `hacs.json`, um das Asset zu wählen, daher **MÜSSEN [MUST]** Build-Name und `hacs.json`-`filename` weiterhin übereinstimmen (das Reusable warnt bei Divergenz)
- **MUSS [MUST]** das ZIP-Asset an den Draft-Release anhängen, **bevor** `reusable-release-publish.yml` `draft=false` aufruft — andernfalls entsteht ein Wettlauf, in dem HACS den Release ohne Asset sieht und der Download fehlschlägt; ein separater `on: release published`-Workflow ist für das Asset daher **unzulässig**
- **MUSS [MUST]** als ZIP-Inhalt die Dateien der Integration so packen, dass HACS sie nach `custom_components/<domain>/` entpacken kann (Inhalt des Integrations-Verzeichnisses auf ZIP-Wurzelebene)
- **SOLLTE [SHOULD]** das ZIP deterministisch und reproduzierbar bauen (keine Zeitstempel-/Pfad-Nondeterminismen), damit identischer Quellstand identische Assets erzeugt

### Pre-Releases / Beta-Channel

- **SOLLTE [SHOULD]** einen Beta-/Vorabkanal über das GitHub-Release-Flag **Pre-Release** abbilden; HACS schlägt ein als Pre-Release markiertes Release nicht als neueste Version vor und löst keinen Standard-Update-Hinweis aus ([issue #322](https://github.com/hacs/integration/issues/322), [PR #396](https://github.com/hacs/integration/pull/396))
- **MUSS [MUST]** akzeptieren, dass Pre-Releases opt-in sind — Nutzer aktivieren sie pro Integration (in HACS 2.0 über eine standardmäßig deaktivierte Switch-Entity); stabile Nutzer bleiben unberührt
- **MUSS NICHT [MUST NOT]** einen Pre-Release als regulären Release veröffentlichen, wenn er nur einem Beta-Kreis dienen soll — das Pre-Release-Flag ist der korrekte Mechanismus

### `brands`

- **KANN [MAY]** für ein reines Custom-Repository auf `brands` verzichten; ohne Brand-Assets zeigt HACS ein Fallback-Icon
- **SOLLTE [SHOULD]** auch im Custom-Repository ein lokales `brand/`-Verzeichnis mit mindestens `icon.png` ausliefern **oder** die Domain im Repository [`home-assistant/brands`](https://github.com/home-assistant/brands) hinterlegen, um korrekte Icons zu erhalten; das lokale `brand/icon.png` hat Vorrang vor dem Brands-CDN
- **MUSS [MUST]** für eine Default-Store-Aufnahme die `brands`-Prüfung erfüllen: ein `brand/`-Verzeichnis mit `icon.png` ausliefern **oder** die Domain (passend zu `manifest.json` → `domain`) im `home-assistant/brands`-Repository per PR hinterlegen ([publish/include](https://www.hacs.xyz/docs/publish/include/))

### Default-Store-Aufnahme (optionale Zusatzstufe)

Die Aufnahme in den offiziellen `hacs/default`-Index ist optional; sie hebt die Anforderungen gegenüber dem Custom-Repository an.

- **MUSS [MUST]** die HACS-Action **ohne Fehler und ohne `ignore`** bestehen sowie hassfest bestehen, bevor der Aufnahme-PR gestellt wird ([publish/include](https://www.hacs.xyz/docs/publish/include/))
- **MUSS [MUST]** nach erfolgreichen Actions ein echtes GitHub-Release erzeugen (nicht nur einen Tag)
- **MUSS [MUST]** die `brands`-Anforderung erfüllen (siehe `### brands`)
- **MUSS [MUST]** den Aufnahme-PR gegen `hacs/default` regelkonform stellen: alphabetisch einsortiert, das PR-Template exakt ausgefüllt, eingereicht vom Repo-Eigentümer oder einem maßgeblichen Beitragenden — andernfalls wird der PR ohne weitere Rückmeldung geschlossen
- **SOLLTE [SHOULD]** beachten, dass Default-Store-Repositories aus vorgenerierten HACS-Daten ausgeliefert werden (nicht live über die GitHub-API) — Aktualisierungen propagieren mit Verzögerung

### Wiederverwendbare Workflows (`gh-plumbing`)

Die CI-/CD-Logik lebt als wiederverwendbare Workflows in `nolte/gh-plumbing` und wird von der Integration via `uses:` referenziert — analog zu den bestehenden `reusable-release-*`-Workflows.

- **MUSS [MUST]** die HACS-/hassfest-Validierung als Reusable `reusable-hacs-validate.yml` bereitstellen, der `hacs/action` (category `integration`, optionaler `ignore`-Input) und `home-assistant/actions/hassfest@master` kapselt; die konsumierende Integration ruft ihn aus ihrem CI-Workflow auf `push`/`pull_request` auf
- **MUSS [MUST]** den ZIP-Asset-Bau im Veröffentlichungspfad verankern, sodass das Asset vor `draft=false` am Release hängt — entweder als Schritt in `reusable-release-publish.yml` (HACS-Quelle erkannt) oder als dedizierter, vor dem Publish ausgeführter Reusable; **nicht** als nachgelagerter `on: release published`-Workflow
- **SOLLTE [SHOULD]** das bestehende `app-id`/`token`-Muster der `reusable-release-*`-Workflows übernehmen (Portfolio-App-Token mit Fallback auf `GITHUB_TOKEN`) und Action-Referenzen pinnen
- **SOLLTE [SHOULD]** den konsumierenden Integrationen Workflow-Stubs als Vorlage bereitstellen (CI-Aufruf von `reusable-hacs-validate.yml`; `hacs.json`-Muster), damit der Prozess reproduzierbar aufgesetzt wird

### Verhältnis zu anderen Specs

- **MUSS [MUST]** auf `ha/integration-manifest` verweisen für die `manifest.json`-Feldregeln; diese Spec beantwortet dessen offene Frage „Version-Bump-Automatisierung": Der Bump erfolgt **nicht** im Scaffold, sondern über den `chore(release): <tag>`-Pfad des Release-Workflows
- **MUSS NICHT [MUST NOT]** die in `release-automation` (`claude-shared`) definierten Regeln (Draft → Published, versionstragende Dateien, Alignment-Pfade, Berechtigungen, Cascade-Constraints) neu definieren — referenzieren statt duplizieren
- **SOLLTE [SHOULD]** auf `ha/quality-scale` (Release-/Owner-bezogene Regeln) und `ha/dev-workflow` (lokale Validierung vor dem Release) querverweisen
- **SOLLTE [SHOULD]** mit `release-skill-layer` abgegrenzt bleiben: Release-Notes-Kuratierung und der lokale Publish-Trigger liegen dort, nicht in dieser Spec

## Referenz-Vorlagen

Die folgenden Vorlagen setzen den Prozess in einer konsumierenden Integration reproduzierbar auf. Platzhalter (`<domain>`, `<owner>`, `<repo>`, Anzeigename) sind zu ersetzen. Tag- und Versionsableitung, Draft → Published, `main`-Refresh und der ZIP-Asset-Bau stammen aus den `gh-plumbing`-Reusables und müssen nicht je Integration neu geschrieben werden.

### `hacs.json` (Repo-Wurzel)

```json
{
  "name": "<Anzeigename>",
  "homeassistant": "2024.1.0",
  "zip_release": true,
  "filename": "<domain>.zip",
  "hide_default_branch": true
}
```

### `manifest.json` (Release-relevante Felder)

```json
{
  "domain": "<domain>",
  "name": "<Anzeigename>",
  "version": "0.0.0",
  "documentation": "https://github.com/<owner>/<repo>",
  "issue_tracker": "https://github.com/<owner>/<repo>/issues",
  "codeowners": ["@<owner>"]
}
```

`version` wird nicht von Hand gepflegt; der `chore(release): <tag>`-Pfad richtet sie auf den Tag aus (siehe `### Versions-Synchronisation der manifest.json`).

### CI-Validierung (`.github/workflows/ci.yml`)

```yaml
name: ci

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

permissions:
  contents: read

jobs:
  hacs-validate:
    uses: nolte/gh-plumbing/.github/workflows/reusable-hacs-validate.yaml@v1.1.24
    # Custom-Repo: einzelne Checks per `ignore` deaktivierbar (z. B. "brands").
    # Default-Store: KEIN ignore — siehe §Default-Store-Aufnahme.
    # with:
    #   ignore: "brands"
```

### Release-Workflows (Standard aus `gh-plumbing`)

Die Release-Workflows sind identisch zum portfolioweiten Standard (`release-drafter.yml`, `release-publish.yml`, `release-cd-refresh-master.yml`). `reusable-release-publish.yml` erkennt die HACS-Integration über `custom_components/<domain>/manifest.json` selbst und hängt das `<domain>.zip`-Asset vor `draft=false` an — kein integrationsspezifischer Zusatz nötig.

```yaml
# .github/workflows/release-publish.yml
on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Draft-Tag, der veröffentlicht werden soll (muss zu einem offenen Draft passen)."
        required: true
        type: string
      dry_run:
        description: "Nur validieren (inkl. ZIP-Bau), ohne draft=false."
        required: false
        default: false
        type: boolean

permissions:
  contents: write

jobs:
  publish:
    uses: nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml@v1.1.24
    with:
      tag: ${{ inputs.tag }}
      dry_run: ${{ inputs.dry_run }}
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

## Akzeptanzkriterien

- [ ] Die Integration liegt in genau einem Verzeichnis `custom_components/<domain>/`; das Repository enthält keine zweite Integration
- [ ] `manifest.json` setzt mindestens `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version`
- [ ] `hacs.json` liegt im Repo-Root, ist valides JSON, setzt `name`, `zip_release: true` und `filename: <domain>.zip`
- [ ] Jeder Release ist ein echtes GitHub-Release-Objekt mit Tag `v<MAJOR>.<MINOR>.<PATCH>` — kein nackter Tag
- [ ] `manifest.json` → `$.version` entspricht am Release-Ziel-SHA dem Tag (unter `strip-leading-v`); der Abgleich stammt aus einem `chore(release): <tag>`-Commit
- [ ] `reusable-release-publish.yml` verweigert den Publish bei Versions-Abweichung (Quelle `hacs` erkannt)
- [ ] Das CI führt `hacs/action` (`category: integration`) und `home-assistant/actions/hassfest@master` auf `push` und `pull_request` aus
- [ ] Ein ZIP-Asset mit exakt `<domain>.zip` hängt am Release **vor** dessen Veröffentlichung
- [ ] Beta-Releases sind als GitHub-Pre-Release markiert und werden stabilen Nutzern nicht als Update angeboten
- [ ] `reusable-hacs-validate.yml` existiert in `nolte/gh-plumbing` und wird von der Integration referenziert
- [ ] Für eine Default-Store-Aufnahme: HACS-Action ohne `ignore` grün, hassfest grün, `brands` erfüllt, regelkonformer `hacs/default`-PR

## Offene Fragen

- **ZIP-Innenlayout** (festgelegt als Annahme, nicht primärbelegt): Das `zip_release`-Asset enthält den **Inhalt** von `custom_components/<domain>/` auf ZIP-Wurzelebene (das etablierte `integration_blueprint`-Muster); HACS entpackt das benannte Asset nach `custom_components/<domain>/`. Diese Annahme trägt den CD-ZIP-Build in `reusable-release-publish.yml`. Vor einer Default-Store-Aufnahme **sollte** sie durch eine reale Test-Installation gegen das HACS-Verhalten gegengeprüft werden; `content_in_root`-Layouts sind ausgenommen.
- **Vollständiges `hacs.json`-Schema**: Die überlebenden Quellen bestätigen einzelne Felder, aber keine einzige kanonische Vollschema-Referenz mit exakten Defaults und Semantik von `content_in_root`, `country`, `persistent_directory`, `render_readme`. Sollte eine kanonische Schema-Quelle nachgezogen werden?
- **Versioning-Tooling-Alternative**: Diese Spec bestätigt den `release-drafter`-+-`chore(release)`-Pfad. Soll `python-semantic-release` (Stamping von `manifest.json` via `version_variables`, da kein `version_json` existiert) als dokumentierte Alternative aufgenommen werden, oder bleibt der bestehende Pfad die einzige normierte Lösung? Welches Tooling sich in der HA-Community durchsetzt, ist nicht belegt.
- **ZIP im Primär- vs. dediziertem Reusable**: Soll der ZIP-Asset-Bau in `reusable-release-publish.yml` integriert werden (HACS-Quelle bereits erkannt) oder als eigener, vor dem Publish aufgerufener Reusable — Abwägung zwischen Kohäsion und Trennung der Verantwortlichkeiten.
- **`hide_default_branch`-Verbindlichkeit**: Soll `hide_default_branch: true` von `SOLLTE` zu `MUSS` werden, da diese Spec ohnehin echte Releases für jeden Versionsstand verlangt?
