# Skill: `ha-esphome-display-author`

Status: draft

## Kontext

`spec/ha/esp32-s3-box-display` ist die umfangreichste Rendering-Spec im ESPHome-Cluster und hatte kein operationalisierendes Artefakt: Sie legt die Entscheidung über den Rendering-Pfad fest, ein aus einer ausgelieferten Konfiguration gemessenes Layout-Raster, die Redraw-Disziplin, die `update_interval: never` erzwingt, und die Asset-Kosten, die entscheiden, was in den Flash passt. Diese Regeln lassen sich aus den ESPHome-Komponenten-Seiten nicht ableiten — sie sind das Ergebnis einer genauen Lektüre einer Referenzkonfiguration — und genau deshalb erzeugt Bildschirm-Inhalt aus dem Gedächtnis Layouts, die validieren und falsch rendern.

Ihre Schwester-Spec `spec/ha/esp32-s3-box-display-design` liefert die Ebene, die jene Spec ausdrücklich ausschließt: Palette, Typo-Skala, Icon-Skala und Page-Struktur, aus denen ein Screen komponiert wird. Dieser Skill operationalisiert beide, denn die Trennung ist eine Grenze der Spec-Autorenschaft, keine des Arbeitsablaufs — niemand platziert eine Page, ohne auch ihre Farben und Größen zu wählen, und genau diese je Page wählen zu lassen erzeugt ein Gerät, auf dem jeder Screen wie ein anderes Produkt aussieht.

## Scope

Ein Display eines Geräts pro Aufruf. Pages, das einzelne Redraw-Skript, Layout-Zonen, Fonts, Bilder, Farben, das darauf angewandte Design-System und die Guards, die Render-Code vor Faults bewahren. Beide Rendering-Pfade werden unterstützt; die Wahl fällt einmal und wird nie gemischt, und das Design-System ist über beide hinweg identisch.

## Ziele

- Die Entscheidung über den Rendering-Pfad explizit und dokumentiert machen — im Wissen, dass ihre Umkehr ein Rewrite und kein Refactoring ist
- Jedem erreichbaren Zustand — auch den degradierten — eine Page geben, sodass ein Gerät nie ein veraltetes Bild statt eines Problems zeigt
- Render-Code rein halten: Zustand in Globals oder Text-Sensoren, Formatierung vor dem Render-Schritt, Guards gegen alles, was fehlen kann
- Geometrie am Zonen-Raster der Spec verankern statt sie je Page neu zu erfinden
- Farbe, Typografie und Icon-Größe zu einem Nachschlagen im Design-System machen statt zu einer Entscheidung je Page, damit ein Gerät sich als ein Produkt liest
- Asset-Kosten zu einer genannten Zahl machen, bevor daraus eine Firmware wird, die nicht mehr passt

## Nicht-Ziele

- Die Hardware-Anbindung des Panels — SPI-Pins, Model-Preset, Backlight (Eigentum von `ha-esphome-config-augment` mit `spec/ha/esp32-s3-box`)
- Woher die angezeigten Werte stammen (Eigentum von `ha-esphome-binding-add`)
- Der Voice-Assistant-Lebenszyklus, der die Referenz-Screens treibt (Eigentum von `ha-esphome-voice-satellite-add`)
- Divoom-Pixoo-Displays — eine eigene Gerätefamilie mit eigenen Specs und Skills
- Das Design-System selbst zu erweitern — eine Farbrolle, eine Typo-Stufe oder eine Icon-Größe, die es nicht gibt, ist eine Änderung an `spec/ha/esp32-s3-box-display-design`, einmal entschieden und nicht im Lauf improvisiert
- Panel-Geometrien jenseits der von den Grounding-Specs vermessenen

## Anforderungen

