# ESPHome: Home-Assistant-gesteuerte Geräteinhalte

Status: draft

## Kontext

Die ESPHome-Specs dieses Portfolios beschreiben eine Richtung gut: Ein Gerät veröffentlicht Entities, und Home Assistant konsumiert sie. Die Gegenrichtung — **Home Assistant entscheidet, was das Gerät zeigt oder tut** — kommt nirgends vor. Genau diese Lücke lässt ein Display-Gerät halb konfiguriert zurück: [`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md) verlangt, Live-Werte vor dem Rendern in `text_sensor: {platform: template}` oder `globals:` bereitzustellen, sagt aber nie, woher diese Werte kommen.

ESPHome bietet dafür vier unterschiedliche Mechanismen, und sie sind nicht austauschbar:

1. **Zustands-Abo** — das Gerät importiert den Zustand einer Home-Assistant-Entity über die native API (`platform: homeassistant` an `sensor` und `text_sensor`). Home Assistant ändert eine Entity; das Gerät folgt.
2. **Aufrufbare Aktionen** — das Gerät deklariert unter `api:` Aktionen, die in Home Assistant als `esphome.{node_name}_{action_name}` erscheinen und typisierte Argumente annehmen. Home Assistant ruft; das Gerät handelt einmal.
3. **Schreibbare Entities** — das Gerät exponiert eine `template`-**Text**-Entity mit `set_action`, die Home Assistants Frontend setzen kann. Home Assistant schreibt einen Wert; das Gerät speichert und reagiert.
4. **Rückkanal** — das Gerät feuert Events oder ruft Aktionen zurück nach Home Assistant (`homeassistant.event`, `homeassistant.action`, `api.respond`).

Die Wahl zwischen ihnen ist die Substanz dieser Spec: Ein fortlaufend gespiegelter Wert ist ein Abo, ein einmaliger Befehl eine Aktion, ein vom Menschen setzbarer Wert eine schreibbare Entity. Die falsche Wahl erzeugt entweder ein Gerät, das pollt, was man ihm hätte sagen können, oder eine Automation, die in ein Gerät ohne Empfänger feuert.

Diese Spec ist geräteunabhängig und gilt für jeden ESPHome-Node an Home Assistant. Das Rendern der resultierenden Werte gehört [`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md); die Gestalt der Gerätekonfiguration [`ha/esphome-config-patterns`](../esphome-config-patterns/de.md); die Wiederverwendung auf Repository-Ebene [`ha/esphome-project-structure`](../esphome-project-structure/de.md).

### Quellen-Tiers

