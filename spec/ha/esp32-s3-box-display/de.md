# ESPHome-Gerät: ESP32-S3-BOX-Display (Rendering und Platzierung)

Status: draft

## Kontext

Die ESP32-S3-BOX trägt ein 2,4-Zoll-Farbpanel mit **320×240** an SPI — das eine Bauteil des Geräts, auf das ein Nutzer dauerhaft schaut. [`ha/esp32-s3-box`](../esp32-s3-box/de.md) legt fest, *dass* das Panel existiert und wie es verdrahtet und gebunden wird (SPI-Pins, Model-Preset, `invert_colors`, Backlight). Diese Spec setzt dort an, wo jene aufhört: **was auf diesen 76.800 Pixeln gezeichnet werden kann und wo.**

ESPHome bietet auf diesem Panel zwei sich gegenseitig ausschließende Rendering-Wege, und die Wahl ist architektonisch, nicht kosmetisch:

- die **`display:`-Komponente** mit `pages:` und C++-`lambda`-Blöcken — eine Immediate-Mode-Leinwand, bei der jedes Bild vom Config-Autor komplett neu gezeichnet wird. So arbeiten alle drei offiziellen Referenzkonfigurationen `[ref-config]`.
- **`lvgl:`** — ein Retained-Mode-Widget-Toolkit mit Objekten, Styles, Layouts und Event-Handlern, bei dem das Framework verfolgt, was sich geändert hat, und nur das neu zeichnet `[doc]`.

Keiner der beiden ist eine Obermenge des anderen. Der Immediate-Mode-Weg ist kompakt und vollständig vorhersagbar, aber jede Layout-Entscheidung ist eine fest codierte Pixel-Koordinate. Der LVGL-Weg bringt Ausrichtung, Layouts und Touch-Interaktion — zum Preis von Speicher, Binärgröße und einem zweiten Denkmodell. Eine Device-Config wählt einen Weg pro Display und bleibt dabei.

Die Pixel-Layout-Konventionen dieser Spec sind an der ESPHome-Referenzkonfiguration der BOX-3 verankert, die ein vollständig ausgearbeitetes Beispiel des Immediate-Mode-Wegs ist: vollflächige Illustrationen, gerahmte Textboxen an festen Koordinaten, ein Fortschrittsbalken in den unteren 15 Pixeln und ein zentriertes Timer-Widget `[ref-config]`. Diese konkreten Konstanten sind die empirische Grundlage des hier vorgeschlagenen Layout-Rasters.

Diese Spec ist das BOX-3-Gegenstück zu den Pixoo-Rendering-Specs (`ha/pixoo-pixel-art`) — dieselbe Idee eine Achse weiter: Die Geräte-Spec sagt, wie die Hardware gebunden wird, die Rendering-Spec sagt, wie man etwas Sinnvolles darauf bringt.

### Quellen-Tiers

Die Evidenz-Tiers werden exakt so verwendet wie in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) §„Quellen-Tiers" definiert: `[doc]` für die offizielle ESPHome-Komponenten-Dokumentation, `[ref-config]` für die offiziellen Board-Configs in `esphome/wake-word-voice-assistants`, `[bsp]` für Espressifs Board-Support-Package, `[vendor]` für Espressifs Produktdokumentation, `[src]` für Verhalten, das real, aber undokumentiert ist und deshalb aus dem ESPHome-Quellbaum belegt wird, und `[policy]` für eine nolte-Portfolio-Regel, die kein Upstream-Fakt ist. Mit `[ref-config]` markierte Layout-Konstanten sind aus einer ausgelieferten Konfiguration gemessen; das daraus abgeleitete Raster ist `[policy]`.

Verifiziert 2026-08.

## Ziele

- Die Wahl des Rendering-Wegs (`display:` + `pages:` gegenüber `lvgl:`) zu einer expliziten, begründeten Entscheidung machen statt zu einem Zufall des zuerst kopierten Beispiels
- Die Leinwand fixieren: Koordinatensystem, Ursprung, Schutzzonen und ein wiederverwendbares Layout-Raster für 320×240, abgeleitet aus einer ausgelieferten Konfiguration
- Die vollständige Zeichenfläche dokumentieren — Primitive, Text, Bilder, Farben — samt der Einschränkungen, die auf diesem Panel wirklich beißen (Anti-Aliasing braucht eine Hintergrundfarbe, Fonts kosten Flash, Bilder kosten sehr viel Flash)
- Das Refresh-Modell definieren: warum dieses Panel mit `update_interval: never` betrieben wird, wer ein Neuzeichnen auslöst und wie Flackern vermieden wird
- Datengetriebenen Inhalten eine Disziplin geben: wie Live-Werte auf den Bildschirm kommen und was passiert, wenn sie länger sind als der zugewiesene Platz
- Das Speicherbudget ehrlich benennen — ein vollflächiger Framebuffer kostet auf diesem Panel ~150 KiB, und diese Zahl entscheidet, was sonst noch hineinpasst
- Den LVGL-Weg so weit abdecken, dass ein Projekt ihn bewusst wählen und wissen kann, was er verändert

## Nicht-Ziele

