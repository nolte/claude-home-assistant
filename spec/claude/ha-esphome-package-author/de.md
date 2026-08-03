# Skill: `ha-esphome-package-author`

Status: draft

## Kontext

`spec/ha/esphome-project-structure` macht `packages:` zum einzigen Wiederverwendungs-Mechanismus einer ESPHome-Fleet und verwendet den Großteil seiner Anforderungen darauf, wie dieses eine Feature gut benutzt wird — Concern-Schnitte, Substitutions-Interfaces mit Defaults, `id:`-Abdeckung, `!extend` / `!remove` statt Forks, Remote-Pinning. Das sind Per-Package-Entscheidungen, die über die Lebenszeit eines Repositories wiederholt anfallen, nicht einmalig beim Scaffolding. Dieser Skill besitzt sie: Hier wird ein duplizierter Block zum Package, hier bekommt ein Package einen Parameter, und hier wird ein abweichendes Gerät gelöst, ohne dass eine Beinahe-Dublette entsteht.

## Scope

Ein Package pro Aufruf plus die Konsumenten, die die Änderung erreicht. Fünf Operationen: `cut`, `parameterise`, `deviate`, `promote`, `remote`. Endet beim geschriebenen Package, den aktualisierten Konsumenten und einem flottenweiten Validierungsbericht.

## Ziele

- Die Regel „zwei Vorkommen ergeben einen Parameter“ operationalisieren statt sie nur zu postulieren
- Jedes Package-Interface explizit halten: welche Variablen es liest, welche Defaults tragen, welche Komponenten überschreibbar sind
- Abweichung ohne Fork lösen und erkennen, wann eine Abweichung die Promotion verdient hat
- Die Merge-Konsequenzen einer Package-Änderung sichtbar machen, bevor die Änderung geschrieben wird
- Sicherstellen, dass eine Package-Änderung gegen **jeden** Konsumenten validiert wird, nicht nur gegen das auslösende Gerät

## Nicht-Ziele

- Der Repository-Baum und das initiale Package-Set (Eigentum von `ha-esphome-fleet-scaffold`)
- Geräteeigene Blöcke (Eigentum von `ha-esphome-config-augment`)
- Home-Assistant-getriebene Bindings innerhalb eines Packages (Eigentum von `ha-esphome-binding-add`)
- Ein Konformitätsurteil über die Package-Architektur (Eigentum des read-only `ha-esphome-fleet-reviewer`)
- Compile, Flash und Rollout

## Anforderungen

- **MUSS** `spec/ha/esphome-project-structure/en.md` §Package architecture, §Parameterisation, §Deviating without forking und §Remote packages sowie das Package und **jeden** Konsumenten lesen, bevor geschrieben wird
- **MUSS** vor einem `cut` die Duplikation belegen: Ein einzelnes Vorkommen ist kein Package
- **MUSS** einen Concern pro Package halten und **DARF NICHT** ein Package anlegen, das sich von einem bestehenden in einem einzigen Key unterscheidet
- **MUSS** eine erste Abweichung über `!extend` / `!remove` auf der Config-ID der Komponente lösen — nie auf einem Package-Key, dem die Dokumentation jede Bedeutung abspricht — und **MUSS** das Override in eine defaultete Variable überführen, sobald ein zweites Gerät es braucht
- **MUSS** für jede Variable, die ein Package liest und die nicht alle Konsumenten setzen, einen `defaults:`-Eintrag deklarieren, und **MUSS** eine ohne Default hinzugefügte Variable als Breaking Change für bestehende Konsumenten melden
- **MUSS** jeder überschreibbar werdenden Komponente ein explizites `id:` geben und benennen, dass diese Ergänzung jeden Konsumenten erreicht
- **MUSS** die Merge-Konsequenzen — Dictionaries Key für Key, Komponenten-Listen nach ID, andere Listen per Konkatenation, alle übrigen Werte durch den späteren ersetzt — für die anstehende Änderung nennen, bevor geschrieben wird
- **MUSS** Credentials als `!env_var` belassen, **DARF NICHT** einen `!secret`-Lookup in ein Package legen, das remote ist oder werden könnte, und **MUSS** jede neue Variable im selben Lauf dokumentieren
- **MUSS** ein Remote-Package auf ein Tag oder einen Commit pinnen oder es nach `common/` vendoren; ein wandernder Branch verlangt ein dokumentiertes, bewusstes `refresh`
- **MUSS** **jeden** Konsumenten mit `esphome config` validieren, wo die Toolchain verfügbar ist, und es sonst als offenen Schritt des Aufrufers melden
- **MUSS** Package-, Substitutions-, `!extend`-, `!remove`- und `vars:`-Semantik gegen die offizielle ESPHome-Doku gemäß `spec/ha/upstream-docs-verification` verifizieren
- **DARF NICHT** mehr als ein Package pro Lauf ändern

## Akzeptanzkriterien

- [ ] Ein `cut`-Lauf erzeugt ein Concern-scoped Package und schreibt jeden Konsumenten um, ohne einen duplizierten Block zurückzulassen
- [ ] Ein `parameterise`- oder `promote`-Lauf lässt jeden bestehenden Konsumenten unverändert bauen, weil die neue Variable einen aus diesen Konsumenten abgeleiteten Default trägt
- [ ] Ein `deviate`-Lauf ändert nur das konsumierende Device-File; das Package bleibt unangetastet
- [ ] Der Bericht nennt die Wirkung je Konsument und das Validierungsergebnis je Konsument, nicht nur für das auslösende Gerät

## Offene Fragen

_Derzeit keine._
