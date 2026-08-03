# ESPHome-Gerät: ESP32-S3-BOX-Display-Design (Icons, Farbe, Struktur)

Status: draft

## Kontext

[`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md) regelt die **Mechanik**, Pixel auf das ESP32-S3-BOX-Panel zu bringen — Rendering-Pfad, Canvas, Refresh-Modell, Pages, Primitive, Platzierung. Grafikdesign benennt diese Spec ausdrücklich als Non-Goal: „diese Spec regelt die Mechanik der Platzierung, nicht den Geschmack, der darauf angewendet wird". Diese Spec ist die fehlende Hälfte. Sie ist das Design-System, **aus dem** ein Screen komponiert wird, damit „welche Farbe, welches Icon, welche Größe, und was steht wo" nicht mehr pro Page von dem entschieden wird, der gerade das Lambda schreibt.

Die Zielgruppe ist ein Designer, nicht primär ein Config-Autor. Deshalb sagt sie zuerst, was die Oberfläche tatsächlich ist, bevor sie Regeln dafür aufstellt — und die Oberfläche ist kleiner und härter, als die Zahl 320×240 vermuten lässt:

- Das Panel hat **48,8 mm × 36,6 mm** aktive Fläche (2,4 Zoll Diagonale bei 320×240 → 166,7 ppi, ein Pixel = 0,152 mm) `[derived]`
- Es rendert **RGB565**, nicht True Color: 65 536 Farben aus 5 Bit Rot, 6 Grün, 5 Blau `[doc]`
- Seine Helligkeit ist eine nutzersteuerbare Light-Entity, die nicht immer auf 100 % steht `[ref-config]`

Zwei Konsequenzen tragen alles Weitere. Erstens ist dies ein **Nahbereichsgerät**: Auf einem Meter Abstand hat 16-Pixel-Text einen Sehwinkel von etwa 5,9 Bogenminuten — knapp über der Auflösungsgrenze von ~5 Bogenminuten eines normalsichtigen Auges und weit unter den 16–20 Bogenminuten, die üblicherweise als komfortabel gelten. Nur Display-Größen überstehen Raumdistanz. Zweitens genügt ein Design nicht, das bloß *lesbar* ist — es muss bei gedimmter Hintergrundbeleuchtung lesbar bleiben, und das ist ein Kontrast-, kein Farbgeschmacksproblem.

Das Farb- und Typo-System hier ist nicht erfunden. Es sind die **Home-Assistant-Frontend-Design-Tokens**, auf konkrete Werte aufgelöst und auf das Panel übertragen, damit ein BOX-Screen und ein HA-Dashboard sich einig sind, wie „Warnung" aussieht. HAs Token-Ebene trennt *Core*-Rampen (`--ha-color-<hue>-05` … `-95`) von *semantischen* Rollen (`--ha-color-on-warning-normal`) und liefert ein eigenes Dark-Set; das Dark-Set ist das hier verwendete, weil ein wand- oder tischmontiertes Panel im Raum eine Oberfläche mit dunklem Hintergrund ist.

### Quellen-Tiers

Erweitert die in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) §„Quellen-Tiers" definierten Tiers:

- `[doc]` — offizielle ESPHome-Komponenten-Doku
- `[src]` — Verhalten real, aber undokumentiert (oder von der Doku widersprochen), aus dem ESPHome-Quellbaum belegt; undokumentierte API trägt keine Kompatibilitätszusage
- `[ref-config]` — ESPHomes offizielle Board-Configs in `esphome/wake-word-voice-assistants`
- `[ha-tokens]` — Home-Assistant-Frontend-Design-Tokens, gelesen aus `home-assistant/frontend` `src/resources/theme/`
- `[md-icons]` — Googles Material-Design-System-Icon-Guidelines, denen Material Design Icons folgt
- `[wcag]` — W3C-WCAG-2.2-Erfolgskriterien
- `[derived]` — hier aus einer angegebenen Eingabe berechnet (Panel-Geometrie, RGB565-Quantisierung, WCAG-Kontrastformel); reproduzierbar, kein Zitat
- `[policy]` — nolte-Portfolio-Regel, kein Upstream-Fakt

Verifiziert 2026-08.

## Ziele

- Eine **feste, benannte Farbpalette** mit konkreten Werten liefern, abgeleitet aus den Home-Assistant-Dark-Design-Tokens, damit Zustandsfarbe ein Nachschlagen statt einer Entscheidung pro Page ist
- Diese Palette auf diesem Panel belegen: Kontrastverhältnisse **nach** RGB565-Quantisierung berechnet, nicht auf den nominellen Hex-Werten
- Eine **Typo-Skala** und eine **Icon-Größenskala** liefern, gebunden an Betrachtungsabstand und an die Layout-Zonen, die die Schwester-Spec bereits definiert
- Klären, wie ein Material-Design-Icon auf diesen Screen kommt — Bezug, Asset-Typ und der eine Mechanismus, mit dem ein einziges Asset jede Zustandsfarbe tragen kann
- Der Struktur eine Regel geben, die einen 48-mm-Screen übersteht: was eine einzelne Page enthalten darf und was eine zweite Page werden muss
- Dasselbe Design-System an beide Rendering-Pfade binden, damit die Wahl zwischen `display:` und `lvgl:` nicht ändert, wie das Gerät aussieht
- Die Flash-Kosten des resultierenden Asset-Sets benennen, denn auf diesem Gerät ist eine Design-Entscheidung eine Firmware-Größen-Entscheidung

## Nicht-Ziele

- Rendering-Mechanik — Canvas, Koordinaten, Refresh-Modell, Page-State-Mapping, Primitive, Truncation-Mechanik und die Layout-Zonen-Geometrie gehören zu [`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md) und werden referenziert, nicht wiederholt
- Hardware-Bindung des Panels (SPI-Pins, Model-Preset, `invert_colors`, Backlight-Entity) — [`ha/esp32-s3-box`](../esp32-s3-box/de.md)
- Woher die angezeigten Werte kommen — [`ha/esphome-ha-driven-content`](../esphome-ha-driven-content/de.md)
- Pixel-Art-Handwerk (Konturen, Schattierung, Rampen, Dithering) — das ist [`ha/pixoo-pixel-art`](../pixoo-pixel-art/de.md), eine andere Oberfläche (selbstleuchtende 64×64-Matrix, 24-Bit-Farbe) mit bewusst offener Palette; diese Spec regelt UI-Design auf einem 320×240-LCD mit geschlossener Palette
- Eine Light-Theme-Variante — das Dark-Set ist hier normativ; eine Light-Variante ist eine offene Frage unten, keine ausgelieferte Alternative
- Motion- und Animations-Design — die Schwester-Spec hält Multi-Frame-Assets als offene Frage, und diese Spec greift dem nicht vor
- Touch-Gesten- und Screen-Flow-Design — abgedeckt ist nur die visuelle Seite interaktiver Zustände
- Icon-Deklarationen für HA-Integrationen (`icons.json`) — das ist [`ha/icons`](../icons/de.md), ein gänzlich anderes Artefakt

