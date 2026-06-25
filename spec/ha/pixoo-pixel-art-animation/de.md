# HA-Gerät: Pixel-Art-Animation auf der 64×64-Matrix

Status: draft

## Kontext

Diese Spec normiert das **Animieren von Pixel-Art** auf der 64×64-RGB-LED-Matrix des Divoom Pixoo 64 — also wie über die Zeit eine **bewegte Darstellung** entsteht. Der von der Frage adressierte Kern: Animation wird durch **Versetzen von Pixeln** (Bewegung) und **Anpassen von Farben** (Farb-/Wertänderung) über aufeinanderfolgende Frames erzeugt.

Entscheidend ist das **Frame-Modell der Integration** (`gickowtf/pixoo-homeassistant`, verifiziert gegen `pixoo64/_pixoo.py` v1.23.0): Jeder Push überträgt **genau einen Frame** (`Draw/SendHttpGif` mit `PicNum: 1`, `PicOffset: 0`, fortlaufender `PicID`, Reset via `Draw/ResetHttpGifId`). Eine Animation ist somit eine **Folge vollständiger Page-Re-Renders über die Zeit**, nicht eine in einem Aufruf übertragene Multi-Frame-Sequenz. Jeder gerenderte Page-Zustand ist ein Frame; „Bewegung" und „Farbwechsel" sind Funktionen einer **Phasen-/Zeitvariable**, die pro Frame neu ausgewertet wird.

Daraus folgt eine harte Eigenschaft des Liefer-Wegs: Frames werden einzeln per HTTP gepusht (Timeout 9 s je Command). Die selbst-treibende Page-Rotation arbeitet in **ganzzahligen Sekunden** — prozedurale Animationen laufen darüber praktisch bei **~1 fps**. Höhere Bildraten erfordern getriebene `update_page`-Schleifen (mit Crash-Risiko, siehe unten). Dieses Gerät/diese Integration eignet sich daher für **langsame Animationen** (Ticken, Pulsieren, langsames Wandern, Zustandswechsel), nicht für flüssige High-FPS-Bewegung.

Abgrenzung: Die statische Bildgestaltung (Palette, Konturen, Schattierung) liegt in `ha/pixoo-pixel-art` und wird hier vorausgesetzt — jeder Frame ist ein gültiges Pixel-Art-Bild nach jener Spec. Die Geräte-/Integrations-Mechanik (Page-Typen, `update_page`/`show_message`-Services, Resample-Modi) liegt in `ha/divoom-pixoo`. Diese Spec behandelt nur die **zeitliche Dimension** darüber.

## Ziele

- Die Animationsmodelle festschreiben: prozedurale Frame-Animation (Fokus), vorgerenderte GIF, native Geräte-Effekte
- Das Frame-Treiber- und Timing-Modell (kurzes `duration`, `update_page`-Schleife, Einzel-Frame-Push, Bildraten-Grenze) verbindlich klären
- Die **Phasen-/Zeitbasis** (aus `now()`, `timer`, `counter`) als Quelle der Frame-Auswahl normieren
- **Bewegung durch Pixel-Versatz** (Position als Funktion der Phase, ganzzahliges Raster, Looping) regeln
- **Farb-Animation** (Palette-Cycling, Wert-Pulsieren, Hue-Shift über Zeit, Blink/Fade in diskreten Stufen) regeln
- Frame-Kohärenz, Flicker-Vermeidung und Lesbarkeit über den Loop hinweg sichern
- Die Liefer-Pfade an `ha/divoom-pixoo` und die Bildgestaltung an `ha/pixoo-pixel-art` anbinden

## Nicht-Ziele

