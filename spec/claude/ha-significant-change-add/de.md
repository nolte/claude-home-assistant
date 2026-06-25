# Skill: `ha-significant-change-add`

Status: draft

## Kontext

`ha/significant-change` definiert die Significant-Change-Platform: HA exportiert Zustände nicht nur, es meldet sie auch an Konsumenten (HomeKit, Voice-Assistenten, Logbuch, externe Bridges). Eine Integration nimmt teil, indem sie ein `significant_change.py`-Plattform-Modul mit der Top-Level-Funktion `async_check_significant_change` bereitstellt. HA ruft diese Funktion automatisch auf, wenn ein Konsument die Signifikanz einer Änderung prüft — übergeben werden ein zuvor als signifikant betrachteter Zustand und der neue Zustand (nicht die letzten beiden bekannten Zustände). Die Funktion entscheidet mit der Drei-Wert-Semantik (`True` signifikant, `False` insignifikant, `None` keine Aussage), ob die Änderung gemeldet werden soll. Bislang gibt es keinen Skill, der das ergänzt. Significant-Change ist klar von `always_update` abzugrenzen: `always_update` triggert den Coordinator-Listener (Re-Render einer Entität), Significant-Change filtert das Reporting an externe Konsumenten — zwei verschiedene Filter-Ebenen.

Dieser Skill ergänzt das `significant_change.py`-Modul in einer **bestehenden** Integration, sobald diese kontinuierliche Messwerte exportiert: das Plattform-Modul, die `@callback async_check_significant_change`-Funktion mit der vorgegebenen Signatur, die per-Device-Class-Schwellenwert-Logik und die Drei-Wert-Rückgabe — spec-konform zu `ha/significant-change`. Vor der Generierung prüft er, ob die Integration überhaupt kontinuierliche Werte exportiert.

## Scope

Ergänzung des Significant-Change-Supports pro Lauf in einer bestehenden `custom_components/<domain>/`-Integration: das `significant_change.py`-Plattform-Modul, die Top-Level-Funktion `async_check_significant_change` mit der HA-Signatur (`hass`, `old_state`, `old_attrs`, `new_state`, `new_attrs`, `**kwargs`), die `@callback`-Dekoration, die per-Domain-/per-Device-Class-Schwellenwert-Logik (optional über `check_absolute_change` / `check_valid_float`) und die Drei-Wert-Rückgabe (`True`/`False`/`None`). Der Skill liest `ha/significant-change` und validiert.

## Ziele

- Aus den exportierten Entity-Typen (Device-Classes) die relevanten Schwellenwerte ableiten und das Modul spec-konform ergänzen
- Die von HA vorgegebene Signatur und die `@callback`-Dekoration erzwingen — inklusive `**kwargs: Any`, damit zukünftige HA-Erweiterungen nicht brechen
- Per-Device-Class-Schwellenwert-Logik vorschreiben, damit Entity-Typen differenziert behandelt werden (ein Temperatur-Schwellenwert gilt nicht für Helligkeit oder Akku)
- Die Drei-Wert-Semantik erzwingen: `True` signifikant, `False` insignifikant, `None` keine Aussage (HA-Default)
- Den User vor unnötigen Modulen bewahren: nur Integrationen mit kontinuierlichen Werten brauchen das Modul, und die Grenze zu `always_update` klar ziehen

## Nicht-Ziele

- Der native Wert der Entität selbst (wie der Zustand zustande kommt) — Entity-Plattform / `ha/entity-architecture`
- `always_update`-Logik des Coordinators (Trigger des Coordinator-Listeners) — `ha/coordinator-patterns`
- Konsumenten-seitige Filter-Implementierung (wie HomeKit/Voice die Rückgabe auswertet) — lebt außerhalb der Integration
- Significant-Change für rein diskrete Entitäten ohne kontinuierlichen Wertebereich — dort reicht HAs Default
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add significant change", „add a significant_change checker", „throttle insignificant updates"
  - „stop reporting micro-changes to HomeKit / voice"
  - „füge Significant-Change-Logik hinzu", „filtere unbedeutende Updates"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die exportierten Entity-Typen / Device-Classes mit kontinuierlichen Werten