## Anforderungen

### Betrachtungsabstand und Lesbarkeitsgrenze

- **MUSS [MUST]** die BOX als **Nahbereichsgerät** für etwa **0,5 m** behandeln und **DARF NICHT [MUST NOT]** erwarten, dass irgendetwas unterhalb der Display-Größe quer durch einen Raum lesbar ist. Versalhöhen berechnet mit 0,70 em auf einem 0,152-mm-Pixel `[derived]`:

  | Größe | Versalhöhe | Auf 0,5 m | Auf 1,0 m | Bewertung |
  |---|---|---|---|---|
  | 12 px | 1,28 mm | 8,8′ | 4,4′ | unter der ~5′-Auflösungsgrenze auf 1 m — nur Nahbereich |
  | 16 px | 1,71 mm | 11,7′ | 5,9′ | lesbar auf 0,5 m, Grenzfall auf 1 m |
  | 20 px | 2,13 mm | 14,7′ | 7,3′ | komfortabel auf 0,5 m |
  | 28 px | 2,99 mm | 20,5′ | 10,3′ | komfortabel auf 0,5 m, lesbar auf 1 m |
  | 48 px | 5,12 mm | 35,2′ | 17,6′ | die einzige Fließtextgröße, die auf 1 m komfortabel ist |
  | 96 px | 10,24 mm | 70,4′ | 35,2′ | quer durch den Raum erfassbar |

- **MUSS [MUST]** sicherstellen, dass auf jeder Page genau **ein** Element aus Raumdistanz lesbar ist — der Hero-Wert oder das Hero-Icon — und alles andere auf dieser Page als Detail behandeln, für das der Nutzer näher herantritt `[policy]`
- **SOLLTE [SHOULD]** gegen eine **gedimmte** Hintergrundbeleuchtung entwerfen statt gegen volle Helligkeit, da Helligkeit eine nutzergesteuerte Entity ist; ein Design, das nur bei 100 % funktioniert, ist ein Design, das abends versagt `[ref-config]` `[policy]`

### Die Farbpalette

- **MUSS [MUST]** diese Palette verwenden und **MUSS [MUST]** jeden Eintrag als `color:`-Komponente mit exakt der ID aus der ersten Spalte deklarieren, damit Pages Rollen statt Literale referenzieren `[policy]`. Die Werte lösen die Home-Assistant-**Dark**-Semantik-Tokens über deren Core-Rampen auf `[ha-tokens]`:

  | Farb-ID | Hex | HA-Dark-Token | Rolle |
  |---|---|---|---|
  | `c_bg` | `000000` | `surface-lower` | vollflächiger Page-Hintergrund |
  | `c_surface` | `202020` | `surface-default` (neutral-10) | Panels und gerahmte Boxen |
  | `c_surface_low` | `141414` | `surface-low` (neutral-05) | vertiefte Bereiche, Statusstreifen |
  | `c_text` | `FFFFFF` | `text-primary` | primärer Text |
  | `c_text_dim` | `CCCCCC` | `text-secondary` (neutral-80) | sekundärer Text, Labels, Einheiten |
  | `c_disabled` | `7A7A7A` | `on-disabled-normal` (neutral-50) | nicht verfügbar / inaktiv |
  | `c_border` | `5E5E5E` | `border-neutral-quiet` (neutral-40) | Boxrahmen, Trennlinien |
  | `c_accent` | `37C8FD` | `on-primary-normal` (primary-60) | aktiv, ausgewählt, in Arbeit |
  | `c_ok` | `00AC49` | `on-success-normal` (green-60) | gesund, geschlossen, fertig |
  | `c_warn` | `F36D00` | `on-warning-normal` (orange-60) | Aufmerksamkeit, eingeschränkt |
  | `c_alarm` | `F3676C` | `on-danger-normal` (red-60) | Fehler, offen, Alarm |

