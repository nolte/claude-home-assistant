# Skill: `ha-esphome-solution`

Status: draft

## Kontext

Jede andere Home-Assistant-Domäne dieses Plugins hat eine Eingangstür; ESPHome hatte keine. Die Routing-Tabelle von `ha-solution` belegt die Lücke: Sie leitet eine ESPHome-Geräteanfrage direkt an zwei Einzel-Skills weiter und verweist für Repository-Struktur, HA-getriebene Inhalte und die BOX-Familie auf Specs ganz ohne zuständigen Skill. Da die ESPHome-Familie nun Struktur, Geräte, Bindings, Rendering, Voice und CI abdeckt, ist ein Router das, was dem Operator erspart zu wissen, welcher davon was erzeugt.

Dieser Skill ist das strukturelle Gegenstück zu `ha-integration-solution`, `ha-lovelace-solution`, `ha-automation-solution` und `ha-pixoo-solution` und bezieht eine bewusste Position, die jene nicht einheitlich teilen: Die Review-Schicht bleibt außerhalb des Erzeugungslaufs.

## Scope

Eine Anforderung pro Aufruf. Klassifikation, ein abhängigkeitsgeordneter Artefakt-Plan, Freigabe, Dispatch der zuständigen `ha-esphome-*`-Skills, Identitäts-Threading und ein Gesamtbericht. Nur Generierung; ein optionaler, separat gegateter Review-Durchlauf kann folgen.

## Ziele

- Ein auffindbarer Einstiegspunkt für ein ESPHome-Ergebnis, gleich welche Artefakt-Kombination es braucht
- Ein Plan, den der Operator vor jeder Generierung freigibt — in Abhängigkeitsreihenfolge und mit benannten durchgereichten Identitäten
- Struktur vor Gerät: Ein Repository ohne Fleet-Layout bekommt eines vor seinem ersten Device-File
- Dispatch, der aus dem lebenden Skill-Inventar aufgelöst wird, sodass die Familie wachsen kann, ohne diesen Skill zu ändern
- Eine Review-Schicht, die vom Verfassen unabhängig bleibt, sodass ein erzeugtes Artefakt nie von dem Lauf beurteilt wird, der es erzeugt hat

## Nicht-Ziele

- Jegliche Inline-Generierung — jedes Artefakt gehört seinem zuständigen Skill
- Custom Components in C++/Python — kein zuständiger Skill; die Grounding-Specs verorten deren Erstellung auf einer späteren Achse
- Home-Assistant-Integrationen, Cards, Automationen und die Pixoo-Familie — die Geschwister-`*-solution`-Skills
- Compile, Flash und Fleet-OTA-Rollout, in jedem Modus
- Das Review-Urteil selbst — das gehört den beiden Reviewer-Agents

## Anforderungen

- **MUSS** ausschließlich klassifizieren und dispatchen; **DARF NICHT** inline generieren
- **MUSS** zuständige Skills zur Laufzeit aus dem lebenden `ha-esphome-*`-Inventar auflösen statt aus einer eingefrorenen Namensliste, auf die Anker-Tabelle nur zurückfallen, wenn das Inventar wirklich nicht ermittelbar ist, und das dann benennen
- **MUSS** den abhängigkeitsgeordneten Artefakt-Plan vorlegen und auf explizite Freigabe warten, bevor irgendetwas dispatcht wird
- **MUSS** zuerst die Anforderungs-Konfidenz einschätzen und unterhalb der Schwelle `requirements-elicit` dispatchen (oder einen gleichwertigen strukturierten Fragepfad, wenn dieser Skill nicht verfügbar ist), statt eine unscharfe Anforderung zu zerlegen
- **MUSS** Struktur vor Geräten planen: Wo kein Fleet-Layout existiert, steht `ha-esphome-fleet-scaffold` vor jedem Device-File
- **MUSS** die von früheren Schritten erzeugten Identitäten — die Substitutionen `name` / `id` / `comment`, die Per-Device-API-Key-Variable, Package-Namen und -Parameter, Home-Assistant-`entity_id`s und die ID des Redraw-Skripts — in die Inputs abhängiger Schritte durchreichen
- **MUSS** bei einem NEEDS-WORK-Ergebnis stoppen und berichten, statt einen abhängigen Schritt auf einem unfertigen Vorgänger aufzusetzen
- **MUSS** den Bericht jedes dispatchten Skills wortgetreu weitergeben, ohne ihn neu zu bewerten
- **DARF NICHT** ein Review als Teil des Erzeugungslaufs ausführen, **DARF NICHT** ein Reviewer-Urteil als eigenes Abnahme-Gate behandeln und **MUSS** auf die unabhängigen Reviewer-Agents als Operator-Folgeschritt verweisen
- **DARF** den Review-Durchlauf ausführen, wenn `review_ready` gesetzt ist, und **MUSS** dann eine zweite, vom Plan-Gate getrennte explizite Freigabe verlangen, **MUSS** jedes Finding an den zuständigen Skill zurückrouten statt es inline anzuwenden, und **MUSS** den Reviewer nach einer Korrektur erneut laufen lassen, statt das Finding für erledigt zu erklären
- **DARF NICHT** in irgendeinem Modus kompilieren, flashen oder ausrollen
- **MUSS** ESPHome-Fakten gegen die offizielle ESPHome-Dokumentation und Home-Assistant-seitige Fakten gegen die offizielle Home-Assistant-Dokumentation gemäß `spec/ha/upstream-docs-verification` verifizieren
- **MUSS** Resume gemäß `spec/claude/resumable-work/` unterstützen und den freigegebenen Plan samt Dispatch-Status je Schritt als Checkpoint sichern

## Akzeptanzkriterien

- [ ] Eine Ein-Artefakt-Anforderung wird an den zuständigen Skill geleitet statt in einen Plan zerlegt
- [ ] Ein Lauf gegen ein Repository ohne Fleet-Layout plant `ha-esphome-fleet-scaffold` als Schritt 0
- [ ] Vor der expliziten Plan-Freigabe findet keine Generierung statt
- [ ] Der Standard-Lauf endet, ohne einen Reviewer zu dispatchen, und nennt beide Reviewer-Agents als Folgeschritte
- [ ] Ein `review_ready`-Lauf gatet das Review separat und routet Findings an zuständige Skills, statt sie anzuwenden

## Offene Fragen

- Ob die ESPHome-Familie nach dem Drei-Plugin-Split einen eigenen Router behält oder der eine beworbene Router des `ha-esphome`-Plugins ihn aufnimmt, entscheidet jener Umbau (Anforderung R3), nicht diese Spec.