- Statische Einzelbild-Gestaltung (Palette, Konturen, Schattierung) — gehört zu `ha/pixoo-pixel-art`
- Geräte-/Integrations-Mechanik (Page-Typen, Service-Parameter, Entitäten, Resampling) — gehört zu `ha/divoom-pixoo`
- Das Erstellen der GIF-Dateien selbst (externes Tooling, Frame-Authoring, Hosting)
- Native, nicht von der Integration gesteuerte Animationen der Firmware (Clock-Faces, Visualizer, App-Channels) jenseits ihrer Einbindung als Page
- Garantien für flüssige Bildraten — das Einzel-Frame-Push-Modell macht hohe, gleichmäßige FPS geräteseitig nicht zusagbar

## Anforderungen

### Animationsmodelle

- **MUSS [MUST]** das passende Modell wählen: (a) **prozedurale Frame-Animation** — eine `components`-Page, deren Positionen/Farben aus einer Phasenvariable berechnet werden und die wiederholt re-gerendert wird (Fokus dieser Spec); (b) **vorgerendertes GIF** über `page_type: gif` (`Device/PlayTFGif`, exakt 16/32/64 px, vom Gerät nativ abgespielt); (c) **native Geräte-Effekte** (z. B. Clock/Visualizer) nur über ihre Page-Einbindung
- **MUSS [MUST]** verstehen, dass im prozeduralen Modell **jeder Frame ein vollständiger Page-Re-Render** ist, der genau einen Buffer pusht (`PicNum: 1`) — es gibt keine in einem Aufruf übertragene Frame-Liste
- **SOLLTE [SHOULD]** für **kontinuierliche, nicht daten-abhängige** Bewegung (Logo-Loop, Lauflicht) das vorgerenderte GIF bevorzugen; für **daten-getriebene** Animation (Werte, Zustände, Fortschritt) den prozeduralen Pfad
- **MUSS NICHT [MUST NOT]** annehmen, dass die `components`-`text`-Komponente nativ scrollt — der protokollseitige `Draw/SendHttpText`-Scroll (`speed`/`dir`) wird vom Komponenten-Pfad nicht genutzt; scrollender Text muss prozedural per Pixel-Versatz oder als GIF gelöst werden

### Frame-Treiber & Timing

- **MUSS [MUST]** einen Frame-Treiber wählen: **kurzes `duration`** auf der (Single-)Page (self-treibend — die Page re-rendert sich nach jedem Intervall) **oder** wiederholte **`update_page`**-Aufrufe aus einer Automation/einem Skript (event-getrieben)
- **MUSS [MUST]** akzeptieren, dass die `duration`-getriebene Rotation in **ganzzahligen Sekunden** arbeitet — die praktische Untergrenze liegt bei ~1 s/Frame (~1 fps); für „schnellere" Animation ist eine `update_page`-Schleife nötig
- **MUSS NICHT [MUST NOT]** `update_page` exzessiv „spammen" — häufiges Erzwingen von Re-Renders kann das Gerät zum Absturz bringen (siehe `ha/divoom-pixoo` §Services); Frame-Intervalle bewusst begrenzen
- **SOLLTE [SHOULD]** Bildraten **niedrig und gerätegeprüft** ansetzen — jeder Frame ist ein HTTP-Push (Timeout 9 s); Sub-Sekunden-Glätte ist nicht zugesichert
- **SOLLTE [SHOULD]** Frames **günstig** halten (wenige Komponenten, einfache Templates) — ein teurer Re-Render verlängert das effektive Frame-Intervall
- **KANN [MAY]** sich auf den internen `PicID`-Zähler und dessen automatischen Reset (`Draw/ResetHttpGifId`) verlassen — die Integration verwaltet ihn; eigene Frame-IDs sind nicht nötig

### Phasen-/Zeitbasis