- **DARF NICHT [MUST NOT]** einen weiteren Farbton zur Bedeutungsträgerschaft hinzufügen. Home Assistants semantische Ebene hat genau diese Kanäle — primary, neutral, success, warning, danger, plus disabled — und liefert insbesondere **keine** eigene `info`-Rolle; informative Hervorhebung ist `c_accent` `[ha-tokens]` `[policy]`
- **KANN [MAY]** die eine Stufe helleren `-70`-Rampenvarianten verwenden, wo eine große gefüllte Fläche mehr Trennung zum Hintergrund braucht: Accent `7BD4FB`, Success `5DC36F`, Warning `FF9342`, Danger `FD8F90` `[ha-tokens]`
- **DARF NICHT [MUST NOT]** ein Hex-Literal in einem Page-Lambda oder Widget hartkodieren, wo eine Rolle existiert; ein neues Literal ist ein Antrag, diese Tabelle zu erweitern — einmal entschieden, nicht pro Page `[policy]`
- **SOLLTE [SHOULD]** `c_bg` (echtes Schwarz) statt `c_surface` als Standard-Page-Hintergrund beibehalten: Es maximiert den Kontrast für jede Vordergrundrolle und ist auf diesem Panel das eine Grau, das garantiert exakt wie spezifiziert dargestellt wird (siehe unten) `[derived]` `[policy]`

### Was RGB565 mit diesen Farben macht

- **MUSS [MUST]** akzeptieren, dass das Panel 5 Bit Rot, 6 Grün, 5 Blau speichert (`pixel_mode: 16bit`, der `mipi_spi`-Default), sodass jede Farbe der obigen Tabelle vor der Anzeige quantisiert wird `[doc]`
- **MUSS [MUST]** verstehen, dass **neutrale Grautöne nicht neutral bleiben**. Grün hat ein Bit mehr als Rot und Blau, sodass ein Grau `(v,v,v)` im Allgemeinen zu ungleichen Kanälen quantisiert — `141414` erreicht das Panel als `101410` und `202020` als `212021`. Nur **8** der 256 Graustufen überleben exakt (`00`, `08`, `10`, `18`, `E7`, `EF`, `F7`, `FF`), und sie liegen alle an den Extremen; im gesamten Mittelfeld **existiert** kein exakt neutrales Grau `[derived]`
- **DARF NICHT [MUST NOT]** darauf mit einem Einrasten der Grautöne auf das neutrale Set reagieren — das nächste exakte Neutral zu `neutral-50` liegt 98 Stufen entfernt, was die Rampe zerstört, um einen unsichtbaren Defekt zu beheben. Die Abweichung ist auf **4/255 (1,57 %)** begrenzt bei einem Mittel von 2/255 und liegt damit unter der Wahrnehmungsschwelle auf einem 2,4-Zoll-Panel. Den HA-Wert spezifizieren, den Farbstich akzeptieren `[derived]` `[policy]`
- **DARF NICHT [MUST NOT]** großflächige Verläufe verwenden. Über die 240 Pixel Höhe haben Rot und Blau nur 32 Stufen — ein Band alle 7,5 Pixel — sodass ein Vollbildverlauf sichtbar bandet. Flächen sind flach; Trennung entsteht durch Kontrast, nicht durch Schattierung `[derived]` `[policy]`
- **SOLLTE [SHOULD]** eine verdächtige Farbdarstellung mit `show_test_card: true` prüfen, bevor die Palette verdächtigt wird — aber beachten, dass die Testkarte ein echtes `update_interval` **erfordert**: Die Doku hält fest, dass sie bei `update_interval: never` nicht gezeichnet wird, also genau in dem Modus, den die Schwester-Spec vorschreibt. Die Karte zu testen heißt daher, diesen Key vorübergehend zu ändern `[doc]`

### Kontrast

- **MUSS [MUST]** **4,5:1** für Text unter 24 px erreichen, **3:1** für Text ab 24 px und **3:1** für jedes bedeutungstragende Icon oder Grafikelement `[wcag]`
- **MUSS [MUST]** den Kontrast gegen die **quantisierte** Farbe berechnen, nicht gegen den nominellen Hex-Wert. Gemessen für diese Palette auf den beiden normativen Hintergründen `[derived]`:

  | Vordergrund | auf `c_bg` `000000` | auf `c_surface` `202020` |
  |---|---|---|
  | `c_text` `FFFFFF` | 21,00 | 16,24 |
  | `c_text_dim` `CCCCCC` | 13,44 | 10,39 |
  | `c_accent` `37C8FD` | 11,12 | 8,60 |
  | `c_ok` `00AC49` | 7,15 | 5,53 |
  | `c_warn` `F36D00` | 7,14 | 5,52 |
  | `c_alarm` `F3676C` | 7,03 | 5,43 |
  | `c_border` `5E5E5E` | 3,15 | 2,43 |
  | `c_disabled` `7A7A7A` | 4,86 | 3,76 |

