# HA-Integration: `icons.json`

Status: draft

## Kontext

Home Assistant erlaubt seit 2024.1, **Icons pro Translation-Key** über eine `icons.json` neben `strings.json` zu deklarieren — sowohl für Entitäten (Default-Icon und State-spezifische Icons) als auch für Services. Davor wurden Icons über `_attr_icon`-Properties oder dynamische `icon`-Methoden auf jeder Entity-Klasse gesetzt, was zu Drift zwischen ähnlichen Entitäten und schwer pflegbarem Logik-im-Code führte.

`nolte/kamerplanter-ha` nutzt `icons.json` durchgängig: Default-Icons pro `translation_key`, State-spezifische Icons für Enum-Sensoren (z. B. unterschiedliche Phase-Symbole), und Service-Icons. Material Design Icons (`mdi:...`) sind das Default-Icon-Set; HA unterstützt zusätzlich SVG-Pfad-Icons, aber das Skill-Output bleibt bei `mdi:`. Diese Spec überführt das Pattern in eine generische Verpflichtung.

Quality-Scale-Marker: **Bronze** (Icons über `icons.json` statt im Code sind eine Bronze-Konvention; ohne Icons rendert HA generische Default-Symbole, was technisch nicht falsch, aber UX-arm ist).

## Ziele

- `icons.json` als alleinigen Ort für Icon-Deklarationen festschreiben — keine `_attr_icon`-Hardcodes, keine `icon`-Properties auf Entity-Klassen
- Default-Icons pro `translation_key` und State-spezifische Icons für Enum-Sensoren als Standard-Pattern etablieren
- Service-Icons zentralisiert mitführen, sodass die HA-Service-UI konsistente Symbole rendert
- Material Design Icons (`mdi:...`) als Default-Icon-Set vorgeben

## Nicht-Ziele

- Custom-SVG-Icons (eigene Vektor-Pfade) — HA unterstützt sie technisch, aber das Skill-Output bleibt bei `mdi:`; eine Folge-Spec adressiert SVG-Icons, sobald die erste Integration sie braucht
- Branding-Icons (Logo der Integration) — leben im `brand/`-Ordner und folgen einer anderen Konvention; eigene Folge-Spec
- Lovelace-Card-Icons (Card-spezifisches Icon) — Card-Property, gehört zu `ha/lovelace-card-patterns`
- Translation der Icon-Auswahl pro Sprache — Icons sind sprach­unabhängig

## Anforderungen

### `icons.json`-Existenz

- **MUSS [MUST]** im `custom_components/<domain>/`-Ordner eine `icons.json` enthalten, sobald die Integration mindestens eine Entity oder einen Service definiert
- **SOLLTE [SHOULD]** alle Translation-Keys aus `strings.json` mit einem Default-Icon abdecken — fehlende Keys rendern HA-Defaults, die meistens nicht passen

### Schema

Die `icons.json` ist hierarchisch nach Plattform und Translation-Key strukturiert:

```text
{
  "entity": {
    "<platform>": {
      "<translation_key>": {
        "default": "mdi:<icon-name>",
        "state": {
          "<value>": "mdi:<icon-name>",
          ...
        }
      }
    }
  },
  "services": {
    "<service>": {
      "service": "mdi:<icon-name>"
    }
  }
}
```

- **MUSS [MUST]** Plattform-Namen unter `entity` als Top-Level-Schlüssel führen (`sensor`, `binary_sensor`, `button`, `calendar`, `todo`, `switch`, `number`, `select`, …)
- **MUSS [MUST]** unter jeder Plattform den `translation_key` der Entity als Schlüssel verwenden — derselbe Key wie in `strings.json`
- **MUSS [MUST]** unter `entity.<platform>.<translation_key>` mindestens `default` setzen
- **KANN [MAY]** unter `entity.<platform>.<translation_key>` zusätzlich einen `state:`-Block mit `<value> → mdi:<icon>`-Mappings führen — der State-spezifische Icon hat Vorrang vor `default`, wenn er den aktuellen State-Wert matched
- **MUSS [MUST]** Services unter dem Top-Level-Schlüssel `services` führen, mit `services.<service>.service` als Icon-Pfad
- **MUSS NICHT [MUST NOT]** Plattform-namen in PascalCase oder gemischter Schreibweise führen — HA-Konvention ist lowercase

