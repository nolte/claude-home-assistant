# Skill: `ha-dev-workflow-apply`

Status: draft

## Kontext

`spec/ha/dev-workflow` bündelt den HA-Coding-Workflow — Code-Stil (Ruff-Format, geordnete Imports, alphabetische Konstanten/Listen, f-Strings), strikte Typisierung (`from __future__ import annotations`, vollständige Annotationen, mypy, das `.strict-typing`-Opt-in) und Validierung (`hassfest`, voluptuous-Config-Validierung) — in eine erzwingbare Verpflichtung. Bislang hatte er **keinen zuständigen Skill**: Der Platinum-Tier von `ha-integration-solution` löste sich in einen bloßen `ha/dev-workflow`-Checklistenpunkt auf, und die lokale Strict-Typing-Pflicht war von nichts implementiert. Dieser Skill schließt die Spec-vs-Skill-Lücke: Er wendet die MUST-Regeln der Spec auf eine bestehende Custom-Integration an und berichtet die Konformität, und ist der Skill, den `ha-integration-solution` für `target_tier: platinum` dispatcht, statt einen Checklistenpunkt anzuzeigen.

## Scope

Anwenden und Validieren der `spec/ha/dev-workflow`-MUST-Regeln gegen eine bestehende Custom-Integration unter `custom_components/<domain>/`, nach einem Ziel-Tier gestaffelt (Stil + `hassfest` als Bronze-Untergrenze, strikte Typisierung als Platinum-Brücke). Es ist das Apply-/Validate-Gegenstück zum read-only `ha-quality-scale-audit`. Eine Integration pro Lauf → mechanische Fixes angewendet (oder ein Dry-Run-Diff) → ein CONFORMANT- / NEEDS-WORK-Bericht.

## Ziele

- HA-Code-Stil anwenden (PEP8/PEP257, `ruff format`, geordnete Imports, alphabetische Konstanten/Listen, f-Strings mit der Logging-Ausnahme, Header-Docstrings)
- Die Strict-Typing-Brücke für Platinum anwenden — vollständige Annotationen, `from __future__ import annotations`, ein lokales mypy-Strict-Profil als Standalone-Gegenstück zu Cores `.strict-typing` und ein sauberer mypy-Lauf
- Die verfügbare `hassfest`-Variante ausführen und die Integration so formen, dass sie besteht (Manifest, Strings, Services)
- Voluptuous-Config-Validierung für YAML-konfigurierbare Plattformen anwenden (`const.py`-Konstanten, `required` vor `optional`, gültige Defaults)
- Einen CONFORMANT- / NEEDS-WORK-Bericht ausgeben, verankert an den Akzeptanzkriterien von `spec/ha/dev-workflow`
- Von `ha-integration-solution` für den Platinum-Tier dispatchbar sein

## Nicht-Ziele

- Die read-only Quality-Scale-Tier-Bewertung — `ha-quality-scale-audit`
- Security-Härtung — `ha-security-audit`
- Die pytest-Harness (Fixtures, `MockConfigEntry`, Snapshot-Tests, Coverage) — `ha-test-harness-augment` / `ha/test-harness`
- Devcontainer- / Kind- / `script/setup`- / venv-Setup — `ha/dev-environment`
- Async- / Event-Loop-Patterns — `ha/async-patterns`
- Manifest-Schema-Authoring im Detail — `ha/integration-manifest`; dieser Skill verlangt nur, dass `hassfest` es validiert
- Deployment / Verifikation gegen eine laufende HA-Instanz — die `ha-integration-deployer`- / `ha-integration-verifier`-Agenten

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** bei Anfragen aktivieren, den HA-Dev-Workflow auf einer bestehenden Integration anzuwenden oder zu erzwingen:
  - „wende den HA-Dev-Workflow an", „erzwinge HA-Code-Stil"
  - „mach diese Integration strict-typing- / platinum-tauglich"
  - „führe ruff + mypy strict + hassfest auf meiner Integration aus"
  - „apply the HA dev workflow", „make this integration platinum-ready"
- **SOLLTE [SHOULD]** nicht bei einem read-only Tier-Check (`ha-quality-scale-audit`), einem Security-Audit (`ha-security-audit`) oder Test-Authoring (`ha-test-harness-augment`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root mit `custom_components/<domain>/`)
- **KANN [MAY]** erfassen: `target_tier` (Default `bronze`; `platinum` aktiviert den Strict-Typing-Pass) und `apply` (Default `true`; `false` = nur Dry-Run-Bericht)

### Pre-Flight

- **MUSS [MUST]** bestätigen, dass `target_dir` ein Git-Work-Tree ist und `custom_components/<domain>/manifest.json` existiert (`domain` lesen)
- **MUSS [MUST]** verfügbares Tooling erkennen (`ruff`, `mypy`, einen `hassfest`-Pfad) und ein fehlendes Tool für den Bericht vermerken, statt still zu scheitern