- Die Hardware-Bindung des Panels erneut darstellen — SPI-Pins, Model-Preset, `invert_colors`, Reset-Pin-Invertierung und die Backlight-Light-Entity gehören zu [`ha/esp32-s3-box`](../esp32-s3-box/de.md) und werden referenziert, nicht wiederholt
- Eine vollständige LVGL-Widget-Referenz — der LVGL-Abschnitt deckt Platzierung, Styling, Pages, Touch-Bindung und Laufzeit-Updates ab; Options-Kataloge je Widget bleiben bei der Upstream-Dokumentation
- Grafikdesign-Beratung (Farbenlehre, Ikonografie, typografische Ästhetik) — diese Spec regelt die Mechanik der Platzierung, nicht den darauf angewandten Geschmack
- Die Verallgemeinerung dieser Regeln auf jedes ESPHome-Display — die Konstanten hier sind 320×240-spezifisch; eine generische Rendering-Spec kann später destilliert werden, wenn eine zweite Panel-Geometrie ins Portfolio kommt
- Touch-*Gesten*-Semantik und Screen-Flow-Design — Touch wird nur so weit behandelt, wie es in LVGL oder einen Seitenwechsel einbindet
- Die Voice-Assistant-Zustandsmaschine, die die Referenzbildschirme treibt — dieser Lebenszyklus lebt in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) §„Voice-Assistant-Bindung"; hier ist er nur Konsument von Pages

## Anforderungen

### Wahl des Rendering-Wegs

- Pro Display **MUSS [MUST]** genau ein Rendering-Weg gewählt und die Wahl in der Config festgehalten werden: `display:` mit `pages:`/`lambda` (Immediate Mode) **oder** `lvgl:` (Retained Mode) `[policy]`
- Beide **DÜRFEN NICHT [MUST NOT]** auf einem Display gemischt werden: LVGL verlangt, dass ihm das Display übergeben wird (`auto_clear_enabled: false`, kein Display-`lambda`), sodass ein übrig gebliebenes Page-Lambda entweder wirkungslos ist oder mit LVGL um den Puffer kämpft `[doc]`
- Für Status-Anzeigegeräte **SOLLTE [SHOULD]** der **Immediate-Mode**-Weg gewählt werden — ein fester Satz vollflächiger Zustände, getrieben von externen Ereignissen, mit wenig oder keiner Touch-Interaktion; so arbeiten die Referenzkonfigurationen, und die gesamte UI bleibt in einer Datei reviewbar `[ref-config]` `[policy]`
- **LVGL** **SOLLTE [SHOULD]** gewählt werden, wenn der Bildschirm eine interaktive Bedienfläche ist — Buttons, Slider, Arcs, Tabs, scrollende Listen oder alles, wo Touch den Zustand auf dem Gerät selbst ändert `[doc]` `[policy]`
- Die Entscheidung **SOLLTE [SHOULD]** als teuer umkehrbar behandelt werden: Page-Lambdas und Widget-Bäume teilen keinen Code, ein späterer Wechsel ist also eine Neuschreibung der gesamten UI, kein Refactoring `[policy]`

### Leinwand und Koordinatensystem

- Die Leinwand **MUSS [MUST]** als **320 breit × 240 hoch** mit dem Ursprung `(0, 0)` **oben links** behandelt werden; x wächst nach rechts, y nach unten `[doc]` `[ref-config]`
- Die Abmessungen **SOLLTEN [SHOULD]** zur Laufzeit über `it.get_width()` / `it.get_height()` gelesen werden, statt 320/240 überall dort fest zu codieren, wo eine Mitte oder eine Kante gemeint ist — die Referenzkonfiguration zentriert ihre Illustrationen mit `it.image(it.get_width() / 2, it.get_height() / 2, id(...), ImageAlign::CENTER)` `[ref-config]` `[doc]`
- Es **MUSS [MUST]** berücksichtigt werden, dass `rotation:` die effektive Breite und Höhe ändert: Ein um 90° oder 270° gedrehtes Display bietet eine 240×320-Leinwand, und jede fest codierte Koordinate wandert stillschweigend `[doc]`
- Außerhalb von `0…319` / `0…239` **DARF NICHT [MUST NOT]** gezeichnet werden; wo Inhalt überlaufen kann, ist der Bereich mit `it.start_clipping(left, top, right, bottom)` / `it.end_clipping()` bewusst zu begrenzen `[doc]`
- Ein **20-Pixel-Außenrand** **SOLLTE [SHOULD]** frei von wesentlichem Inhalt bleiben und die unteren **15 Pixel** als Statusstreifen behandelt werden, passend zum Referenz-Layout `[ref-config]` `[policy]`

### Refresh-Modell und Redraw-Disziplin

