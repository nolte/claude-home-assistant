# Skill: `ha-pixoo-animation-author`

Status: draft

## Kontext

Animation auf dem Pixoo 64 ist Phasen-Mathematik, kein Video: eine Components-Page, deren Positionen `position = f(phase)` und deren Farben `color = f(phase)` innerhalb der Ramps der Spec sind, angetrieben von einer Automation, die die Phase weiterschaltet — geregelt in `spec/ha/pixoo-pixel-art-animation/de.md`. Handgebaute Animationen driften aus der Ramp-Disziplin oder vergessen die antreibende Automation ganz. Dieser Skill besitzt den Bewegungs-Schnitt der gerätespezifischen Pixoo-Familie.

## Scope

Ein beschriebener Bewegungs-/Effekt-Wunsch pro Aufruf, produziert die phasengetriebene Components-Page plus die antreibende Automation. Statische Art gehört `ha-pixoo-pixel-art-author`; Page-Arten ohne Bewegung `ha-pixoo-page-author`.

## Ziele

- Bewegung als explizite Phasen-Funktionen ausgedrückt, nie als Frame-für-Frame-Kopien
- Die antreibende Automation wird mit der Page geliefert — eine Animation ohne ihren Treiber ist ein unvollständiges Artefakt
- Ramp-konforme Farb-Animation; Koordinaten bleiben über den gesamten Phasen-Bereich innerhalb 64×64

## Nicht-Ziele

- Statische Art, nicht-animierte Pages, Multi-Artefakt-Pläne (`ha-pixoo-solution`), Device-Deploy

## Anforderungen

- **MUSS** vor der Komposition `spec/ha/pixoo-pixel-art-animation/de.md` lesen und Bewegung als `f(phase)`-Funktionen ausdrücken
- **MUSS** Koordinaten-Grenzen über den gesamten Phasen-Bereich verifizieren, nicht nur bei Phase 0
- **MUSS** beide Artefakte emittieren — die Components-Page und die phasen-schaltende Automation — und die Ziel-Device-Entity benennen
- **SOLLTE** die Automation gegen ein unavailable-Gerät guarden

## Akzeptanzkriterien

- [ ] Ein Lauf liefert die Page plus ihre antreibende Automation, beide schema-valide
- [ ] Grenzen halten über den vollen Phasen-Bereich; Farben bleiben in den Ramps
- [ ] Statik- oder Page-Art-Anfragen routen zum zuständigen Geschwister
