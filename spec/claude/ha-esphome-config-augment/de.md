# Skill: `ha-esphome-config-augment`

Status: draft

## Kontext

Geschwister von `ha-esphome-config-scaffold` im Device-YAML-Schnitt der ESPHome-Achse (Audit-Entscheid 2026-07; Fixture `nolte/esphome-configs`). Wo der Scaffold die Greenfield-Datei besitzt, besitzt dieser Skill den deutlich häufigeren Fall: ein weiterer Sensor, Bus, Component-Binding oder eine Shared-Package-Adoption in einer bereits existierenden Device-Datei — die multiplexten I²C-Topologien des Fixtures zeigen, warum ein geratenes Bus-Binding on-device teuer ist und die Ergänzung einen interaktiven, spec-verankerten Skill verdient.

## Scope

Eine Ergänzung an einer bestehenden Device-Datei pro Aufruf, gemäß `spec/ha/esphome-config-patterns/de.md`. Legacy-Merge-Key-Includes in der Datei werden toleriert, aber nie erweitert; Duplikation von Shared-Package-Inhalt wird verweigert.

## Ziele

- Ein Einstiegspunkt fürs Erweitern eines Geräts (`/claude-home-assistant:ha-esphome-config-augment`)
- Schema-Verifikation gegen die offiziellen ESPHome-Docs vor jedem Write
- Explizites Bus-Binding auf multiplexten Topologien; substitution-abgeleitetes Naming bleibt erhalten
- Verweigerung, zu duplizieren, was ein Shared Package schon liefert — stattdessen wird Package-Adoption angeboten

## Nicht-Ziele

- Neue Device-Dateien (`ha-esphome-config-scaffold`), Component-Authoring, Add-ons, Compile/Flash/Deploy
- HA-seitige Konsumtion der neuen Entities (Automation-/Lovelace-Familien)

## Anforderungen

- **MUSS** vor der Komposition die Grounding-Spec, die Ziel-Device-Datei und jede eingebundene Shared-Datei lesen
- **MUSS** den Duplikat-Check ausführen (gleiche Plattform + Adresse/Bus, lokal oder via Package) und Duplikate verweigern
- **MUSS** das Component-Schema gemäß `spec/ha/upstream-docs-verification` upstream verifizieren; deprecated Keys sind Findings, nie Output
- **MUSS** neue I2C-Blöcke auf multiplexten Topologien an eine benannte `bus_id` binden und die Wahl mit dem Operator bestätigen
- **MUSS** Naming substitution-abgeleitet und Credentials als reportete `!secret`-Referenzen halten
- **DARF NICHT** `<<: !include`-Merge-Keys einführen oder erweitern, andere Device-Dateien editieren oder mehr als eine Ergänzung pro Lauf vornehmen
- **SOLLTE** `esphome config <file>`-Validierung anbieten, wenn die Toolchain vorhanden ist

## Akzeptanzkriterien

- [ ] Ein Augment-Lauf auf einem fixture-artigen Multiplex-Gerät bindet den neuen Block an einen explizit benannten Kanal-Bus
- [ ] Die Anforderung eines Blocks, den ein Shared Package schon liefert, wird unter Nennung des Packages verweigert
- [ ] Die Diff-Zusammenfassung benennt jeden neuen `!secret`-Key und lässt unbeteiligte Blöcke byte-identisch

## Offene Fragen

_Derzeit keine._