- Am Display **MUSS [MUST]** `update_interval: never` gesetzt und das Neuzeichnen explizit ausgelöst werden; die Referenzkonfigurationen rendern ereignisgetriebene Bildschirme und rufen `component.update` / `id(display).update()` selbst auf, statt auf einen Timer zu setzen `[ref-config]`
- Jedes Neuzeichnen **MUSS [MUST]** durch **ein** Script laufen (in der Referenzkonfiguration `draw_display`), statt `update`-Aufrufe über Automations zu verstreuen — ein einziger Einstiegspunkt ist das, was Bildschirm- und Anwendungszustand am Auseinanderlaufen hindert `[ref-config]` `[policy]`
- Es **MUSS [MUST]** verstanden werden, dass ein Neuzeichnen im Immediate Mode eine **Vollbild**-Operation ist: Das Display wird vor dem Lambda geleert, sofern nicht `auto_clear_enabled: false` gesetzt ist, und das Lambda muss alles neu malen, was sichtbar sein soll `[doc]`
- Jedes Page-Lambda **SOLLTE [SHOULD]** mit einem expliziten `it.fill(<Hintergrundfarbe>)` beginnen, statt sich auf das implizite Leeren zu verlassen, damit der Hintergrund der Seite eine ausgesprochene Eigenschaft der Seite ist `[ref-config]` `[policy]`
- Neu gezeichnet **SOLLTE [SHOULD]** nur bei tatsächlich sichtbaren Zustandsänderungen werden — Pipeline-Phasenwechsel, Verbindungswechsel, Timer-Ticks — weil jedes Neuzeichnen den vollen Framebuffer über SPI schiebt `[ref-config]` `[policy]`
- Das Redraw-Script **DARF NICHT [MUST NOT]** aus einem Page-Lambda heraus aufgerufen werden; Lambdas sind Render-Code, und ein Render aus einem Render heraus auszulösen ist ein Reentranz-Fehler `[policy]`

### Pages und Zustandsabbildung

- Diskrete Bildschirmzustände **MÜSSEN [MUST]** als `pages:` mit stabilen IDs modelliert werden, eine Seite pro Zustand, statt als Verzweigungen innerhalb eines einzigen Lambdas `[ref-config]` `[doc]`
- Der aktuelle Zustand **SOLLTE [SHOULD]** in einer `globals:`-Variablen gehalten und an genau einer Stelle auf Pages abgebildet werden — die Referenzkonfiguration hält einen Integer `voice_assistant_phase` und schaltet in `draw_display` darauf, mit einem `default:`-Zweig, der auf die Idle-Seite zurückfällt `[ref-config]`
- Für jeden erreichbaren Zustand **MUSS [MUST]** eine Seite existieren, auch für die degradierten: Initialisierung, kein WLAN und kein Home Assistant sind in der Referenzkonfiguration eigene Seiten, kein Fehler-Overlay `[ref-config]`
- Seiten **KÖNNEN [MAY]** mit den Actions `display.page.show`, `display.page.show_next` und `display.page.show_previous` gewechselt und Wechsel über den Trigger `on_page_change` (mit `from`-/`to`-Filter) behandelt werden `[doc]`
- Auf einen Seitenwechsel **MUSS [MUST]** in einer ereignisgetriebenen Config ein explizites Update folgen: Mit `update_interval: never` bringt das Anzeigen einer Seite sie noch nicht auf das Panel `[ref-config]` `[doc]`
- Page-Lambdas **SOLLTEN [SHOULD]** frei von Fachlogik bleiben — rechnen in Scripts oder Globals, rendern im Lambda — damit eine Seite eine reine Funktion des Zustands bleibt `[policy]`

### Zeichen-Primitive

- Der vollständige Primitiv-Satz **MUSS [MUST]** über das `it`-Objekt innerhalb eines Lambdas angesprochen werden: `line`, `rectangle`, `filled_rectangle`, `circle`, `filled_circle`, `triangle`, `filled_triangle`, `filled_ring`, `filled_gauge`, `regular_polygon`, `filled_regular_polygon`, `draw_pixel_at` sowie `fill` — jeweils mit optionalem abschließendem Farbargument. `clear()` existiert ebenfalls, aber nur im Quellcode, nicht in der Komponenten-Dokumentation `[doc]` `[src]`
- Gerahmte Flächen **SOLLTEN [SHOULD]** wie in der Referenzkonfiguration gebaut werden — ein `filled_rectangle` in der Füllfarbe, gefolgt von einem `rectangle` in der Rahmenfarbe an identischen Koordinaten — statt vier Linien zu zeichnen `[ref-config]`
- Für radialen Fortschritt **SOLLTEN [SHOULD]** `filled_gauge` / `filled_ring` und für linearen Fortschritt eine Zwei-Rechteck-Konstruktion verwendet werden; der Referenz-Timerbalken zeichnet eine weiße Spur (`0, 225, 320, 15`) und eine eingerückte farbige Füllung (`0, 226, <n>, 13`), deren Breite dem verbleibenden Anteil der Gesamtzeit entspricht `[doc]` `[ref-config]`
- Fortschrittsbreiten **MÜSSEN [MUST]** in ganzzahligen Pixeln berechnet und der Divisor abgesichert werden: Die Referenzkonfiguration teilt durch `max(total_seconds, 1)`, bevor sie auf 320 px skaliert, und zeichnet gar nicht, wenn das Ergebnis null ist `[ref-config]`
- Ein `graph:`, `qr_code:` oder `image:` **KANN [MAY]** über die entsprechenden Aufrufe `it.graph` / `it.qr_code` / `it.image` gerendert werden, die jeweils ein Alignment-Argument annehmen `[doc]`
- Ein neues Panel oder eine neue Geometrie **SOLLTE [SHOULD]** mit `show_test_card: true` verifiziert werden, bevor ein Layout debuggt wird, damit eine falsche `color_order` oder ein falscher Offset zuerst ausgeschlossen ist `[doc]`

