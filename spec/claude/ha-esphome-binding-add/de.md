# Skill: `ha-esphome-binding-add`

Status: draft

## Kontext

`spec/ha/esphome-ha-driven-content` entstand, weil der Korpus nur eine Richtung beschrieb — ein Gerät publiziert, Home Assistant konsumiert — während die Gegenrichtung Display-Geräte halb konfiguriert zurückließ: Die Rendering-Spec verlangt, dass Live-Werte vor dem Zeichnen bereitgestellt werden, und sagte nie, woher sie kommen. Jene Spec benennt vier nicht austauschbare Mechanismen und macht die Wahl zwischen ihnen zum eigentlichen Inhalt der Arbeit. Dieser Skill operationalisiert genau das: Er entscheidet den Mechanismus nach der Regel der Spec und gibt dann die verifizierte Konfiguration dafür aus.

## Scope

Ein Binding pro Aufruf, in einem Device-File oder dem Package, dem der Concern gehört. Deckt State-Subscription, aufrufbare Action, beschreibbare Entity, Rückkanal und Zeitsynchronisation ab, samt der Boot- und Disconnect-Zustände, die jeder davon verlangt.

## Ziele

- Die Mechanismus-Wahl explizit und regelgetrieben machen statt zur Kopie des zuerst gesehenen Beispiels
- Nur Keys ausgeben, die gegen die zugehörige Komponenten-Seite verifiziert sind — über die mehr als sechs Seiten, die diese Achse umspannt
- Die beiden Randzustände schließen, die jeder Home-Assistant-getriebene Wert hat: vor dem ersten Wert und nach Verbindungsabbruch
- Eingehende Änderungen über den einzelnen Redraw-Einstiegspunkt des Displays führen, statt aus einem Trigger heraus zu zeichnen
- Den Home-Assistant-seitigen Bezeichner und jede nötige Berechtigung benennen, damit die andere Hälfte des Bindings nicht implizit bleibt

## Nicht-Ziele

- Rendering — Koordinaten, Pages, Fonts (Eigentum von `ha-esphome-display-author`)
- Die Geräte-Interaktion der Assist-Pipeline (Eigentum von `ha-esphome-voice-satellite-add`)
- Home-Assistant-seitige Automationen, Skripte und Templates (Eigentum von `ha-automation-solution`)
- MQTT als alternativer Transport — die Grounding-Spec setzt die native API voraus
- Compile, Flash und Rollout

## Anforderungen

- **MUSS** `spec/ha/esphome-ha-driven-content/en.md`, das Ziel-Device-File und seine Packages lesen, bevor ein Mechanismus gewählt wird
- **MUSS** je Wert nach der Regel der Spec wählen — dauerhaft gespiegelt → Subscription, einmalige Anweisung → aufrufbare Action, von einer Person gesetzt → beschreibbare Entity, Home Assistant muss etwas erfahren → Rückkanal — und Wahl samt Begründung im Bericht nennen
- **DARF NICHT** eine Subscription durch eine periodisch aufgerufene Action emulieren oder eine Action durch einen sich schnell ändernden subskribierten Wert
- **MUSS** Subscriptions mit explizitem `entity_id`, explizitem `internal` und einem `id:` ausgeben und **DARF NICHT** `attribute:` auf einer Import-Plattform verwenden, die diesen Key nicht kennt
- **MUSS** aufrufbare Actions mit typisierten `variables:`, Argumentprüfung und einer `api.respond`-Antwort für Fehlaufrufe ausgeben und **MUSS** den Home-Assistant-seitigen Bezeichner als `esphome.{node_name}_{action_name}` samt Umbenennungs-Konsequenz melden
- **MUSS** die dokumentierten Ausschlüsse einer beschreibbaren Template-Text-Entity (`optimistic`, `initial_value`, `restore_value` gegenüber `lambda`) einhalten und **DARF NICHT** sie auf eine ungelesene Template-Plattform übertragen
- **MUSS** die explizite Opt-in-Berechtigung der Integration als Vertrauensentscheidung benennen, wann immer das Gerät Home-Assistant-Actions aufruft
- **MUSS** den Boot-Zustand und den API-Disconnect-Zustand definieren und **MUSS** `api.reboot_timeout` im Offline-Design berücksichtigen
- **MUSS** jede sichtbar werdende Änderung über den einzelnen Redraw-Einstiegspunkt des Displays führen
- **MUSS** jeden Key gegen die zugehörige Komponenten-Seite gemäß `spec/ha/upstream-docs-verification` verifizieren und ein quellenbasiertes Verhalten entsprechend tiern, statt es als dokumentiert auszugeben
- **DARF NICHT** mehr als ein Binding pro Lauf ergänzen und **DARF NICHT** deployen

## Akzeptanzkriterien

- [ ] Der Bericht nennt den gewählten Mechanismus, die Regel, die dazu führte, und den Home-Assistant-seitigen Bezeichner
- [ ] Ein Subscription-Lauf gibt explizites `entity_id` und `internal` aus, und die Config definiert, was vor dem ersten Wert angezeigt wird
- [ ] Ein Action-Lauf gibt typisierte Variablen mit Prüfung und einen `api.respond`-Pfad für ungültige Eingaben aus
- [ ] Der Disconnect-Zustand ist definiert und `reboot_timeout` ist berücksichtigt
- [ ] Kein ausgegebener Trigger zeichnet direkt; sichtbare Änderungen rufen das Redraw-Skript

## Offene Fragen

- Die offene Frage der Grounding-Spec zur Kopplung des Action-Namens an den Node-Namen wird hier geerbt, nicht beantwortet: Bis sie geklärt ist, bevorzugt dieser Skill Subscriptions und beschreibbare Entities, wo die Anforderung beides zulässt, und meldet die Kopplung, wann immer er eine Action ausgibt.