- **KANN [MAY]** erfassen: die per-Device-Class-Schwellenwerte (z. B. Temperatur >= X Grad) und ob HA-Helper (`check_absolute_change`/`check_valid_float`) genutzt werden sollen

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** den Bedarfs-Check fahren: exportiert die Integration kontinuierliche Messwerte (Sensoren mit Mess-Skalen, Climate)? Für rein diskrete Entitäten **MUSS NICHT [MUST NOT]** der Skill das Modul ergänzen und **SOLLTE [SHOULD]** abraten. Der Skill **MUSS [MUST]** die Grenze zu `always_update` (Coordinator-Listener vs. Konsumenten-Report) benennen
- **MUSS [MUST]** die `ha/significant-change`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes `significant_change.py` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/significant-change`)

- **MUSS [MUST]** das `significant_change.py`-Plattform-Modul im `custom_components/<domain>/`-Ordner erzeugen
- **MUSS [MUST]** `async_check_significant_change` als Top-Level-Funktion mit der vorgegebenen Signatur exportieren: `(hass: HomeAssistant, old_state: str, old_attrs: dict, new_state: str, new_attrs: dict, **kwargs: Any) -> bool | None`
- **MUSS [MUST]** die Funktion mit `@callback` dekorieren — sie läuft synchron im Event-Loop und darf nicht blockieren — und den `**kwargs: Any`-Parameter führen
- **MUSS [MUST]** bei der Entscheidung `old_attrs`/`new_attrs` berücksichtigen, nicht nur den nackten Zustandswert
- **MUSS [MUST]** Device-Classes verwenden, um zwischen Entity-Typen zu unterscheiden; **SOLLTE [SHOULD]** pro relevanter Device-Class einen absoluten Schwellenwert definieren, unterhalb dessen die Änderung als insignifikant gilt
- **KANN [MAY]** HA-Helper wie `check_absolute_change` und `check_valid_float` nutzen, um Float-Werte zu validieren und absolute Differenzen gegen einen Schwellenwert zu prüfen
- **MUSS [MUST]** ausschließlich `True` (signifikant, melden), `False` (insignifikant, nicht melden) oder `None` (keine Aussage, HA-Default) zurückgeben
- **MUSS NICHT [MUST NOT]** `unknown`-/`unavailable`-Übergänge selbst behandeln — diese Fälle behandelt HA automatisch
- **MUSS NICHT [MUST NOT]** annehmen, dass die Funktion die letzten beiden bekannten Zustände erhält — übergeben werden ein zuvor als signifikant betrachteter Zustand und der neue Zustand
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `significant_change.py` existiert; `async_check_significant_change` ist Top-Level mit der vorgegebenen Signatur und `**kwargs: Any`; die Funktion ist `@callback`-dekoriert; die Entscheidung nutzt `old_attrs`/`new_attrs` und differenziert über Device-Classes; pro relevanter Device-Class ist ein Schwellenwert definiert; die Rückgabe ist auf `True`/`False`/`None` beschränkt; es gibt keine eigene `unknown`/`unavailable`-Behandlung
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/significant-change` liefern, plus die geänderten Datei-Pfade und den Hinweis auf die Grenze zu `always_update`

### Verbote

- **MUSS NICHT [MUST NOT]** das Modul für rein diskrete Entitäten ohne kontinuierlichen Wertebereich ergänzen
- **MUSS NICHT [MUST NOT]** konsumenten-spezifische Schwellenwerte oder Filter-Auswertung implementieren — die Funktion liefert eine einzige Signifikanz-Entscheidung
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill fährt den Bedarfs-Check (kontinuierliche Werte?) inkl. Abgrenzung zu `always_update`
- [ ] `custom_components/<domain>/significant_change.py` existiert
- [ ] `async_check_significant_change` ist Top-Level mit der vorgegebenen Signatur (`hass`, `old_state`, `old_attrs`, `new_state`, `new_attrs`, `**kwargs`)
- [ ] Die Funktion ist `@callback`-dekoriert und führt den `**kwargs: Any`-Parameter
- [ ] Die Entscheidung berücksichtigt `old_attrs`/`new_attrs` und differenziert über Device-Classes mit einem absoluten Schwellenwert pro relevanter Device-Class
- [ ] Die Funktion gibt ausschließlich `True`, `False` oder `None` zurück; keine eigene `unknown`/`unavailable`-Behandlung
- [ ] Bericht nennt Datei-Pfade und die Grenze zu `always_update`

## Offene Fragen

- **Schwellenwert-Quelle**: Sollen die Device-Class-Schwellenwerte (Temperatur, Helligkeit, Akku) portfolioweit als Konstanten standardisiert oder pro Integration kalibriert werden? `ha/significant-change` formuliert es als SOLLTE pro Device-Class; der Skill fragt im Zweifel nach.
- **`check_absolute_change`-Verfügbarkeit**: Die Helper stammen aus dem Core-Significant-Change-Modul. Bis zu welcher HA-Mindest-Version sind sie stabil importierbar, und braucht es einen Fallback? Offen in `ha/significant-change`; der Skill folgt der dort genannten KANN-Regel.
- **Diskret-vs-kontinuierlich-Schwelle**: Ab wann gilt eine Entität als „kontinuierlich genug", um das Modul zu verlangen? Aktuell fährt der Skill den Bedarfs-Check als Dialog und rät bei rein diskreten Entitäten ab.