### Icon-Set

- **SOLLTE [SHOULD]** Material Design Icons (`mdi:<name>`) als Default-Icon-Set verwenden — HA bündelt die `mdi:`-Bibliothek out-of-the-box
- **KANN [MAY]** alternative Icon-Sets verwenden, wenn HA sie unterstützt (z. B. `hass:<name>` für HA-eigene Icons); die Spec verlangt keine Vereinheitlichung über das `mdi:`-Default hinaus
- **MUSS NICHT [MUST NOT]** absolute URLs als Icon-Pfade verwenden — HA bundelt Icons; externe URLs brechen Offline-Setups

### Konsistenz mit `strings.json`

- **MUSS [MUST]** die `translation_key`-Werte in `icons.json` exakt mit den Keys in `strings.json` matchen — Drift (Icon-Eintrag ohne Translation oder umgekehrt) wird als Bug klassifiziert
- **SOLLTE [SHOULD]** beim Hinzufügen einer neuen Entity in `strings.json` und `icons.json` parallel pflegen — typischer Skill-Flow scaffolded beide gemeinsam
- **MUSS NICHT [MUST NOT]** Icons in `strings.json` einbetten — `strings.json` ist für Strings, nicht für Visuals

### Verbote

- **MUSS NICHT [MUST NOT]** `_attr_icon = "mdi:..."` als Hardcoded-Property auf Entity-Klassen setzen — Icons gehören in `icons.json`, nicht in den Code
- **MUSS NICHT [MUST NOT]** dynamische `icon`-Methoden auf Entity-Klassen schreiben — State-spezifische Icons gehören in den `state:`-Block der `icons.json`
- **MUSS NICHT [MUST NOT]** `EntityDescription.icon` als Default verwenden, wenn `icons.json` denselben Eintrag tragen kann — `icons.json` ist die kanonische Quelle; `EntityDescription.icon` bleibt als Fallback erlaubt, wenn die Entity keinen `translation_key` hat (selten)

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/icons.json` existiert
- [ ] Top-Level-Sektionen sind auf `entity` und `services` beschränkt
- [ ] Plattform-Namen unter `entity` sind lowercase und matchen HA-Plattform-Namen
- [ ] Jeder `translation_key` mit zugehöriger Entity hat mindestens `default` in `icons.json`
- [ ] Sensoren mit Enum-State haben einen `state:`-Block mit Icons pro Backend-Wert
- [ ] Services haben `services.<service>.service` als Icon-Eintrag
- [ ] Eine `grep`-Suche nach `_attr_icon = "mdi:` in den Plattform-Modulen liefert keine Treffer
- [ ] Eine `grep`-Suche nach `def icon` in den Plattform-Modulen liefert keine dynamischen `icon`-Property-Methoden
- [ ] Quality-Scale-Marker: **Bronze**

## Offene Fragen

- **State-Block-Vollständigkeits-Pflicht**: Soll der `state:`-Block alle möglichen Werte abdecken (Pflicht) oder reicht eine Auswahl der häufigsten (Soll)? `kamerplanter-ha` deckt die häufigsten ab, nicht alle.
- **`hass:`- vs. `mdi:`-Mix**: Soll die Spec `mdi:` exklusiv verlangen oder einen Mix mit HA-eigenen Icons (`hass:`) erlauben? Aktuell als KANN formuliert.
- **`EntityDescription.icon`-Verbot**: Aktuell als „nicht verwenden, wenn `icons.json` möglich ist" formuliert; ein vollständiges Verbot würde Konsistenz erzwingen. Gibt es legitime Use-Cases für `EntityDescription.icon`?
- **Custom-Icons (SVG-Pfade)**: Wann verlangt eine Folge-Spec Custom-SVG-Icons? Aktuell als Nicht-Ziel ausgeschlossen.