- **MUSS [MUST]** diese Tabelle als Beleg lesen, dass die Palette sicher ist: Jede Text- und Zustandsrolle übertrifft 4,5:1 auf beiden Hintergründen, und die Quantisierung verschiebt die Verhältnisse um höchstens ±0,3 `[derived]`
- **DARF NICHT [MUST NOT]** `c_disabled` für Text verwenden, der gelesen werden soll — mit 3,76:1 auf `c_surface` liegt er unter der Fließtextschwelle. Legitim ist er genau deshalb, weil WCAG inaktive Komponenten ausnimmt: Er *soll* als nicht verfügbar gelesen werden. Sekundärer lesbarer Text ist `c_text_dim` `[wcag]` `[derived]`
- **DARF NICHT [MUST NOT]** `c_border` als Vordergrund für Text oder ein bedeutungstragendes Icon verwenden; mit 2,43:1 auf `c_surface` verfehlt er selbst die 3:1-Grafikschwelle und ist ausschließlich Strukturlinie `[derived]`
- **SOLLTE [SHOULD]** die Berechnung neu ausführen statt dieser Tabelle zu vertrauen, sobald sich eine Farbe, ein Hintergrund oder `pixel_mode` ändert `[policy]`

### Farbsemantik und redundante Kodierung

- **DARF NICHT [MUST NOT]** Farbe zum alleinigen Träger einer Bedeutung machen. Jeder durch Farbe unterschiedene Zustand **MUSS [MUST]** sich zusätzlich in mindestens einem der folgenden Merkmale unterscheiden: Icon-Glyphe, Text oder Position auf dem Screen `[wcag]` `[policy]`
- **MUSS [MUST]** Zustände über alle Pages eines Geräts konsistent auf die Rollen abbilden — `c_ok` bedeutet nie auf einem Screen „Aufmerksamkeit" und auf einem anderen „gesund" `[policy]`
- **MUSS [MUST]** dem Nicht-verfügbar-Zustand eine eigene visuelle Behandlung geben (`c_disabled` plus Platzhalter-Glyphe oder -String), statt einen veralteten letzten Wert in einer Live-Farbe zu rendern; die Schwester-Spec verlangt bereits einen expliziten Platzhalter, und dies ist dessen visuelle Hälfte `[ref-config]` `[policy]`
- **SOLLTE [SHOULD]** `c_alarm` für Zustände reservieren, die es rechtfertigen, jemanden zu unterbrechen; ein Screen, auf dem die Gefahrenfarbe dauerhaft präsent ist, hat sie verbraucht `[policy]`

### Die Typo-Skala

- **MUSS [MUST]** genau diese vier Stufen verwenden und **MUSS [MUST]** je Stufe eine `font:`-Komponente deklarieren, da eine Schrift zur Compile-Zeit pro Größe gerastert wird `[doc]` `[policy]`:

  | Font-ID | Größe | HA-Token | Zonenpassung (Schwester-Spec) | Verwendung |
  |---|---|---|---|---|
  | `f_caption` | 12 px | `--ha-font-size-s` | Statusstreifen (15 px) | Einheiten, Zeitstempel, Streifen-Labels |
  | `f_body` | 16 px | `--ha-font-size-l` | Header-/Footer-Box (30 px) | primäre und sekundäre Zeilen |
  | `f_display` | 28 px | `--ha-font-size-3xl` | Zentral-Widget (50 px) | der modale Wert |
  | `f_hero` | 48 px | über der HA-Skala | vollflächig | der eine Wert für Raumdistanz |

- **MUSS [MUST]** `f_hero` als bewusste Abweichung behandeln: Home Assistants Skala endet bei 40 px (`--ha-font-size-5xl`), was auf diesem Panel auf einem Meter nur 14,7 Bogenminuten erreicht. Die 48 px stammen aus der Lesbarkeitstabelle oben, nicht aus dem Token-Set, weil HAs Skala auf Bildschirme im Schreibtischabstand kalibriert ist `[ha-tokens]` `[derived]` `[policy]`
- **MUSS [MUST]** **Roboto** als Familie verwenden (`file: "gfonts://Roboto"`), Home Assistants `--ha-font-family-body`. Das weicht bewusst von Figtree der Referenz-Configs ab: Ausschlaggebend ist Konsistenz mit dem HA-Frontend, nicht mit dem Upstream-Beispiel `[ha-tokens]` `[ref-config]` `[policy]`
- **MUSS [MUST]** auf jeder Schrift ein explizites `size:` setzen — es ist im Schema optional und **defaultet auf 20**, sodass eine ausgelassene Größe stillschweigend in der falschen Stufe rendert `[doc]`
- **MUSS [MUST]** `bpp: 4` auf `f_display` und `f_hero` setzen und **KANN [MAY]** den Default `bpp: 1` auf `f_caption` und `f_body` belassen. Große Glyphen zeigen ihre Treppenstufen, kleine meist nicht, und höhere Bittiefen „increase the binary size considerably" `[doc]` `[policy]`
- **MUSS [MUST]** überall dort, wo `bpp` über 1 liegt, die **Hintergrundfarbe** an den Print-Aufruf übergeben, und zwar an der Position, die die jeweilige Überladung erwartet — `print` nimmt sie **nach** dem Text, `printf` nimmt sie an **fünfter** Stelle, vor dem Align. Beide sind dokumentiert und beide sind reale Signaturen; die falsche Position bindet eine andere Überladung, und die Farbe wird stillschweigend als Format-Argument verbraucht `[doc]` `[src]`
- **MUSS [MUST]** Schriftschnitt statt einer fünften Größe zur Trennung von Label und Wert einsetzen: `gfonts://Roboto@500` für den Wert gegen den regulären Schnitt für sein Label. HAs eigene Skala ist 300/400/500/700 `[doc]` `[ha-tokens]` `[policy]`
- **DARF NICHT [MUST NOT]** Text unterhalb von `f_caption` setzen; 12 px ist die Untergrenze und bereits nur im Nahbereich brauchbar `[derived]`
- **SOLLTE [SHOULD]** `glyphsets:` auf `GF_Latin_Core` begrenzen und `GF_Latin_Kernel` ergänzen, wo Ziffern und Leerzeichen gebraucht werden, da jede Glyphe in jeder Größe Flash kostet `[doc]`