### Text und Fonts

- Jeder Font **MUSS [MUST]** als `font:`-Komponente mit explizitem `size:` in Pixeln deklariert werden. Das ist eine Portfolio-Regel, keine Schema-Anforderung: `size` ist optional und **defaultet auf 20** bei skalierbaren Fonts (bzw. auf die erste verfügbare Größe bei Bitmap-Fonts) — eine weggelassene Größe rendert also still in der falschen Größe, statt zu scheitern. Da ein Font pro Größe zur Compile-Zeit gerastert wird, bedeutet dieselbe Schrift in zwei Größen **zwei** Font-Komponenten `[doc]` `[policy]`
- Der Zeichensatz **MUSS [MUST]** über `glyphs:` oder `glyphsets:` bewusst eingeschränkt werden, weil jedes zusätzliche Glyph in jeder deklarierten Größe Flash kostet. `glyphsets` defaultet auf `GF_Latin_Kernel`; die Referenzkonfigurationen überschreiben das mit `GF_Latin_Core` und deklarieren **kein** `glyphs:` — ihre Substitution `allowed_characters` ist tote Konfiguration, nirgends referenziert, und Upstream vermerkt selbst, dass sie mit dem ausgelieferten rein lateinischen Font sinnlos ist. Beim Überschreiben von `glyphsets` ist die dokumentierte Falle zu beachten, dass `GF_Latin_Kernel` für Ziffern und Leerzeichen weiterhin eingebunden werden muss `[doc]` `[ref-config]`
- Eine **Hintergrundfarbe** **MUSS [MUST]** übergeben werden, wenn der Font antialiast ist (`bpp` größer als 1), und sie **MUSS [MUST]** an der Position stehen, die das jeweilige Overload erwartet — beide unterscheiden sich, das ist die Falle:
  - `it.print(x, y, font, foreground, align, text, background)` — Hintergrund **zuletzt**, nach dem Text. Diese Form zeigt die Dokumentation.
  - `it.printf(x, y, font, foreground, background, align, format, …)` — Hintergrund an **fünfter** Stelle, vor dem Align, weil die variadischen Format-Argumente zuletzt stehen müssen. Dieses Overload existiert real, ist aber **undokumentiert**; es steht nur in `esphome/components/display/display.h`.

  Einen Hintergrund in der `print`-Position an `printf` zu übergeben scheitert nicht laut — es bindet ein anderes Overload, und die Farbe wird als Format-Argument verbraucht `[doc]` `[src]`
- `bpp` **SOLLTE [SHOULD]** für kleine UI-Texte niedrig bleiben (Default) und nur für große Schaugrößen erhöht werden, da höhere Bittiefen „die Binärgröße erheblich vergrößern" `[doc]`
- Text **MUSS [MUST]** mit einem expliziten `TextAlign`-Wert positioniert werden, statt sich auf den Default `TOP_LEFT` zu verlassen, wenn der Anker eine Mitte oder eine rechte Kante sein soll; verfügbar sind die neun Box-Ausrichtungen plus `BASELINE_LEFT` / `BASELINE_CENTER` / `BASELINE_RIGHT` `[doc]`
- Zentrierter Text **SOLLTE [SHOULD]** an `it.get_width() / 2` mit `TextAlign::TOP_CENTER` (oder einer `CENTER`-Variante) verankert werden, statt einen linken Offset aus der erwarteten Stringbreite zu schätzen `[doc]` `[policy]`
- Jeder String variabler Länge **MUSS [MUST]** vor dem Zeichnen begrenzt werden: Die Referenzkonfiguration kürzt bei 32 Zeichen über `esphome::str_truncate(name, 31)` plus Auslassungszeichen, angewandt im `on_value` des Text-Sensors statt im Lambda `[ref-config]`
- Dieses Limit **MUSS [MUST]** durch Messen ermittelt und in einer kleinen projektweisen Tabelle festgehalten werden (Font × Größe × Boxbreite → Zeichenbudget), statt es zur Render-Zeit zu berechnen: Bei den 15 Pixel Figtree der Referenz in einem 280-Pixel-Rahmen passen rund 32 Zeichen, und jeder neue Font, jede neue Größe oder Boxbreite ergänzt eine gemessene Zeile, statt diese Zahl wiederzuverwenden `[ref-config]` `[policy]`
- Formatierte Zeit **KANN [MAY]** mit `it.strftime(x, y, font, color, align, format, time)` gerendert werden; für vergangene/verbleibende Dauern formatiert die Referenzkonfiguration die Ziffern selbst (`HH:MM` oberhalb einer Stunde, sonst `MM:SS`) und gibt sie mit `printf` aus `[doc]` `[ref-config]`

### Bilder

