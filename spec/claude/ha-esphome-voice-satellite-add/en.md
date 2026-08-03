# Skill: `ha-esphome-voice-satellite-add`

Status: draft

## Context

A voice satellite is the one ESPHome result whose correctness is split across two systems: the device YAML binds microphones, codecs, wake word, and mute, while the Assist pipeline, its engines, the satellite assignment, and entity exposure live in Home Assistant. `spec/ha/esp32-s3-box` and `spec/ha/assist-pipeline` cover both halves and warn repeatedly about failures that look like success — a wrong codec pair for the generation, a 32-bit default against a 16-bit ADC, a disabled amplifier, a device bound to nothing that validates cleanly. This skill owns the device half and refuses to leave the Home Assistant half implicit.

## Scope

One device per invocation: the audio path, `voice_assistant:`, wake-word placement, the mute control, and the offline states. Plus an ordered Home-Assistant-side checklist the operator executes — this skill never configures Home Assistant itself.

## Goals

- Make the board generation an established fact before any pin or codec is written
- Emit an audio path that is correct for that generation rather than for the family
- Keep wake-word placement a decision made against language coverage, offline behaviour, host load, and continuous streaming
- Treat mute as a mandatory privacy control rather than a convenience
- Hand over the Home-Assistant-side work explicitly, including the engine choice that can strip a headline feature of the device

## Non-Goals

- Screen content driven by the pipeline (owned by `ha-esphome-display-author`)
- Home-Assistant-driven values unrelated to voice (owned by `ha-esphome-binding-add`)
- Custom sentences, intent scripts, and automations (owned by `ha-automation-solution`)
- Installing or hosting speech engines, and creating pipelines in Home Assistant — the operator's host
- Compile, flash, and on-device bring-up

## Requirements

- **MUST** read `spec/ha/esp32-s3-box/en.md` §Audio binding / §Voice-assistant binding and `spec/ha/assist-pipeline/en.md` before writing
- **MUST** establish and record the board generation before emitting a pin or a codec, resolving an ambiguous unit empirically rather than by appearance
- **MUST** emit the codec pair the generation actually carries, declared as external converters, and keep the documented capture/playback sample-rate asymmetry
- **MUST** state `bits_per_sample` explicitly on the microphone and set `adc_type: external`
- **MUST** expose the power amplifier as a switch that defaults on
- **MUST** bind `voice_assistant:` to a microphone and a response path, since the schema enforces neither and an unbound device validates cleanly while doing nothing
- **SHOULD** prefer on-device wake word, and where placement is offered at runtime, switch the start action accordingly rather than deciding it at compile time
- **MUST** emit a discoverable mute control wired to the microphone mute actions
- **MUST** handle the no-Wi-Fi and no-Home-Assistant cases explicitly and keep the AP-fallback recovery path intact
- **MUST NOT** duplicate the pipeline's text-to-speech with a manual speech call for the same response
- **MUST** apply gain once in the chain and record where
- **MUST** report the Home-Assistant-side checklist: one pipeline per language, explicit per-satellite assignment, engine choice against documented host capacity and feature support, the `assist_satellite` binding with deprecated voice binary sensors migrated, minimal exposure as a security boundary, and the sentence-parser-first debugging order with time-boxed debug recording
- **MUST** verify device keys against the official ESPHome docs and Home-Assistant-side facts against the official Home Assistant docs per `spec/ha/upstream-docs-verification`
- **MUST NOT** deploy, flash, or claim on-device verification it did not perform

## Acceptance Criteria

- [ ] The report names the generation and how it was established
- [ ] The emitted codec pair, LRCLK pin, and microphone bit depth match that generation
- [ ] A mute control exists and the disconnected states are handled
- [ ] The report contains the ordered Home-Assistant checklist, including the engine consequence for timer features
- [ ] On-device bring-up (display, microphone, speaker) is reported as still owed

## Open Questions

- The grounding spec's open questions on engine sizing and agent fallback are inherited: this skill reports the documented calibration points and requires the operator to measure on the real host rather than fixing a portfolio default.