### Icons: Bezug und Größe

- **MUSS [MUST]** Icons von **Material Design Icons** beziehen, die ESPHome nativ auflöst: `file: mdi:<icon-name>` auf der `file`-Plattform oder die typisierte Form `source: mdi` / `icon: <name>`. Die Schwesterfamilien `mdil:` (Material Design Light) und `memory:` werden ebenfalls akzeptiert `[doc]`
- **DARF NICHT [MUST NOT]** Icon-Familien innerhalb eines Geräts mischen; MDI ist das Standard-Set und dasjenige, das Home Assistant selbst verwendet `[doc]` `[policy]`
- **MUSS [MUST]** ausnutzen, dass diese Icons als **SVG** geholt und zur Compile-Zeit auf die `resize:`-Box gerastert werden — ein Icon wird also in jeder Größe aus Vektorgeometrie skaliert, ohne Resampling-Verlust, und es gibt keinen Grund, Raster-Icon-Assets von Hand zu erstellen `[doc]`
- **MUSS [MUST]** genau diese Icon-Größen verwenden, je gepaart mit einer Typo-Stufe `[policy]`:

  | Größe | Paart mit | Verwendung |
  |---|---|---|
  | 24 px | `f_body` (16 px) | Inline-Status-Icon in einer Header- oder Footer-Zeile |
  | 40 px | `f_display` (28 px) | führendes Icon neben dem modalen Wert |
  | 96 px | — | die Hero-Glyphe, die einen Vollbild-Zustand trägt |

- **DARF NICHT [MUST NOT]** ein MDI-Icon unterhalb von **24 px** rendern. MDI folgt Googles System-Icon-Raster: 24 dp Trim-Fläche, 20 × 20 dp Live-Fläche und **2 dp** Strichstärke. Bei Rendergröße N px skaliert der Strich auf `N/24 × 2` px — 2,0 px bei 24, aber 1,33 px bei 16 und 1,0 px bei 12, wo Striche unter einen Pixel fallen und ausdünnen oder abreißen `[md-icons]` `[derived]`
- **MUSS [MUST]** die Box gegen die **Trim**-Fläche bemessen, nicht gegen die Zeichnung: `resize:` passt das Bild unter Wahrung des Seitenverhältnisses in die angegebene Box ein, und MDIs 2 dp Padding sind Teil des Assets — ein 24-px-Icon malt daher etwa 20 px Farbe, was die korrekte optische Größe neben 16-px-Text ist `[doc]` `[md-icons]`
- **SOLLTE [SHOULD]** Icons, deren Silhouette sich von ihren Nachbarn auf demselben Screen unterscheidet, gegenüber semantisch präziseren, aber visuell ähnlichen bevorzugen; bei 24 px auf einem 48-mm-Panel ist die Silhouette das, was das Auge auflöst `[md-icons]` `[policy]`

### Icons: Asset-Typ und Laufzeitfarbe

Die Wahl von `type:` ist die folgenreichste Icon-Entscheidung, denn sie entscheidet, ob ein Asset jede Zustandsfarbe tragen kann oder ob jede Farbe ein eigenes Asset braucht.

- **MUSS [MUST]** monochrome Icons als **`type: GRAYSCALE` mit `transparency: alpha_channel`** deklarieren und mit beiden Farbargumenten zeichnen: `it.image(x, y, id(icon), <Vordergrund>, <Hintergrund>)`. Diese Form speichert **ein Byte pro Pixel** (nur den Alphakanal) und blendet `color_on` pro Pixel anhand des Alphawerts gegen `color_off` — ein einzelnes Asset rendert also in beliebiger Zustandsfarbe **mit erhaltenem Antialiasing** `[doc]` `[src]`
- **MUSS [MUST]** dies bewusst als `[src]`-Fakt behandeln, weil die Doku das Gegenteil behauptet: Sie sagt, die Display-Lambda-Funktionen „will draw or not draw the pixel, no blending with the background will be done", und `alpha_channel` sei „useful mainly when using LVGL". Das gilt für `RGB565` und `RGB`, die binär auf `alpha >= 0x80` entscheiden, aber **nicht** für `GRAYSCALE`, dessen Zeichenpfad `on = gray/255` berechnet und die beiden Farben mischt. Verifiziert in `esphome/components/image/image.cpp`; als undokumentiertes Verhalten trägt es keine Kompatibilitätszusage und gehört auf die Re-Verifikationsliste unten `[doc]` `[src]`
- **MUSS [MUST]** die **tatsächliche** Hintergrundfarbe der Zone als zweites Farbargument übergeben. Der Default ist `COLOR_OFF` (Schwarz), sodass ein über eine `c_surface`-Fläche geblendetes Icon mit Default-Wert einen dunklen Halo um jede Kante erzeugt — dasselbe Fehlerbild wie eine antialiasierte Schrift, die ohne ihren Hintergrund gedruckt wird `[src]` `[policy]`
- **KANN [MAY]** `type: BINARY` mit `transparency: chroma_key` verwenden, wo Flash wichtiger ist als Kantenqualität: Diese Kombination kostet **ein Bit pro Pixel** und bleibt zur Laufzeit einfärbbar (die nicht gesetzten Pixel werden schlicht übersprungen), hat aber kein Antialiasing, sodass bei 24 px die 2-px-Striche mit sichtbarer Treppenbildung rendern `[doc]` `[src]`
- **DARF NICHT [MUST NOT]** `type: RGB` mit `transparency: alpha_channel` für ein monochromes Icon verwenden. Es kostet **vier Byte pro Pixel** — das 32-Fache der GRAYSCALE-Form —, ist zur Laufzeit nicht einfärbbar und bringt auf dem Immediate-Mode-Pfad nichts, wo sein Alpha auf einen Binärtest reduziert wird. Es ist die Wahl der Referenz-Configs für vollflächige *Illustrationen*, was eine andere Asset-Klasse ist `[doc]` `[ref-config]` `[src]`
- **DARF NICHT [MUST NOT]** ein Asset pro Zustandsfarbe deklarieren. Drei Zustände eines Icons sind ein GRAYSCALE-Asset, gezeichnet mit drei Vordergründen — nicht drei Bilder `[policy]`
- **DARF NICHT [MUST NOT]** den Typ `RGBA` verwenden — es gibt ihn nicht; ein Alphakanal wird über `transparency:` angefordert `[doc]`

