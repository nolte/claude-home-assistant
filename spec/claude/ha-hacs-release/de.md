# Skill: `ha-hacs-release`

Status: draft

## Kontext

Eine Custom Integration wird in der Regel über HACS distribuiert, und `ha/hacs-release` definiert die vollständige HACS-spezifische Distributions-Schicht: eine valide `hacs.json`, die Tatsache, dass HACS die installierbare Version aus dem **Tag-Namen des zuletzt veröffentlichten GitHub-Releases** liest (nicht `manifest.json:version`, das dennoch dem Tag entsprechen muss), das ZIP-Release-Distributionsmodell (`zip_release: true` + `filename: <domain>.zip`), das HACS/hassfest-Validierungs-Gate und die `brands`-Registrierung. Diese Schicht sitzt auf dem generischen `release-automation`-Flow des Portfolios (release-drafter, `chore(release): <tag>`-Alignment, `reusable-release-publish`). Die `ha/hacs-release`-Spec existiert und ist doc-verankert, aber kein Skill oder Agent operationalisiert sie — eine Consumer-Integration muss `hacs.json`, das Version-Alignment und die ZIP-CD von Hand verdrahten, wo die häufigen Fehler ein fehlendes `filename` neben `zip_release`, eine aus dem Tag laufende `manifest.json`-Version und ein bloßer Tag ohne veröffentlichtes Release-Objekt sind.

Dieser Skill schließt die Lücke: Er macht eine bestehende Integration HACS-release-fertig, indem er die HACS-Schicht gemäß `ha/hacs-release` scaffoldet und verifiziert, auf `release-automation` aufsetzend, ohne es neu zu definieren. Er ist die Distributions-Schwester von `ha-integration-ci-scaffold` (das die CI-Validierung besitzt).

## Scope

Genau eine bestehende `custom_components/<domain>/`-Integration HACS-release-fertig machen: `hacs.json` erzeugen oder verifizieren (`name`, `zip_release` + `filename` fürs ZIP-Modell, `homeassistant`-Floor, `hide_default_branch`, optionale Keys), das `manifest.json:version`-Alignment zum `v<MAJOR>.<MINOR>.<PATCH>`-Tag-Schema verifizieren, die ZIP-Asset-CD-Pflicht über einen `nolte/gh-plumbing`-Reusable verdrahten und die `brands`-Registrierung sowie die generischen `release-automation`-Voraussetzungen ausweisen. Der Skill liest `ha/hacs-release`, entscheidet das Distributionsmodell und validiert offline; er definiert den generischen Release-Flow nicht neu.

## Ziele

- `ha/hacs-release` operationalisieren — eine Consumer-Integration über HACS installier- und aktualisierbar machen
- Eine valide `hacs.json` erzeugen, `zip_release: true` mit `filename: <domain>.zip` fürs ZIP-Modell paaren und den HA-Versions-Floor und `hide_default_branch` sinnvoll setzen
- Erzwingen, dass die Versionsquelle der GitHub-Release-**Tag** ist, dass `manifest.json:version` ihm entspricht und dass ein echtes veröffentlichtes Release (kein bloßer Tag) das ist, was HACS liest
- Die ZIP-Asset-CD-Pflicht über einen `nolte/gh-plumbing`-Reusable verdrahten und `brands` sowie die `release-automation`-Voraussetzungen ausweisen
- Die HACS-Schicht ergänzen, ohne die generischen release-automation-Regeln neu zu definieren

## Nicht-Ziele

- Der generische Release-Publish-Flow (Draft → Published, Version-bearing Files, `chore(release)`-Alignment) — `release-automation`
- Der CI-Validierungs-Workflow (hassfest / HACS-Action / pytest) — `ha-integration-ci-scaffold`
- Die Substanz der `manifest.json`-Felder jenseits ihrer Release-Relevanz — `ha/integration-manifest`
- HACS-Kategorien außer `integration` (Cards, Themes, …) — außerhalb des Scopes
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „make this integration HACS-release-ready", „add a hacs.json", „set up ZIP release for HACS"
  - „mach die Integration HACS-release-fertig", „füge eine hacs.json hinzu"