### Apply-Regeln

- **MUSS [MUST]** die Bronze-Untergrenze-Stil-Regeln immer anwenden: `ruff format`, Ruff-Import-Ordnung, alphabetische Konstanten/Listen, f-Strings (Logging behält Prozent-Formatierung), Header-Docstrings
- **MUSS [MUST]** den Strict-Typing-Pass nur anwenden, wenn `target_tier` `platinum` ist (oder explizit gewünscht): `from __future__ import annotations`, vollständige Annotationen, ein `[tool.mypy]`-Strict-Profil in `pyproject.toml` mit Scope auf `custom_components.<domain>` (das Standalone-`.strict-typing`-Gegenstück) und ein mypy-Lauf, dessen Rest-Fehler zu NEEDS-WORK-Punkten werden
- **MUSS [MUST]** `assert`-basierte Typ-Einengung ausschließlich in `if TYPE_CHECKING:`-Blöcken halten
- **MUSS [MUST]** die verfügbare `hassfest`-Variante ausführen (die `home-assistant/actions`-hassfest-Action, ein vendored `hassfest` oder den Pre-Commit-Hook) und die Integration formen, bis sie besteht; ist keine Variante verfügbar, dies als NEEDS-WORK-Lücke vermerken, statt still zu überspringen
- **MUSS [MUST]** voluptuous-Config-Validierung für YAML-konfigurierbare Plattformen anwenden, mit `const.py`-Konstanten, `required` vor `optional` und gültigen Nicht-`None`-Defaults für `cv.string`
- **MUSS NICHT [MUST NOT]** Secrets loggen und **MUSS NICHT [MUST NOT]** Setup-Mechanik, die pytest-Harness oder Async-Patterns hineinfalten — die Schwester-Spec per Slug referenzieren und stoppen
- **MUSS [MUST]** HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Berichtsformat

- **MUSS [MUST]** mit einem CONFORMANT- / NEEDS-WORK-Bericht als Tabelle abschließen, verankert an den Akzeptanzkriterien von `spec/ha/dev-workflow`, plus einem einzeiligen Verdikt
- **MUSS [MUST]** für jeden NEEDS-WORK-Punkt die konkrete verbleibende Aktion benennen (file:line oder das fehlende Artefakt/Tool)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Integration pro Lauf verarbeiten
- **MUSS NICHT [MUST NOT]** den Strict-Typing-Pass unterhalb des Platinum-Tiers anwenden, außer explizit gewünscht
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Wendet die Bronze-Untergrenze-Stil-Regeln an (ruff format, geordnete Imports, sortierte Konstanten/Listen, f-Strings mit Logging-Ausnahme, Header-Docstrings)
- [ ] Wendet für Platinum die Strict-Typing-Brücke an (Annotationen, `from __future__ import annotations`, lokales mypy-Strict-Profil, mypy-Lauf) und verschiebt `assert`-Einengung in `if TYPE_CHECKING:`
- [ ] Führt die verfügbare `hassfest`-Variante aus und vermerkt eine fehlende Variante als NEEDS-WORK-Lücke
- [ ] Wendet voluptuous-Config-Validierung für YAML-konfigurierbare Plattformen an
- [ ] Gibt einen CONFORMANT- / NEEDS-WORK-Bericht aus, verankert an den `spec/ha/dev-workflow`-Akzeptanzkriterien, mit einer konkreten Aktion je NEEDS-WORK-Punkt
- [ ] `ha-integration-solution` dispatcht diesen Skill für `target_tier: platinum`, statt einen Checklistenpunkt anzuzeigen

## Offene Fragen

- **`.strict-typing`-Gegenstück**: Die Core-`.strict-typing`-Datei ist außerhalb von Core nicht verfügbar, daher nutzt dieser Skill ein `pyproject.toml`-`[tool.mypy]`-Strict-Profil mit Scope auf das Integrations-Paket. Sollte dieses Snippet normativ in `spec/ha/dev-workflow` (dessen offene Frage) gepinnt und hier nur konsumiert werden?
- **`hassfest`-Varianten-Präferenz**: Action vs. vendored vs. Pre-Commit — die portfolioweit bevorzugte Variante ist in `spec/ha/dev-workflow` noch offen; dieser Skill führt die vorhandene aus und meldet sonst eine Lücke.
- **`apply: false`-Umfang**: Soll der Dry-Run-Modus mypy/hassfest weiterhin (read-only) ausführen, um den Bericht zu füllen, oder nur die Stil-Diffs berechnen? Aktuell führt er die read-only Checks aus und listet die Stil-Diffs, ohne zu schreiben.