- Jedes Bild **MUSS [MUST]** unter `image:` mit explizitem **`platform:`** (`file` für zur Compile-Zeit eingebettete Assets, `animation` für mehrbildrige, `online_image` für Laufzeit-Download), einer `id:` und einem Compile-Zeit-`resize:` für die einzunehmende Box deklariert werden. `image:` ist upstream zur Plattform-Komponente geworden; die Referenzkonfigurationen nutzen noch die ältere plattformlose Form, die akzeptiert wird, aber nicht dem entspricht, was die Dokumentation zeigt. Zu beachten: `resize` passt das Bild **unter Wahrung des Seitenverhältnisses in die Box ein** — `resize: 320x240` füllt dieses Panel nur bei einer 4:3-Quelle `[doc]` `[ref-config]`
- `type:` **MUSS [MUST]** bewusst gewählt werden — der Key ist **erforderlich**, und die dokumentierten Werte sind `BINARY`, `GRAYSCALE`, `RGB565` und `RGB`. Ein **`RGBA` existiert nicht**: Ein Alphakanal wird über `transparency:` angefordert, was bei `RGB565` und `RGB` je ein Byte pro Pixel hinzufügt. Der Typ bestimmt die Flash-Kosten pro Pixel: `BINARY` 1 Bit, `GRAYSCALE` 1 Byte, `RGB565` 2 Byte (3 mit Alpha), `RGB` 3 Byte (4 mit Alpha) `[doc]` `[ref-config]`
- Der Flash-Bedarf eines Bildes **SOLLTE [SHOULD]** vor dem Hinzufügen budgetiert werden, mit den obigen Kosten pro Pixel gegen die 76 800 Pixel dieses Panels: `RGB565` sind 150 KiB pro vollflächigem Bild, und die Wahl der Referenzkonfigurationen selbst — `type: RGB` mit `transparency: alpha_channel`, vier Byte pro Pixel — sind **300 KiB je Bild**. Jene Konfigurationen liefern acht solcher Illustrationen aus, rund 2,4 MB Flash vor jedem weiteren Asset; deshalb sollte ein Statusgerät mit wenigen Screens zuerst zu `RGB565` oder `GRAYSCALE` greifen `[doc]` `[ref-config]` `[policy]`
- `transparency: chroma_key` oder `alpha_channel` **KANN [MAY]** genutzt werden, um ein Bild über einen Hintergrund zu komponieren, statt den Hintergrund in jedes Asset einzubacken — auf dem **Immediate-Mode-Pfad, den diese Spec als Hauptweg führt, bringt `alpha_channel` jedoch nichts**: Die Dokumentation ist ausdrücklich, dass die Bildfunktionen des Display-Lambdas „will draw or not draw the pixel, no blending with the background will be done", und dass Alpha-Blending „useful mainly when using LVGL" ist. Auf diesem Pfad ist `alpha_channel` ein zusätzliches Byte pro Pixel für ein binäres Ergebnis, das `chroma_key` bereits liefert. Graustufenbilder mit Transparenz bleiben bei einem Byte pro Pixel `[doc]`
- Bilder **MÜSSEN [MUST]** mit einem expliziten `ImageAlign` platziert werden, wenn der Anker nicht oben links liegt — ESPHome richtet standardmäßig oben links aus, eine zentrierte Illustration ist also `it.image(w / 2, h / 2, id(img), ImageAlign::CENTER)` `[doc]` `[ref-config]`
- Ein Bild **KANN [MAY]** zur **Compile**-Zeit aus einer URL bezogen werden (die Referenzkonfiguration zieht ihre Illustrationen von einer GitHub-Raw-URL) oder aus Material Design Icons; Laufzeit-Download ist eine andere Plattform (`online_image`) mit eigenem Speicherbedarf `[doc]` `[ref-config]`
- Bild-Assets **MÜSSEN [MUST]** ins Config-Repository gevendort und unter Versionskontrolle gehalten werden, statt darauf zu bauen, dass eine Upstream-URL zur Build-Zeit erreichbar bleibt — der Build bleibt reproduzierbar und offline-fähig, zum Preis der Repository-Größe `[policy]`

### Farben

- Wiederverwendbare Farben **MÜSSEN [MUST]** als `color:`-Komponenten mit IDs definiert (Hex-, Prozent- oder Integer-Form) und in Lambdas per ID referenziert werden, statt Literale über Seiten hinweg zu wiederholen — die Referenzkonfiguration definiert eine Farbe je Bildschirmzustand plus die beiden Timerbalken-Farben `[doc]` `[ref-config]`
- Eine Ad-hoc-Farbe **KANN [MAY]** inline als `Color(r, g, b)` in einem Lambda konstruiert werden, wo ein Einzelwert wirklich lokal ist `[doc]`
- Die Konstanten `Color::WHITE` / `Color::BLACK` **KÖNNEN [MAY]** genutzt werden, auf die sich die Referenzkonfiguration für Rahmen und Text stützt: Sie sind in ESPHomes eigenem `esphome/core/color.h` als `static const Color BLACK;` / `static const Color WHITE;` deklariert, sind also echte API und kein undokumentierter Zufall — sie fehlen lediglich in der Komponenten-Dokumentation, wofür genau der `[src]`-Tier existiert `[ref-config]` `[src]`
- Hintergrundfarben je Zustand **MÜSSEN [MUST]** über Substitutions parametrisiert werden, wenn eine Config nachträglich umthemebar sein soll, so wie die Referenzkonfiguration es mit ihren `*_illustration_background_color`-Substitutions tut `[ref-config]`
- Der Kontrast **SOLLTE [SHOULD]** am physischen Panel geprüft werden statt am Monitor — dies ist ein kleines, helles 2,4-Zoll-LCD, und die Backlight-Stufe ist eine nutzergesteuerte Light-Entity, die nicht immer auf 100 % steht `[policy]`