- **MUSS [MUST]** eine **Phasenvariable** als Quelle der Frame-Auswahl definieren, abgeleitet aus `now()` (z. B. Sekunde/Minute), einem `timer` oder einem `counter`; alle Positionen/Farben sind Funktionen dieser Phase
- **SOLLTE [SHOULD]** die Phase für einen **nahtlosen Loop** modulo der Frame-Anzahl bilden (`phase = tick % frames`), sodass der letzte Frame stetig in den ersten übergeht
- **SOLLTE [SHOULD]** die Phase aus einer **monoton fortlaufenden** Quelle ziehen (z. B. `now().timestamp() | int`), nicht aus einem Wert, der springen/zurückspringen kann — sonst ruckelt die Bewegung
- **KANN [MAY]** mehrere unabhängige Phasen kombinieren (z. B. eine für Bewegung, eine langsamere für Farb-Cycling)

### Bewegung durch Pixel-Versatz

- **MUSS [MUST]** Bewegung als **Position = f(Phase)** umsetzen — Komponenten-`position`/`rectangle`-Koordinaten werden pro Frame aus der Phase berechnet; das Versetzen derselben Form über Frames erzeugt die wahrgenommene Bewegung
- **MUSS [MUST]** das **ganzzahlige 64×64-Raster** beachten: es gibt **kein Sub-Pixel** — Bewegung ist schrittweise; weiche Geschwindigkeit entsteht über die Frame-Frequenz und Schrittweiten, nicht über Fließkomma-Positionen
- **SOLLTE [SHOULD]** pro Frame **mindestens 1 px** versetzen, damit Bewegung sichtbar ist, aber **nicht so weit**, dass die Form zwischen Frames „springt" und unlesbar wird — Schrittweite zur Frame-Rate passend wählen
- **SOLLTE [SHOULD]** Looping/Wrapping bewusst gestalten (am Rand 0…63 herauslaufen und gegenüber wieder herein), damit die Bewegung nahtlos schließt
- **KANN [MAY]** **Easing** über eine vorab berechnete Schrittweiten-Tabelle (Phase → Offset) statt über lineare Schritte umsetzen, um Beschleunigen/Abbremsen anzudeuten
- **SOLLTE [SHOULD]** die **Silhouette über alle Frames konsistent** halten (gleiche Form/Schattierung, nur verschoben), damit das Auge ein bewegtes Objekt und kein flackerndes Muster sieht

### Farb-Animation

- **MUSS [MUST]** Farbänderung als **Farbe = f(Phase)** umsetzen — Komponenten-`color` wird pro Frame aus der Phase berechnet
- **SOLLTE [SHOULD]** Farb-Animation **innerhalb der Palette/Ramps** aus `ha/pixoo-pixel-art` halten: **Palette-Cycling** (Ramp-Index über die Phase rotieren), **Wert-Pulsieren** (Helligkeit entlang der Ramp auf-/abwandern), **Hue-Shift über Zeit** — statt freier RGB-Sprünge
- **SOLLTE [SHOULD]** Blink/Fade in **diskreten Stufen** über die Ramp ausführen (z. B. 3–4 Werte) statt als kontinuierlichen RGB-Verlauf — das passt zur Pixel-Art-Ästhetik und bleibt auf dem LED-Panel lesbar
- **MUSS NICHT [MUST NOT]** ungewolltes **Flicker** erzeugen — z. B. zwischen zwei stark kontrastierenden Vollflächen-Farben jeden Frame hin- und herschalten; auf dem hellen LED-Panel ermüdet das und wirkt fehlerhaft
- **KANN [MAY]** Bewegung und Farb-Animation kombinieren (z. B. ein wanderndes Glanzlicht über eine statische Form: Position **und** Wert variieren mit der Phase)

### Frame-Kohärenz & Lesbarkeit

- **MUSS [MUST]** in jedem Frame ein **gültiges Pixel-Art-Bild** nach `ha/pixoo-pixel-art` liefern (konsistente Lichtquelle, Konturen, Schattierung) — die Lichtrichtung bleibt über die Frames stabil, auch wenn sich Objekte bewegen
- **SOLLTE [SHOULD]** Frames **lang genug halten**, dass der Inhalt lesbar ist, bevor der nächste kommt — bei ~1 fps ist jeder Frame faktisch ein kurz stehendes Bild
- **SOLLTE [SHOULD]** **harte, sprunghafte Wechsel** zwischen Frames vermeiden (außer als bewusster Effekt); benachbarte Frames sollten sich nur graduell unterscheiden
- **SOLLTE [SHOULD]** den **Loop nahtlos** schließen (letzter → erster Frame ohne sichtbaren Sprung), wenn die Animation kontinuierlich läuft

