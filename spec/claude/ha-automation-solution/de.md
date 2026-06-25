# Skill: `ha-automation-solution`

Status: draft

## Kontext

Die drei Authoring-Skills `ha-automation-author`, `ha-helper-scaffold` und `ha-derived-sensor-author` (plus `ha-blueprint-scaffold`) erzeugen je **ein** Artefakt aus einer eng gefassten Absicht. Reale Anforderungen sind aber selten ein einzelnes Artefakt: „Tagesstromverbrauch der Wärmepumpe aufs Dashboard, plus Warnung bei > 10 kWh" ist eine Kette aus `integration` (Riemann) → `utility_meter` → `threshold`-Sensor → `automation`. Ein Nutzer, der die Skills nicht kennt, müsste diese Zerlegung selbst leisten — welche Integration, welcher Helfer, welche Reihenfolge, welche `entity_id` referenziert welche. Genau diese Mapping-Last soll der Nutzer nicht tragen.

Dieser Skill ist die **vorgelagerte Planungs- und Dispatch-Schicht**: Er nimmt eine unscharfe Anforderung, zerlegt sie in die minimale Kombination von Artefakten, legt die Abhängigkeits-Reihenfolge fest, bestätigt den Plan mit dem Nutzer und dispatcht dann die zuständigen Authoring-Skills nacheinander, wobei er die `entity_id`s früherer Schritte als Eingaben der späteren durchreicht. Er generiert **selbst kein** Artefakt — die Generierung und Spec-Konformität bleiben bei den Einzel-Skills.

## Scope

Planung und Orchestrierung über die `ha-automation/`-Skill-Familie plus `ha-blueprint-scaffold`. Eine Anforderung pro Lauf → ein Artefakt-Plan → N dispatchte Authoring-Aufrufe → ein Gesamt-Bericht. Der Skill entscheidet die *Kombination* (welche Artefakte, welcher Typ je Artefakt, welche Reihenfolge, welche Verdrahtung), nicht den Inhalt eines einzelnen Artefakts.

## Ziele

- Aus einer Prosa-Anforderung die richtige *Kombination* von Artefakten ableiten, ohne dass der Nutzer die Skill-Landschaft kennen muss
- Einen abarbeitbaren Artefakt-Plan in Abhängigkeits-Reihenfolge erstellen (pro Eintrag: Artefakt, Typ, zuständiger Skill, Abhängigkeit, Zweck) und vor jeder Generierung bestätigen lassen
- Die Einzel-Skills in korrekter Reihenfolge dispatchen und die `entity_id`s/Bezeichner früherer Artefakte als Eingaben der späteren durchreichen
- Anforderungen, die kein YAML-Artefakt, sondern eine Python-Custom-Integration verlangen (eigenes Geräte-/Cloud-Protokoll, Polling, Config-Flow), als solche erkennen und an `ha-integration-scaffold` verweisen statt sie in Helfer/Templates zu pressen
- Einen Gesamt-Bericht liefern, der alle erzeugten Dateien und ihre Verdrahtung benennt

## Nicht-Ziele

- Die Generierung eines einzelnen Artefakts samt Spec-Konformität — das bleibt bei `ha-automation-author`, `ha-helper-scaffold`, `ha-derived-sensor-author`, `ha-blueprint-scaffold`
- Das Scaffolding einer Python-Custom-Integration — das ist `ha-integration-scaffold` (der Skill erkennt nur, dass es nötig ist, und verweist)
- Deployment in eine laufende HA-Instanz — Generierung only
- Eine eigene Validierungs- oder Konformitäts-Logik — jeder dispatchte Skill validiert sein eigenes Artefakt; dieser Skill aggregiert nur die Berichte

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf zusammengesetzte, lösungsorientierte Anfragen aktivieren, bei denen der Nutzer das Ergebnis, nicht das Artefakt beschreibt:
  - „I want my heat pump's daily energy on the dashboard and an alert when it's high"
  - „set up presence-based lighting that only runs in the evening"
  - „baue mir eine Lösung, die …", „ich möchte, dass … (mehrteilig)", „richte … ein"
- **SOLLTE [SHOULD]** nicht aktivieren, wenn die Anforderung klar ein einzelnes Artefakt ist (dann greift direkt der zuständige Einzel-Skill); im Zweifel plant dieser Skill und schlägt einen Ein-Artefakt-Plan vor

### Eingaben

- **MUSS [MUST]** erfassen: `requirement` (Prosa, das gewünschte Ergebnis)
- **KANN [MAY]** erfassen: `target_dir` / `target_file`-Hinweise und bereits existierende `entity_id`s, die als Quellen dienen

### Pre-Flight

- **MUSS [MUST]** `requirement` als nichtleer prüfen; bei Unterspezifikation gezielt 1–3 Rückfragen stellen (welche Quell-Entity, welcher Schwellwert, welche Zeitfenster), bevor er plant
- **MUSS [MUST]** prüfen, ob die Anforderung eine Custom-Integration verlangt; wenn ja, das im Plan ausweisen und an `ha-integration-scaffold` verweisen statt es zu erzwingen