### Struktur

- **MUSS [MUST]** jede Page auf **eine Aussage** begrenzen: ein einzelnes Subjekt, dessen Zustand und höchstens zwei stützende Fakten. Das Zonenraster der Schwester-Spec bietet vier Inhaltszonen; alle vier mit unzusammenhängenden Messwerten zu füllen, ergibt einen Screen, den bei 48 mm niemand erfasst `[policy]`
- **MUSS [MUST]** eine Page aus dieser Hierarchie komponieren, von oben nach unten in Lesepriorität `[policy]`:
  1. **Identität** — worum es geht (Header-Zeile, `f_body`, `c_text_dim`)
  2. **Zustand** — das Hero-Icon oder der Hero-Wert, in der Zustandsfarbe (`f_display` / `f_hero`, 40 oder 96 px Icon)
  3. **Qualifizierer** — eine Einheit, ein Zeitstempel, ein sekundärer Messwert (`f_caption`, `c_text_dim`)
  4. **Systemstatus** — Konnektivität und Fortschritt, begrenzt auf den Statusstreifen
- **MUSS [MUST]** den Statusstreifen (untere 15 px) ausschließlich für Zustände auf Geräteebene reservieren — Verbindung, Pipeline-Phase, Fortschritt —, niemals für Inhalt, damit der Nutzer einen festen Ort lernt, an dem er prüft, ob der Screen überhaupt aktuell ist `[ref-config]` `[policy]`
- **MUSS [MUST]** teilen statt verkleinern: Wenn Inhalt in den vorgeschriebenen Größen nicht passt, wird er eine zweite Page, nicht kleinere Schrift. Die Schwester-Spec modelliert Zustände bereits als Pages mit einem einzigen Redraw-Einstiegspunkt `[policy]`
- **SOLLTE [SHOULD]** die Ausrichtung über Pages hinweg konsistent halten — ein Wert, der auf einer Page zentriert und auf der nächsten linksbündig steht, liest sich wie zwei verschiedene Geräte; Hero-Inhalt zentrieren, Textzeilen linksbündig setzen `[policy]`
- **SOLLTE [SHOULD]** Position wiederholen statt neu zu erklären: Derselbe Fakt gehört auf jeder Page, auf der er erscheint, in dieselbe Zone — genau das lässt einen Blick das Lesen ersetzen `[policy]`

### Der Immediate-Mode-Pfad

- **MUSS [MUST]** die Palette als `color:`-Komponenten und die vier Schriften als `font:`-Komponenten einmal pro Gerät deklarieren und sie aus jedem Page-Lambda per ID referenzieren `[doc]` `[policy]`
- **MUSS [MUST]** jede Page mit `it.fill(id(c_bg))` beginnen, damit der Hintergrund eine ausgesprochene Eigenschaft der Page ist und kein geerbter Zufall `[ref-config]` `[policy]`
- **MUSS [MUST]** geteiltes Design-Mobiliar — Statusstreifen, Hero-Icon-Block, Label-Wert-Paar — aus wiederverwendbaren `script:`-Einträgen zeichnen statt Zeichenaufrufe zwischen Page-Lambdas zu kopieren, damit eine Design-Änderung an einer Stelle landet `[ref-config]` `[policy]`
- **SOLLTE [SHOULD]** eine gerahmte Fläche als `filled_rectangle` in `c_surface` gefolgt von einem `rectangle` in `c_border` bei identischen Koordinaten aufbauen `[ref-config]`
- **KANN [MAY]** eine MDI-Glyphe **inline in einem Textlauf** ausgeben statt ein Bild zu platzieren, indem die Glyphe mit ihrem Codepoint in den `extras:`-Block einer Schrift aufgenommen wird (`\U000F02D1` für `mdi-heart`); das Icon erbt dann Größe, Farbe und Grundlinie des Textes, was der sauberste Weg ist, ein Symbol *innerhalb* eines Satzes zu setzen. Es kostet eine Glyphe in dieser Schrift statt eines separaten Assets `[doc]`
- **MUSS [MUST]** bei dieser Inline-Form Codepoints exakt escapen — kleines `\u` mit 4 Hex-Ziffern bis `0xFFFF`, großes `\U` mit 8 Ziffern darüber; MDI liegt im Private-Use-Bereich oberhalb `0xFFFF`, also ist es immer die `\U`-Form `[doc]`

