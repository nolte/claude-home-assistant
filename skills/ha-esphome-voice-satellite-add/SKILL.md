---
name: ha-esphome-voice-satellite-add
description: "Turns an ESPHome device into a Home Assistant voice satellite per spec/ha/esp32-s3-box and spec/ha/assist-pipeline — emitting the generation-correct audio binding (one I2S bus, the external audio_adc / audio_dac pair the board actually carries, the capture/playback rate asymmetry, the power-amplifier switch), microphone and speaker, voice_assistant bound to both, on-device wake word, a discoverable mute control, and explicit no-Wi-Fi and no-Home-Assistant handling. Reports the HA-side steps it cannot perform: a pipeline per language, engine choice against host capacity, the assist_satellite binding, minimal entity exposure, and the debugging order. Activate on \"make this device a voice satellite\", \"add Assist to my ESPHome box\", or equivalent German requests. Do not activate for screen content (ha-esphome-display-author), for Home-Assistant-driven values (ha-esphome-binding-add), or for custom sentences and intent scripts (ha-automation-solution)."
tags: [home-assistant, esphome, voice, yaml]
phase: build
summary: "Turns an ESPHome device into a voice satellite — audio binding, microphone, speaker, voice_assistant, on-device wake word, mute, offline states."
summary_de: "Macht ein ESPHome-Gerät zum Sprach-Satelliten — Audio-Binding, Mikrofon, Lautsprecher, voice_assistant, On-Device-Wake-Word, Mute, Offline-Zustände."
use_when:
  - "you want an ESPHome device to become a Home Assistant voice satellite"
  - "you want on-device wake word wired to the Assist pipeline"
  - "you want the audio path bound correctly for the board generation in hand"
dont_use_when:
  - situation: "You want the screens the pipeline drives"
    alternative: ha-esphome-display-author
  - situation: "You want a Home-Assistant-driven value on the device"
    alternative: ha-esphome-binding-add
  - situation: "You want a sensor, bus, or component added"
    alternative: ha-esphome-config-augment
  - situation: "You want custom sentences, intent scripts, or automations"
    alternative: ha-automation-solution
see_also:
  - ha-esphome-display-author
  - ha-esphome-binding-add
  - ha-esphome-config-augment
  - ha-esphome-config-reviewer
  - ha-esphome-solution
---

# HA ESPHome Voice Satellite Add

Spec: `spec/claude/ha-esphome-voice-satellite-add/en.md` (EN canonical) / `spec/claude/ha-esphome-voice-satellite-add/de.md` (DE translation). Grounding specs: `spec/ha/esp32-s3-box/en.md` §Audio binding / §Voice-assistant binding (device side) and `spec/ha/assist-pipeline/en.md` (Home Assistant side).

Binds the voice path of one device per invocation, and states plainly which half of the result lives in Home Assistant rather than in the YAML.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** the board generation, the wake-word placement, and the engine consequences are decisions with hardware and privacy weight — a wrong codec pair addresses ICs that are not on the board, and server-side wake word means satellites stream continuously.
- **Two-sided result:** the device YAML is written here, the pipeline is configured by the operator in Home Assistant; that handover is a conversation, not a report.
- **Counter-dimension considered:** the pin and codec lookup per generation is mechanical (agent bias), but it is inseparable from the "which generation is actually in hand" question the operator answers; skill wins.

## When this skill activates

The user wants an ESPHome device to hear and speak — "mach die Box zum Assist-Satelliten", "add wake word to this device", "wire the microphone and speaker".

## When NOT to activate

- what the screen shows during a pipeline run → `ha-esphome-display-author`
- a Home-Assistant-driven value or command unrelated to voice → `ha-esphome-binding-add`
- a sensor, bus, or component → `ha-esphome-config-augment`
- custom sentences, `intent_script`, or automations reacting to the satellite → `ha-automation-solution`
- installing or hosting the speech engines (Wyoming services, Supervisor apps) → the operator's Home Assistant host

## Hard rules

