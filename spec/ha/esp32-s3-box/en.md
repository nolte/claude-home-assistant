# ESPHome Device: ESP32-S3-BOX Family (BOX / BOX-Lite / BOX-3 / BOX-3B)

Status: draft

## Context

The **ESP32-S3-BOX** family is Espressif's AI-voice development kit line built around the ESP32-S3-WROOM-1 module: a 2.4-inch 320×240 SPI display, a dual-microphone array behind an ES7210 audio ADC, a speaker behind an ES8311 codec, buttons, an IMU, and an expansion connector. Three generations are in circulation and are **not pin-compatible with each other**: the original **ESP32-S3-BOX**, the cost-reduced **ESP32-S3-BOX-Lite**, and the current **ESP32-S3-BOX-3** (shipped as `ESP32-S3-BOX-3` with four accessories and as `ESP32-S3-BOX-3B` with fewer accessories — an accessory-bundle distinction, not a board distinction) `[vendor]`.

In this portfolio the BOX is driven by **ESPHome**, not by ESP-IDF application code: the device is described declaratively in one YAML file, compiled and flashed by the ESPHome toolchain, and surfaced in Home Assistant through the native API. ESPHome maintains an **official, per-board reference configuration** for all three generations in [`esphome/wake-word-voice-assistants`](https://github.com/esphome/wake-word-voice-assistants) — that repository, not a forum post, is the normative source for how this hardware binds to ESPHome components `[ref-config]`.

This spec exists because the BOX is the first device in this portfolio where **the hardware itself is the hard part**. A generic ESPHome config spec cannot tell an author that the backlight pin and the I²S word-clock pin are *swapped* between BOX and BOX-3, that three of the required pins are strapping pins, or that the on-board IMU has no ESPHome component at all. It is therefore a **device-reference spec**: it pins down the board facts, the ESPHome component bindings derived from them, and the development process (bring-up → baseline → increment → validate → recover) that a skill layer can later automate.

It is scoped as a *sibling* of [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md), not a replacement: that spec owns the cross-device rules (file layout, `packages:` reuse, secret handling, API encryption, OTA); this one owns everything specific to the BOX hardware. Where the two touch, this spec defers.

### Source tiers

Espressif's own hardware-overview page for the BOX-3 carries its pinouts **as images only**, so it cannot be quoted for pin facts. Every claim below therefore carries an evidence tier, and a reviewer may hold this spec to it:

- `[bsp]` — Espressif's board-support package, [`espressif/esp-bsp`](https://github.com/espressif/esp-bsp) (`bsp/esp-box-3/include/bsp/esp-box-3.h`, `bsp/esp-box/include/bsp/esp-box.h`, `bsp/esp-box-3/idf_component.yml`): authoritative for GPIO assignments and fitted ICs.
- `[ref-config]` — ESPHome's official board configs in [`esphome/wake-word-voice-assistants`](https://github.com/esphome/wake-word-voice-assistants) (`esp32-s3-box-3/`, `esp32-s3-box/`, `esp32-s3-box-lite/`): authoritative for the ESPHome-side binding of those pins.
- `[doc]` — the official ESPHome component documentation at <https://esphome.io>: authoritative for component schemas.
- `[vendor]` — Espressif's [`esp-box`](https://github.com/espressif/esp-box) product documentation: authoritative for product/variant framing.
- `[policy]` — a nolte-portfolio rule, not a hardware or upstream fact.

Verified 2026-08; the reference configs pin `min_version: 2026.4.0` `[ref-config]`.

## Goals

- Pin down the board facts of the BOX family — SoC, memory, fitted ICs, and a per-generation GPIO map — from quotable sources rather than from memory
- Make the **generation differences** explicit and unmissable, above all the backlight ⇄ I²S-LRCLK pin swap between BOX and BOX-3, which silently produces a dark screen or silent audio
- Bind each hardware block to its concrete ESPHome component (display, audio ADC/DAC, microphone, speaker, media player, wake word, voice assistant, touch, buttons) with the pin values the official reference configs use
- Define the **development process** for an ESPHome project on this device — variant identification, baseline flash, incremental augmentation, validation, and recovery — so it can be executed repeatably and later automated by a skill
- Mark honestly where the hardware has **no ESPHome path** (IMU) or where the sources are ambiguous (touch controller, display controller), instead of asserting a plausible answer
- Give the future ESPHome plugin (three-plugin split, roadmap item R-2) a device-reference anchor to build device-specific skills on

## Non-Goals

- Re-specifying the cross-device ESPHome rules — file layout, `packages:` reuse, `secrets.yaml` handling, API encryption, OTA discipline live in [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md) and are referenced, not restated
- ESP-IDF / ESP-ADF application development on the BOX (the vendor's own `esp-box` demo firmware, LVGL C code, the `esp_lcd`/`esp_codec_dev` driver layer) — this portfolio drives the device through ESPHome
- Authoring ESPHome **custom components** in C++/Python (`external_components`) — a deliberately separate axis; *consuming* a third-party component from a device YAML is in scope
- A complete LVGL widget reference — LVGL is bound here only at the level of "how it attaches to this board's display and touchscreen"
- The Home Assistant Assist pipeline itself (STT/TTS/conversation-agent selection, wake-word training) — the BOX is a client of that pipeline; configuring the pipeline is an HA-side concern
- Other Espressif voice hardware (ESP32-S3-Korvo, ESP32-P4 boards) and the Home Assistant Voice Preview Edition, which is a different product with its own reference config
- Accessory-module bring-up beyond naming the parts (BOX-3-SENSOR radar/IR, BOX-3-DOCK camera) — no pin-level claims are made for accessories, because the vendor publishes those pinouts as images only

## Requirements

### Board identity and variant selection

- **MUST** determine which generation is in hand **before** any config is written: BOX, BOX-Lite, and BOX-3 differ in pin assignment and display parameters, and a config for the wrong generation compiles and flashes cleanly while failing at runtime `[bsp]` `[ref-config]`
- **MUST** record the determined generation in the device YAML (substitution or comment) so a later reader can tell which pin map applies `[policy]`
- **SHOULD** treat `ESP32-S3-BOX-3` and `ESP32-S3-BOX-3B` as the **same board** for configuration purposes — the published difference is the bundled accessory set, not the PCB `[vendor]`
- **SHOULD** resolve an ambiguous unit empirically rather than by appearance: flash a minimal config with an I²C bus on `SCL: GPIO18` / `SDA: GPIO8` and read the scan results from the log, then match the responding addresses against the fitted ICs below `[policy]`

### Core platform configuration

- **MUST** declare `flash_size: 16MB` — the BOX carries 16 MB flash, while the ESPHome `esp32` component defaults to `4MB`; leaving the default wastes flash and breaks partition assumptions for larger firmwares `[doc]` `[ref-config]`
- **MUST** enable PSRAM as `psram: {mode: octal, speed: 80MHz}` — the module carries 16 MB **octal** PSRAM, and `micro_wake_word`, full-frame images, and LVGL buffers depend on it `[bsp]` `[ref-config]`
- **MUST** use the **ESP-IDF** framework; it is the default and recommended framework for ESP32 chips in current ESPHome releases, and the reference configs use it `[doc]` `[ref-config]`
- **SHOULD** set `cpu_frequency: 240MHz`; the reference configs additionally set the sdkconfig options `CONFIG_ESP32S3_DEFAULT_CPU_FREQ_240`, `CONFIG_ESP32S3_DATA_CACHE_64KB`, and `CONFIG_ESP32S3_DATA_CACHE_LINE_64B` `[ref-config]`
- **SHOULD** route the logger over the native USB peripheral with `logger: {hardware_uart: USB_SERIAL_JTAG}` — the BOX exposes a single USB-C port and has no separate UART bridge `[ref-config]`
- **SHOULD** keep `board: esp32s3box` as all three reference configs do. The `esp32` documentation calls `board` "no longer recommended" in favour of `variant`, but also states it "only affects pin aliases and some internal settings", and that a `variant`-only config has its board "automatically filled using a standard Espressif devkit board". Since this spec names every pin explicitly and relies on no alias, either form works — following upstream keeps portfolio configs diffable against the reference `[doc]` `[ref-config]` `[policy]`

### GPIO map (per generation)

- **MUST** take pin values from this table rather than from a generic "ESP32-S3" pinout; all three columns are `[bsp]` for the hardware and `[ref-config]` for the ESPHome usage, each verified against that generation's own BSP header (`bsp/esp-box-3`, `bsp/esp-box`, `bsp/esp-box-lite`):

| Function | BOX-3 | BOX (original) | BOX-Lite |
|---|---|---|---|
| I²C SCL | `GPIO18` | `GPIO18` | `GPIO18` |
| I²C SDA | `GPIO8` | `GPIO8` | `GPIO8` |
| I²S BCLK (SCLK) | `GPIO17` | `GPIO17` | `GPIO17` |
| I²S MCLK | `GPIO2` | `GPIO2` | `GPIO2` |
| **I²S LRCLK (WS)** | **`GPIO45`** | **`GPIO47`** | **`GPIO47`** |
| I²S DOUT → speaker | `GPIO15` | `GPIO15` | `GPIO15` |
| I²S DIN ← microphones | `GPIO16` | `GPIO16` | `GPIO16` |
| Power-amplifier enable | `GPIO46` | `GPIO46` | `GPIO46` |
| **Display backlight** | **`GPIO47`** | **`GPIO45`** | **`GPIO45`** (inverted) |
| Display SPI CLK (PCLK) | `GPIO7` | `GPIO7` | `GPIO7` |
| Display SPI MOSI (DATA0) | `GPIO6` | `GPIO6` | `GPIO6` |
| Display CS | `GPIO5` | `GPIO5` | `GPIO5` |
| Display DC | `GPIO4` | `GPIO4` | `GPIO4` |
| Display RESET | `GPIO48` (inverted) | `GPIO48` | `GPIO48` |
| Touch interrupt | `GPIO3` | `GPIO3` | — *(no touch: `BSP_CAPS_TOUCH 0`)* |
| Config / boot button | `GPIO0` | `GPIO0` | `GPIO0` *(the only button in its BSP)* |
| Mute button / status | `GPIO1` | `GPIO1` | `GPIO1` *(ADC button ladder, not mute)* |
| Red main button | *(via touch controller)* | *(via touch controller)* | — |
| Dock / expansion I²C SCL / SDA | `GPIO40` / `GPIO41` | — | — |
| USB D+ / D− | `GPIO20` / `GPIO19` | `GPIO20` / `GPIO19` | `GPIO20` / `GPIO19` |

- **MUST** treat the **backlight ⇄ LRCLK swap** between BOX-3 (`backlight 47`, `LRCLK 45`) and BOX/BOX-Lite (`backlight 45`, `LRCLK 47`) as the family's primary failure mode: swapping them yields a device that boots, connects, and logs normally but shows a black screen and/or produces no audio `[bsp]` `[ref-config]`
- **MUST** set `ignore_strapping_warning: true` deliberately on the strapping pins the board reuses — `GPIO0` (config button), `GPIO45` (I²S LRCLK on BOX-3), and `GPIO46` (amplifier enable); the reference configs set it on exactly these `[ref-config]`
- **SHOULD** treat the SD-card and PMOD/expansion pins as board-specific and read them from the BSP header for the generation in hand rather than assuming them; on the BOX-3 the SD slot is `CLK GPIO11`, `CMD GPIO14`, `D0 GPIO9`, `D1 GPIO13`, `D2 GPIO42`, `D3 GPIO12`, power `GPIO43`, and the two PMOD headers overlap that set `[bsp]`
- **MUST NOT** assign a GPIO to a project-specific peripheral without checking it against this table plus the BSP's PMOD/SD ranges — the BOX exposes far fewer free pins than a bare ESP32-S3 devkit `[policy]`

### Fitted components

- **MUST** assume this IC set on the BOX-3 and bind ESPHome components accordingly: display controller (see below), capacitive touch controller (see below), **ES7210** audio ADC at I²C `0x40` (microphone array), **ES8311** audio codec at I²C `0x18` (speaker path), an **ICM-42670 / ICM-42607-P** IMU, and an **AHT30** temperature/humidity sensor `[bsp]` `[doc]`
- **MUST NOT** carry the BOX-3 IC set over to the **BOX-Lite**, which is a different board behind the same silhouette: its BSP names an **ES7243E** audio ADC and an **ES8156** audio DAC (not ES7210/ES8311), an **ST7789** display controller, **no touch controller at all** (`BSP_CAPS_TOUCH 0`), and a single config button — the audio bindings below therefore differ per generation `[bsp]` `[ref-config]`
- **MUST** count **three** buttons but only **two** button GPIOs on BOX and BOX-3: Espressif's BSP enumerates `BSP_BUTTON_CONFIG`, `BSP_BUTTON_MUTE`, and `BSP_BUTTON_MAIN`, while only `GPIO0` (config) and `GPIO1` (mute) are GPIO-backed — the third, the red button below the screen, is a **touch key read through the touch controller**, not a GPIO `[bsp]` `[doc]`
- **MUST NOT** treat the mute button as a plain contact on `GPIO1`: the BSP records it as "wired to Logic Gates, result mapped to `GPIO_NUM_1`", so the pin carries a derived **mute status**, and the hardware mute path exists independently of any ESPHome logic `[bsp]`
- **SHOULD** resolve where the **AHT30** actually sits before promising it: Espressif's product documentation lists temperature/humidity under the separate BOX-3-SENSOR accessory, while the BOX-3 BSP declares `BSP_CAPS_HUMITURE 1` and pulls an `aht30` driver — an I²C scan on the unit in hand settles it `[vendor]` `[bsp]`
- **SHOULD** treat the **microSD** slot as out of reach for a plain device YAML: the BSP defines a full SDMMC pin set (and an SPI alternative), but ESPHome's official component index carries no SD-card component (verified 2026-08), so SD access requires `external_components` `[bsp]` `[doc]`
- **MUST** verify the **display controller** on the unit in hand instead of trusting a single source: Espressif's BSP header comments name **ST7789**, while the same BSP's dependency set pulls `esp_lcd_ili9341`, and ESPHome binds the panel through a board **model preset** rather than a raw controller name — the preset is the supported path, and a wrong manual controller choice shows as inverted or shifted colours `[bsp]` `[doc]`
- **MUST** verify the **touch controller** empirically (I²C scan) rather than assuming: Espressif's BOX-3 BSP declares drivers for **both** `esp_lcd_touch_gt911` and `esp_lcd_touch_tt21100`, which means the fitted controller varies by revision; ESPHome ships `gt911` and `tt21100` touchscreen platforms for exactly this reason `[bsp]` `[doc]`
- **MUST NOT** plan on reading the **IMU** from ESPHome: the ICM-42670 has **no** component in the ESPHome sensor catalogue (which ships BMI270, LSM6DS, and QMI8658 as accelerometer/gyroscope platforms); using it requires an `external_components` implementation and is out of scope for a device-YAML slice `[doc]` `[bsp]`
- **MUST** bind an AHT30 through the `aht10` platform with `variant: AHT20`: the component documents support for "your AHT10, AHT20 or AHT30 I²C-based sensor", and its `variant` enum offers `AHT10` (the default) and `AHT20`, the latter covering AHT20 and AHT30 — leaving the default on an AHT30 selects the wrong register set `[doc]`

### Display binding

- **MUST** declare the SPI bus explicitly as `clk_pin: 7` / `mosi_pin: 6`; the display is the only device on it in the reference configs `[ref-config]`
- **MUST** use the board **model preset** rather than hand-rolled panel parameters — `model: S3BOX` for BOX-3 and BOX; for BOX-Lite the preset's spelling differs by platform (`S3BOX_LITE` under `ili9xxx`, as the reference config uses it, versus `S3BOXLITE` in the `mipi_spi` model list), so it **MUST** be taken from the documentation of the platform actually declared. The model sets resolution and panel defaults, and remaining keys override it `[doc]` `[ref-config]`
- **MUST** carry the per-generation display parameters exactly as the reference configs do `[ref-config]`:
  - **BOX-3** — `platform: mipi_spi`, `model: S3BOX`, `invert_colors: false`, `data_rate: 40MHz`, `cs_pin: 5`, `dc_pin: 4`, `reset_pin: {number: 48, inverted: true}`
  - **BOX** — `platform: ili9xxx`, `model: S3BOX`, `invert_colors: false`, `data_rate: 40MHz`, `cs_pin: 5`, `dc_pin: 4`, `reset_pin: 48` (**not** inverted)
  - **BOX-Lite** — `platform: ili9xxx`, `model: S3BOX_LITE`, **`invert_colors: true`** (the one generation that inverts), plus a backlight output declared `inverted: true`
- **SHOULD** prefer the newer `mipi_spi` platform for new configs; the BOX-3 reference config has moved to it while the older BOX config still uses `ili9xxx` `[ref-config]`
- **MUST** drive the backlight as a dimmable light rather than a bare GPIO: `output: {platform: ledc, pin: <backlight>}` plus `light: {platform: monochromatic}`, so screen brightness is an HA entity `[ref-config]`
- **SHOULD** set `update_interval: never` on the display and redraw explicitly from automations or scripts; the reference configs render event-driven pages and call `component.update` themselves `[ref-config]`
- **MUST** take everything beyond the binding — canvas geometry, pages, drawing primitives, fonts, images, colours, layout zones, and the LVGL widget path — from [`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md), which owns rendering on this panel `[policy]`
- **MUST** when using **LVGL** instead of `display` pages set `auto_clear_enabled: false` and `update_interval: never` on the display, bind the touchscreen into `lvgl:`, and size `buffer_size` deliberately — LVGL owns rendering, and on a PSRAM board a small internal-RAM buffer can outperform a full PSRAM buffer `[doc]`

### Touch and buttons

- **MUST** bind the touchscreen through the platform matching the fitted controller — `touchscreen: {platform: gt911}` or `{platform: tt21100}` — on the shared I²C bus, with `interrupt_pin: GPIO3`; the GT911 answers at `0x5D` or `0x14` depending on variant `[doc]` `[bsp]`
- **MUST NOT** give the touchscreen its own `reset_pin` when the display and touch controller share the reset line, as they do on the BOX: the component documentation states the reset pin must then be configured on the **display only** `[doc]`
- **MUST** read the **red main button** below the screen as a touch key of the touch controller, not as a GPIO: both platforms expose `binary_sensor: {platform: gt911|tt21100, index: 0…3}` for up to four buttons outside the display area, and the ESPHome documentation names the BOX's red button as the example for exactly this `[doc]`
- **SHOULD** determine the button's `index` empirically on first bring-up (log the binary sensors for indices 0…3 and press the button) rather than assuming an index `[policy]`
- **MUST** declare the **config button** on `GPIO0` as `binary_sensor: {platform: gpio, mode: INPUT_PULLUP, inverted: true, ignore_strapping_warning: true}` — the reference configs use exactly this shape and hang both a short-press action and the long-press factory reset off `on_multi_click` `[ref-config]`
- **MAY** expose the **mute button/status** on `GPIO1` as a further GPIO binary sensor on BOX and BOX-3, keeping in mind that it reports the logic-gate-derived mute state; note that the upstream reference configs do **not** bind `GPIO1` and instead ship a software `switch: {platform: template}` named "Mute" that drives `microphone.mute` / `microphone.unmute` `[bsp]` `[ref-config]`
- **MUST** on **BOX-Lite** read the three front buttons as an **ADC ladder** on `GPIO1` instead of as GPIO buttons: the reference config polls `sensor: {platform: adc, pin: GPIO1, attenuation: 12db, update_interval: 16ms}` and maps voltage bands (none ≈ 3.121 V, left ≈ 2.392 V, middle ≈ 1.965 V, right ≈ 0.794 V, plus the combination bands) onto three `binary_sensor: {platform: template}` entities `[ref-config]`
- **SHOULD** treat those BOX-Lite thresholds as board-calibrated values to be re-verified per unit, not as universal constants — they are the measured bands of one reference device `[policy]`
- **SHOULD** bind the touchscreen into `lvgl:` when a widget UI is used, rather than handling raw touch coordinates in lambdas `[doc]`

### Audio binding

- **MUST** declare one I²S bus with `i2s_bclk_pin: GPIO17`, `i2s_mclk_pin: GPIO2`, and the generation-correct `i2s_lrclk_pin`, and one I²C bus (`SCL 18` / `SDA 8`) that both codecs share `[ref-config]`
- **MUST** declare the codecs as **external** converters, not as raw I²S, and **MUST** pick the pair that matches the generation `[ref-config]` `[doc]` `[bsp]`:
  - **BOX-3 and BOX** — `audio_adc: {platform: es7210, bits_per_sample: 16bit, sample_rate: 16000}` and `audio_dac: {platform: es8311, bits_per_sample: 16bit, sample_rate: 48000}`, both bound to the shared `i2c_id`
  - **BOX-Lite** — `audio_adc: {platform: es7243e}` and `audio_dac: {platform: es8156}`; both platforms exist in ESPHome and are what the BOX-Lite reference config declares. An `es7210`/`es8311` pair on a BOX-Lite addresses ICs that are not on the board
- **SHOULD** leave the codec I²C addresses at their component defaults, which already match the board — `0x40` for the ES7210 and `0x18` for the ES8311 — and set them explicitly only when an I²C scan shows otherwise `[doc]` `[bsp]`
- **SHOULD** tune microphone sensitivity through the ES7210's `mic_gain` (range `0DB`…`37.5DB`, default `24DB`) before reaching for the voice assistant's `volume_multiplier` or `auto_gain`, so the gain is applied once in the analogue path rather than twice `[doc]` `[ref-config]`
- **MUST NOT** set `use_microphone: true` on the ES8311: the BOX's microphones hang on the ES7210, and the ES8311's own microphone path (with its separate `mic_gain`, default `42DB`) is unused on this board — the key defaults to `false` and must stay there `[doc]` `[bsp]`
- **MUST** declare the microphone with `platform: i2s_audio`, `i2s_din_pin: GPIO16`, `adc_type: external`, `sample_rate: 16000`, `bits_per_sample: 16bit` — the ES7210 does the conversion, so an `internal` ADC type is wrong for this board and the documentation records `internal` as no longer supported `[ref-config]` `[doc]`
- **MUST** state `bits_per_sample: 16bit` explicitly on the microphone rather than relying on the platform default, which is `32bit` — the reference configs set 16-bit to match the ES7210 declaration, and a silent mismatch between the two produces noise, not an error `[doc]` `[ref-config]`
- **SHOULD** understand that the board's **two microphones** are not two ESPHome entities: they are two ADC channels of the ES7210 that arrive over one I²S stream, and the microphone platform selects from it via `channel` (`left`, `right`, `stereo`; default `right`). The reference configs leave the default in place and consume a **single** channel for the voice pipeline; `stereo` doubles the payload and is only worth it when both channels are actually processed `[doc]` `[ref-config]`
- **MUST** declare the speaker with `platform: i2s_audio`, `i2s_dout_pin: GPIO15`, `dac_type: external`, `audio_dac: <es8311 id>`, `sample_rate: 48000`, `bits_per_sample: 16bit`, `channel: left` `[ref-config]`
- **MUST** expose the power amplifier as a GPIO switch on `GPIO46` with `restore_mode: RESTORE_DEFAULT_ON` — with the amplifier disabled the pipeline runs and logs normally but the speaker stays silent `[ref-config]`
- **SHOULD** note the deliberate **sample-rate asymmetry** (capture at 16 kHz, playback at 48 kHz) and keep it when adding media playback, rather than unifying the rates `[ref-config]`
- **SHOULD** wrap the speaker in `media_player: {platform: speaker}` when the device should also play announcements and media, and constrain the volume range (`volume_min` / `volume_max`) so the small enclosure is not driven into distortion `[ref-config]`

### Voice-assistant binding

- **MUST** bind `voice_assistant:` to the microphone, and to a `media_player`/`speaker` for the response path; `microphone` is the only required key of the component `[doc]` `[ref-config]`
- **SHOULD** run wake-word detection **on device** via `micro_wake_word:` with one or more models, and start the pipeline from `on_wake_word_detected`; the reference config ships `okay_nabu`, `hey_mycroft`, and `hey_jarvis` `[ref-config]` `[doc]`
- **SHOULD** offer the on-device / in-Home-Assistant wake-word location as a runtime `select:` rather than a compile-time decision, and switch between `micro_wake_word.start` and `voice_assistant.start_continuous` accordingly — the reference config treats this as a first-class user setting `[ref-config]`
- **SHOULD** drive the display from the pipeline lifecycle (`on_listening`, `on_stt_end`, `on_tts_start`, `on_end`, `on_error`) and from the timer triggers (`on_timer_started`, `on_timer_finished`, `on_timer_tick`, …), so screen state and pipeline state cannot diverge `[doc]` `[ref-config]`
- **SHOULD** expose a **mute** control that calls `microphone.mute` / `microphone.unmute` and reflects the muted state on screen; a voice device without a discoverable mute is a privacy defect, not a missing convenience `[policy]` `[ref-config]`
- **MUST** handle the disconnected case explicitly — the reference config renders dedicated "no Wi-Fi" and "no Home Assistant" screens and stops wake-word processing when the API client disconnects `[ref-config]`
- **SHOULD** verify the required Home Assistant version for the pipeline features in use against the component documentation before promising them (the component documents a 2023.5 floor for basic voice-assistant support and later floors for newer features) `[doc]`

### Sensors, storage, and expansion

- **MUST** treat the on-board **IMU** as unavailable from a plain device YAML — see *Fitted components*; if motion is actually required, the cost is an `external_components` driver, and that decision belongs in the project scope, not in a scaffold `[doc]` `[bsp]`
- **SHOULD** bind an **AHT30** (once its presence is confirmed) as `sensor: {platform: aht10, variant: AHT20}` on the shared I²C bus, per *Fitted components* `[doc]`
- **MUST NOT** publish the ESP32's own die temperature (`sensor: {platform: internal_temperature}`) as a room temperature: it measures the SoC next to a running display and amplifier, reads high, and some ESP32 variants return invalid values that the component discards `[doc]` `[policy]`
- **SHOULD** ship the standard diagnostic entities on a device that is expected to stay deployed — `sensor: {platform: wifi_signal}`, `sensor: {platform: uptime}`, and optionally `internal_temperature` — each with `entity_category: diagnostic` so they do not clutter the user-facing dashboard `[doc]` `[policy]`
- **MAY** use the BOX-3's **second I²C bus** on `GPIO40` / `GPIO41` (the dock/expansion bus) for project-specific sensors, keeping the codec bus on `GPIO18` / `GPIO8` free of unrelated traffic `[bsp]`
- **MUST** check any expansion pin against the SD and PMOD assignments before use — the two PMOD headers overlap the SD-card pins (`GPIO9`, `GPIO11`…`GPIO14`, `GPIO42`, `GPIO43`), so a peripheral on a PMOD pin can collide with SD usage `[bsp]`
- **SHOULD** treat accessory-module peripherals (BOX-3-SENSOR radar and IR, BOX-3-DOCK camera) as unspecified here: no pin claim is made for them, and any binding must be derived and verified on hardware first `[vendor]`

### Connectivity, secrets, and reuse

- **MUST** apply [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md) unchanged for wifi/secrets/API-encryption/OTA — in particular `api:` with `encryption`, `ota:` with a password, and no literal credentials in any file `[policy]`
- **MUST NOT** infer the portfolio's security baseline from the ESPHome reference config: that config is a *distribution* firmware adopted by unknown users and therefore ships without a pre-shared encryption key; a portfolio device config is a *known-owner* config and carries the key `[policy]` `[ref-config]`
- **MUST** reuse the board's baseline through `packages:` — either the upstream board config as a remote package or a repo-local board package — instead of copying the reference YAML into each new device file `[policy]`
- **SHOULD** keep the project-specific delta (extra sensors, custom pages, automations) in the device file and the board plumbing (pins, codecs, display) in the package, so a board revision is a one-file change `[policy]`
- **SHOULD** declare `esphome: {min_version: ...}` and treat a bump as a reviewed change; the reference configs pin `min_version: 2026.4.0` `[ref-config]`
- **MUST** take the Home-Assistant-side contract — Assist pipeline, engine choice, entity exposure, `assist_satellite` binding, and pipeline debugging — from [`ha/assist-pipeline`](../assist-pipeline/en.md); a correctly bound device in front of an unconfigured pipeline is mute `[policy]`
- **MUST** keep the device's mDNS name unique on the network, since the native API is discovered by that name; the reference configs achieve this with `name_add_mac_suffix: true`, and removing it makes uniqueness the author's responsibility `[ref-config]` `[policy]`
- **SHOULD** decide `api: {reboot_timeout: ...}` deliberately: it defaults to 15 minutes, so a device whose Home Assistant is offline for longer reboots on that cycle — the mechanism exists because the ESP can report connectivity it does not have, and only a reboot recovers it `[doc]` `[policy]`

### Development process

- **MUST** run the process in this order — skipping identification or baseline is what produces the silent-failure modes above `[policy]`:
  1. **Identify** — determine the generation (see *Board identity*), record it in the config
  2. **Baseline** — flash the unmodified upstream reference config for that generation and confirm display, microphone, speaker, and HA connection all work
  3. **Increment** — add project-specific blocks one at a time on top of the baseline package
  4. **Validate** — `esphome config` for schema, `esphome compile` for the build, `esphome logs` for runtime
  5. **Recover** — when a step bricks the behaviour, fall back per *Recovery* below
- **MUST** flash the **first** image over USB-C (serial) and every later image over OTA; the device has one USB-C port that serves power, flashing, and logging `[vendor]` `[ref-config]`
- **MUST** validate every generated or edited config with `esphome config <file>` before flashing, and report validation as an open caller step when the toolchain is unavailable `[policy]`
- **SHOULD** compile before flashing (`esphome compile`) so a build failure is separated from a flash failure; on this board a full clean build is minutes long, and a wrong-generation config fails *after* the build, not during it `[policy]`
- **SHOULD** read runtime behaviour from `esphome logs` over the USB serial-JTAG logger during bring-up, and over the network afterwards `[ref-config]`
- **MUST NOT** treat a successful compile-and-flash as evidence that the pin map is right — display, audio, and touch must each be exercised on the device before the config is considered good `[policy]`

### Recovery

- **MUST** keep a recovery path in every config: a Wi-Fi `ap:` fallback plus `captive_portal:` so an unreachable device stays reconfigurable without a cable `[ref-config]`
- **SHOULD** wire the `GPIO0` button to a `factory_reset` button on a long press (the reference config uses a 10-second hold) so a misconfigured device can be recovered without disassembly `[ref-config]`
- **SHOULD** fall back to serial flashing over USB-C when OTA and the AP fallback both fail; this is the unconditional recovery path and requires physical access `[policy]`

### Verification

- **MUST** verify ESPHome component schema facts against the official ESPHome documentation (<https://esphome.io>) and hardware facts against Espressif's `esp-box` / `esp-bsp` repositories, per [`ha/upstream-docs-verification`](../upstream-docs-verification/en.md) — never from memory `[policy]`
- **MUST** treat the ESPHome reference configs in `esphome/wake-word-voice-assistants` as the normative binding of this hardware to ESPHome components, and prefer them over any third-party config when the two disagree `[policy]`
- **MUST NOT** quote Espressif's rendered hardware-overview pages for pin values — their pinouts are published as images, and a pin number "read" from them is unverifiable `[vendor]`
- **SHOULD** carry an evidence tier on every non-obvious claim added to this spec later, using the tiers defined in *Source tiers* `[policy]`
- **SHOULD** re-verify this spec when the upstream reference configs bump their `min_version`, since ESPHome audio and voice components have changed schema repeatedly across releases `[policy]`

## Acceptance Criteria

- [ ] The generation in hand (BOX / BOX-Lite / BOX-3) is determined before configuration and recorded in the device YAML
- [ ] `flash_size: 16MB`, octal PSRAM at 80 MHz, and the ESP-IDF framework are set; the logger runs over `USB_SERIAL_JTAG`
- [ ] Every GPIO in the generated config matches the per-generation table, with the backlight and I²S-LRCLK pins verified against the correct column
- [ ] `ignore_strapping_warning` is set deliberately on `GPIO0`, and on `GPIO45`/`GPIO46` where the generation uses them
- [ ] The display uses the board model preset with the generation-correct `invert_colors` and reset-pin inversion, and the backlight is a dimmable `monochromatic` light entity
- [ ] The audio chain declares ES7210 as `audio_adc` and ES8311 as `audio_dac` on the shared I²C bus, with `adc_type: external` / `dac_type: external` and the 16 kHz / 48 kHz split preserved
- [ ] The amplifier-enable switch on `GPIO46` exists and defaults to on
- [ ] The microphone declares `bits_per_sample: 16bit` explicitly, and its `channel` selection is a deliberate choice rather than an inherited default
- [ ] `use_microphone` on the ES8311 is left at `false`
- [ ] All three buttons are accounted for: `GPIO0` as a GPIO binary sensor, the mute path (hardware status on `GPIO1` and/or the software mute switch), and the red main button as a touch-controller `binary_sensor` with a verified `index` — on BOX-Lite instead the ADC ladder on `GPIO1` driving three template binary sensors
- [ ] Where a touchscreen is used, it is bound on the shared I²C bus with `interrupt_pin: GPIO3` and **without** its own `reset_pin`
- [ ] No sensor entity presents the SoC die temperature as an ambient measurement; diagnostic entities carry `entity_category: diagnostic`
- [ ] A voice pipeline is bound (microphone + media player, wake word on device or in HA) and the display reflects listening / thinking / replying / error / muted states
- [ ] A mute control exists and calls `microphone.mute` / `microphone.unmute`
- [ ] API encryption, OTA password, and secret handling follow `ha/esphome-config-patterns`; no literal credential appears in any file
- [ ] The board baseline is consumed through `packages:`; the device file contains only the project-specific delta
- [ ] The config passes `esphome config`, and display, audio, and (if used) touch have each been exercised on the physical device
- [ ] An AP fallback plus captive portal and a `GPIO0` long-press factory reset are present as recovery paths
- [ ] The touch controller (GT911 vs TT21100) was determined empirically before a touchscreen block was written
- [ ] No claim in a generated config depends on the ICM-42670 IMU without an `external_components` implementation

## Open Questions

- **Display controller**: Espressif's BSP header comments name ST7789 while its dependency set pulls `esp_lcd_ili9341`. Since ESPHome binds via a model preset, the contradiction is currently harmless — but it should be resolved (or recorded as revision-dependent) before any config sets panel parameters manually.
- **Touch controller by revision**: is there a reliable, non-empirical way (silkscreen marking, serial-number range) to tell a GT911 unit from a TT21100 unit, or does the I²C scan remain the only dependable method?
- **IMU path**: is an `external_components` ICM-42670 implementation worth pulling into the portfolio, or does the IMU stay out of scope for ESPHome-driven BOX projects?
- **Red-button index**: which `index` (0…3) the red main button occupies on the GT911 and on the TT21100 is not documented per board. Should this portfolio record the measured index per generation once verified, so scaffolds can emit it directly?
- **Second microphone**: is there a use case in this portfolio that justifies `channel: stereo` (beamforming, direction detection) — and does the voice pipeline consume more than one channel at all, or is the second microphone effectively unused under ESPHome?
- **SD-card path**: the slot is wired and the pins are known, and the absence of any SD/storage component in ESPHome's index was re-confirmed 2026-08. Is an `external_components` SD driver worth adopting (local audio files, logging), or does the slot stay unused?
- **Accessory pinouts**: the BOX-3-DOCK / -SENSOR / -BREAD pinouts are published as images only. Should this portfolio derive and maintain its own text pin table for the accessories (verified on hardware), or keep accessories out of scope?
- **Baseline package source**: should the board baseline be consumed as a remote `packages:` reference to `esphome/wake-word-voice-assistants` (always current, network-dependent, upstream-controlled) or vendored into a repo-local package (reviewable, pinned, manual to update)?
- **Version pinning**: the reference configs pin `min_version: 2026.4.0`. Should the portfolio pin the same floor for BOX configs, and how is a bump reviewed given the repeated schema changes in ESPHome's audio components?
