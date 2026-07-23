# Skill: `ha-pixoo-pixel-art-author`

Status: draft

## Kontext

Detaillierte 64×64-Pixel-Art für den Pixoo 64 hat gemäß `spec/ha/pixoo-pixel-art/de.md` zwei legitime Bau-Pfade: eine prozedurale Component-Liste (rectangle/templatable, per-Pixel, optional data-driven), gerendert von der Integration, oder einen präzisen Bauplan für ein exakt 64×64 großes PNG. Beide stehen und fallen mit Palette-Disziplin, Silhouette-first-Konstruktion und Koordinaten-Exaktheit. Dieser Skill besitzt den Statik-Art-Schnitt der gerätespezifischen Pixoo-Familie.

## Scope

Ein Motiv pro Aufruf, ein gewählter Bau-Pfad, Output entweder die Component-Liste oder der PNG-Bauplan. Bewegung gehört `ha-pixoo-animation-author`; Page-Einbettung `ha-pixoo-page-author`.

## Ziele

- Bewusste Pfadwahl (prozedural versus PNG-Plan) mit benannten Kriterien gemäß Grounding-Spec
- Silhouette-first-Konstruktion mit den Palette-Ramps der Spec; keine matschigen Anti-Aliasing-Artefakte
- Data-driven Art bleibt templatable, wo das Motiv es verlangt

## Nicht-Ziele

- Animation (`ha-pixoo-animation-author`), Page-Komposition (`ha-pixoo-page-author`), mehrere Artefakte umfassende Pläne (`ha-pixoo-solution`), Rendern/Hochladen aufs Gerät

## Anforderungen

- **MUSS** vor dem Zeichnen `spec/ha/pixoo-pixel-art/de.md` lesen und den Bau-Pfad mit benannter Begründung wählen
- **MUSS** jede Koordinate innerhalb 64×64 und jede Farbe innerhalb der Ramp-Disziplin der Spec halten
- **MUSS** auf dem prozeduralen Pfad Components emittieren, die das `divoom_pixoo`-Schema akzeptiert; auf dem PNG-Pfad einen Plan, der die Art pixel-exakt reproduzierbar macht
- **SOLLTE** die templatable Variante vorschlagen, wenn das Motiv state-getrieben ist

## Akzeptanzkriterien

- [ ] Ein Lauf liefert genau ein Artefakt (Component-Liste oder PNG-Plan) mit Pfad-Begründung
- [ ] Palette- und Koordinaten-Checks bestehen gegen die Grounding-Spec
- [ ] Bewegungs- oder Page-Einbettungs-Anfragen routen zum zuständigen Geschwister