### Layout-Zonen und Platzierung

- Bildschirme **SOLLTEN [SHOULD]** aus diesem Zonenraster komponiert werden, abgeleitet aus dem Referenz-Layout, statt pro Seite Koordinaten zu erfinden `[ref-config]` `[policy]`:

| Zone | Rechteck (x, y, b, h) | Zweck |
|---|---|---|
| Vollflächiger Hintergrund | `0, 0, 320, 240` | `fill()` oder zentrierte vollflächige Illustration |
| Kopfbox | `20, 20, 280, 30` | Primärzeile (Anfrage / Titel), Text eingerückt bei `30, 25` |
| Zentrums-Widget | `80, 40, 160, 50` | Modaler Wert (Timer, große Zahl), Text verankert bei `120, 47` |
| Fußbox | `20, 190, 280, 30` | Sekundärzeile (Antwort / Status), Text eingerückt bei `30, 195` |
| Statusstreifen | `0, 225, 320, 15` | Fortschrittsbalken / Timeline, eingerückte Füllung bei `0, 226, …, 13` |

- Der 20-Pixel-Seitenrand und der 10-Pixel-Texteinzug **MÜSSEN [MUST]** über alle Seiten hinweg konsistent bleiben: Die Referenzboxen beginnen bei x = 20 mit einer Breite von 280 (was rechts 20 px lässt), und ihr Text beginnt bei x = 30 `[ref-config]`
- 30 Pixel **SOLLTEN [SHOULD]** als Standard-Zeilenhöhe für einen 15-Pixel-Font gelten — eine Textzeile plus Polsterung — und 50 Pixel für den 30-Pixel-Schaufont `[ref-config]` `[policy]`
- Ein Widget fester Breite **SOLLTE [SHOULD]** rechnerisch statt nach Augenmaß zentriert werden: Das Referenz-Timer-Widget ist 160 px breit bei x = 80, also exakt `(320 − 160) / 2` `[ref-config]`
- Zwei Zonen **DÜRFEN NICHT [MUST NOT]** auf derselben Seite überlappen, sofern die Überlappung nicht bewusste Schichtung ist (Illustration darunter, gerahmte Box darüber) — im Immediate Mode überschreibt der spätere Aufruf den früheren schlicht, ohne Warnung `[doc]` `[policy]`
- Gemeinsames Mobiliar (Statusstreifen, Timer-Widget) **SOLLTE [SHOULD]** aus kleinen wiederverwendbaren `script:`-Einträgen gezeichnet werden, die jede Seite aufruft — so wie die Referenzkonfiguration es mit `draw_timer_timeline` und `draw_active_timer_widget` tut — statt den Zeichencode in jedes Page-Lambda zu kopieren `[ref-config]` `[policy]`

### Datengetriebene Inhalte

- Live-Werte **SOLLTEN [SHOULD]** in `text_sensor: {platform: template}` oder `globals:` bereitgestellt und im Lambda gelesen werden, statt aus Render-Code in den Zustand anderer Komponenten zu greifen `[ref-config]` `[policy]`
- Der Mechanismus, der diese Werte aus Home Assistant füllt — Zustands-Abo, aufrufbare Aktion, schreibbare Entity oder Rückkanal — **MUSS [MUST]** aus [`ha/esphome-ha-driven-content`](../esphome-ha-driven-content/de.md) bezogen werden, die auch das resultierende `on_value` an den einzigen Redraw-Einstiegspunkt dieser Spec bindet `[policy]`
- Formatierung, Kürzung und Einheitenbehandlung **MÜSSEN [MUST]** **vor** dem Render-Schritt erfolgen — im `on_value` des Sensors oder in einem Script — damit das Lambda nur bereits darstellbare Strings positioniert `[ref-config]` `[policy]`
- Für einen noch nicht verfügbaren Wert **MUSS [MUST]** ein expliziter Platzhalter gerendert werden statt eines leeren Bereichs; die Referenzkonfiguration veröffentlicht `"..."` in ihre Anfrage-/Antwort-Sensoren, wenn eine Pipeline-Runde beginnt `[ref-config]`
- Transiente Strings **SOLLTEN [SHOULD]** gelöscht werden, wenn der Zustand endet, der sie erzeugt hat, damit keine veraltete Antwort hinter einem späteren Bildschirm verharrt `[ref-config]`
- Lambdas **MÜSSEN [MUST]** gegen nicht verfügbare Eingaben abgesichert werden — eine nicht verfügbare Entity, eine leere Timer-Liste oder eine Division durch eine Gesamtzeit von null führt sonst innerhalb des Render-Codes zum Fehler, wo er sich als eingefrorener Bildschirm zeigt `[ref-config]` `[policy]`

