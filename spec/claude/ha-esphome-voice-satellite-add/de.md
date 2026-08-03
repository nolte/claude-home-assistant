# Skill: `ha-esphome-voice-satellite-add`

Status: draft

## Kontext

Ein Sprach-Satellit ist das eine ESPHome-Ergebnis, dessen Korrektheit sich über zwei Systeme verteilt: Das Device-YAML bindet Mikrofone, Codecs, Wake-Word und Mute, während Assist-Pipeline, deren Engines, die Satelliten-Zuordnung und die Entity-Freigabe in Home Assistant leben. `spec/ha/esp32-s3-box` und `spec/ha/assist-pipeline` decken beide Hälften ab und warnen wiederholt vor Fehlern, die wie Erfolg aussehen — ein falsches Codec-Paar für die Generation, ein 32-Bit-Default gegen einen 16-Bit-ADC, ein deaktivierter Verstärker, ein an nichts gebundenes Gerät, das sauber validiert. Dieser Skill besitzt die Geräte-Hälfte und weigert sich, die Home-Assistant-Hälfte implizit zu lassen.

## Scope

Ein Gerät pro Aufruf: der Audio-Pfad, `voice_assistant:`, die Wake-Word-Platzierung, die Mute-Steuerung und die Offline-Zustände. Dazu eine geordnete Home-Assistant-seitige Checkliste, die der Operator ausführt — dieser Skill konfiguriert Home Assistant nie selbst.

## Ziele

- Die Board-Generation zur festgestellten Tatsache machen, bevor ein Pin oder Codec geschrieben wird
- Einen Audio-Pfad ausgeben, der für diese Generation korrekt ist statt für die Familie
- Die Wake-Word-Platzierung als Entscheidung gegen Sprachabdeckung, Offline-Verhalten, Host-Last und dauerhaftes Streaming halten
- Mute als verpflichtende Privacy-Kontrolle behandeln, nicht als Komfort
- Die Home-Assistant-seitige Arbeit ausdrücklich übergeben, inklusive der Engine-Wahl, die dem Gerät ein Kernfeature nehmen kann

## Nicht-Ziele

- Bildschirm-Inhalte, die die Pipeline treibt (Eigentum von `ha-esphome-display-author`)
- Home-Assistant-getriebene Werte ohne Sprachbezug (Eigentum von `ha-esphome-binding-add`)
- Eigene Sätze, Intent-Skripte und Automationen (Eigentum von `ha-automation-solution`)
- Installation und Betrieb der Sprach-Engines sowie das Anlegen von Pipelines in Home Assistant — der Host des Operators
- Compile, Flash und Inbetriebnahme am Gerät

## Anforderungen

- **MUSS** `spec/ha/esp32-s3-box/en.md` §Audio binding / §Voice-assistant binding und `spec/ha/assist-pipeline/en.md` lesen, bevor geschrieben wird
- **MUSS** die Board-Generation feststellen und dokumentieren, bevor ein Pin oder Codec ausgegeben wird, und ein mehrdeutiges Gerät empirisch statt nach Aussehen auflösen
- **MUSS** das Codec-Paar ausgeben, das die Generation tatsächlich trägt, als externe Wandler deklariert, und die dokumentierte Asymmetrie von Aufnahme- und Wiedergabe-Samplerate wahren
- **MUSS** `bits_per_sample` am Mikrofon explizit nennen und `adc_type: external` setzen
- **MUSS** den Endstufen-Verstärker als Schalter exponieren, der standardmäßig eingeschaltet ist
- **MUSS** `voice_assistant:` an ein Mikrofon und einen Antwortpfad binden, da das Schema beides nicht erzwingt und ein ungebundenes Gerät sauber validiert und nichts tut
- **SOLLTE** On-Device-Wake-Word bevorzugen und, wo die Platzierung zur Laufzeit wählbar ist, die Start-Action entsprechend umschalten statt sie zur Compile-Zeit festzulegen
- **MUSS** eine auffindbare Mute-Steuerung ausgeben, die an die Mikrofon-Mute-Actions gebunden ist
- **MUSS** die Fälle „kein WLAN“ und „kein Home Assistant“ ausdrücklich behandeln und den AP-Fallback-Wiederherstellungspfad intakt lassen
- **DARF NICHT** die Text-to-Speech-Stufe der Pipeline durch einen manuellen Sprachaufruf für dieselbe Antwort duplizieren
- **MUSS** Verstärkung einmal in der Kette anwenden und festhalten, wo
- **MUSS** die Home-Assistant-seitige Checkliste melden: eine Pipeline je Sprache, explizite Zuordnung je Satellit, Engine-Wahl gegen dokumentierte Host-Kapazität und Feature-Unterstützung, die `assist_satellite`-Anbindung mit migrierten veralteten Voice-Binary-Sensoren, minimale Freigabe als Sicherheitsgrenze und die Debug-Reihenfolge beginnend beim Satz-Parser samt zeitlich befristeter Debug-Aufzeichnung
- **MUSS** Geräte-Keys gegen die offizielle ESPHome-Doku und Home-Assistant-seitige Fakten gegen die offizielle Home-Assistant-Doku gemäß `spec/ha/upstream-docs-verification` verifizieren
- **DARF NICHT** deployen, flashen oder eine Verifikation am Gerät behaupten, die nicht stattgefunden hat

## Akzeptanzkriterien

- [ ] Der Bericht nennt die Generation und wie sie festgestellt wurde
- [ ] Ausgegebenes Codec-Paar, LRCLK-Pin und Mikrofon-Bittiefe passen zu dieser Generation
- [ ] Eine Mute-Steuerung existiert und die Disconnect-Zustände sind behandelt
- [ ] Der Bericht enthält die geordnete Home-Assistant-Checkliste inklusive der Engine-Konsequenz für Timer-Funktionen
- [ ] Die Inbetriebnahme am Gerät (Display, Mikrofon, Lautsprecher) ist als noch offen gemeldet

## Offene Fragen

- Die offenen Fragen der Grounding-Spec zu Engine-Dimensionierung und Agent-Fallback werden geerbt: Dieser Skill meldet die dokumentierten Kalibrierpunkte und verlangt, dass der Operator am realen Host misst, statt einen Portfolio-Default festzuschreiben.
