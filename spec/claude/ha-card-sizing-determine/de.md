# Skill: `ha-card-sizing-determine`

Status: draft

## Kontext

Das Sizing einer Custom-Lovelace-Card oder eines Panels ist zuerst ein Bestimmungs-, dann ein Implementierungsproblem: die korrekte `getGridOptions()`- (Sections-View) und `getCardSize()`-Deklaration (Masonry/Panel/Stacks) hängt davon ab, ob der Inhalt deterministisch oder content-abhängig ist, von den `rows: "auto"`-CSS-Vorbedingungen und vom Edit-Mode-Overlay-Verhalten — alles geregelt in `spec/ha/card-panel-sizing/de.md`. Fehler zeigen sich als abgeschnittene Cards oder überlappende Edit-Mode-Chrome. Dieser Skill isoliert den Bestimmungs-Schritt, damit die Sizing-Entscheidung explizit und übergabefähig ist, statt in einem Scaffold vergraben.

## Scope

Eine bestehende Card oder ein Panel pro Aufruf. Der Skill klassifiziert, verifiziert Vorbedingungen und produziert die Size-Deklaration plus Hand-off: Inline-Patch der beiden Callbacks oder Dispatch an den zuständigen, aus dem Live-Inventar aufgelösten Implementierungs-Spezialisten.

## Ziele

- Deterministische Klassifikation: content-abhängig (`rows: "auto"` + `min_columns`) versus deterministisch (numerische `rows` + `min_rows`)
- Verifizierte `rows: "auto"`-CSS-Vorbedingungen, bevor diese Variante je empfohlen wird
- Edit-Mode-Overlay-Überlappung als Sizing-Defekt mit konkretem Fix behandelt, nicht als Kosmetik
- Explizite Analyse-versus-Apply-Grenze: Bestimmung hier, Patchen im Hand-off

## Nicht-Ziele

- Scaffolding von Cards/Panels (`ha-lovelace-card-scaffold`, `ha-panel-add`/`ha-panel-author`), Feature-Rows (`ha-card-features-add`), Frontend-Gesamtlösungen (`ha-lovelace-solution`), Live-Instanz-Arbeit

## Anforderungen

- **MUSS** vor der Klassifikation `spec/ha/card-panel-sizing/de.md` und die Ziel-Quelle lesen; nie aus dem Gedächtnis sizen
- **MUSS** die `rows: "auto"`-CSS-Vorbedingungen verifizieren und die Variante bei Fehlschlag unter Nennung der scheiternden Vorbedingung verweigern
- **MUSS** die Deklarationen beider Callbacks (Sections- und Masonry-Pfad) produzieren und die Klassifikations-Begründung nennen
- **MUSS** die Analyse-zu-Hand-off-Grenze halten: Option (a) Inline-Patch genau der beiden Callbacks, Option (b) Dispatch an den aus dem Live-Inventar aufgelösten Spezialisten
- **SOLLTE** erkannte Edit-Mode-Überlappung als Sizing-Defekt mit spec-verankertem Fix flaggen

## Akzeptanzkriterien

- [ ] Ein Lauf auf einer content-abhängigen Card liefert `rows: "auto"` + `min_columns` mit verifizierten Vorbedingungen oder eine explizite Verweigerung mit benannter Vorbedingung
- [ ] Ein Lauf auf einer deterministischen Card liefert numerische `rows` + `min_rows` konsistent zu `getCardSize()`
- [ ] Der Hand-off benennt entweder die Inline-Patch-Fläche oder einen auflösbaren Spezialisten