### LVGL-Weg

- Wird LVGL gewählt, **MUSS [MUST]** ihm das Display übergeben werden: `auto_clear_enabled: false`, kein Display-`lambda` und `update_interval: never` am Display, wobei LVGL den Refresh-Zyklus besitzt (Default 16 ms) `[doc]`
- Der Touchscreen **MUSS [MUST]** über LVGLs `touchscreens:`-Key gebunden werden, statt rohe Koordinaten zu verarbeiten, damit Widgets `on_pressed`- / `on_long_pressed`-Events erhalten und Koordinaten LVGLs Rotation folgen `[doc]`
- Widgets **SOLLTEN [SHOULD]** mit `align:` gegen das Elternobjekt plus `x`-/`y`-Offsets positioniert werden statt mit absoluten Koordinaten — die Ausrichtungs-Konstanten (`TOP_LEFT`, `TOP_CENTER`, `CENTER`, `BOTTOM_RIGHT`, …) sind das, was ein Layout eine Größen- oder Rotationsänderung überleben lässt `[doc]`
- Für alles Listenartige oder Tabellarische **SOLLTE [SHOULD]** ein `flex`- oder `grid`-Layout auf einem Container verwendet und die manuelle `x`/`y`-Platzierung (`layout: NONE`, der Default) echten Freiform-Bildschirmen vorbehalten werden `[doc]`
- Bildschirmzustände **MÜSSEN [MUST]** als LVGL-`pages:` modelliert und mit `lvgl.page.show` / `lvgl.page.next` / `lvgl.page.previous` gewechselt werden; vom Durchblättern ausgenommene Seiten tragen `skip: true` `[doc]`
- Gestylt **SOLLTE [SHOULD]** über die dokumentierten Style-Keys werden (`bg_color`, `bg_opa`, `text_color`, `text_font`, `border_width`, `border_color`, `radius`, `pad_*`, `margin_*`) statt dekorative Primitive hinter Widgets zu zeichnen `[doc]`
- Widget-Inhalte **MÜSSEN [MUST]** zur Laufzeit über die Update-Actions geändert werden (`lvgl.label.update`, `lvgl.style.update` sowie die widget-gebundenen Komponenten-Plattformen), statt eine Seite neu aufzubauen — LVGL zeichnet dann nur den betroffenen Bereich neu `[doc]`
- `buffer_size` **SOLLTE [SHOULD]** bewusst dimensioniert werden: Der Default ist 100 % mit Laufzeit-Rückfall auf 12 %, falls die Allokation scheitert, und auf einem PSRAM-Board kann ein 12-%-Puffer im internen RAM einen vollen Puffer im PSRAM schlagen `[doc]`

### Speicher- und Performance-Budget

- Der Framebuffer **MUSS [MUST]** eingeplant werden, bevor weitere PSRAM-Verbraucher hinzukommen: Der `mipi_spi`-Treiber allokiert einen über `buffer_size` dimensionierten Puffer, standardmäßig 100 % des Bildschirms bei vorhandenem PSRAM — bei 320×240 und 16-Bit-Farbe sind das ~150 KiB `[doc]`
- Der volle Standardpuffer **SOLLTE [SHOULD]** auf diesem Board beibehalten werden, da es 16 MB Octal-PSRAM hat; ein verkleinertes `buffer_size` erzwingt mehrere Zeichendurchläufe pro Bild und kostet Performance, um Speicher zu sparen, den die BOX nicht sparen muss `[doc]` `[policy]`
- Die `data_rate` des Displays **MUSS [MUST]** bei den dokumentierten `40MHz` des Boards bleiben, sofern kein gemessenes Problem eine Änderung rechtfertigt — das BSP fixiert den Pixeltakt des Panels auf 40 MHz `[bsp]` `[ref-config]`
- Vollbild-Neuzeichnungen **SOLLTEN [SHOULD]** als dominierender Kostenfaktor dieses Panels behandelt und zuerst die Redraw-*Frequenz* reduziert werden (bei Zustandsänderung, nicht auf Timer), bevor einzelne Zeichenaufrufe optimiert werden `[ref-config]` `[policy]`
- `draw_rounding` **SOLLTE [SHOULD]** auf dem Default 2 bleiben, solange keine Artefakte auftreten; es rundet Zeichenbereiche auf eine Grenze für Controller, die das verlangen, und diese Grenzen sind „usually powers of 2" — die Dokumentation nennt das als Eigenschaft solcher Displays, nicht als Bedingung, die der Wert erfüllen müsste `[doc]`
- Font- und Bild-Assets **MÜSSEN [MUST]** gegen Flash gerechnet werden, nicht gegen RAM: Beide werden in die Firmware kompiliert, und einige vollflächige Bilder plus mehrere Fontgrößen dominieren das Binary `[doc]` `[policy]`

### Verifikation

