# ESPHome-Gerät: ESP32-S3-BOX-Familie (BOX / BOX-Lite / BOX-3 / BOX-3B)

Status: draft

## Kontext

Die **ESP32-S3-BOX**-Familie ist Espressifs AI-Voice-Devkit-Linie rund um das ESP32-S3-WROOM-1-Modul: ein 2,4-Zoll-SPI-Display mit 320×240, ein Doppelmikrofon-Array hinter einem ES7210-Audio-ADC, ein Lautsprecher hinter einem ES8311-Codec, Taster, eine IMU und ein Erweiterungs-Connector. Drei Generationen sind im Umlauf und sind **untereinander nicht pin-kompatibel**: die ursprüngliche **ESP32-S3-BOX**, die kostenreduzierte **ESP32-S3-BOX-Lite** und die aktuelle **ESP32-S3-BOX-3** (ausgeliefert als `ESP32-S3-BOX-3` mit vier Zubehörteilen und als `ESP32-S3-BOX-3B` mit weniger Zubehör — eine Unterscheidung des Zubehör-Bundles, keine Board-Unterscheidung) `[vendor]`.

In diesem Portfolio wird die BOX über **ESPHome** betrieben, nicht über ESP-IDF-Anwendungscode: Das Gerät wird deklarativ in einer YAML-Datei beschrieben, von der ESPHome-Toolchain kompiliert und geflasht und über die native API in Home Assistant sichtbar. ESPHome pflegt für alle drei Generationen eine **offizielle, board-spezifische Referenzkonfiguration** in [`esphome/wake-word-voice-assistants`](https://github.com/esphome/wake-word-voice-assistants) — dieses Repository, nicht ein Forenbeitrag, ist die normative Quelle dafür, wie diese Hardware an ESPHome-Komponenten gebunden wird `[ref-config]`.

Diese Spec existiert, weil die BOX das erste Gerät in diesem Portfolio ist, bei dem **die Hardware selbst der schwierige Teil ist**. Eine generische ESPHome-Config-Spec kann einem Autor nicht sagen, dass Backlight-Pin und I²S-Wordclock-Pin zwischen BOX und BOX-3 *vertauscht* sind, dass drei der benötigten Pins Strapping-Pins sind oder dass die verbaute IMU überhaupt keine ESPHome-Komponente hat. Sie ist deshalb eine **Geräte-Referenz-Spec**: Sie fixiert die Board-Fakten, die daraus abgeleiteten ESPHome-Komponenten-Bindings und den Entwicklungsprozess (Bring-up → Baseline → Inkrement → Validierung → Recovery), den eine spätere Skill-Schicht automatisieren kann.

Sie ist als *Schwester* von [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md) angelegt, nicht als Ersatz: Jene Spec besitzt die geräteübergreifenden Regeln (Datei-Layout, `packages:`-Wiederverwendung, Secret-Handling, API-Verschlüsselung, OTA); diese hier besitzt alles, was spezifisch für die BOX-Hardware ist. Wo beide sich berühren, tritt diese Spec zurück.

### Quellen-Tiers

Espressifs eigene Hardware-Übersichtsseite zur BOX-3 führt die Pinouts **ausschließlich als Bilder**, ist für Pin-Fakten also nicht zitierbar. Jede Aussage unten trägt deshalb ein Evidenz-Tier, und ein Reviewer darf diese Spec daran messen:

- `[bsp]` — Espressifs Board-Support-Package [`espressif/esp-bsp`](https://github.com/espressif/esp-bsp) (`bsp/esp-box-3/include/bsp/esp-box-3.h`, `bsp/esp-box/include/bsp/esp-box.h`, `bsp/esp-box-3/idf_component.yml`): maßgeblich für GPIO-Zuordnungen und bestückte ICs.
- `[ref-config]` — ESPHomes offizielle Board-Configs in [`esphome/wake-word-voice-assistants`](https://github.com/esphome/wake-word-voice-assistants) (`esp32-s3-box-3/`, `esp32-s3-box/`, `esp32-s3-box-lite/`): maßgeblich für die ESPHome-seitige Bindung dieser Pins.
- `[doc]` — die offizielle ESPHome-Komponenten-Dokumentation unter <https://esphome.io>: maßgeblich für Komponenten-Schemata.
- `[vendor]` — Espressifs Produktdokumentation [`esp-box`](https://github.com/espressif/esp-box): maßgeblich für Produkt-/Varianten-Einordnung.
- `[policy]` — eine nolte-Portfolio-Regel, kein Hardware- oder Upstream-Fakt.

Verifiziert 2026-08; die Referenzkonfigurationen pinnen `min_version: 2026.4.0` `[ref-config]`.

## Ziele

- Die Board-Fakten der BOX-Familie fixieren — SoC, Speicher, bestückte ICs und eine GPIO-Karte pro Generation — aus zitierbaren Quellen statt aus dem Gedächtnis
- Die **Generationsunterschiede** explizit und unübersehbar machen, allen voran den Backlight-⇄-I²S-LRCLK-Pintausch zwischen BOX und BOX-3, der stillschweigend einen schwarzen Bildschirm oder stummes Audio erzeugt
- Jeden Hardware-Block an seine konkrete ESPHome-Komponente binden (Display, Audio-ADC/-DAC, Mikrofon, Lautsprecher, Media-Player, Wake-Word, Voice-Assistant, Touch, Taster) — mit den Pin-Werten, die die offiziellen Referenzkonfigurationen verwenden
- Den **Entwicklungsprozess** für ein ESPHome-Projekt auf diesem Gerät definieren — Variantenbestimmung, Baseline-Flash, inkrementelle Erweiterung, Validierung und Recovery — sodass er wiederholbar ausführbar und später durch einen Skill automatisierbar ist
- Ehrlich markieren, wo die Hardware **keinen ESPHome-Pfad** hat (IMU) oder wo die Quellen mehrdeutig sind (Touch-Controller, Display-Controller), statt eine plausible Antwort zu behaupten
- Dem künftigen ESPHome-Plugin (Drei-Plugin-Split, Roadmap-Item R-2) einen Geräte-Referenzanker geben, auf dem gerätespezifische Skills aufsetzen

## Nicht-Ziele

- Die geräteübergreifenden ESPHome-Regeln erneut spezifizieren — Datei-Layout, `packages:`-Wiederverwendung, `secrets.yaml`-Handling, API-Verschlüsselung und OTA-Disziplin leben in [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md) und werden referenziert, nicht wiederholt
- ESP-IDF-/ESP-ADF-Anwendungsentwicklung auf der BOX (Espressifs eigene `esp-box`-Demo-Firmware, LVGL-C-Code, die `esp_lcd`-/`esp_codec_dev`-Treiberschicht) — dieses Portfolio betreibt das Gerät über ESPHome
- Das Authoring von ESPHome-**Custom-Components** in C++/Python (`external_components`) — bewusst eine separate Achse; das *Konsumieren* einer Drittanbieter-Component aus einem Device-YAML ist in Scope
- Eine vollständige LVGL-Widget-Referenz — LVGL wird hier nur auf der Ebene „wie es an Display und Touchscreen dieses Boards andockt" gebunden
- Die Home-Assistant-Assist-Pipeline selbst (STT/TTS/Conversation-Agent-Auswahl, Wake-Word-Training) — die BOX ist Client dieser Pipeline; deren Konfiguration ist ein HA-seitiges Thema
- Andere Espressif-Voice-Hardware (ESP32-S3-Korvo, ESP32-P4-Boards) und die Home Assistant Voice Preview Edition, die ein eigenes Produkt mit eigener Referenzkonfiguration ist
- Zubehör-Bring-up über das Benennen der Bauteile hinaus (BOX-3-SENSOR Radar/IR, BOX-3-DOCK Kamera) — für Zubehör werden keine Pin-Aussagen getroffen, weil der Hersteller diese Pinouts ausschließlich als Bilder veröffentlicht

## Anforderungen

### Board-Identität und Variantenwahl

- Es **MUSS [MUST]** **vor** dem Schreiben einer Config bestimmt werden, welche Generation vorliegt: BOX, BOX-Lite und BOX-3 unterscheiden sich in Pin-Belegung und Display-Parametern, und eine Config für die falsche Generation kompiliert und flasht sauber, scheitert aber zur Laufzeit `[bsp]` `[ref-config]`
- Die bestimmte Generation **MUSS [MUST]** im Device-YAML festgehalten werden (Substitution oder Kommentar), damit ein späterer Leser erkennt, welche Pin-Karte gilt `[policy]`
- `ESP32-S3-BOX-3` und `ESP32-S3-BOX-3B` **SOLLTEN [SHOULD]** konfigurationsseitig als **dasselbe Board** behandelt werden — der publizierte Unterschied ist der Zubehörumfang, nicht die Platine `[vendor]`
- Ein mehrdeutiges Exemplar **SOLLTE [SHOULD]** empirisch statt nach Aussehen aufgelöst werden: eine minimale Config mit einem I²C-Bus auf `SCL: GPIO18` / `SDA: GPIO8` flashen, die Scan-Ergebnisse aus dem Log lesen und die antwortenden Adressen gegen die unten genannten bestückten ICs abgleichen `[policy]`

### Kern-Plattformkonfiguration

- `flash_size: 16MB` **MUSS [MUST]** deklariert werden — die BOX trägt 16 MB Flash, während die ESPHome-`esp32`-Komponente auf `4MB` defaultet; der Default verschenkt Flash und bricht Partitionsannahmen für größere Firmwares `[doc]` `[ref-config]`
- PSRAM **MUSS [MUST]** als `psram: {mode: octal, speed: 80MHz}` aktiviert werden — das Modul trägt 16 MB **Octal**-PSRAM, und `micro_wake_word`, vollflächige Bilder sowie LVGL-Puffer hängen davon ab `[bsp]` `[ref-config]`
- Es **MUSS [MUST]** das **ESP-IDF**-Framework verwendet werden; es ist in aktuellen ESPHome-Releases das Default- und empfohlene Framework für ESP32-Chips, und die Referenzkonfigurationen nutzen es `[doc]` `[ref-config]`
- `cpu_frequency: 240MHz` **SOLLTE [SHOULD]** gesetzt werden; die Referenzkonfigurationen setzen zusätzlich die sdkconfig-Optionen `CONFIG_ESP32S3_DEFAULT_CPU_FREQ_240`, `CONFIG_ESP32S3_DATA_CACHE_64KB` und `CONFIG_ESP32S3_DATA_CACHE_LINE_64B` `[ref-config]`
- Der Logger **SOLLTE [SHOULD]** über die native USB-Peripherie laufen (`logger: {hardware_uart: USB_SERIAL_JTAG}`) — die BOX hat genau einen USB-C-Port und keine separate UART-Bridge `[ref-config]`
- `board: esp32s3box` **SOLLTE [SHOULD]** beibehalten werden, wie es alle drei Referenzkonfigurationen tun. Die `esp32`-Dokumentation nennt `board` zwar „no longer recommended" zugunsten von `variant`, sagt aber ebenso, es beeinflusse „only pin aliases and some internal settings", und bei einer reinen `variant`-Config werde das Board „automatically filled using a standard Espressif devkit board". Da diese Spec jeden Pin explizit benennt und auf keinen Alias baut, funktionieren beide Formen — Upstream zu folgen hält Portfolio-Configs gegen die Referenz diffbar `[doc]` `[ref-config]` `[policy]`

### GPIO-Karte (pro Generation)

- Pin-Werte **MÜSSEN [MUST]** dieser Tabelle entnommen werden statt einem generischen „ESP32-S3"-Pinout; alle drei Spalten sind `[bsp]` für die Hardware und `[ref-config]` für die ESPHome-Nutzung, jeweils gegen den BSP-Header der eigenen Generation verifiziert (`bsp/esp-box-3`, `bsp/esp-box`, `bsp/esp-box-lite`):

| Funktion | BOX-3 | BOX (Original) | BOX-Lite |
|---|---|---|---|
| I²C SCL | `GPIO18` | `GPIO18` | `GPIO18` |
| I²C SDA | `GPIO8` | `GPIO8` | `GPIO8` |
| I²S BCLK (SCLK) | `GPIO17` | `GPIO17` | `GPIO17` |
| I²S MCLK | `GPIO2` | `GPIO2` | `GPIO2` |
| **I²S LRCLK (WS)** | **`GPIO45`** | **`GPIO47`** | **`GPIO47`** |
| I²S DOUT → Lautsprecher | `GPIO15` | `GPIO15` | `GPIO15` |
| I²S DIN ← Mikrofone | `GPIO16` | `GPIO16` | `GPIO16` |
| Endstufen-Freigabe | `GPIO46` | `GPIO46` | `GPIO46` |
| **Display-Backlight** | **`GPIO47`** | **`GPIO45`** | **`GPIO45`** (invertiert) |
| Display-SPI CLK (PCLK) | `GPIO7` | `GPIO7` | `GPIO7` |
| Display-SPI MOSI (DATA0) | `GPIO6` | `GPIO6` | `GPIO6` |
| Display CS | `GPIO5` | `GPIO5` | `GPIO5` |
| Display DC | `GPIO4` | `GPIO4` | `GPIO4` |
| Display RESET | `GPIO48` (invertiert) | `GPIO48` | `GPIO48` |
| Touch-Interrupt | `GPIO3` | `GPIO3` | — *(kein Touch: `BSP_CAPS_TOUCH 0`)* |
| Config-/Boot-Taster | `GPIO0` | `GPIO0` | `GPIO0` *(einziger Taster im BSP)* |
| Mute-Taster / -Status | `GPIO1` | `GPIO1` | `GPIO1` *(ADC-Tasterkette, kein Mute)* |
| Roter Haupttaster | *(über Touch-Controller)* | *(über Touch-Controller)* | — |
| Dock-/Erweiterungs-I²C SCL / SDA | `GPIO40` / `GPIO41` | — | — |
| USB D+ / D− | `GPIO20` / `GPIO19` | `GPIO20` / `GPIO19` | `GPIO20` / `GPIO19` |

- Der **Backlight-⇄-LRCLK-Tausch** zwischen BOX-3 (`Backlight 47`, `LRCLK 45`) und BOX/BOX-Lite (`Backlight 45`, `LRCLK 47`) **MUSS [MUST]** als primärer Fehlermodus der Familie behandelt werden: Vertauscht man sie, bootet, verbindet und loggt das Gerät normal, zeigt aber einen schwarzen Bildschirm und/oder gibt keinen Ton aus `[bsp]` `[ref-config]`
- `ignore_strapping_warning: true` **MUSS [MUST]** bewusst auf den Strapping-Pins gesetzt werden, die das Board mitbenutzt — `GPIO0` (Config-Taster), `GPIO45` (I²S-LRCLK auf der BOX-3) und `GPIO46` (Endstufen-Freigabe); die Referenzkonfigurationen setzen es auf genau diesen `[ref-config]`
- SD-Karten- und PMOD-/Erweiterungs-Pins **SOLLTEN [SHOULD]** als board-spezifisch behandelt und für die vorliegende Generation aus dem BSP-Header gelesen statt angenommen werden; auf der BOX-3 ist der SD-Slot `CLK GPIO11`, `CMD GPIO14`, `D0 GPIO9`, `D1 GPIO13`, `D2 GPIO42`, `D3 GPIO12`, Power `GPIO43`, und die beiden PMOD-Header überlappen diesen Satz `[bsp]`
- Ein GPIO **DARF NICHT [MUST NOT]** einem projektspezifischen Peripheriegerät zugewiesen werden, ohne ihn gegen diese Tabelle plus die PMOD-/SD-Bereiche des BSP zu prüfen — die BOX exponiert weit weniger freie Pins als ein nacktes ESP32-S3-Devkit `[policy]`

### Bestückte Bauteile

- Auf der BOX-3 **MUSS [MUST]** von diesem IC-Satz ausgegangen und die ESPHome-Komponenten entsprechend gebunden werden: Display-Controller (siehe unten), kapazitiver Touch-Controller (siehe unten), **ES7210**-Audio-ADC auf I²C `0x40` (Mikrofon-Array), **ES8311**-Audio-Codec auf I²C `0x18` (Lautsprecherpfad), eine **ICM-42670-/ICM-42607-P**-IMU und ein **AHT30**-Temperatur-/Feuchtesensor `[bsp]` `[doc]`
- Der IC-Satz der BOX-3 **DARF NICHT [MUST NOT]** auf die **BOX-Lite** übertragen werden, die hinter derselben Silhouette ein anderes Board ist: Ihr BSP nennt einen **ES7243E**-Audio-ADC und einen **ES8156**-Audio-DAC (nicht ES7210/ES8311), einen **ST7789**-Display-Controller, **überhaupt keinen Touch-Controller** (`BSP_CAPS_TOUCH 0`) und einen einzigen Config-Taster — die Audio-Bindungen unten unterscheiden sich daher je Generation `[bsp]` `[ref-config]`
- Auf BOX und BOX-3 **MÜSSEN [MUST]** **drei** Taster, aber nur **zwei** Taster-GPIOs gezählt werden: Espressifs BSP führt im Enum `BSP_BUTTON_CONFIG`, `BSP_BUTTON_MUTE` und `BSP_BUTTON_MAIN`, während nur `GPIO0` (Config) und `GPIO1` (Mute) GPIO-gestützt sind — der dritte, der rote Taster unter dem Bildschirm, ist ein **über den Touch-Controller gelesener Touch-Key**, kein GPIO `[bsp]` `[doc]`
- Der Mute-Taster **DARF NICHT [MUST NOT]** als einfacher Kontakt an `GPIO1` behandelt werden: Das BSP hält fest, er sei „wired to Logic Gates, result mapped to `GPIO_NUM_1`" — der Pin trägt also einen abgeleiteten **Mute-Status**, und der Hardware-Mute-Pfad existiert unabhängig von jeder ESPHome-Logik `[bsp]`
- Wo der **AHT30** tatsächlich sitzt, **SOLLTE [SHOULD]** geklärt werden, bevor er zugesagt wird: Espressifs Produktdokumentation führt Temperatur/Feuchte unter dem separaten Zubehör BOX-3-SENSOR, während das BOX-3-BSP `BSP_CAPS_HUMITURE 1` deklariert und einen `aht30`-Treiber zieht — ein I²C-Scan am vorliegenden Exemplar entscheidet `[vendor]` `[bsp]`
- Der **Display-Controller** **MUSS [MUST]** am vorliegenden Exemplar verifiziert werden, statt einer einzelnen Quelle zu vertrauen: Espressifs BSP-Header-Kommentare nennen **ST7789**, während der Dependency-Satz desselben BSP `esp_lcd_ili9341` zieht — und ESPHome bindet das Panel über ein Board-**Model-Preset** statt über einen rohen Controller-Namen; das Preset ist der unterstützte Pfad, eine falsche manuelle Controller-Wahl zeigt sich als invertierte oder verschobene Farben `[bsp]` `[doc]`
- Der **Touch-Controller** **MUSS [MUST]** empirisch verifiziert werden (I²C-Scan) statt angenommen: Espressifs BOX-3-BSP deklariert Treiber für **beide**, `esp_lcd_touch_gt911` und `esp_lcd_touch_tt21100`, was bedeutet, dass der bestückte Controller je nach Revision variiert; ESPHome liefert genau deshalb die Touchscreen-Plattformen `gt911` und `tt21100` `[bsp]` `[doc]`
- Es **DARF NICHT [MUST NOT]** eingeplant werden, die **IMU** aus ESPHome auszulesen: Für die ICM-42670 existiert **keine** Komponente im ESPHome-Sensor-Katalog (der BMI270, LSM6DS und QMI8658 als Beschleunigungs-/Gyroskop-Plattformen führt); ihre Nutzung erfordert eine `external_components`-Implementierung und liegt außerhalb eines Device-YAML-Schnitts `[doc]` `[bsp]`
- Ein AHT30 **MUSS [MUST]** über die `aht10`-Plattform mit `variant: AHT20` gebunden werden: Die Komponente dokumentiert Unterstützung für „your AHT10, AHT20 or AHT30 I²C-based sensor", und ihr `variant`-Enum bietet `AHT10` (Default) und `AHT20`, wobei letzteres AHT20 und AHT30 abdeckt — der Default an einem AHT30 wählt den falschen Registersatz `[doc]`

### Display-Bindung

- Der SPI-Bus **MUSS [MUST]** explizit als `clk_pin: 7` / `mosi_pin: 6` deklariert werden; das Display ist in den Referenzkonfigurationen das einzige Gerät daran `[ref-config]`
- Es **MUSS [MUST]** das Board-**Model-Preset** statt handgeschriebener Panel-Parameter verwendet werden — `model: S3BOX` für BOX-3 und BOX; für BOX-Lite unterscheidet sich die Schreibweise des Presets je nach Plattform (`S3BOX_LITE` unter `ili9xxx`, wie die Referenzkonfiguration es nutzt, gegenüber `S3BOXLITE` in der `mipi_spi`-Modellliste), sie **MUSS [MUST]** daher der Dokumentation der tatsächlich deklarierten Plattform entnommen werden. Das Model setzt Auflösung und Panel-Defaults, verbleibende Keys überschreiben es `[doc]` `[ref-config]`
- Die generationsspezifischen Display-Parameter **MÜSSEN [MUST]** exakt so geführt werden wie in den Referenzkonfigurationen `[ref-config]`:
  - **BOX-3** — `platform: mipi_spi`, `model: S3BOX`, `invert_colors: false`, `data_rate: 40MHz`, `cs_pin: 5`, `dc_pin: 4`, `reset_pin: {number: 48, inverted: true}`
  - **BOX** — `platform: ili9xxx`, `model: S3BOX`, `invert_colors: false`, `data_rate: 40MHz`, `cs_pin: 5`, `dc_pin: 4`, `reset_pin: 48` (**nicht** invertiert)
  - **BOX-Lite** — `platform: ili9xxx`, `model: S3BOX_LITE`, **`invert_colors: true`** (die einzige Generation, die invertiert), dazu ein Backlight-Output mit `inverted: true`
- Für neue Configs **SOLLTE [SHOULD]** die neuere `mipi_spi`-Plattform bevorzugt werden; die BOX-3-Referenzkonfiguration ist bereits darauf gewechselt, während die ältere BOX-Config noch `ili9xxx` nutzt `[ref-config]`
- Das Backlight **MUSS [MUST]** als dimmbares Licht statt als nackter GPIO betrieben werden: `output: {platform: ledc, pin: <backlight>}` plus `light: {platform: monochromatic}`, damit die Bildschirmhelligkeit eine HA-Entity ist `[ref-config]`
- `update_interval: never` **SOLLTE [SHOULD]** am Display gesetzt und explizit aus Automations oder Scripts neu gezeichnet werden; die Referenzkonfigurationen rendern ereignisgetriebene Pages und rufen `component.update` selbst auf `[ref-config]`
- Alles jenseits der Bindung — Leinwand-Geometrie, Pages, Zeichen-Primitive, Fonts, Bilder, Farben, Layout-Zonen und der LVGL-Widget-Weg — **MUSS [MUST]** aus [`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md) bezogen werden, die das Rendering auf diesem Panel besitzt `[policy]`
- Bei Nutzung von **LVGL** statt `display`-Pages **MÜSSEN [MUST]** am Display `auto_clear_enabled: false` und `update_interval: never` gesetzt, der Touchscreen in `lvgl:` eingebunden und `buffer_size` bewusst dimensioniert werden — LVGL besitzt das Rendering, und auf einem PSRAM-Board kann ein kleiner Puffer im internen RAM einen vollen PSRAM-Puffer schlagen `[doc]`

### Touch und Taster

- Der Touchscreen **MUSS [MUST]** über die zum bestückten Controller passende Plattform gebunden werden — `touchscreen: {platform: gt911}` oder `{platform: tt21100}` — am gemeinsamen I²C-Bus, mit `interrupt_pin: GPIO3`; der GT911 antwortet je nach Variante auf `0x5D` oder `0x14` `[doc]` `[bsp]`
- Dem Touchscreen **DARF NICHT [MUST NOT]** ein eigener `reset_pin` gegeben werden, wenn Display und Touch-Controller sich die Reset-Leitung teilen, wie es auf der BOX der Fall ist: Die Komponenten-Dokumentation verlangt, den Reset-Pin dann **nur am Display** zu konfigurieren `[doc]`
- Der **rote Haupttaster** unter dem Bildschirm **MUSS [MUST]** als Touch-Key des Touch-Controllers gelesen werden, nicht als GPIO: Beide Plattformen exponieren `binary_sensor: {platform: gt911|tt21100, index: 0…3}` für bis zu vier Taster außerhalb der Displayfläche, und die ESPHome-Dokumentation nennt den roten Taster der BOX genau dafür als Beispiel `[doc]`
- Der `index` des Tasters **SOLLTE [SHOULD]** beim ersten Bring-up empirisch bestimmt werden (Binary-Sensoren für die Indizes 0…3 loggen und den Taster drücken) statt angenommen zu werden `[policy]`
- Der **Config-Taster** an `GPIO0` **MUSS [MUST]** als `binary_sensor: {platform: gpio, mode: INPUT_PULLUP, inverted: true, ignore_strapping_warning: true}` deklariert werden — die Referenzkonfigurationen nutzen genau diese Form und hängen sowohl eine Kurzdruck-Aktion als auch den Langdruck-Factory-Reset an `on_multi_click` `[ref-config]`
- Der **Mute-Taster/-Status** an `GPIO1` **KANN [MAY]** auf BOX und BOX-3 als weiterer GPIO-Binary-Sensor exponiert werden, unter Beachtung dessen, dass er den über Logikgatter abgeleiteten Mute-Zustand meldet; zu beachten ist, dass die Upstream-Referenzkonfigurationen `GPIO1` **nicht** binden und stattdessen einen Software-`switch: {platform: template}` namens „Mute" ausliefern, der `microphone.mute` / `microphone.unmute` fährt `[bsp]` `[ref-config]`
- Auf der **BOX-Lite** **MÜSSEN [MUST]** die drei Fronttaster als **ADC-Kette** an `GPIO1` gelesen werden statt als GPIO-Taster: Die Referenzkonfiguration pollt `sensor: {platform: adc, pin: GPIO1, attenuation: 12db, update_interval: 16ms}` und bildet Spannungsbänder (keiner ≈ 3,121 V, links ≈ 2,392 V, Mitte ≈ 1,965 V, rechts ≈ 0,794 V, dazu die Kombinationsbänder) auf drei `binary_sensor: {platform: template}`-Entities ab `[ref-config]`
- Diese BOX-Lite-Schwellen **SOLLTEN [SHOULD]** als board-kalibrierte, pro Exemplar nachzumessende Werte behandelt werden, nicht als universelle Konstanten — sie sind die gemessenen Bänder eines Referenzgeräts `[policy]`
- Bei einer Widget-UI **SOLLTE [SHOULD]** der Touchscreen in `lvgl:` eingebunden werden, statt rohe Touch-Koordinaten in Lambdas zu verarbeiten `[doc]`

### Audio-Bindung

- Es **MUSS [MUST]** ein I²S-Bus mit `i2s_bclk_pin: GPIO17`, `i2s_mclk_pin: GPIO2` und dem generationsrichtigen `i2s_lrclk_pin` deklariert werden sowie ein I²C-Bus (`SCL 18` / `SDA 8`), den sich beide Codecs teilen `[ref-config]`
- Die Codecs **MÜSSEN [MUST]** als **externe** Wandler deklariert werden, nicht als rohes I²S, und es **MUSS [MUST]** das zur Generation passende Paar gewählt werden `[ref-config]` `[doc]` `[bsp]`:
  - **BOX-3 und BOX** — `audio_adc: {platform: es7210, bits_per_sample: 16bit, sample_rate: 16000}` und `audio_dac: {platform: es8311, bits_per_sample: 16bit, sample_rate: 48000}`, beide an die gemeinsame `i2c_id` gebunden
  - **BOX-Lite** — `audio_adc: {platform: es7243e}` und `audio_dac: {platform: es8156}`; beide Plattformen existieren in ESPHome und sind das, was die BOX-Lite-Referenzkonfiguration deklariert. Ein `es7210`/`es8311`-Paar adressiert auf einer BOX-Lite ICs, die nicht auf dem Board sind
- Die I²C-Adressen der Codecs **SOLLTEN [SHOULD]** auf ihren Komponenten-Defaults bleiben, die bereits zum Board passen — auf BOX-3 und BOX sind das `0x40` für den ES7210 und `0x18` für den ES8311 — und nur dann explizit gesetzt werden, wenn ein I²C-Scan etwas anderes zeigt `[doc]` `[bsp]`
- Die Mikrofonempfindlichkeit **SOLLTE [SHOULD]** über das `mic_gain` des jeweiligen Audio-ADC eingestellt werden, bevor zu `volume_multiplier` oder `auto_gain` des Voice-Assistants gegriffen wird, damit die Verstärkung einmal im analogen Pfad statt zweimal wirkt; beim ES7210 reicht der Bereich von `0DB` bis `37.5DB` mit `24DB` als Default `[doc]` `[ref-config]`
- Wo ein **ES8311** verbaut ist (BOX-3 und BOX), **DARF NICHT [MUST NOT]** `use_microphone: true` gesetzt werden: Die Mikrofone dieser Boards hängen am ES7210, und der eigene Mikrofonpfad des ES8311 (mit separatem `mic_gain`, Default `42DB`) ist ungenutzt — der Key defaultet auf `false` und muss dort bleiben `[doc]` `[bsp]`
- Das Mikrofon **MUSS [MUST]** mit `platform: i2s_audio`, `i2s_din_pin: GPIO16`, `adc_type: external`, `sample_rate: 16000`, `bits_per_sample: 16bit` deklariert werden — der externe Audio-ADC übernimmt die Wandlung auf jeder Generation, ein `internal`-ADC-Typ ist für dieses Board also falsch und laut Dokumentation ohnehin nicht mehr unterstützt `[ref-config]` `[doc]`
- `bits_per_sample: 16bit` **MUSS [MUST]** am Mikrofon explizit angegeben werden, statt sich auf den Plattform-Default `32bit` zu verlassen — die Referenzkonfigurationen setzen 16 Bit passend zur `audio_adc`-Deklaration, und ein stiller Unterschied zwischen beiden erzeugt Rauschen, keinen Fehler `[doc]` `[ref-config]`
- Es **SOLLTE [SHOULD]** verstanden werden, dass die **zwei Mikrofone** des Boards keine zwei ESPHome-Entities sind: Sie sind zwei ADC-Kanäle des Audio-ADC, die über einen I²S-Strom ankommen, und die Mikrofon-Plattform wählt daraus über `channel` (`left`, `right`, `stereo`; Default `right`). Die Referenzkonfigurationen belassen den Default und konsumieren für die Voice-Pipeline **einen** Kanal. Dieses Portfolio tut dasselbe: Das zweite Mikrofon bleibt ungenutzt, weil `stereo` nur die Nutzlast verdoppelt, solange nichts beide Kanäle verarbeitet, und ESPHome selbst kein Beamforming mitbringt `[doc]` `[ref-config]` `[policy]`
- Der Lautsprecher **MUSS [MUST]** mit `platform: i2s_audio`, `i2s_dout_pin: GPIO15`, `dac_type: external`, `audio_dac: <ID des Audio-DAC der Generation>`, `sample_rate: 48000`, `bits_per_sample: 16bit`, `channel: left` deklariert werden `[ref-config]`
- Die Endstufe **MUSS [MUST]** als GPIO-Switch auf `GPIO46` mit `restore_mode: RESTORE_DEFAULT_ON` exponiert werden — bei deaktivierter Endstufe läuft und loggt die Pipeline normal, der Lautsprecher bleibt aber stumm `[ref-config]`
- Die bewusste **Abtastraten-Asymmetrie** (Aufnahme mit 16 kHz, Wiedergabe mit 48 kHz) **SOLLTE [SHOULD]** beachtet und beim Ergänzen von Medienwiedergabe beibehalten statt vereinheitlicht werden `[ref-config]`
- Der Lautsprecher **SOLLTE [SHOULD]** in `media_player: {platform: speaker}` eingefasst werden, wenn das Gerät auch Ansagen und Medien abspielen soll, und der Lautstärkebereich (`volume_min` / `volume_max`) **SOLLTE [SHOULD]** begrenzt werden, damit das kleine Gehäuse nicht in die Verzerrung gefahren wird `[ref-config]`

### Voice-Assistant-Bindung

- `voice_assistant:` **MUSS [MUST]** an das Mikrofon und für den Antwortpfad an einen `media_player`/`speaker` gebunden werden; `microphone` ist der einzige Pflicht-Key der Komponente `[doc]` `[ref-config]`
- Wake-Word-Erkennung **SOLLTE [SHOULD]** **auf dem Gerät** über `micro_wake_word:` mit einem oder mehreren Modellen laufen und die Pipeline aus `on_wake_word_detected` starten; die Referenzkonfiguration liefert `okay_nabu`, `hey_mycroft` und `hey_jarvis` `[ref-config]` `[doc]`
- Der Ort der Wake-Word-Erkennung (On-Device / in Home Assistant) **SOLLTE [SHOULD]** als Laufzeit-`select:` statt als Compile-Zeit-Entscheidung angeboten werden, mit entsprechendem Umschalten zwischen `micro_wake_word.start` und `voice_assistant.start_continuous` — die Referenzkonfiguration behandelt dies als vollwertige Nutzereinstellung `[ref-config]`
- Das Display **SOLLTE [SHOULD]** aus dem Pipeline-Lebenszyklus heraus gesteuert werden (`on_listening`, `on_stt_end`, `on_tts_start`, `on_end`, `on_error`) sowie aus den Timer-Triggern (`on_timer_started`, `on_timer_finished`, `on_timer_tick`, …), damit Bildschirm- und Pipeline-Zustand nicht auseinanderlaufen können `[doc]` `[ref-config]`
- Es **SOLLTE [SHOULD]** eine **Mute**-Steuerung exponiert werden, die `microphone.mute` / `microphone.unmute` aufruft und den Mute-Zustand auf dem Bildschirm spiegelt; ein Sprachgerät ohne auffindbares Mute ist ein Datenschutzdefekt, keine fehlende Bequemlichkeit `[policy]` `[ref-config]`
- Der Trennungsfall **MUSS [MUST]** explizit behandelt werden — die Referenzkonfiguration rendert eigene „kein WLAN"- und „kein Home Assistant"-Bildschirme und stoppt die Wake-Word-Verarbeitung, wenn der API-Client die Verbindung verliert `[ref-config]`
- Die benötigte Home-Assistant-Version für die genutzten Pipeline-Features **SOLLTE [SHOULD]** gegen die Komponenten-Dokumentation verifiziert werden, bevor sie zugesagt wird (die Komponente dokumentiert 2023.5 als Untergrenze für grundlegenden Voice-Assistant-Support und spätere Untergrenzen für neuere Features) `[doc]`

### Sensorik, Speicher und Erweiterung

- Die verbaute **IMU** **MUSS [MUST]** als außerhalb des Scopes dieses Portfolios behandelt werden: Sie hat keine ESPHome-Komponente (siehe *Bestückte Bauteile*), und kein Anwendungsfall an einem wandmontierten Sprachgerät rechtfertigt einen fremden C++-Treiber im Build. Nur gegen eine konkrete Anforderung erneut zu bewerten `[doc]` `[bsp]` `[policy]`
- Der **microSD**-Slot **MUSS [MUST]** ungenutzt bleiben: Das BSP definiert einen vollständigen SDMMC-Pinsatz (plus SPI-Alternative), ESPHomes offizieller Komponenten-Index führt aber keine SD-Karten-Komponente (verifiziert 2026-08), jede Nutzung bedeutete also `external_components`. Lokaler Audiobedarf **MUSS [MUST]** stattdessen aus dem Flash gedeckt werden — die `media_player`-Speaker-Plattform bettet Sounddateien direkt ein, so wie die Referenzkonfiguration es für ihren Timer-Klang tut `[bsp]` `[doc]` `[ref-config]` `[policy]`
- Ein **AHT30** **SOLLTE [SHOULD]** (sobald sein Vorhandensein bestätigt ist) als `sensor: {platform: aht10, variant: AHT20}` am gemeinsamen I²C-Bus gebunden werden, gemäß *Bestückte Bauteile* `[doc]`
- Die Chip-Temperatur des ESP32 (`sensor: {platform: internal_temperature}`) **DARF NICHT [MUST NOT]** als Raumtemperatur veröffentlicht werden: Sie misst den SoC neben laufendem Display und Endstufe, liest zu hoch, und einige ESP32-Varianten liefern ungültige Werte, die die Komponente verwirft `[doc]` `[policy]`
- Auf einem dauerhaft eingesetzten Gerät **SOLLTEN [SHOULD]** die üblichen Diagnose-Entities mitgeliefert werden — `sensor: {platform: wifi_signal}`, `sensor: {platform: uptime}` und optional `internal_temperature` — jeweils mit `entity_category: diagnostic`, damit sie das nutzerseitige Dashboard nicht zumüllen `[doc]` `[policy]`
- Der **zweite I²C-Bus** der BOX-3 an `GPIO40` / `GPIO41` (Dock-/Erweiterungsbus) **KANN [MAY]** für projektspezifische Sensoren genutzt werden, wodurch der Codec-Bus an `GPIO18` / `GPIO8` frei von fremdem Verkehr bleibt `[bsp]`
- Jeder Erweiterungs-Pin **MUSS [MUST]** vor der Nutzung gegen die SD- und PMOD-Belegungen geprüft werden — die beiden PMOD-Header überlappen die SD-Karten-Pins (`GPIO9`, `GPIO11`…`GPIO14`, `GPIO42`, `GPIO43`), sodass ein Peripheriegerät an einem PMOD-Pin mit SD-Nutzung kollidieren kann `[bsp]`
- Peripherie der Zubehörmodule (Radar und IR des BOX-3-SENSOR, Kamera des BOX-3-DOCK) **SOLLTE [SHOULD]** hier als unspezifiziert gelten: Für sie wird keine Pin-Aussage getroffen, und jede Bindung muss zuerst am Gerät abgeleitet und verifiziert werden `[vendor]`

### Konnektivität, Secrets und Wiederverwendung

- [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md) **MUSS [MUST]** unverändert für WLAN/Secrets/API-Verschlüsselung/OTA angewendet werden — insbesondere `api:` mit `encryption`, `ota:` mit Passwort und keine literalen Zugangsdaten in irgendeiner Datei `[policy]`
- Die Sicherheits-Baseline des Portfolios **DARF NICHT [MUST NOT]** aus der ESPHome-Referenzkonfiguration abgeleitet werden: Jene Config ist eine *Distributions*-Firmware für unbekannte Nutzer und liefert deshalb keinen vorab geteilten Verschlüsselungsschlüssel aus; eine Portfolio-Device-Config ist eine Config mit *bekanntem Eigentümer* und trägt den Schlüssel `[policy]` `[ref-config]`
- Die Board-Baseline **MUSS [MUST]** über `packages:` wiederverwendet werden, und zwar **ins Config-Repository gevendort** statt remote referenziert: Die Upstream-Board-Config wird einmal hineinkopiert, reviewt und bewusst aktualisiert, sodass ein Build weder von Netzzugriff abhängt noch sich ändert, weil Upstream sich geändert hat `[policy]`
- Das projektspezifische Delta (zusätzliche Sensoren, eigene Pages, Automations) **SOLLTE [SHOULD]** in der Device-Datei liegen und die Board-Verrohrung (Pins, Codecs, Display) im Package, damit eine Board-Revision eine Ein-Datei-Änderung bleibt `[policy]`
- `esphome: {min_version: ...}` **MUSS [MUST]** auf dem Floor deklariert werden, den die Upstream-Referenzkonfigurationen pinnen (`2026.4.0`, Stand 2026-08), und eine Anhebung ist eine reviewte Änderung, ausgelöst durch einen Upstream-Bump — ESPHomes Audio-Komponenten haben ihr Schema wiederholt geändert, eine ungepinnte Config bricht beim Upgrade also stillschweigend `[ref-config]` `[policy]`
- Der Home-Assistant-seitige Kontrakt — Assist-Pipeline, Engine-Wahl, Entity-Freigabe, `assist_satellite`-Bindung und Pipeline-Debugging — **MUSS [MUST]** aus [`ha/assist-pipeline`](../assist-pipeline/de.md) bezogen werden; ein korrekt gebundenes Gerät vor einer unkonfigurierten Pipeline ist stumm `[policy]`
- Der mDNS-Name des Geräts **MUSS [MUST]** im Netzwerk eindeutig bleiben, da die native API über diesen Namen entdeckt wird; die Referenzkonfigurationen erreichen das mit `name_add_mac_suffix: true`, und wer es entfernt, übernimmt die Verantwortung für die Eindeutigkeit `[ref-config]` `[policy]`
- `api: {reboot_timeout: ...}` **SOLLTE [SHOULD]** bewusst entschieden werden: Der Default sind 15 Minuten, sodass ein Gerät, dessen Home Assistant länger offline ist, in diesem Takt neu startet — der Mechanismus existiert, weil der ESP eine Verbindung melden kann, die er nicht hat, und nur ein Reboot das behebt `[doc]` `[policy]`

### Entwicklungsprozess

- Der Prozess **MUSS [MUST]** in dieser Reihenfolge durchlaufen werden — das Überspringen von Identifikation oder Baseline erzeugt genau die oben beschriebenen stillen Fehlermodi `[policy]`:
  1. **Identifizieren** — die Generation bestimmen (siehe *Board-Identität*) und in der Config festhalten
  2. **Baseline** — die unveränderte Upstream-Referenzkonfiguration dieser Generation flashen und bestätigen, dass Display, Mikrofon, Lautsprecher und HA-Verbindung funktionieren
  3. **Inkrementieren** — projektspezifische Blöcke einzeln auf der Baseline-Package aufsetzen
  4. **Validieren** — `esphome config` für das Schema, `esphome compile` für den Build, `esphome logs` für die Laufzeit
  5. **Recovern** — wenn ein Schritt das Verhalten zerschießt, gemäß *Recovery* zurückfallen
- Das **erste** Image **MUSS [MUST]** über USB-C (seriell) geflasht werden, jedes weitere über OTA; das Gerät hat einen USB-C-Port für Strom, Flashen und Logging zugleich `[vendor]` `[ref-config]`
- Jede generierte oder bearbeitete Config **MUSS [MUST]** vor dem Flashen mit `esphome config <file>` validiert werden; ist die Toolchain nicht verfügbar, **MUSS [MUST]** die Validierung als offener Caller-Schritt gemeldet werden `[policy]`
- Vor dem Flashen **SOLLTE [SHOULD]** kompiliert werden (`esphome compile`), damit ein Build-Fehler von einem Flash-Fehler getrennt bleibt; auf diesem Board dauert ein vollständiger Clean-Build Minuten, und eine Config für die falsche Generation scheitert *nach* dem Build, nicht währenddessen `[policy]`
- Das Laufzeitverhalten **SOLLTE [SHOULD]** während des Bring-ups über `esphome logs` am USB-Serial-JTAG-Logger gelesen werden, danach über das Netzwerk `[ref-config]`
- Ein erfolgreiches Kompilieren und Flashen **DARF NICHT [MUST NOT]** als Beleg dafür gewertet werden, dass die Pin-Karte stimmt — Display, Audio und Touch **MÜSSEN [MUST]** jeweils am Gerät ausgeübt werden, bevor die Config als gut gilt `[policy]`

### Recovery

- Jede Config **MUSS [MUST]** einen Recovery-Pfad enthalten: einen WLAN-`ap:`-Fallback plus `captive_portal:`, damit ein unerreichbares Gerät ohne Kabel rekonfigurierbar bleibt `[ref-config]`
- Der `GPIO0`-Taster **SOLLTE [SHOULD]** auf einen `factory_reset`-Button bei langem Druck gelegt werden (die Referenzkonfiguration nutzt 10 Sekunden Halten), damit ein fehlkonfiguriertes Gerät ohne Demontage wiederherstellbar ist `[ref-config]`
- Wenn OTA und AP-Fallback beide versagen, **SOLLTE [SHOULD]** auf serielles Flashen über USB-C zurückgefallen werden; das ist der bedingungslose Recovery-Pfad und erfordert physischen Zugriff `[policy]`

### Verifikation

- ESPHome-Komponenten-Schema-Fakten **MÜSSEN [MUST]** gegen die offizielle ESPHome-Dokumentation (<https://esphome.io>) und Hardware-Fakten gegen Espressifs `esp-box`-/`esp-bsp`-Repositories verifiziert werden, gemäß [`ha/upstream-docs-verification`](../upstream-docs-verification/de.md) — nie aus dem Gedächtnis `[policy]`
- Die ESPHome-Referenzkonfigurationen in `esphome/wake-word-voice-assistants` **MÜSSEN [MUST]** als normative Bindung dieser Hardware an ESPHome-Komponenten behandelt und jeder Drittanbieter-Config vorgezogen werden, wenn beide sich widersprechen `[policy]`
- Espressifs gerenderte Hardware-Übersichtsseiten **DÜRFEN NICHT [MUST NOT]** für Pin-Werte zitiert werden — ihre Pinouts sind als Bilder veröffentlicht, und eine daraus „abgelesene" Pin-Nummer ist nicht überprüfbar `[vendor]`
- Jede später ergänzte, nicht offensichtliche Aussage **SOLLTE [SHOULD]** ein Evidenz-Tier gemäß *Quellen-Tiers* tragen `[policy]`
- Diese Spec **SOLLTE [SHOULD]** neu verifiziert werden, wenn die Upstream-Referenzkonfigurationen ihre `min_version` anheben, da ESPHomes Audio- und Voice-Komponenten über Releases hinweg wiederholt ihr Schema geändert haben `[policy]`

## Akzeptanzkriterien

- [ ] Die vorliegende Generation (BOX / BOX-Lite / BOX-3) ist vor der Konfiguration bestimmt und im Device-YAML festgehalten
- [ ] `flash_size: 16MB`, Octal-PSRAM mit 80 MHz und das ESP-IDF-Framework sind gesetzt; der Logger läuft über `USB_SERIAL_JTAG`
- [ ] Jeder GPIO in der generierten Config entspricht der generationsspezifischen Tabelle, wobei Backlight- und I²S-LRCLK-Pin gegen die richtige Spalte verifiziert sind
- [ ] `ignore_strapping_warning` ist bewusst auf `GPIO0` gesetzt sowie auf `GPIO45`/`GPIO46`, soweit die Generation sie nutzt
- [ ] Das Display nutzt das Board-Model-Preset mit generationsrichtigem `invert_colors` und Reset-Pin-Invertierung, und das Backlight ist eine dimmbare `monochromatic`-Light-Entity
- [ ] Die Audiokette deklariert das Codec-Paar der jeweiligen Generation am gemeinsamen I²C-Bus — ES7210 + ES8311 auf BOX-3 und BOX, ES7243E + ES8156 auf BOX-Lite — mit `adc_type: external` / `dac_type: external` und erhaltener 16-kHz-/48-kHz-Aufteilung
- [ ] Der Endstufen-Freigabe-Switch auf `GPIO46` existiert und ist standardmäßig eingeschaltet
- [ ] Das Mikrofon deklariert `bits_per_sample: 16bit` explizit, und seine `channel`-Wahl ist eine bewusste Entscheidung statt eines geerbten Defaults
- [ ] Wo ein ES8311 verbaut ist, bleibt dessen `use_microphone` auf `false`
- [ ] Alle drei Taster sind berücksichtigt: `GPIO0` als GPIO-Binary-Sensor, der Mute-Pfad (Hardware-Status an `GPIO1` und/oder der Software-Mute-Switch) und der rote Haupttaster als `binary_sensor` des Touch-Controllers mit verifiziertem `index` — auf der BOX-Lite stattdessen die ADC-Kette an `GPIO1`, die drei Template-Binary-Sensoren treibt
- [ ] Wo ein Touchscreen genutzt wird, ist er am gemeinsamen I²C-Bus mit `interrupt_pin: GPIO3` und **ohne** eigenen `reset_pin` gebunden
- [ ] Keine Sensor-Entity gibt die SoC-Chip-Temperatur als Umgebungsmessung aus; Diagnose-Entities tragen `entity_category: diagnostic`
- [ ] Eine Voice-Pipeline ist gebunden (Mikrofon + Media-Player, Wake-Word on-device oder in HA), und das Display spiegelt die Zustände Listening / Thinking / Replying / Error / Muted
- [ ] Eine Mute-Steuerung existiert und ruft `microphone.mute` / `microphone.unmute` auf
- [ ] API-Verschlüsselung, OTA-Passwort und Secret-Handling folgen `ha/esphome-config-patterns`; keine literalen Zugangsdaten in irgendeiner Datei
- [ ] Die Board-Baseline wird über `packages:` konsumiert; die Device-Datei enthält nur das projektspezifische Delta
- [ ] Die Config besteht `esphome config`, und Display, Audio sowie (falls genutzt) Touch wurden jeweils am physischen Gerät ausgeübt
- [ ] Ein AP-Fallback plus Captive-Portal und ein `GPIO0`-Langdruck-Factory-Reset sind als Recovery-Pfade vorhanden
- [ ] Der Touch-Controller (GT911 vs. TT21100) wurde empirisch bestimmt, bevor ein Touchscreen-Block geschrieben wurde
- [ ] Keine Aussage in einer generierten Config hängt ohne `external_components`-Implementierung von der ICM-42670-IMU ab

## Offene Fragen

- **Display-Controller**: Espressifs BSP-Header-Kommentare nennen ST7789, während der Dependency-Satz `esp_lcd_ili9341` zieht. Da ESPHome über ein Model-Preset bindet, ist der Widerspruch derzeit harmlos — er sollte aber aufgelöst (oder als revisionsabhängig festgehalten) werden, bevor eine Config Panel-Parameter manuell setzt.
- **Touch-Controller nach Revision**: Gibt es einen verlässlichen, nicht-empirischen Weg (Aufdruck, Seriennummernbereich), ein GT911- von einem TT21100-Exemplar zu unterscheiden, oder bleibt der I²C-Scan die einzige belastbare Methode?
- **Index des roten Tasters**: Welchen `index` (0…3) der rote Haupttaster am GT911 bzw. am TT21100 belegt, ist nicht pro Board dokumentiert. Der gemessene Index ist pro Generation festzuhalten, sobald ein Gerät verfügbar ist, damit Scaffolds ihn direkt ausgeben können.

Per Entscheidung erledigt (hier festgehalten, damit die Begründung auffindbar bleibt, nicht als offene Arbeit): IMU und microSD-Slot sind **außerhalb des Scopes**, lokales Audio kommt aus dem Flash; das zweite Mikrofon bleibt **ungenutzt** (ein Kanal, wie Upstream); für Zubehör-Pinouts entsteht **keine** Portfolio-Tabelle, solange sie nur als Bild vorliegen; die Board-Baseline wird **gevendort** statt remote referenziert; und `min_version` folgt dem **Upstream-Floor** als reviewter Bump.
