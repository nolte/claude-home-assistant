# HA-Gerät: Pixel-Art auf der 64×64-Matrix (Schattierung & Konturen)

Status: draft

## Kontext

Der Divoom Pixoo 64 ist eine **64×64-RGB-LED-Matrix** (4096 Pixel, voller 24-Bit-Farbraum). Diese Spec normiert das **Gestalten von Informationen als Pixel-Art** auf dieser Fläche — mit dem Ziel, möglichst detaillierte, lesbare Bilder zu erzeugen. Schwerpunkt sind die beiden Handwerks-Dimensionen, nach denen explizit gefragt wurde: **Konturen** (Outlining) und **Schattierung** (Shading), eingebettet in Palette, Anti-Aliasing, Dithering und die Besonderheiten eines selbstleuchtenden LED-Panels.

Die Spec ist **liefer-pfad-neutral**: Der gestalterische Kern (Palette, Konturen, Schattierung, Dithering) gilt unabhängig davon, ob das Bild als **vorgerendertes PNG** (über die `image`-Komponente) oder **prozedural** (über `rectangle`/`templatable`-Komponenten, per-Pixel aus Entity-States) aufs Display kommt. Beide Wege werden als Anwendungs-Abschnitte referenziert.

Abgrenzung: Die Geräte-/Integrations-Mechanik (Anschluss, Entitäten, Page-Typen, Service-Aufrufe, Resample-Modi der `image`-Komponente) liegt in `ha/divoom-pixoo`. Diese Spec setzt darauf auf und behandelt **was** auf die Matrix gezeichnet wird und **wie es gut aussieht**, nicht **wie** es technisch übertragen wird.