### Zerlegungs-Heuristik (Anforderung → Artefakt-Typ → Skill)

- **MUSS [MUST]** einen gemessenen oder abgeleiteten Wert (Rate, Glättung, Integral, Aggregat, Schwelle, Trend, Verbrauchsperiode, Wahrscheinlichkeit) auf `ha-derived-sensor-author` abbilden
- **MUSS [MUST]** einen manuell/per Automation gehaltenen Zustand, Modus-Schalter, Countdown oder Wochenplan auf `ha-helper-scaffold` abbilden
- **MUSS [MUST]** Event→Aktion-Logik auf `ha-automation-author` (`automation`) und wiederverwendbare manuell aufrufbare Aktionssequenzen auf `script` abbilden; einen HTTP-/Shell-/Python-Escape-Hatch auf das jeweilige Command-Artefakt von `ha-automation-author`
- **SOLLTE [SHOULD]** ein wiederverwendbares, parametrisiertes, teilbares Muster auf `ha-blueprint-scaffold` abbilden statt auf eine fest verdrahtete `automation`
- **MUSS [MUST]** die Artefakte minimal halten — keine Helfer/Sensoren erzeugen, die ein einzelnes Artefakt bereits abdeckt

### Plan & Dispatch

- **MUSS [MUST]** vor jeder Generierung einen Artefakt-Plan als Tabelle in Abhängigkeits-Reihenfolge präsentieren: pro Eintrag `#`, Artefakt-Name/`entity_id`, Typ, zuständiger Skill, Abhängigkeit (`depends-on`), Zweck — und explizite Bestätigung abwarten
- **MUSS NICHT [MUST NOT]** ein Artefakt selbst inline generieren; jede Generierung läuft über den zuständigen Einzel-Skill
- **MUSS [MUST]** die Skills in Abhängigkeits-Reihenfolge dispatchen und die in einem Schritt erzeugten `entity_id`s/Bezeichner als Eingaben der abhängigen Schritte durchreichen
- **MUSS [MUST]** abbrechen und zurückmelden, wenn ein dispatchter Skill einen NEEDS-WORK-Bericht liefert, statt auf einem unfertigen Vorgänger-Artefakt weiterzubauen
- **MUSS [MUST]** alle Bezeichner über die Artefakte hinweg konsistent nach `ha/naming-conventions` halten und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Gesamt-Bericht

- **MUSS [MUST]** am Ende jeden erzeugten Datei-Pfad, das zugehörige Artefakt und die Verdrahtung (welche `entity_id` welche referenziert) auflisten
- **MUSS [MUST]** die aggregierten CONFORMANT / NEEDS-WORK-Berichte der Einzel-Skills weiterreichen, ohne sie neu zu bewerten

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Anforderung pro Lauf orchestrieren
- **MUSS NICHT [MUST NOT]** einen Plan ohne Nutzer-Bestätigung ausführen
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill erfragt fehlende Eckdaten (Quelle, Schwellwert, Zeitfenster), bevor er plant
- [ ] Skill präsentiert einen Artefakt-Plan in Abhängigkeits-Reihenfolge und wartet auf Bestätigung
- [ ] Skill dispatcht die zuständigen Einzel-Skills statt selbst zu generieren
- [ ] `entity_id`s früherer Artefakte werden als Eingaben der abhängigen Schritte durchgereicht
- [ ] Eine Custom-Integration-Anforderung wird erkannt und an `ha-integration-scaffold` verwiesen
- [ ] Abbruch bei einem NEEDS-WORK-Vorgänger statt Weiterbau
- [ ] Gesamt-Bericht listet alle Dateien und die Verdrahtung und reicht die Einzel-Berichte weiter

## Offene Fragen

- **Agent- vs. Skill-Dispatch**: Sollen die Einzel-Schritte als Skills (sichtbar, sequentiell) oder über einen Generierungs-Agent (isoliert, parallel) ausgeführt werden? Aktuell Skill-Dispatch, weil die Plan-Bestätigung und die `entity_id`-Verdrahtung im Nutzer-Kontext sichtbar bleiben sollen.
- **Plan-Persistenz**: Soll der Artefakt-Plan als Datei (z. B. unter `.plans/`) persistiert werden, damit ein unterbrochener Lauf fortsetzbar ist? Aktuell in-conversation.
- **Bestehende-Config-Awareness**: Soll der Skill die vorhandene HA-Config einlesen, um Quell-`entity_id`s vorzuschlagen und Kollisionen früh zu erkennen? Aktuell vom Nutzer benannt.
- **Grenze zu Blueprints**: Wann ist ein wiederverwendbares Muster ein Blueprint und wann eine instanzierte Kombination? Heuristik vorhanden (teilbar/parametrisiert → Blueprint), aber der Grenzfall „einmal, aber generisch" bleibt eine Ermessensfrage.