- **MUSS NICHT [MUST NOT]** für den generischen Release-Publish-Flow (`release-automation`) oder den CI-Validierungs-Workflow (`ha-integration-ci-scaffold`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Integration-Repo-Root)
- **KANN [MAY]** erfassen: `distribution` (`zip` Default, oder `default-branch`), `min_ha_version` (`hacs.json:homeassistant`) und `min_hacs_version` (`hacs.json:hacs`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo ist und `custom_components/<domain>/manifest.json` existiert; `domain`, `version`, `documentation`, `issue_tracker`, `codeowners` lesen
- **MUSS [MUST]** `ha/hacs-release` lesen und eine bestehende `hacs.json` sowie das release-automation-Wiring erkennen

### Generierungs-Regeln

- **MUSS [MUST]** `hacs.json` erzeugen/verifizieren, die mindestens `name` trägt; fürs ZIP-Modell `zip_release: true` **und** `filename: <domain>.zip` zusammen setzen (nur Integrationen); **SOLLTE [SHOULD]** `homeassistant` und `hide_default_branch: true` setzen, wenn Releases der einzige Kanal sind; **KANN [MAY]** `render_readme`, `hacs`, `country` setzen
- **MUSS [MUST]** verifizieren, dass `manifest.json:version` dem `v<MAJOR>.<MINOR>.<PATCH>`-Tag-Schema entspricht und die Pflichtfelder vorhanden sind (Feld-Detail an `ha/integration-manifest` delegiert)
- **MUSS [MUST]** angeben, dass HACS die Version aus dem zuletzt **veröffentlichten** Release-Tag liest, nicht aus `manifest.json:version`, und dass ein bloßer Tag ohne Release-Objekt ignoriert wird
- **MUSS [MUST]** die ZIP-Asset-CD-Pflicht (Build + Attach `<domain>.zip`) über einen `nolte/gh-plumbing`-Reusable verdrahten, wenn `zip_release`, und den Validierungs-Workflow an `ha-integration-ci-scaffold` delegieren
- **MUSS NICHT [MUST NOT]** die generischen `release-automation`-Regeln neu definieren; sie referenzieren und die `brands`-Registrierung als Checklist-Pointer auf `home-assistant/brands` ausweisen
- **MUSS [MUST]** HA-/HACS-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`; HACS-Publish-Regeln in `ha/hacs-release` verankert)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `hacs.json` ist valide; `zip_release` ist mit `filename` gepaart; `manifest.json:version` entspricht dem Tag-Schema; die ZIP-CD-Pflicht und das Validierungs-Gate sind verdrahtet oder benannt; `brands` ist ausgewiesen
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an die `ha/hacs-release`-Akzeptanzkriterien plus die geänderten Datei-Pfade anknüpft

### Verbote

- **MUSS NICHT [MUST NOT]** `zip_release` ohne `filename` setzen (oder umgekehrt)
- **MUSS NICHT [MUST NOT]** den generischen release-automation-Flow neu definieren oder duplizieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] `hacs.json` ist valide; `zip_release: true` ist mit `filename: <domain>.zip` fürs ZIP-Modell gepaart
- [ ] `manifest.json:version` entspricht dem `v<MAJOR>.<MINOR>.<PATCH>`-Tag-Schema
- [ ] Die Versionsquellen-Regel (veröffentlichter Release-Tag, nicht `manifest.json`) ist angegeben
- [ ] Die ZIP-Asset-CD-Pflicht ist über einen `nolte/gh-plumbing`-Reusable verdrahtet oder benannt; das Validierungs-Gate ist an `ha-integration-ci-scaffold` delegiert
- [ ] Die `brands`-Registrierung und die `release-automation`-Voraussetzungen sind ausgewiesen
- [ ] Der Bericht benennt die geänderten Datei-Pfade, verankert an `ha/hacs-release`

## Offene Fragen

- **Reusable-Abdeckung**: Liefert `nolte/gh-plumbing` bereits den ZIP-Asset-Build-Reusable, oder definiert dieser Skill die Pflicht und übergibt sie an einen Folge-Schritt? `ha/hacs-release` benennt die Reusable-Schicht.
- **Default-Branch-Distribution**: `distribution: default-branch` ist ein Fallback. Wann ist es je dem ZIP-Release vorzuziehen, wenn `hide_default_branch` der empfohlene Endzustand ist?
- **`brands`-Automatisierung**: Die `brands`-Registrierung ist ein PR an `home-assistant/brands`. Ist das für immer ein manueller Checklist-Punkt oder ein Kandidat für einen künftigen Skill?
