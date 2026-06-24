# HA-Integration: Significant-Change

Status: draft

## Kontext

Home Assistant sammelt nicht nur Daten, es exportiert sie auch an diverse Konsumenten — HomeKit, Voice-Assistenten, Logbuch-Aggregatoren, externe Bridges. Nicht jeder dieser Dienste interessiert sich für jede Zustandsänderung. Ein Temperatursensor, der um 0,1 Grad Celsius wackelt, ein Akku, der 0,1 % Ladung verliert, ein Licht, das um 2 Helligkeitsstufen springt — solche Mikro-Änderungen erzeugen beim Konsumenten Rauschen ohne Mehrwert.

Damit Konsumenten unbedeutende Änderungen herausfiltern können, stellt HA die **Significant-Change-Platform** bereit: Die Integration legt ein `significant_change.py`-Plattform-Modul mit der Funktion `async_check_significant_change` an. Diese Funktion bekommt einen zuvor als signifikant betrachteten Zustand und den neuen Zustand übergeben — nicht etwa die letzten beiden bekannten Zustände — und entscheidet, ob die Differenz signifikant genug ist, um an die Konsumenten gemeldet zu werden. Die Quelle (`developers.home-assistant`, `docs/core/platform/significant_change.md`) beschreibt das Pattern; diese Spec überführt es in eine Verpflichtung für Integrationen mit kontinuierlichen Messwerten.

Diese Spec grenzt sich klar von `ha/coordinator-patterns` ab: `always_update` steuert, ob ein **Coordinator-Listener** (also eine Entität) bei einem Tick überhaupt neu rendert; Significant-Change steuert, ob ein bereits gerenderter Zustand an **externe Konsumenten** gemeldet wird. Das sind zwei unterschiedliche Filter-Ebenen.

## Ziele

- `significant_change.py` als Standard-Modul für Integrationen mit kontinuierlichen Messwerten (Sensoren, Climate) etablieren
- `async_check_significant_change` mit der von HA vorgegebenen Signatur und der Drei-Wert-Semantik (`True` / `False` / `None`) verpflichtend machen
- Device-Class-basierte Schwellenwert-Logik vorschreiben, damit Entity-Typen differenziert behandelt werden
- Die Grenze zu `always_update` (Coordinator-Listener-Trigger) klar ziehen, damit beide Filter-Ebenen nicht verwechselt werden

## Nicht-Ziele

- `always_update`-Logik des Coordinators — gehört in `ha/coordinator-patterns`; Significant-Change ist Reporting an Konsumenten, `always_update` ist das Triggern der Coordinator-Listener
- Konsumenten-seitige Filter-Implementierung (wie HomeKit oder Voice die Rückgabe auswerten) — lebt außerhalb der Integration
- Significant-Change für rein diskrete Entitäten (Binary-Sensor, Switch, Select) ohne kontinuierlichen Wertebereich — dort ist die Default-Behandlung ausreichend
- Schwellenwert-Kalibrierung pro Konsument — die Funktion liefert eine einzige Signifikanz-Entscheidung, keine konsumenten-spezifischen Schwellen

## Anforderungen

### Zweck & Konsumenten

- **MUSS [MUST]** Significant-Change-Support als Mechanismus verstehen, mit dem die Integration HA und nachgelagerten Konsumenten (HomeKit, Voice, Bridges) mitteilt, ob eine Zustandsänderung signifikant genug ist, um gemeldet zu werden
- **MUSS [MUST]** unbedeutende Änderungen herausfilterbar machen — die in der Quelle genannten Beispiele (Akku verliert 0,1 % Ladung, Temperatursensor ändert sich um 0,1 Celsius, Licht ändert sich um 2 Helligkeitsstufen) gelten als insignifikant
- **MUSS NICHT [MUST NOT]** annehmen, dass die Funktion die letzten beiden bekannten Zustände erhält — übergeben werden ein zuvor als signifikant betrachteter Zustand und der neue Zustand

### `significant_change.py`-Platform

- **MUSS [MUST]** den Support durch ein `significant_change.py`-Plattform-Modul im `custom_components/<domain>/`-Ordner bereitstellen, sobald die Integration kontinuierliche Messwerte exportiert
- **MUSS [MUST]** in diesem Modul die Funktion `async_check_significant_change` als Top-Level-Funktion exportieren — HA ruft sie automatisch auf, wenn ein Konsument die Signifikanz einer Änderung prüft
- **KANN [MAY]** das Modul über `python3 -m script.scaffold significant_change` scaffolden (Upstream-Core-Workflow); in einer Custom Integration wird die Datei manuell nach demselben Schema angelegt

### `async_check_significant_change`-Signatur

- **MUSS [MUST]** die von HA vorgegebene Signatur verwenden:

```python
from typing import Any, Optional
from homeassistant.core import HomeAssistant, callback

@callback
def async_check_significant_change(
    hass: HomeAssistant,
    old_state: str,
    old_attrs: dict,
    new_state: str,
    new_attrs: dict,
    **kwargs: Any,
) -> bool | None:
```