- `[doc]` — offizielle Dokumentation, zitiert von der jeweils in der Anforderung genannten Seite: ESPHome unter <https://esphome.io> für geräteseitige Schlüssel, Home Assistant unter <https://www.home-assistant.io> für die Einstellungen der Integration selbst.
- `[policy]` — eine nolte-Portfolio-Regel, kein Upstream-Fakt.
- `[src]` — Verhalten, das real, aber undokumentiert ist, belegt aus dem ESPHome-Quellbaum ([`esphome/esphome`](https://github.com/esphome/esphome)). Schwächer als `[doc]`: Es kann sich ohne Dokumentationsänderung ändern.
- **Nicht ausgesagt** — wo die Dokumentation schweigt, sagt diese Spec das, statt zu schlussfolgern.

Verifiziert 2026-08; erneut verifiziert am 2026-08-02, als die beiden ursprünglich festgehaltenen Dokumentationslücken aus der Quelle geschlossen statt offengelassen wurden. Jeder YAML-Schlüssel dieser Spec wurde auf seiner Komponenten-Seite gelesen; nichts hier ist aus dem Gedächtnis wiedergegeben.

## Ziele

- Die dokumentierte Lücke zwischen „Home Assistant hat die Daten" und „das Gerät zeigt sie" schließen
- Die Wahl zwischen Abo, Aktion, schreibbarer Entity und Rückkanal zu einer expliziten Entscheidung mit genannten Kriterien machen
- Die exakte Konfigurationsfläche jedes Mechanismus fixieren, zitiert von der Komponenten-Dokumentation
- Home-Assistant-gesteuerte Werte an die Redraw-Disziplin binden, die die Display-Spec bereits vorschreibt, sodass ein eingehender Wert den einzigen Redraw-Einstiegspunkt nicht umgeht
- Trennen, was die Dokumentation garantiert, von dem, was sie lediglich nicht widerlegt — besonders beim Aktualisierungsmechanismus
- Dem Fehlerfall eine Regel geben: Was tut das Gerät, während Home Assistant nicht erreichbar ist

## Nicht-Ziele

- Rendering — Koordinaten, Fonts, Layout-Zonen und Page-Mechanik gehören [`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md)
- Die Home-Assistant-Seite des Automations-Authorings (Trigger, Bedingungen, Skripte) — siehe den `ha-automation/`-Korpus
- Die geräteseitige Interaktion der Assist-Pipeline (`announce`, `start_conversation`), die [`ha/assist-pipeline`](../assist-pipeline/de.md) gehört
- MQTT als alternativer Transport — diese Spec setzt die native API voraus
- Bluetooth-Proxy und andere Durchleit-Rollen, die ein Gerät zusätzlich ausfüllen kann

## Anforderungen

### Wahl des Mechanismus

- Die Wahl **MUSS [MUST]** je Wert getroffen werden, nicht je Gerät, nach dieser Regel `[policy]`:
  - ein Wert, den das Gerät **fortlaufend spiegeln** muss (eine Temperatur, ein Zustandsname, ein Anwesenheits-Flag) → **Zustands-Abo**
  - eine **einmalige Anweisung** mit Argumenten („zeige diese Nachricht", „führe diese Sequenz aus") → **aufrufbare Aktion**
  - ein Wert, den ein **Mensch setzen** soll, aus dem Home-Assistant-UI → **schreibbare Entity** am Gerät
  - etwas, das Home Assistant erfahren muss → **Rückkanal**
- Ein Abo **DARF NICHT [MUST NOT]** durch eine periodisch aufgerufene Aktion nachgebildet werden, und eine Aktion nicht durch einen schnell wechselnden abonnierten Wert — beides funktioniert kurz und scheitert unter Last oder bei Trennung `[policy]`
- Ein Abo **SOLLTE [SHOULD]** bevorzugt werden, wenn Home Assistant den Wert ohnehin als Entity führt: Es braucht keine Automation, und das Gerät bleibt nach einem Neustart auf einer der beiden Seiten korrekt, ohne dass jemand etwas nachtriggert `[policy]`

### Zustands-Abo bei Home Assistant

- Ein numerischer Wert **MUSS [MUST]** mit `sensor: {platform: homeassistant, entity_id: <entity>}` importiert werden; `entity_id` ist erforderlich, und `attribute` wählt optional ein Zustands-Attribut statt des Zustands selbst `[doc]`
- Ein textueller Wert **MUSS [MUST]** mit `text_sensor: {platform: homeassistant, entity_id: <entity>}` importiert werden, das dieselben Schlüssel `entity_id` und optional `attribute` annimmt — die `sensor`-Plattform verarbeitet ausschließlich numerische Werte `[doc]`
- Die weiteren Import-Plattformen der Komponente **KÖNNEN [MAY]** genutzt werden; die Dokumentation deckt sie ungleichmäßig ab: `binary_sensor` für einen booleschen Zustand sowie `number` / `switch` für Werte, die das Gerät liest und zurückschreibt. Das lesende Trio (`sensor`, `text_sensor`, `binary_sensor`) teilt sich `HOME_ASSISTANT_IMPORT_SCHEMA` und unterstützt daher `attribute:`; `number` und `switch` nutzen `HOME_ASSISTANT_IMPORT_CONTROL_SCHEMA`, das **kein** `attribute` kennt — sie binden also nur an den Zustand einer Entity `[src]`
- Es **MUSS [MUST]** bekannt sein, dass die importierten Werte der `sensor`-Plattform **standardmäßig `internal`** sind, dokumentiert als „to avoid exporting them back to Home Assistant"; `internal: false` ist nur zu setzen, wenn ein Rückweg wirklich gewollt ist `[doc]`
- Derselbe Default **MUSS [MUST]** auf **jede** Home-Assistant-Import-Plattform angewendet werden, `text_sensor` eingeschlossen. Die Dokumentation nennt ihn nur für `sensor`, aber alle erweitern ein gemeinsames Schema, `HOME_ASSISTANT_IMPORT_SCHEMA`, das `cv.Optional(CONF_INTERNAL, default=True)` deklariert — der Default ist strukturell identisch, weil es buchstäblich dieselbe Codezeile ist. `internal:` explizit zu setzen bleibt der Lesbarkeit halber sinnvoll, aber nicht mehr zur Absicherung gegen einen unbekannten Default `[src]` `[doc]`
- Es **MUSS [MUST]** verstanden werden, dass diese Abos **Push-basiert** sind, auch wenn keine Komponenten-Seite das sagt. Das Gerät registriert jedes Abo einmalig, indem es eine `SubscribeHomeAssistantStateResponse` über die native API-Verbindung sendet — mit einem `once`-Flag, das einen einmaligen Lesevorgang von einem stehenden Abo unterscheidet; Home Assistant pusht daraufhin `HomeAssistantStateResponse`-Nachrichten, die `APIConnection::on_home_assistant_state_response` an die registrierten Callbacks verteilt. Einen geräteseitigen Polling-Loop gibt es nicht. Die praktische Folge: Die Aktualisierungslatenz ist die von Home Assistant, und ein Wert trifft erst *nach* dem Verbinden des API-Clients ein — weshalb die Boot-Zustands-Anforderung weiter unten nicht optional ist `[src]`
- Jeder abonnierte Wert **SOLLTE [SHOULD]** eine `id:` bekommen und in Lambdas über diese ID konsumiert werden, damit das Abo die einzige Quelle ist und kein Lambda gedanklich nach Home Assistant greift `[policy]`
- An einen abonnierten Sensor **SOLLTE [SHOULD]** `on_value` gehängt werden, wenn eine Änderung sichtbar werden muss, und dieser Trigger **SOLLTE [SHOULD]** das einzige Redraw-Script des Displays aufrufen statt selbst zu zeichnen `[policy]`

### Aktionen, die Home Assistant aufrufen kann

- Eine aufrufbare Aktion **MUSS [MUST]** unter `api:` als Eintrag in `actions:` mit `action:`-Name und `then:`-Block deklariert werden `[doc]`:

  ```yaml
  api:
    actions:
      - action: start_laundry
        then:
          - switch.turn_on: relay
  ```

- Typisierte `variables:` **MÜSSEN [MUST]** deklariert werden, wenn der Aufrufer Argumente übergibt, und in Lambdas namentlich gelesen werden `[doc]`:

  ```yaml
  api:
    actions:
      - action: start_effect
        variables:
          my_brightness: int
          my_effect: string
        then:
          - light.turn_on:
              id: my_light
              brightness: !lambda 'return my_brightness;'
              effect: !lambda 'return my_effect;'
  ```

- Die Aktion **MUSS [MUST]** aus Home Assistant als **`esphome.{node_name}_{action_name}`** adressiert werden — das dokumentierte Beispiel löst `start_laundry` auf Node `livingroom` zu `esphome.livingroom_start_laundry` auf `[doc]`
- Es **MUSS [MUST]** einkalkuliert werden, dass der Node-Name Teil dieses Bezeichners ist: Eine Geräte-Umbenennung ändert den Aktionsnamen und bricht jede aufrufende Automation — ein weiterer Grund, warum die Naming-Regeln in [`ha/esphome-project-structure`](../esphome-project-structure/de.md) `name` als stabil behandeln `[doc]` `[policy]`
- Dem Aufrufer **KÖNNEN [MAY]** mit `api.respond` Daten zurückgegeben werden, entweder als Status (`success: true` / `success: false` mit `error_message:`) oder als strukturierte Daten, in einem Lambda über `root[…]` gebaut `[doc]`
- Eine Aktion **KANN [MAY]** als reine Abfrage mit `supports_response: only` deklariert werden, was die Dokumentation mit Geräte-Fakten wie `App.get_name()` und `ESPHOME_VERSION` zeigt `[doc]`
- Argumente **SOLLTEN [SHOULD]** innerhalb der Aktion validiert und ein fehlerhafter Aufruf mit `api.respond: {success: false, error_message: …}` beantwortet werden, statt auf Unsinn zu handeln — das Beispiel der Dokumentation tut genau das für eine negative Zahl `[doc]` `[policy]`

### Schreibbare Entities am Gerät

- Home Assistant **KANN [MAY]** einen Wert schreiben, indem das Gerät eine `text: {platform: template}`-Entity mit `set_action` exponiert, dokumentiert als „the action that should be performed when the remote (like Home Assistant's frontend) requests to set the text value", wobei der neue Wert Lambdas als `x` zur Verfügung steht `[doc]`
- Die Regeln dieses Abschnitts **DÜRFEN NICHT [MUST NOT]** ungeprüft auf die anderen Template-Plattformen (`number`, `select`, `switch`, …) übertragen werden: Für diese Spec wurde ausschließlich `text/template` gelesen, und die dokumentierten Ausschlüsse gelten allein dafür `[policy]`
- Zwischen `optimistic: true` und `set_action` **MUSS [MUST]** bewusst gewählt werden: Der optimistische Modus bedeutet „any command sent to the template text will immediately update the reported state", und die Dokumentation stellt fest, dass er **nicht mit `lambda`** verwendbar ist `[doc]`
- Die dokumentierten wechselseitigen Ausschlüsse eines Template-Text **MÜSSEN [MUST]** beachtet werden: `optimistic`, `initial_value` und `restore_value` sind jeweils **nicht mit `lambda`** verwendbar `[doc]`
- `restore_value: true` **SOLLTE [SHOULD]** gesetzt werden, wo ein von Home Assistant gesetzter Wert einen Geräteneustart überleben muss, unter Inkaufnahme dessen, dass es „saves and loads the state to RTC/Flash" `[doc]` `[policy]`
- Eine schreibbare Entity **SOLLTE [SHOULD]** nur als Mechanismus für Werte gelten, die ein **Mensch** setzt; ein von einer Automation berechneter Wert gehört in ein Abo oder ein Aktions-Argument `[policy]`

### Rückkanal

- Ein Event **KANN [MAY]** mit `homeassistant.event` in Home Assistants Event-Bus gefeuert werden, unter Benennung des Events und Übergabe von `data:`, `data_template:` und lambda-berechneten `variables:` `[doc]`:

  ```yaml
  on_...:
    - homeassistant.event:
        event: esphome.button_pressed
        data:
          message: Button was pressed
  ```

- Eine Home-Assistant-Aktion **KANN [MAY]** vom Gerät mit `homeassistant.action` aufgerufen werden, mit `data:`, `data_template:` und `variables:`, deren Werte aus Lambdas stammen `[doc]`
- Das Ergebnis eines solchen Aufrufs **KANN [MAY]** mit `capture_response: true` plus `response_template:` erfasst und in `on_success:` / `on_error:` behandelt werden — das dokumentierte Beispiel liest eine Vorhersage-Temperatur in ein Lambda zurück `[doc]`
- Ein Event **SOLLTE [SHOULD]** einer Aktion vorgezogen werden, wenn Home Assistant entscheiden soll, was passiert: Ein Event trägt den Sachverhalt, eine Aktion setzt die Reaktion voraus `[policy]`
- Ruft ein Gerät Home-Assistant-Aktionen auf, **MUSS [MUST]** die entsprechende Berechtigung aktiviert werden — das Setup der ESPHome-Integration bietet dafür ein ausdrückliches Opt-in, dort als vertrauensbedürftig beschrieben; es ist eine Vertrauensentscheidung, keine Formalie `[doc]` `[policy]`

### Zeit von Home Assistant

- Die Uhr des Geräts **KANN [MAY]** mit `time: {platform: homeassistant, id: <id>}` von Home Assistant bezogen werden, was über die native API-Verbindung synchronisiert `[doc]`
- Der Node **MUSS [MUST]** dafür in Home Assistant registriert sein — die Dokumentation hält fest, dass „this component still requires you to register the node under Home Assistant", selbst wenn das Gerät nichts exportiert `[doc]`
- Die Zeitzone **SOLLTE [SHOULD]** bewusst entschieden werden: Ist sie nicht explizit gesetzt, wird sie vom Build-Host abgeleitet und dann zur Laufzeit von Home Assistant aktualisiert, während ein explizites Setzen dieses Laufzeit-Update verhindert `[doc]`

### Redraw und Verfügbarkeit

- Jede Home-Assistant-getriebene Änderung, die sichtbar werden muss, **MUSS [MUST]** über den einzigen Redraw-Einstiegspunkt des Displays laufen, gemäß [`ha/esp32-s3-box-display`](../esp32-s3-box-display/de.md) — ein `on_value`, das direkt zeichnet, umgeht die Disziplin, die Bildschirm- und Anwendungszustand ausgerichtet hält `[policy]`
- Es **MUSS [MUST]** definiert sein, was das Gerät zeigt, bevor Home Assistant je einen Wert geliefert hat: Ein abonnierter Sensor hat beim Booten keinen Zustand, und ein Lambda, das ihn ungeprüft formatiert, rendert Unsinn oder fällt aus `[policy]`
- Es **MUSS [MUST]** definiert sein, was das Gerät zeigt, wenn die API-Verbindung abreißt. `api:` bietet dafür die Trigger `on_client_connected` / `on_client_disconnected`, und die Referenzkonfiguration in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) nutzt sie, um auf einen eigenen Bildschirm zu wechseln `[doc]` `[policy]`
- Das Gerät **SOLLTE [SHOULD]** im getrennten Zustand für das nutzbar bleiben, was es allein kann, statt das letzte Home-Assistant-getriebene Bild einzufrieren, als wäre es aktuell `[policy]`
- Beim Entwurf des Offline-Verhaltens **MUSS [MUST]** `api.reboot_timeout` (Default 15 Minuten) einkalkuliert werden: Ein Gerät ohne verbundenen Client startet in diesem Takt neu, sofern der Timeout nicht geändert wird — „zeigt den Offline-Bildschirm dauerhaft" ist also nicht das Standardverhalten `[doc]` `[policy]`

### Verifikation

- Jeder Schlüssel dieser Spec **MUSS [MUST]** vor der Nutzung gegen die zugehörige Komponenten-Seite verifiziert werden, gemäß [`ha/upstream-docs-verification`](../upstream-docs-verification/de.md) — die Mechanismen hier verteilen sich über mindestens sechs getrennte Seiten (`api`, `sensor/homeassistant`, `text_sensor/homeassistant`, `time/homeassistant`, `text/template` und die Display-Komponenten) `[policy]`
- Eine Dokumentationslücke **DARF NICHT [MUST NOT]** durch Schlussfolgerung gefüllt werden — vorher **MUSS [MUST]** aber die Quelle probiert werden. Beide ursprünglich festgehaltenen Lücken (Aktualisierungsmechanismus der Abos, `internal`-Default außerhalb von `sensor`) waren aus `esphome/components/homeassistant/` und `esphome/components/api/` in Minuten beantwortbar; keine brauchte Hardware, keine brauchte eine Annahme. Wo die Quelle entscheidet, ist das Ergebnis `[src]` zu tiern und auszusagen; wo selbst die Quelle mehrdeutig ist, ist die Lücke festzuhalten und eine in beiden Fällen korrekte Konfiguration zu schreiben `[policy]`
- Ein unverifiziertes Verhalten **SOLLTE [SHOULD]** empirisch am Gerät bestätigt werden (abonnierten Wert loggen und die Home-Assistant-Entity ändern), bevor eine Konfiguration davon abhängt `[policy]`

## Akzeptanzkriterien

- [ ] Jeder Home-Assistant-getriebene Wert hat einen gewählten Mechanismus, und die Wahl folgt der Regel: fortlaufend → Abo, einmalig → Aktion, vom Menschen gesetzt → schreibbare Entity
- [ ] Abos nutzen `platform: homeassistant` mit explizitem `entity_id` und `attribute`, wo ein Attribut statt des Zustands gemeint ist
- [ ] `internal` ist an `text_sensor`-Abos explizit gesetzt, statt sich auf einen undokumentierten Default zu verlassen
- [ ] Kein Wert wird gerendert, bevor er angekommen ist: Abos sind Push-basiert, also existiert zwischen Boot und erstem API-Client kein Wert
- [ ] Aufrufbare Aktionen deklarieren typisierte `variables:`, validieren sie und beantworten fehlerhafte Eingaben über `api.respond`
- [ ] Jede aufrufende Automation nutzt die Form `esphome.{node_name}_{action_name}`, und die Folge einer Geräte-Umbenennung ist verstanden
- [ ] Schreibbare `text`-Template-Entities beachten die dokumentierten Ausschlüsse (`optimistic`, `initial_value`, `restore_value` gegenüber `lambda`), und keine Regel dieses Abschnitts wurde auf eine ungelesene Template-Plattform angewandt
- [ ] Geräte, die Home-Assistant-Aktionen aufrufen, haben die entsprechende Berechtigung bewusst aktiviert
- [ ] Jede eingehende Änderung, die sichtbar werden muss, läuft über den einzigen Redraw-Einstiegspunkt
- [ ] Das Gerät definiert einen Zustand für „Wert noch nicht empfangen" und für „API getrennt", und `reboot_timeout` ist im Offline-Entwurf berücksichtigt
- [ ] Jedes von der Dokumentation nicht ausgesagte Verhalten wurde an der Hardware bestätigt, bevor darauf gebaut wurde

## Offene Fragen

- **Kopplung des Action-Namens an den Node-Namen**: `esphome.{node_name}_{action_name}` bindet Automationen an den Gerätenamen. Sollte das Portfolio deshalb Abos und schreibbare Entities gegenüber aufrufbaren Actions bevorzugen — oder die Kopplung akzeptieren und Geräte-Umbenennungen als Breaking Change mit Migrationsschritt behandeln?
- **Round-Trip-Schleifen**: Ein abonnierter Wert mit `internal: false` wird nach Home Assistant zurückexportiert. Gibt es dafür in diesem Portfolio eine legitime Verwendung, oder sollte es rundheraus verboten werden, um Rückkopplungen auszuschließen?

Am 2026-08-02 aus dem ESPHome-Quellcode geklärt und hier festgehalten, damit die Antworten auffindbar bleiben statt bei der nächsten Lektüre erneut gestellt zu werden:

- **Aktualisierungsmechanismus der Abos** — **Push**. Das Gerät registriert jedes Abo einmalig per `SubscribeHomeAssistantStateResponse` (deren `once`-Flag einen einmaligen Lesevorgang von einem stehenden Abo trennt), und Home Assistant pusht `HomeAssistantStateResponse`-Nachrichten zurück, verteilt von `APIConnection::on_home_assistant_state_response`. Einen geräteseitigen Polling-Loop gibt es nicht. Weder Hardware noch ein Upstream-Doku-Issue waren nötig.
- **`internal`-Default außerhalb von `sensor`** — **derselbe, `true`**, und nicht zufällig: Jede Import-Plattform erweitert ein gemeinsames `HOME_ASSISTANT_IMPORT_SCHEMA` mit `cv.Optional(CONF_INTERNAL, default=True)`.
- **Binärer Zustand** — eine `binary_sensor`-Plattform existiert, ebenso `number` und `switch`. Die lesenden Plattformen teilen sich obiges Schema; `number` und `switch` nutzen `HOME_ASSISTANT_IMPORT_CONTROL_SCHEMA`, das `attribute:` weglässt.