- **MUSS** `spec/ha/esp32-s3-box-display/en.md` und `spec/ha/esp32-s3-box-display-design/en.md` lesen, bevor eine Koordinate, ein Key, ein Default, eine Farbe oder eine Größe ausgegeben wird, und `spec/ha/esp32-s3-box/en.md` für die zugrunde liegende Anbindung heranziehen
- **MUSS** genau einen Rendering-Pfad je Display festlegen, ihn dokumentieren und **DARF NICHT** Immediate-Mode-Pages mit LVGL auf demselben Display mischen
- **MUSS** `update_interval: never` mit einem einzelnen Redraw-Skript ausgeben, nach einem Page-Wechsel explizit aktualisieren und keinen Redraw aus einem Lambda heraus auslösen
- **MUSS** jedem erreichbaren Zustand eine eigene Page mit stabiler ID geben — inklusive Initialisierung, kein WLAN und kein Home Assistant — mit einem Default-Fallback im State-Mapping
- **MUSS** Berechnung, Formatierung und Kürzung aus Lambdas heraushalten und **MUSS** Lambdas gegen nicht verfügbare Werte, leere Collections und Division durch null absichern
- **MUSS** Geometrie aus dem Zonen-Raster der Spec zusammensetzen, den 20-Pixel-Rand und den 15-Pixel-Statusstreifen wahren und Mittelpunkte rechnerisch statt nach Augenmaß ableiten
- **MUSS** für anti-aliasten Text eine explizite Hintergrundfarbe an der Position übergeben, die das gewählte Overload erwartet, und an jedem Anker ein `TextAlign` nennen
- **MUSS** Fonts mit explizitem `size:` und begrenztem Zeichensatz deklarieren sowie Bilder mit explizitem `type:` und `resize:` in der zum `min_version` der Config passenden Deklarationsform
- **MUSS** jede Farbe aus den Palettenrollen der Design-Spec und jede Textgröße aus deren vierstufiger Skala nehmen und **DARF NICHT** ein Hex-Literal in ein Lambda oder Widget ausgeben oder eine Größe außerhalb der Skala einführen
- **MUSS** Icons ausschließlich aus MDI in den zugelassenen Größen beziehen, monochrome Icons als `GRAYSCALE` + `alpha_channel` deklarieren und sie mit explizitem Vordergrund **und** der tatsächlichen Hintergrundfarbe der Zone zeichnen
- **DARF NICHT** einen Zustand allein durch Farbe unterscheiden — jeder Zustand unterscheidet sich zusätzlich in Glyphe, Text oder Position — und **MUSS** berichten, welcher zweite Hinweisträger jeden Zustand trägt
- **MUSS** jede Page auf eine Aussage in der Hierarchie Identität → Zustand → Qualifizierer → Systemstatus begrenzen und auf eine weitere Page aufteilen, statt unter die Skala zu verkleinern
- **MUSS** das Flash- und Framebuffer-Budget der ergänzten Assets gegen die Pixelzahl des Panels beziffern
- **MUSS** Kürzungsgrenzen als gemessene Tabelle je Font, Größe und Boxbreite festhalten und sie vor dem Render-Schritt anwenden
- **MUSS** Bild-Assets ins Repository vendoren, statt zur Buildzeit auf eine Upstream-URL zu verweisen
- **MUSS** jede Rendering-API und jeden Key gegen die offizielle ESPHome-Dokumentation gemäß `spec/ha/upstream-docs-verification` verifizieren
- **MUSS** die Verifikation am Gerät als offenen Schritt melden, weil `esphome config` ein Layout akzeptiert, das außerhalb des Bildschirms rendert

## Akzeptanzkriterien

- [ ] Ein Lauf dokumentiert den Rendering-Pfad und erzeugt keine Konfiguration, die beide mischt
- [ ] Jeder im Pre-flight genannte Zustand, degradierte eingeschlossen, hat eine Page und ist über das State-Mapping erreichbar
- [ ] Die ausgegebenen Lambdas enthalten keine Formatierung, keine Geschäftslogik und keinen ungeprüften Divisions- oder Entity-Zugriff
- [ ] Jede ausgegebene Farbe löst sich auf eine Palettenrolle und jede Textgröße auf eine Skalenstufe auf; kein Hex-Literal erreicht ein Lambda oder Widget
- [ ] Icons sind MDI mit 24 / 40 / 96 px, monochrome sind `GRAYSCALE` + `alpha_channel` und werden mit beiden Farbargumenten gezeichnet, und keine Zustandsfarbe wird von einem duplizierten Asset getragen
- [ ] Der Bericht nennt Flash-Kosten der ergänzten Assets, das Framebuffer-Budget, die Kürzungstabelle, die verwendeten Palettenrollen und Typo-Stufen, den zweiten Hinweisträger jedes farblich unterschiedenen Zustands und die noch offene Verifikation am Gerät samt Prüfung bei gedimmter Hintergrundbeleuchtung

## Offene Fragen

- Die offene Animations-Frage der Grounding-Spec wird geerbt: Dieser Skill gibt Multi-Frame-Assets nur auf ausdrückliche Operator-Entscheidung aus und nennt dann die Flash-Kosten pro Frame.
- Das `GRAYSCALE`-`alpha_channel`-Blending-Verhalten der Design-Spec ist `[src]`-Tier und wird von der ESPHome-Dokumentation widersprochen. Dieser Skill gibt es als Standard-Icon-Form aus; ändert ein künftiges ESPHome-Release diesen Zeichenpfad, wird jedes umgefärbte Icon zu einem flachen Block, und die Icon-Regel des Skills muss neu entschieden statt je Gerät geflickt werden.