1. **Read both grounding specs first**, plus the device file and its packages. Never generate pins, codecs, or component keys from memory.
2. **Determine the board generation before writing anything**, and record it in the config. The backlight ⇄ LRCLK swap between generations produces a device that boots and logs normally while showing nothing or staying silent.
3. **Bind the codec pair the board actually carries.** An `es7210` / `es8311` pair on a board fitted with `es7243e` / `es8156` addresses ICs that do not exist there. Declare the converters as external, and keep the deliberate 16 kHz capture / 48 kHz playback asymmetry.
4. **State `bits_per_sample: 16bit` explicitly on the microphone** rather than relying on the 32-bit platform default — a silent mismatch produces noise, not an error — and set `adc_type: external`.
5. **Expose the power amplifier as a GPIO switch with `restore_mode: RESTORE_DEFAULT_ON`.** With it disabled the pipeline runs and logs normally while the speaker stays silent.
6. **`voice_assistant:` binds a microphone and a response path.** The schema enforces neither — every key is optional — so a device that binds nothing validates cleanly and does nothing. This is a portfolio rule the skill applies.
7. **Prefer on-device wake word** (`micro_wake_word:` with the pipeline started from `on_wake_word_detected`), and where the placement is offered at runtime, switch between `micro_wake_word.start` and `voice_assistant.start_continuous` rather than deciding it at compile time.
8. **A discoverable mute is mandatory.** A voice device without one is a privacy defect, not a missing convenience; wire it to `microphone.mute` / `microphone.unmute` and reflect the muted state.
9. **Handle the disconnected cases explicitly** — dedicated no-Wi-Fi and no-Home-Assistant states, wake-word processing stopped when the API client disconnects — and keep the `ap:` fallback plus `captive_portal:` recovery path intact.
10. **Never duplicate the pipeline's own text-to-speech** with a manual `tts.speak` for the same response; that produces doubled or overlapping audio.
11. **Tune gain once in the chain.** Either the audio ADC's `mic_gain` or the pipeline's `auto_gain` / `volume_multiplier` — not both, and record which was chosen and why.
12. **Report the Home-Assistant-side steps rather than pretending they are done:** one pipeline per language with an explicit per-satellite assignment, the engine choice against documented host capacity (a speech-to-text engine that does not support naming a timer strips that feature), the `assist_satellite` entity binding with any deprecated voice binary sensors migrated, minimal entity exposure as a security boundary, and the debugging order — sentence parser, then pipeline debug, then time-boxed debug recording that is deleted afterwards.
13. **One device per run. No deploy.** The run ends at the edited file, the Home-Assistant checklist, and the validation report.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `device_file` | yes | — | the device YAML to turn into a satellite |
| `generation` | yes | — | the board generation in hand; resolved empirically when uncertain |
| `wake_word_placement` | no | on-device | `on-device`, `server-side`, or `runtime-selectable` |
| `wake_word_models` | no | asked | the models to ship for on-device detection |
| `media_playback` | no | false | whether the speaker is also wrapped in a `media_player` |

## Pre-flight (every run, in order — abort on first failure)

1. Read the device file and packages: existing audio, I²S/I²C buses, display, and any prior voice configuration.
2. Establish the generation — from the recorded substitution or comment, or by the spec's empirical I²C-scan route; do not proceed on an assumption.
3. Check the pin map for conflicts with anything already bound, and confirm the strapping-pin flags the board's reused pins need.
4. Confirm the wake-word placement against its consequences (language coverage, offline behaviour, host load, continuous streaming) with the operator.
5. Present the planned blocks and the Home-Assistant-side checklist; wait for approval before writing.

## Workflow

1. Verify every component key and default against the official ESPHome documentation, and every Home-Assistant-side claim against the official Home Assistant documentation, per `spec/ha/upstream-docs-verification`.
2. Emit the audio layer: the I²S bus with the generation-correct LRCLK, the shared I²C bus, the `audio_adc` / `audio_dac` pair, the microphone, the speaker, and the amplifier switch.
3. Emit `voice_assistant:` bound to microphone and response path, plus `micro_wake_word:` and the `on_wake_word_detected` start where wake word runs on the device.
4. Emit the mute control and, where a display exists, the pipeline-lifecycle triggers that drive it — routed through the display's single redraw script, never drawing directly.
5. Emit the offline handling and confirm the recovery path (`ap:` fallback, `captive_portal:`, factory-reset button) is present.
6. Validate with `esphome config <file>` where the toolchain is available; otherwise report it as the open caller step.
7. **Report:** the generation and how it was established, the emitted blocks, the gain decision, the wake-word placement and its privacy consequence, the ordered Home-Assistant checklist (pipeline, engines, satellite assignment, exposure), validation status, and the on-device bring-up that is still owed — display, microphone, and speaker each exercised before the config counts as good.

## Boundaries

- Screen content and pages → `ha-esphome-display-author`
- Home-Assistant-driven values unrelated to voice → `ha-esphome-binding-add`
- Sentences, intents, and automations → `ha-automation-solution`
- Engine hosting and pipeline creation in Home Assistant → the operator, per the reported checklist
- A conformance verdict on the result → `ha-esphome-config-reviewer` (independent, read-only)
- Compile, flash, on-device bring-up → the ESPHome toolchain / operator