### Der LVGL-Pfad

- **MUSS [MUST]** dieselbe Palette und Skala auf dem LVGL-Pfad reproduzieren, damit das Design-System unabhängig von der Rendering-Entscheidung ist. LVGL akzeptiert eine ESPHome-`color:`-ID direkt überall dort, wo eine Farbe erwartet wird, sodass der `color:`-Block geteilt und nicht dupliziert wird `[doc]` `[policy]`
- **MUSS [MUST]** `theme:` mit `dark_mode: true` als Grundlage setzen und dann pro Widget-Typ überschreiben, statt jedes Widget einzeln zu stylen `[doc]` `[policy]`
- **MUSS [MUST]** die Palette als `style_definitions:`-Einträge ausdrücken, benannt nach ihren Rollen, und sie über `styles:` an Widgets anwenden; die Präzedenz lautet Zustands-Styles > lokal > `style_definitions` > Theme > Top-Level, und genau das lässt ein rollenbasiertes System tragen `[doc]`
- **MUSS [MUST]** interaktives Feedback an LVGLs eigene Zustände binden — `pressed`, `checked`, `disabled`, `focused` — statt Widgets aus Automationen neu einzufärben: `disabled` nutzt `c_disabled`, `checked` nutzt `c_accent` `[doc]` `[policy]`
- **MUSS [MUST]** ein Icon über `image_recolor` **zusammen mit** `image_recolor_opa` umfärben, das auf `TRANSP` defaultet — die Farbe allein zu setzen hat keinen sichtbaren Effekt `[doc]`
- **SOLLTE [SHOULD]** `text_font` auf die ESPHome-`font:`-IDs der Typo-Skala setzen statt auf LVGLs eingebaute `montserrat_*`-Schnitte, damit beide Pfade dieselbe Typografie rendern; der eingebaute Default ist `montserrat_14`, keine Stufe dieser Skala `[doc]` `[policy]`
- **SOLLTE [SHOULD]** `radius` und `pad_all` zur Trennung einsetzen statt Rahmen zu zeichnen, wo ein Flächenwechsel genügt; LVGL folgt dem CSS-Border-Box-Modell, sodass Padding die Inhaltsfläche verkleinert `[doc]`
- **DARF NICHT [MUST NOT]** Verläufe über `bg_grad` auf großen Flächen einführen, aus dem oben genannten Banding-Grund `[derived]` `[policy]`

### Asset- und Flash-Budget

- **MUSS [MUST]** Icons vor dem Hinzufügen budgetieren, zu den Pro-Pixel-Kosten dieses Panels `[doc]` `[derived]`:

  | Form | Byte/px | 24-px-Icon | 40-px-Icon | 96-px-Icon |
  |---|---|---|---|---|
  | `BINARY` + `chroma_key` | 0,125 | 72 B | 200 B | 1,1 KiB |
  | `GRAYSCALE` + `alpha_channel` | 1 | 576 B | 1,6 KiB | 9 KiB |
  | `RGB` + `alpha_channel` | 4 | 2,3 KiB | 6,3 KiB | 36 KiB |

- **MUSS [MUST]** die damit geklärte Größenordnung festhalten: Eine **vollflächige** `RGB`-`alpha_channel`-Illustration kostet **300 KiB**, der Design-Unterschied zwischen einem Icon-System und einem Illustrations-System beträgt also rund zwei Größenordnungen pro Asset `[doc]` `[ref-config]` `[derived]`
- **SOLLTE [SHOULD]** das gesamte Icon-Set unter ~64 KiB Flash halten, was die GRAYSCALE-Form bequem erlaubt — etwa vierzig 24-px-Icons plus eine Handvoll Hero-Glyphen `[derived]` `[policy]`
- **MUSS [MUST]** Schriften gegen dasselbe Budget rechnen: vier Größen, zwei davon mit `bpp: 4`, über einem begrenzten Glyphen-Set — und **MUSS [MUST]** die Firmware-Größe nach jeder Änderung an `bpp` oder einem Glyphen-Set neu prüfen, da beide multiplizieren `[doc]`
- **MUSS [MUST]** Icon- und Schrift-Assets ins Config-Repository einchecken, statt darauf zu bauen, dass eine Upstream-URL zur Build-Zeit auflöst — so bleibt der Build reproduzierbar und offline-fähig `[policy]`

### Verifikation