### Liefer-Pfade (Anbindung)

- **MUSS [MUST]** prozedurale Frames als `components`-Page mit phasen-abhängigen `position`/`color` bauen; für **per-Pixel**-Animation eine `templatable`-Komponente nutzen, die pro Frame eine aus der Phase berechnete Liste von Pixel-Komponenten zurückgibt (siehe `ha/divoom-pixoo` §Komponenten und `ha/pixoo-pixel-art` §Liefer-Pfade)
- **MUSS [MUST]** für vorgerenderte Bewegtbilder ein **GIF in exakt 16/32/64 px** über `page_type: gif` einbinden — abweichende Größen werden nicht korrekt dargestellt (siehe `ha/divoom-pixoo`)
- **KANN [MAY]** `show_message` für eine **einmalige, kurze Animation als Push** verwenden, indem die Page wiederholt mit fortschreitender Phase gesendet wird — beachten: `enabled`/`variables` gelten im Service nicht (HA-`variables` aus der Automation nutzen)
- **SOLLTE [SHOULD]** das Ergebnis **am realen Gerät** verifizieren: tatsächliche Bildrate, Flicker, Bewegungs-Glätte und Loop-Übergang weichen vom Editor/Vorschau ab

## Akzeptanzkriterien

- [ ] Das Animationsmodell ist bewusst gewählt (prozedural / GIF / nativ) und passend zur Daten-Abhängigkeit
- [ ] Ein Frame-Treiber ist gesetzt (kurzes `duration` self-treibend oder `update_page`-Schleife) ohne exzessives Spamming; die Bildraten-Grenze (~1 fps via Rotation) ist berücksichtigt
- [ ] Eine Phasenvariable aus monoton fortlaufender Quelle (`now()`/`timer`/`counter`) treibt Frame-Auswahl; der Loop ist modulo der Frame-Anzahl gebildet
- [ ] Bewegung ist als Position=f(Phase) im ganzzahligen Raster umgesetzt; Schrittweite passt zur Frame-Rate; kein „Springen" der Form; Wrapping ist nahtlos
- [ ] Farb-Animation ist Farbe=f(Phase) **innerhalb** der Ramps (Cycling/Pulsieren/Hue-Shift, diskrete Stufen); kein ermüdendes Vollflächen-Flicker
- [ ] Jeder Frame ist ein gültiges Pixel-Art-Bild nach `ha/pixoo-pixel-art` mit stabiler Lichtrichtung; Frames unterscheiden sich nur graduell; der Loop schließt nahtlos
- [ ] Per-Pixel-Animation nutzt `templatable` mit phasen-berechneter Komponentenliste; GIF-Pfad nutzt exakt 16/32/64 px
- [ ] Die Animation wurde am echten Pixoo gegen Bildrate, Flicker, Bewegungs-Glätte und Loop-Übergang verifiziert

## Offene Fragen

- Lohnt ein wiederverwendbarer Helfer (Skript/Makro), der eine Animation als Phasen-→-Frame-Tabelle kapselt und die `update_page`-Taktung (inkl. Crash-sicherer Mindest-Intervalle) standardisiert?
- Welche praktische Maximal-Bildrate hält das konkrete Gerät im LAN stabil aus, bevor `update_page`-Takt zu Aussetzern/Crashes führt — sollte ein gemessener Richtwert in `home-assistant-config` dokumentiert werden?
- Soll für wiederkehrende Bewegtbilder ein kuratierter Satz vorgerenderter 64×64-GIFs (statt prozedural) gepflegt werden, um Geräte-Last und Netz-Traffic zu senken?
