# Skill: `ha-pixoo-page-author`

Status: draft

## Kontext

Der Divoom Pixoo 64 rendert, was die `pages_data`-Liste der `divoom_pixoo`-Integration deklariert — Components-Pages (text/image/rectangle/templatable), Special-Pages (PV/progress_bar/fuel) und Native-Pages (channel/clock/gif/visualizer), jede mit eigenem Key-Schema und 64×64-Koordinaten-Disziplin gemäß `spec/ha/divoom-pixoo/de.md`. Handgeschriebene Pages laden zu Off-by-one-Layout-Fehlern und Schema-Drift ein. Dieser Skill ist der Einzelseiten-Authoring-Einstieg der gerätespezifischen Pixoo-Familie (eine optionale Familie, keine allgemeine HA-Domäne).

## Scope

Genau eine Page pro Aufruf, als spec-konformes YAML für die `pages_data`-Liste, aus einem beschriebenen Informationsbedarf. Statische Pixel-Art gehört `ha-pixoo-pixel-art-author`; Bewegung gehört `ha-pixoo-animation-author`; Multi-Artefakt-Kombinationen laufen über `ha-pixoo-solution`.

## Ziele

- Ein auffindbarer Einstieg für „zeig X auf dem Pixoo", der die Page-Art (components/special/native) bewusst wählt
- Template-getriebene dynamische Werte gegen reale Entity-States verdrahtet, geguardet gegen unavailable-States
- 64×64-Layout-Disziplin: verifizierte Koordinaten, kein abgeschnittener Text, Palette gemäß Grounding-Spec

## Nicht-Ziele

- Detaillierte Pixel-Art (`ha-pixoo-pixel-art-author`), Animation (`ha-pixoo-animation-author`), Multi-Page-Pläne (`ha-pixoo-solution`), Device-Deploy

## Anforderungen

- **MUSS** vor der Komposition `spec/ha/divoom-pixoo/de.md` lesen und die Page-Art mit benannter Begründung wählen
- **MUSS** jeden Page-Key gegen das dokumentierte Schema der Integration verifizieren; unbekannte Keys sind Findings, nie Output
- **MUSS** jedes Template gegen unavailable/unknown-States guarden und Koordinaten innerhalb 64×64 halten
- **MUSS** genau einen Page-Eintrag emittieren, paste-fertig für `pages_data`, und die Ziel-Device-Entity benennen
- **SOLLTE** an die Geschwister-Skills übergeben, wenn die Anfrage eigentlich Art, Bewegung oder eine Kombination ist

## Akzeptanzkriterien

- [ ] Ein Lauf liefert einen schema-validen Page-Eintrag mit Art-Begründung und geguardeten Templates
- [ ] Koordinaten-/Palette-Checks bestehen gegen die Grounding-Spec
- [ ] Art-/Bewegungs-/Kombinations-Anfragen werden an das zuständige Geschwister geroutet statt hier halb bedient