- **MUSS [MUST]** jede Farb-, Größen- und Asset-Entscheidung auf dem **physischen Panel** verifizieren, bevor sie als fertig gilt; `esphome config` validiert Schema, nicht Lesbarkeit, und Kontrast bei gedimmter Hintergrundbeleuchtung ist nur auf dem Gerät belegbar `[policy]`
- **MUSS [MUST]** jeden Screen im **vorgesehenen Betrachtungsabstand** und bei **reduzierter Hintergrundbeleuchtung** prüfen, nicht nur auf Armlänge bei voller Helligkeit `[policy]`
- **MUSS [MUST]** das `GRAYSCALE`-`alpha_channel`-Blending-Verhalten bei jedem Major-Version-Sprung erneut gegen den ESPHome-Quellcode prüfen, da es `[src]`-Tier ist und der Doku widerspricht — eine stille Änderung dort macht aus jedem umgefärbten Icon einen flachen Block `[policy]`
- **MUSS [MUST]** jeden ESPHome-Key und -Default gegen die offizielle Doku verifizieren, bevor er in eine Config eingeht, gemäß [`ha/upstream-docs-verification`](../upstream-docs-verification/de.md) `[policy]`
- **SOLLTE [SHOULD]** die Kontrastberechnung neu ausführen, sobald sich die Palette, ein Hintergrund oder `pixel_mode` ändert, statt der obigen Tabelle zu vertrauen `[derived]` `[policy]`

## Akzeptanzkriterien

- [ ] Jede auf dem Gerät verwendete Farbe ist eine der elf Palettenrollen, deklariert als `color:`-Komponente mit der spezifizierten ID; kein Hex-Literal steht in einem Page-Lambda oder Widget
- [ ] Der Kontrast wurde auf den **quantisierten** Werten berechnet, und jeder Text und jedes bedeutungstragende Icon erreicht 4,5:1 (unter 24 px) bzw. 3:1 (ab 24 px)
- [ ] `c_disabled` trägt keinen lesbaren Text, und `c_border` trägt weder Text noch ein bedeutungstragendes Icon
- [ ] Kein Zustand wird allein durch Farbe unterschieden — jeder unterscheidet sich zusätzlich in Glyphe, Text oder Position
- [ ] Es sind genau vier Schriften deklariert, mit 12 / 16 / 28 / 48 px, in Roboto, jede mit explizitem `size:`; `f_display` und `f_hero` nutzen `bpp: 4`
- [ ] Jeder antialiasierte Print-Aufruf übergibt eine Hintergrundfarbe, an der von seiner Überladung erwarteten Position
- [ ] Icons stammen aus MDI, werden ausschließlich mit 24 / 40 / 96 px gerendert, und keines ist kleiner als 24 px
- [ ] Monochrome Icons sind `GRAYSCALE` + `alpha_channel`, gezeichnet mit explizitem Vordergrund **und** der tatsächlichen Hintergrundfarbe der Zone; keine Zustandsfarbe wird durch ein dupliziertes Asset getragen
- [ ] Kein Icon verwendet `RGB` + `alpha_channel`, und kein Bild deklariert den nicht existierenden Typ `RGBA`
- [ ] Jede Page trägt eine Aussage, folgt der Hierarchie Identität → Zustand → Qualifizierer → Systemstatus, und der Statusstreifen trägt ausschließlich Gerätezustand
- [ ] Inhalt, der in den vorgeschriebenen Größen nicht passt, wurde zu einer zweiten Page und nicht zu kleinerer Schrift
- [ ] Auf dem LVGL-Pfad werden dieselbe Palette und Skala verwendet, `dark_mode: true` ist die Grundlage, Rollen sind `style_definitions:`, interaktives Feedback ist an LVGL-Zustände gebunden, und jedes `image_recolor` ist mit `image_recolor_opa` gepaart
- [ ] Auf keinem der beiden Pfade existiert ein großflächiger Verlauf
- [ ] Das Icon- und Schrift-Asset-Set wurde gegen Flash budgetiert und die Firmware-Größe neu geprüft
- [ ] Das Ergebnis wurde auf dem physischen Panel im vorgesehenen Betrachtungsabstand und bei reduzierter Hintergrundbeleuchtung begutachtet

## Offene Fragen

- **Light-Variante**: Die Palette ist nur dunkel. Home Assistant liefert ein vollständiges Light-Token-Set, und eine BOX auf einem hellen Schreibtisch mag es wollen — aber ein Theme-Wechsel zur Laufzeit macht jede `color:`-ID zu einem Lambda, was der Immediate-Mode-Pfad nicht günstig abbildet. Ob eine zweite statische Palette zur Build-Zeit ausgewählt werden soll oder gar nichts, braucht ein reales Deployment, das sie will.
- **Hero-Icon gegen Illustration**: Diese Spec macht die 96-px-MDI-Glyphe zum Zustandsträger für Raumdistanz, bei ~9 KiB. Die Referenz-Configs verwenden stattdessen vollflächige Illustrationen mit je ~300 KiB. Der Tausch ist Lesbarkeit-pro-Byte gegen Wärme, und er wurde auf diesem Panel nicht mit Nutzern getestet.
- **Typo-Skala gegen das Referenz-Zonenraster**: Die Zonenhöhen der Schwester-Spec wurden an einem Layout mit 15-px- und 30-px-Schriften gemessen; diese Spec spezifiziert 16 px und 28 px aus der HA-Skala. Die Stufen passen in die bestehenden Zonenhöhen von 30 px und 50 px, aber die Zonentabelle wurde dafür nicht neu abgeleitet — ob die Einzüge optisch noch zentrieren, ist eine Messung am Gerät.
- **`mdil:` für große Glyphen**: Material Design Light ist eine Familie mit dünnerem Strich. Bei 96 px könnte der Standard-MDI-Strich als schwer wirken, und `mdil:` wäre möglicherweise die bessere Hero-Familie — hier ungetestet, und sie deckt deutlich weniger Icons ab, was das Set entgegen der obigen Regel auf zwei Familien aufteilen würde.