- **MUSS [MUST]** die Funktion mit `@callback` dekorieren — sie läuft synchron im Event-Loop und darf nicht blockieren
- **MUSS [MUST]** den `**kwargs: Any`-Parameter in der Signatur führen, damit zukünftige HA-Erweiterungen die Funktion nicht brechen

### Schwellenwerte & Device-Class-Logik

- **MUSS [MUST]** bei der Signifikanz-Entscheidung alle bekannten Attribute berücksichtigen (`old_attrs`, `new_attrs`), nicht nur den nackten Zustandswert
- **MUSS [MUST]** Device-Classes verwenden, um zwischen Entity-Typen zu unterscheiden — ein Temperatur-Schwellenwert gilt nicht für einen Helligkeits- oder Akku-Wert
- **SOLLTE [SHOULD]** pro Device-Class einen absoluten Schwellenwert definieren (z. B. Temperatur ändert sich um >= X Grad), unterhalb dessen die Änderung als insignifikant gilt
- **KANN [MAY]** vorhandene HA-Helper wie `check_absolute_change` und `check_valid_float` aus dem Significant-Change-Modul nutzen, um Float-Werte zu validieren und absolute Differenzen gegen einen Schwellenwert zu prüfen

### Rückgabe-Semantik (True/False/None)

- **MUSS [MUST]** `True` zurückgeben, wenn die Änderung signifikant ist und an Konsumenten gemeldet werden soll
- **MUSS [MUST]** `False` zurückgeben, wenn die Änderung als insignifikant gilt und nicht gemeldet werden soll
- **MUSS [MUST]** `None` zurückgeben, wenn die Funktion keine Aussage treffen kann — HA wendet dann sein Default-Verhalten an
- **MUSS NICHT [MUST NOT]** `unknown`- und `unavailable`-Übergänge selbst behandeln — diese Fälle behandelt HA automatisch

### Wann implementieren

- **SOLLTE [SHOULD]** Significant-Change implementieren, wenn die Integration Entitäten mit kontinuierlichen Werten exportiert (Sensoren mit Mess-Skalen, Climate-Entitäten mit Temperatur-/Feuchte-Werten)
- **MUSS NICHT [MUST NOT]** Significant-Change für rein diskrete Entitäten ohne kontinuierlichen Wertebereich implementieren — dort ist HAs Default-Behandlung ausreichend und ein zusätzlicher Filter erzeugt nur Aufwand
- **KANN [MAY]** auf das Modul verzichten, wenn die Integration ausschließlich Zustandswechsel mit diskreter, ohnehin seltener Änderung exportiert

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/significant_change.py` existiert, sobald die Integration kontinuierliche Messwerte exportiert
- [ ] `async_check_significant_change` ist als Top-Level-Funktion mit der vorgegebenen Signatur (`hass`, `old_state`, `old_attrs`, `new_state`, `new_attrs`, `**kwargs`) exportiert
- [ ] Die Funktion ist mit `@callback` dekoriert und enthält den `**kwargs: Any`-Parameter
- [ ] Die Signifikanz-Entscheidung berücksichtigt `old_attrs`/`new_attrs` und differenziert über Device-Classes
- [ ] Pro relevanter Device-Class ist ein absoluter Schwellenwert definiert (z. B. via `check_absolute_change`)
- [ ] Die Funktion gibt ausschließlich `True`, `False` oder `None` zurück — `None` für „weiß nicht"
- [ ] Es existiert keine eigene Behandlung von `unknown`/`unavailable` in der Funktion

## Offene Fragen

- **Schwellenwert-Quelle**: Sollen die Device-Class-Schwellenwerte (Temperatur, Helligkeit, Akku) als portfolioweite Konstanten standardisiert werden, oder pro Integration kalibriert? Aktuell als SOLLTE pro Device-Class formuliert.
- **`check_absolute_change`-Verfügbarkeit**: Die Helper `check_absolute_change`/`check_valid_float` stammen aus dem Core-Significant-Change-Modul. Bis zu welcher HA-Mindest-Version sind sie stabil importierbar, und braucht es einen Fallback, wenn die portfolioweite Mindest-Version sie nicht garantiert?
- **Abgrenzung zu `always_update`**: Beide Filter wirken auf Mikro-Änderungen, aber auf verschiedenen Ebenen (Coordinator-Listener vs. Konsumenten-Report). Reicht die textuelle Delimitation, oder braucht es ein gemeinsames Beispiel, das beide Filter im selben Datenfluss zeigt?
- **Diskret-vs-kontinuierlich-Schwelle**: Ab wann gilt eine Entität als „kontinuierlich genug", um das Modul zu verlangen? Aktuell als SOLLTE für Sensoren/Climate formuliert; ein kalibrierter Trigger fehlt.