Primärquellen für das Handwerk: Arne Niklas Janssons Pixel-Art-Tutorial ([androidarts.com/pixtut](https://androidarts.com/pixtut/pixelart.htm)), die Lospec-Tutorials ([lospec.com](https://lospec.com/pixel-art-tutorials)) und etablierte Pixel-Art-Farblehre (Ramps, Hue-Shifting). Render-/Hardware-Constraints sind gegen den Integrations-Code (`pixoo64/_pixoo.py`, `sensor.py`) von `gickowtf/pixoo-homeassistant` v1.23.0 verifiziert.

## Ziele

- Die Hardware-/Render-Constraints der 64×64-LED-Matrix als verbindlichen Rahmen für Pixel-Art festschreiben
- Eine **begrenzte, ramp-basierte Palette** mit Hue-Shifting als Grundlage für Schattierung vorgeben
- **Konturen** normieren: selektives Outlining, Innen- vs. Außenkontur, schwarze vs. farbige Linien
- **Schattierung** normieren: konsistente Lichtquelle, Schattierungs-Ramps, Terminator, Vermeidung von Pillow-Shading
- **Anti-Aliasing** und **Dithering** als dosierte Werkzeuge mit LED-Matrix-spezifischen Grenzen regeln
- Typische Fehler (Banding, Jaggies, Pillow-Shading) explizit ausschließen
- Die zwei Liefer-Pfade (exaktes 64×64-PNG mit `nearest`-Resampling; prozedurale Komponenten) an `ha/divoom-pixoo` anbinden

## Nicht-Ziele

- Geräte-/Integrations-Mechanik (Anschluss, Config-Flow, Entitäten, Service-Parameter, Page-Typen) — gehört zu `ha/divoom-pixoo`
- Animation/Timing über mehrere Frames (GIF-Sequenzen, Page-Rotation) jenseits einzelner Standbilder
- Typografie/Font-Rendering der `text`-Komponente im Detail (Font-Katalog liegt in `ha/divoom-pixoo`); diese Spec behandelt Text nur, soweit er als Grafikelement Kontur/Kontrast braucht
- Ein konkreter, projekt-fester Paletten-Katalog — die Spec gibt Palette-**Regeln** vor, nicht eine fixe Farbliste
- Tooling-Empfehlungen (Aseprite, Pixelorama o. Ä.) — werkzeug-neutral

## Anforderungen

### Canvas & Hardware-Constraints

- **MUSS [MUST]** das Bild auf dem **64×64-Raster** mit Ursprung oben-links (Koordinaten 0…63) gestalten; jeder Pixel ist eine bewusste Entscheidung — bei nur 4096 Pixeln ist das Detailbudget knapp
- **MUSS [MUST]** akzeptieren, dass das Panel **selbstleuchtend** ist: Farben wirken kräftiger/heller als auf einem Monitor, der Schwarzpunkt ist echtes Aus (Pixel dunkel = unsichtbar), und benachbarte helle/dunkle Pixel kontrastieren stark
- **SOLLTE [SHOULD]** **hohen Kontrast und klare Silhouetten** priorisieren; feine Tonwert-Nuancen, die auf einem Monitor funktionieren, verschwimmen auf der LED-Matrix aus Betrachtungsdistanz
- **SOLLTE [SHOULD]** **1-px-Details sparsam** einsetzen — einzelne isolierte Pixel und 1-px-Linien können auf dem LED-Gitter „blühen"/verschwimmen oder im Kontrast untergehen; tragende Formen mindestens 2 px breit anlegen
- **MUSS [MUST]** den vollen RGB-Farbraum als gegeben, aber **nicht als Lizenz zum Wildmischen** behandeln — die Lesbarkeit kommt aus einer disziplinierten Palette (siehe nächste Sektion), nicht aus Farbreichtum

### Palette & Farb-Ramps

- **MUSS [MUST]** mit einer **begrenzten Palette** arbeiten; eine kleine, bewusst gewählte Farbmenge erzwingt Klarheit und Kohärenz besser als freies 24-Bit-Mischen
- **MUSS [MUST]** Schattierung über **Farb-Ramps** definieren — pro Material/Objekt eine geordnete Reihe von Schatten → Mittelton → Licht (typisch 3–5 Werte)
- **SOLLTE [SHOULD]** **voll gesättigte Farben** nur als Akzente einsetzen; leicht entsättigte Töne erhöhen die Lesbarkeit und vermeiden „Neon"-Flimmern auf der LED-Matrix
- **SOLLTE [SHOULD]** Ramps zwischen Materialien **teilen**, wo möglich, statt für jedes Objekt eine eigene Ramp zu erfinden — das hält die Gesamtpalette klein und kohärent
- **SOLLTE [SHOULD]** Tonwerte (Value/Helligkeit) so spreizen, dass die Silhouette **allein anhand der Helligkeit** lesbar bleibt (Test: in Graustufen prüfen)

### Hue-Shifting

- **SOLLTE [SHOULD]** beim Abdunkeln/Aufhellen **die Farbe nicht nur in Richtung Schwarz/Weiß** ziehen, sondern den **Farbton verschieben**: Schatten Richtung kühl (Blau/Violett), Lichter Richtung warm (Gelb/Orange) — das wirkt plastischer und lebendiger
- **SOLLTE [SHOULD]** das Hue-Shifting über die ganze Ramp **konsistent** anwenden, sodass benachbarte Ramps harmonieren
- **KANN [MAY]** den Lichtfarb-Ton an einer gesetzten Lichtquelle ausrichten (z. B. warmes Sonnenlicht → wärmere Lichter, kühler Schatten)

### Konturen / Outlining

- **MUSS [MUST]** **selektives Outlining (Selout)** anwenden: Konturen bewusst dort setzen, wo Formen getrennt werden müssen — **nicht** zwanghaft jedes Detail schwarz umranden
- **SOLLTE [SHOULD]** zwischen **Außenkontur** (Silhouette gegen den Hintergrund) und **Innenkontur** (Trennung von Formteilen) unterscheiden; Innenkonturen dürfen dünner/farbig/teilweise sein
- **SOLLTE [SHOULD]** **schwarze Linien sparsam** verwenden — sie wirken „subtraktiv" und lassen angrenzende Farben dunkler/matschiger erscheinen; um helle Flächen besser eine **farbige, dunklere Variante der Flächenfarbe** als Kontur nutzen („additive" Kontur)
- **SOLLTE [SHOULD]** die **untere Kontur entfernen oder aufhellen**, wenn ein Objekt am Boden steht — eine durchgehende dunkle Unterkante lässt es „schweben"
- **KANN [MAY]** ganz auf eine geschlossene Außenkontur verzichten und Formen allein über Kontrast/Schattierung trennen, wenn der Hintergrund genug Kontrast bietet (konturloser Stil)

### Schattierung & Lichtquelle

- **MUSS [MUST]** eine **konsistente Lichtrichtung** festlegen und über das ganze Bild beibehalten (Front-oben ist ein robuster Default); alle Schatten/Lichter folgen dieser Richtung
- **MUSS NICHT [MUST NOT]** **Pillow-Shading** erzeugen — also gleichmäßig von der Kontur zur Mitte hin aufhellen, ohne Lichtquelle; das flacht die Form ab
- **SOLLTE [SHOULD]** Schattierungs-Ramps an einer **Terminator-Kante** (Hell-Dunkel-Grenze der Form) klar abschließen, statt weich auszulaufen — die scharfe Grenze definiert die Form
- **SOLLTE [SHOULD]** Tonwert **aufbauen und dann abrupt** gegen einen Schattenwert abgrenzen, um den „Pillow"-Eindruck zu brechen
- **KANN [MAY]** ein **Glanzlicht (Specular)** als kleinste, hellste Akzentfläche auf der lichtzugewandten Seite und **Ambient-Occlusion** (leichte Abdunklung in Kontakt-/Innenecken) setzen, sparsam und konsistent zur Lichtquelle

### Anti-Aliasing

- **SOLLTE [SHOULD]** **manuelles Anti-Aliasing** (Zwischentöne an Kanten/Kurven) gezielt einsetzen, um Treppenstufen zu glätten — aber **dosiert**
- **MUSS NICHT [MUST NOT]** **übermäßig anti-aliasen** — zu viele Zwischentöne machen das Bild matschig und unscharf; Pixel-Art priorisiert grafische Klarheit über glatte Kurven
- **SOLLTE [SHOULD]** auf der LED-Matrix beachten, dass AA-Zwischenpixel aus Distanz als **eigenständige Pixel** statt als weiche Kante gelesen werden können — AA an exponierten Außenkanten gegen dunklen Hintergrund eher zurückhaltend
- **MUSS NICHT [MUST NOT]** AA-Pixel über mehr als ~2 Stufen an einer einzelnen Kante stapeln — das erzeugt unscharfe „Doppelkanten"

### Dithering

- **KANN [MAY]** **Dithering** (alternierende Pixel zweier Farben) einsetzen, um Farbübergänge zu glätten oder Texturen anzudeuten, ohne die Palette zu vergrößern
- **SOLLTE [SHOULD]** Dithering **sparsam und mit konsistentem Muster** verwenden (z. B. 50 %-Schachbrett für eine Mittelstufe, dünner werdende Muster für Verläufe) — uneinheitliches Dithering wirkt wie Rauschen
- **SOLLTE [SHOULD]** Dithering bevorzugt zwischen **zwei tonwert-nahen Farben** anwenden; bei starkem LED-Kontrast und kurzer Betrachtungsdistanz „mischt" das Auge weniger, sodass das Muster sichtbar bleibt — vorher am realen Gerät prüfen
- **KANN [MAY]** Dithering doppelt nutzen: zugleich Verlauf erzeugen **und** Materialtextur andeuten

### Fehler-Vermeidung (Banding & Jaggies)

- **MUSS NICHT [MUST NOT]** **Banding** erzeugen — also Tonwert-Bänder, die als parallele Streifen entlang einer Kontur/Diagonale verlaufen; das lenkt auf den Übergang statt auf die Form
- **SOLLTE [SHOULD]** Banding brechen durch schmalere Bänder, Verlagern des Übergangs an eine natürliche Schattengrenze oder Auflösen per Dithering/Cluster
- **MUSS NICHT [MUST NOT]** **Jaggies** zulassen — unregelmäßige, „zittrige" Pixel-Treppen; Kurven über **saubere, gleichmäßige Pixel-Progressionen** (z. B. 1-1-2-3-Längen) führen
- **SOLLTE [SHOULD]** Linien und Kurven so anlegen, dass die Segmentlängen monoton/regelmäßig wachsen oder fallen, statt unregelmäßig zu springen

### Liefer-Pfade (Anbindung an `ha/divoom-pixoo`)

- **MUSS [MUST]** bei **vorgerenderten Bildern** die Datei in **exakt 64×64 px** anlegen und über die `image`-Komponente mit Resample-Modus **`nearest`** (bzw. `pixel_art`) einbinden — jedes Skalieren mit einem glättenden Modus (`box`, `bilinear`, …) zerstört die Pixel-Art-Kanten (siehe `ha/divoom-pixoo` §Komponenten)
- **MUSS NICHT [MUST NOT]** Pixel-Art kleiner als 64×64 anlegen und hochskalieren lassen — bei Nicht-Vielfachen entstehen ungleich breite Pixel; nativ auf Zielgröße arbeiten
- **KANN [MAY]** Pixel-Art **prozedural** aus Entity-States erzeugen: einzelne Pixel/Flächen über `rectangle`-Komponenten (`size: [1,1]` für Einzelpixel) oder dynamisch über eine `templatable`-Komponente, die eine Liste von Pixel-Komponenten zurückgibt (siehe `ha/divoom-pixoo` §Komponenten)
- **SOLLTE [SHOULD]** beim prozeduralen Pfad dieselben Palette-/Kontur-/Schattierungs-Regeln anwenden wie beim Bild-Pfad — die Liefer-Form ändert das Handwerk nicht
- **SOLLTE [SHOULD]** das Ergebnis **am realen Gerät** verifizieren (Helligkeit, Kontrast, 1-px-Lesbarkeit, Dithering-Wirkung), nicht nur im Editor — das LED-Panel weicht spürbar vom Monitor ab

## Akzeptanzkriterien

- [ ] Das Motiv ist nativ in 64×64 gestaltet; bei PNG-Einbindung wird `nearest`/`pixel_art`-Resampling verwendet, kein glättender Modus
- [ ] Die Palette ist begrenzt und in Ramps (Schatten→Mittel→Licht, 3–5 Werte) organisiert; voll gesättigte Farben nur als Akzent
- [ ] Schattierung folgt einer konsistenten Lichtrichtung; kein Pillow-Shading; Terminator-Kanten sind klar gesetzt
- [ ] Hue-Shifting ist erkennbar (Schatten kühler, Lichter wärmer) und über benachbarte Ramps konsistent
- [ ] Konturen sind selektiv (kein Voll-Schwarz um jedes Detail); Innen- vs. Außenkontur differenziert; Bodenkante nicht „schwebend"
- [ ] Kein Banding und keine Jaggies; Kurven nutzen saubere Pixel-Progressionen; AA ist dosiert
- [ ] Dithering (falls genutzt) ist konsistent gemustert und am realen Gerät auf Wirkung geprüft
- [ ] Die Silhouette ist in Graustufen (nur Value) noch lesbar; das Bild wurde am echten Pixoo gegen Helligkeit/Kontrast/1-px-Lesbarkeit verifiziert
- [ ] Bei prozeduraler Erzeugung (`rectangle`/`templatable`) gelten dieselben Palette-/Kontur-/Schattierungs-Regeln wie beim Bild-Pfad

## Offene Fragen

- Soll ein projekt-fester Paletten-Katalog (z. B. eine 16–32-Farben-Ramp-Sammlung) für `home-assistant-config` definiert werden, damit alle Pixoo-Pages kohärent wirken?
- Lohnt ein wiederverwendbarer Helfer (Skript/Makro), der ein 64×64-Pixel-Raster aus einer kompakten Datenrepräsentation in eine `templatable`-Komponentenliste übersetzt (prozedurale Pixel-Art aus Entity-States)?
- Gibt es eine geräte-spezifische Gamma-/Helligkeits-Korrektur, die zwischen Editor-Vorschau und LED-Darstellung kalibriert werden sollte (Tonwert-Drift)?