- Jede Rendering-API, jeder Config-Key und jeder Default **MUSS [MUST]** gegen die offizielle ESPHome-Dokumentation verifiziert werden, bevor er in eine Config oder in diese Spec eingeht, gemäß [`ha/upstream-docs-verification`](../upstream-docs-verification/de.md) `[policy]`
- Die offiziellen Board-Referenzkonfigurationen **MÜSSEN [MUST]** als normatives Beispiel des Immediate-Mode-Wegs auf diesem Panel behandelt und Drittanbieter-Configs vorgezogen werden, wenn beide sich widersprechen `[policy]`
- Ein Layout **SOLLTE [SHOULD]** am physischen Panel validiert werden, bevor es als fertig gilt — Koordinaten, Kontrast und Kürzungsgrenzen sind nur am Gerät beweisbar, und `esphome config` akzeptiert bereitwillig ein Layout, das außerhalb des Bildschirms rendert `[policy]`
- Die Layout-Konstanten dieser Spec **SOLLTEN [SHOULD]** neu verifiziert werden, wann immer die Upstream-Referenzkonfiguration ihre Bildschirme ändert, da sie aus ihr gemessen und nicht von ihr spezifiziert sind `[policy]`

## Akzeptanzkriterien

- [ ] Der Rendering-Weg (`display:` + `pages:` oder `lvgl:`) ist explizit gewählt, festgehalten und wird auf einem Display nicht gemischt
- [ ] Das Display läuft mit `update_interval: never`, und jedes Neuzeichnen läuft über ein einziges benanntes Script
- [ ] Jeder erreichbare Zustand — inklusive Initialisierung, kein WLAN und kein Home Assistant — hat eine eigene Seite mit stabiler ID, und ein unbekannter Zustand fällt auf einen definierten Default zurück
- [ ] Page-Lambdas enthalten nur Rendering; der Zustand lebt in Globals oder Text-Sensoren, und Formatierung/Kürzung geschieht vor dem Render-Schritt
- [ ] Alle Koordinaten respektieren die 320×240-Leinwand mit einem 20-Pixel-Außenrand, und die unteren 15 Pixel sind dem Statusstreifen vorbehalten
- [ ] Mitten und Kanten sind aus `it.get_width()` / `it.get_height()` oder aus Arithmetik abgeleitet, nicht aus geschätzten Offsets
- [ ] Antialiaster Text wird mit expliziter Hintergrundfarbe gezeichnet, und jeder Textanker nennt sein `TextAlign`
- [ ] Jeder Font deklariert eine explizite `size` und einen begrenzten Zeichensatz; jedes Bild deklariert ein explizites `platform`, `resize` und `type`, und kein Bild nutzt den nicht existierenden Typ `RGBA`
- [ ] Strings variabler Länge werden auf ein für den tatsächlichen Font und die tatsächliche Boxbreite gemessenes Limit gekürzt, mit sichtbarem Auslassungszeichen
- [ ] Wiederverwendbare Farben existieren als `color:`-Komponenten mit IDs; Hintergrundfarben je Zustand sind über Substitutions parametrisiert
- [ ] Gemeinsames Mobiliar (Statusstreifen, Widgets) wird aus wiederverwendbaren Scripts gezeichnet statt pro Seite dupliziert
- [ ] Lambdas sind gegen nicht verfügbare Entities, leere Sammlungen und Null-Divisoren abgesichert
- [ ] Das Framebuffer-Budget (~150 KiB bei 100 % `buffer_size`) ist eingeplant, und die Flash-Kosten für Fonts/Bilder sind gegen die Firmware-Größe geprüft
- [ ] Wo LVGL genutzt wird, ist das Display korrekt übergeben (`auto_clear_enabled: false`, kein Lambda), der Touchscreen über `touchscreens:` gebunden und Widgets über `align:` plus Offsets platziert
- [ ] Das fertige Layout wurde am physischen Panel verifiziert, nicht nur über `esphome config`

## Offene Fragen

- **Animation**: ESPHome liefert `animation` als **Plattform von** `image:` (`image: - platform: animation`) mit allen Optionen der `file`-Plattform plus `next_frame()` / `prev_frame()` / `set_frame()`. Gibt es auf diesem Gerät einen Anwendungsfall, der die Flash-Kosten mehrbildriger Assets rechtfertigt — jedes Einzelbild zahlt denselben Preis pro Pixel wie ein Standbild —, wo doch der Seitenwechsel Zustandsübergänge bereits abdeckt? Ohne konkreten Gestaltungswunsch echt nicht entscheidbar, bleibt daher offen.

Per Entscheidung erledigt (hier festgehalten, damit die Begründung auffindbar bleibt, nicht als offene Arbeit): Der Rendering-Weg bleibt eine **projektweise** Wahl nach dem in *Wahl des Rendering-Wegs* genannten Kriterium — kein portfolioweiter Default; ein gemeinsames Layout-**Package** wird zurückgestellt, bis ein zweiter BOX-Screen es tatsächlich wiederverwenden würde, um nicht aus einem einzigen Beispiel zu abstrahieren; das Kürzungsbudget ist eine **gemessene Tabelle**, keine Render-Zeit-Berechnung; **Rotation** ist außerhalb des Scopes, solange das Zonenraster für 320×240 definiert ist; und Bild-Assets werden ins Config-Repository **gevendort**.
