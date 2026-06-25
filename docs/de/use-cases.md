# Anwendungsfälle

Dieses Plugin bündelt Skills, Agents und Specs entlang von sechs Anwendungsfällen. Jeder Fall hat eine **Front-Door-Skill** (`*-solution`), die aus einer ergebnis-orientierten Anforderung die minimale Kombination an Artefakten plant und die fokussierten Skills aufruft — du musst nicht selbst wissen, welche Skill welches Artefakt erzeugt.

Den vollständigen, automatisch generierten Katalog mit Beschreibung jeder Skill und jedes Agents findest du unter [Skills](skills/index.md) und [Agents](agents/index.md).

!!! info "Front-Door vs. fokussierte Skills"
    Die `*-solution`-Skills **generieren nichts selbst** — sie planen (mit Freigabe-Gate) und dispatchen. Die fokussierten Skills besitzen je ein Artefakt und ihre eigene Spec-Konformanz. Du kannst eine fokussierte Skill auch direkt nutzen, wenn der Bedarf eindeutig ist.

---

## 1. Custom Integration bauen (Python)

Eine vollständige HACS-taugliche Custom Integration unter `custom_components/<domain>/` — vom Skelett bis zu fortgeschrittenen Plattform-Features.

- **Front-Door:** `ha-integration-solution`
- **Skelett:** `ha-integration-scaffold` (Manifest, Lifecycle, Config-Flow, Coordinator, Entity, Plattformen, Translations, Icons, Diagnostics, pytest-Harness)
- **Ergänzen / erweitern:** `ha-config-flow-augment`, `ha-coordinator-add`, `ha-entity-platform-add`, `ha-entity-description-mapper`, `ha-service-definition-generator`, `ha-diagnostics-augment`, `ha-discovery-augment`, `ha-bluetooth-augment`, `ha-oauth2-credentials-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-significant-change-add`, `ha-reproduce-state-add`, `ha-integration-events-add`, `ha-conversation-agent-augment`
- **Qualität:** `ha-translation-sync`, `ha-test-harness-augment`
- **Specs:** `spec/ha/integration-architecture`, `…/config-flow-patterns`, `…/coordinator-patterns`, `…/entity-architecture` und die übrigen `spec/ha/*`-Integration-Topics

## 2. Lovelace-Frontend bauen (TypeScript / JavaScript)

Custom-Frontend für Dashboards — Karten, Editoren, Features, Panels und ihre Backends.

- **Front-Door:** `ha-lovelace-solution`
- **Bausteine:** `ha-lovelace-card-scaffold` (Custom Card), `ha-card-editor-add` (visueller Config-Editor), `ha-card-features-add` (Tile-Features), `ha-badge-add` (Badge), `ha-strategy-add` (Dashboard-Strategie), `ha-panel-add` (Custom-Panel), `ha-websocket-command-add` (Python-WebSocket-Backend)
- **Specs:** `spec/ha/lovelace-card-patterns`, `…/lovelace-card-editor`, `…/lovelace-card-features`, `…/lovelace-badges`, `…/lovelace-strategies`, `…/lovelace-views-panels`, `…/frontend-websocket-commands`

## 3. Automations & Blueprints (YAML)

Automatisierungslogik und teilbare Blueprints für Home Assistant.

- **Front-Door:** `ha-automation-solution`
- **Bausteine:** `ha-automation-author` (Automation / Script / Scene / Template-Entity / Command-Artefakte), `ha-helper-scaffold` (zustandsbehaftete Helper), `ha-derived-sensor-author` (abgeleitete/statistische Sensoren), `ha-device-automation-add` (Device-Automations), `ha-blueprint-scaffold` (→ Agent `ha-blueprint-author` für den Draft)
- **Specs:** `spec/ha-automation/*` (Usage-Korpus), `spec/ha/blueprint-patterns`

## 4. Divoom-Pixoo-Display bauen

Aus einer Anforderung passende Darstellungen für die 64×64-LED-Matrix des Divoom Pixoo 64 erzeugen.

- **Front-Door:** `ha-pixoo-solution`
- **Bausteine:** `ha-pixoo-page-author` (Info-Pages: components / Special-Pages / native Pages), `ha-pixoo-pixel-art-author` (detaillierte Pixel-Art mit Schattierung & Konturen), `ha-pixoo-animation-author` (Bewegung & Farb-Animation)
- **Specs:** `spec/ha/divoom-pixoo` (Gerät & Integration), `spec/ha/pixoo-pixel-art` (Bildgestaltung), `spec/ha/pixoo-pixel-art-animation` (Animation)

## 5. Auf einer Dev-HA betreiben & testen

Eine Integration auf einer wegwerfbaren HA-Instanz im lokalen Kubernetes (Kind) ausrollen, prüfen und testen — getrennt von der Produktion.

- **Bausteine (Agents):** `ha-dev-instance-provision` (Dev-HA bereitstellen / abräumen), `ha-integration-deploy` (per `kubectl cp` ausrollen, `kill 1`-Neustart), `ha-integration-verify` (read-only Diagnose des Pods)
- **Skill:** `ha-test-harness-augment` (pytest-Abdeckung für sekundäre Code-Pfade)
- **Specs:** `spec/ha/dev-environment`, `spec/ha/dev-instance-provisioning`, `spec/ha/test-harness`

## 6. Vor dem Release prüfen & härten

Eine Integration vor PR / Release gegen Qualitäts- und Sicherheits-Standards prüfen.

- **Bausteine:** `ha-quality-scale-audit` (Quality-Scale-Tier), `ha-security-audit` (Security-Hardening), Agent `ha-integration-review` (gebündelter Whole-Picture-Review)
- **Specs:** `spec/ha/quality-scale`, `spec/ha/security-hardening`

---

## Noch nicht abgedeckt

ESPHome-Custom-Components und Home-Assistant-Add-ons (Docker / s6) sind als Anwendungsfälle vorgesehen, aber das Plugin liefert dafür bisher **keine** Skills. Der Tagline-Hinweis auf ESPHome / Add-ons beschreibt die Roadmap, nicht den aktuellen Stand.

## Wie alles zusammenhängt

- **Skills & Agents** sind die ausführenden Bausteine — Skills laufen interaktiv im Gespräch, Agents autonom mit strukturiertem Report.
- **Specs** unter `spec/` sind die Quelle der Wahrheit: `spec/ha/*` für HA-interne Verträge (gegen die offizielle HA-Doku verifiziert), `spec/claude/*` für die Skills/Agents selbst. Jede Skill und jeder Agent ist an seine Spec gebunden.
- **`*-solution`-Front-Doors** sind die empfohlene Einstiegsstelle pro Anwendungsfall, wenn mehr als ein Artefakt nötig ist.
