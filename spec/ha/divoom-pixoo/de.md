# HA-Gerät: Divoom Pixoo 64 (gickowtf-Integration)

Status: draft

## Kontext

Der **Divoom Pixoo 64** ist ein 64×64-Pixel-RGB-Matrix-Display mit WLAN-Anbindung. In Home Assistant wird es über die HACS-Community-Integration [`gickowtf/pixoo-homeassistant`](https://github.com/gickowtf/pixoo-homeassistant) (Domain `divoom_pixoo`) eingebunden. Diese Spec beschreibt **wie das Gerät angeschlossen wird** und **wie sich Informationen darauf darstellen lassen** — als Referenz für Config-Autoren, die Pages, Automationen und Skripte rund um das Pixoo bauen.

Der entscheidende Architektur-Punkt: Die Integration ist `iot_class: local_polling` und steuert das Gerät **rein lokal** über die Divoom-LAN-REST-API (`HTTP POST http://{device_ip}/post` mit JSON-`Command`-Bodies). Nach der einmaligen Geräte-Discovery ist **keine Cloud** für den Betrieb nötig. Informationsdarstellung erfolgt über eine **Page-Liste**, die im Konfigurations-Intervall rotiert, plus vier **Services** für Push-artige Ad-hoc-Anzeige, Buzzer, Neustart und Re-Render.

Diese Spec ist eine **Nutzungs-/Referenz-Spec** für ein konkretes Gerät plus Drittanbieter-Integration. Sie grenzt sich von den HA-Core-Authoring-Specs unter `spec/ha/` ab (die beschreiben, wie man *eigene* Integrationen/Karten baut); hier geht es um die korrekte *Verwendung* einer bestehenden Integration. Primärquelle ist der Integrations-Code und die README bei `gickowtf/pixoo-homeassistant` (`main`, v1.23.0).

Realer Bezugspunkt: Im Bestands-Setup (`home-assistant-config`) existiert das Entity `sensor.divoom_pixoo_64_current_page`; genutzt werden u.a. der Service `divoom_pixoo.play_buzzer` (Blueprint `air_out/notify_window_too_long_open`) und komponentenbasierte Pages (`dix/example.yaml`, Countdown-Anzeigen).

## Ziele

- Den Anschluss des Geräts (lokale REST-API, Discovery, manuelle IP) festschreiben
- Den Setup- und Konfigurations-Pfad der `divoom_pixoo`-Integration (IP, `scan_interval`, `pages_data`) verankern
- Die beiden Geräte-Entitäten (`sensor` "Current Page", `light`) und ihre Rolle als Service-Ziel bzw. Helligkeits-/An-Aus-Steuerung dokumentieren
- Die Informationsdarstellung über Page-Rotation, Page-Typen und Komponenten (Text/Bild/Rechteck/Templatable) inkl. Fonts, Farben und Templating normieren
- Die vier Services (`show_message`, `play_buzzer`, `restart`, `update_page`) mit Parametern, Zielen und Risiken festhalten
- Die Config-only-Einschränkungen (`enabled`, `duration`, `variables`) gegen den Service-Kontext abgrenzen

## Nicht-Ziele

- Authoring einer eigenen Integration oder eines eigenen LAN-API-Clients — diese Spec nutzt die bestehende `divoom_pixoo`-Integration, sie baut sie nicht nach
- Vollständige Referenz der Divoom-LAN-REST-API über die von der Integration genutzten Commands hinaus
- Andere Divoom-Geräte (Pixoo 16/32, Times Gate, Ditoo) — die Integration unterstützt `size ∈ {16, 32, 64}`, diese Spec fokussiert auf das 64er-Gerät
- ClockFace-/Visualizer-ID-Kataloge — diese sind geräte-/app-abhängig (siehe `READMES/CLOCKS.md` der Integration und die `CurClockId`-Debug-Methode)
- Bilder-/GIF-Erzeugung und -Hosting außerhalb von HA (Resize auf 16/32/64 px, externe Hosts)

## Anforderungen

### Anschluss & Netzwerk

- **MUSS [MUST]** das Gerät per WLAN im selben L2/L3-Netz wie der Home-Assistant-Host erreichbar machen; die Integration spricht es lokal über `HTTP POST http://{device_ip}/post` mit JSON-`Command`-Bodies an (Divoom-LAN-REST-API)
- **MUSS [MUST]** dem Gerät eine **stabile IP** geben (DHCP-Reservierung oder statisch) — die Config persistiert die `ip_address`; ein IP-Wechsel bricht die Verbindung, bis der Eintrag neu konfiguriert wird
- **SOLLTE [SHOULD]** akzeptieren, dass die **Discovery** beim Hinzufügen über die Divoom-Cloud `https://app.divoom-gz.com/Device/ReturnSameLANDevice` läuft (liefert `DeviceList` mit `DevicePrivateIP`/`DeviceName`); der **laufende Betrieb** danach ist rein lokal und braucht keine Cloud
- **KANN [MAY]** die Discovery überspringen und die IP manuell eingeben ("Manual IP"), wenn die Cloud-Discovery nichts findet oder vermieden werden soll
- **SOLLTE [SHOULD]** mit einem Request-**Timeout von 9 s** pro Command rechnen; ein nicht erreichbares Gerät wird als nicht verfügbar markiert (siehe Verfügbarkeit) und nicht hart fehlschlagen
- **MUSS NICHT [MUST NOT]** annehmen, dass mehrere Config-Einträge dieselbe IP nutzen können — die Integration lehnt eine bereits konfigurierte IP mit `already_configured` ab

### Integration & Setup

- **MUSS [MUST]** die Integration `divoom_pixoo` ("Divoom Pixoo 64") über HACS installieren (HACS-Default-Repo) und HA neu starten, bevor der Config-Flow verfügbar ist
- **MUSS [MUST]** den Eintrag über *Einstellungen → Geräte & Dienste → Integration hinzufügen → Divoom Pixoo 64* anlegen und ein entdecktes Gerät wählen oder "Manual IP" nutzen
- **MUSS [MUST]** im Config-/Options-Flow setzen: `ip_address` (Pflicht), `scan_interval` (Sekunden, 1…9999, Default 15 — wie lange eine Page sichtbar bleibt) und optional `pages_data` (YAML-Liste der Standard-Pages)
- **SOLLTE [SHOULD]** `pages_data` nachträglich über *Gerät → Konfigurieren* (Options-Flow) pflegen; Änderungen am Eintrag laden die Integration neu
- **KANN [MAY]** sich auf die automatische Migration alter Einträge verlassen (`CURRENT_ENTRY_VERSION = 2`, v1→v2 wird beim Setup erkannt und konvertiert) — neue Konfigurationen sollten aber direkt im v2-Format (`page_type:`-Listen) geschrieben werden

### Entitäten

- **MUSS [MUST]** wissen, dass die Integration **pro Gerät zwei Entitäten** anlegt: ein `sensor` "Current Page" und ein `light` "Light"; beide tragen `DeviceInfo` mit `manufacturer: Divoom`, `model: Pixoo`
- **MUSS [MUST]** den **`sensor`** ("Current Page") als **Ziel aller Services** verwenden — sein State ist der aktuelle Page-Index + 1, das Attribut `TotalPages` die Anzahl der Pages, die `unique_id` lautet `current_page_<entry_id>`
- **MUSS [MUST]** das **`light`** ("Light") für **Display an/aus und Helligkeit** verwenden: `ColorMode.BRIGHTNESS`, An/Aus schaltet den Screen (`Channel/OnOffScreen`), Helligkeit 0…255 wird auf 0…100 % gemappt (`Channel/SetBrightness`)
- **SOLLTE [SHOULD]** die **Verfügbarkeit** über das `light`-Polling verstehen: schlägt das Lesen von State/Helligkeit (`Channel/GetAllConf`) fehl, wird das Gerät auf `available = False` gesetzt; dieser gemeinsame Flag pausiert auch die Page-Rotation des `sensor`, bis das Gerät wieder antwortet
- **MUSS NICHT [MUST NOT]** Service-Calls gegen das `light`-Entity richten — `show_message`, `play_buzzer`, `restart` und `update_page` zielen ausschließlich auf das `sensor`-Entity (`domain: sensor`, `integration: divoom_pixoo`)

### Informationsdarstellung — Pages & Rotation

- **MUSS [MUST]** Standard-Anzeigen als **Liste von Pages** unter `pages_data` definieren; jede Page beginnt mit `- page_type: <typ>` und die Integration **rotiert** durch die Liste
- **SOLLTE [SHOULD]** die Anzeigedauer pro Page über `duration` (Ganzzahl/Float Sekunden oder Template) steuern; ohne `duration` gilt das globale `scan_interval`
- **KANN [MAY]** eine Page über `enabled` (Bool oder Template) dynamisch ein-/ausblenden; als „wahr" gelten die gerenderten Werte `'true'`, `'yes'`, `'on'`, `'1'` — eine deaktivierte Page wird in der Rotation übersprungen
- **MUSS NICHT [MUST NOT]** sich darauf verlassen, dass `enabled`, `duration` und `variables` im **Service-Kontext** wirken — diese Felder gelten **nur in der `pages_data`-Config**, nicht in `show_message`

### Page-Typen

- **MUSS [MUST]** für eigene, daten-getriebene Anzeigen den Page-Typ **`components`** wählen (empfohlener Einstieg) — eine freie Leinwand aus Komponenten (siehe nächste Sektion)
- **KANN [MAY]** die vorgefertigten **Spezial-Pages** nutzen: `PV` (Photovoltaik: `power`, `storage`, `discharge`, `powerhousetotal`, `vomNetz`, `time`), `progress_bar` (`header`, `progress`, `footer` plus Farb-/Offset-Optionen), `fuel` (Tankstellenpreise: `title`, `name1…3`, `price1…3`, `status` plus Farboptionen)
- **KANN [MAY]** Geräte-/App-native Inhalte einbinden: `channel` (`id` 0/1/2 = Custom-Channel 1/2/3 der Divoom-App; Bildwechsel-Rate wird in der App gesetzt), `clock` (`id` = ClockFace-ID; Katalog in `READMES/CLOCKS.md`, ID via Debug-Log-`CurClockId` ermittelbar), `visualizer` (`id` ab 0), `gif` (`gif_url`)
- **MUSS [MUST]** bei `gif` ein GIF mit **exakt** 16×16, 32×32 oder 64×64 px referenzieren (URL); abweichende Größen werden vom Gerät nicht korrekt dargestellt

### Komponenten (Page-Typ `components`)

- **MUSS [MUST]** jede Komponente mit `type` und einer `position: [x, y]` (Ursprung oben-links, Raster 0…63) angeben; mehrere Text-/Bild-/Rechteck-Komponenten teilen sich eine Page als Leinwand
- **MUSS [MUST]** bei `type: text` `position` und `content` setzen; `content` unterstützt Jinja-Templates und Zeilenumbrüche; **der Text wird vor dem Rendern in Großbuchstaben umgewandelt**
- **SOLLTE [SHOULD]** bei Text `font` (Default `pico_8`; gültig: `pico_8`, `gicko`, `five_pix`, `eleven_pix`, `clock`, `pix24`), `color` (`[R, G, B]` oder CSS4-Farbname, Default `white`) und `align` (`left`/`right`/`center`) bewusst wählen
- **MUSS [MUST]** bei `type: image` genau **eine** Quelle angeben: `image_path` (lokale Datei, z. B. `/config/img/x.png`), `image_url` (URL, auch Template) oder `image_data` (Base64); optional `width`/`height` (proportional, längste Seite) und `resample_mode` (`box` Default, sonst `nearest`/`pixel_art`, `bilinear`, `hamming`, `bicubic`, `lanczos`/`antialias`)
- **MUSS NICHT [MUST NOT]** bei `image_path` auf den integrationseigenen Ordner `/config/custom_components/divoom_pixoo/img/` zeigen — eigene Bilder unter einem stabilen Pfad wie `/config/img/` ablegen (der Integrations-Ordner wird bei Updates überschrieben)
- **KANN [MAY]** `type: rectangle` (`position`, `size: [w, h]`, optional `color`, `filled` als Bool/Template) für Balken/Flächen und `type: templatable` (ein Jinja-Template, das eine **Liste weiterer Komponenten** zurückgibt) für dynamisch erzeugte Pixel/Komponenten nutzen
- **KANN [MAY]** auf Komponenten-Ebene `variables:` (benannte Templates) definieren und in den Komponenten-Templates referenzieren — nur in der Config, nicht im Service; im Service stattdessen HA-`variables` aus Automation/Skript verwenden

### Templating

- **SOLLTE [SHOULD]** Entity-States/-Attribute über **Jinja-Templates** in nahezu alle Page-/Komponentenfelder bringen (`content`, `color`, `enabled`, `duration`, Bildpfade/-URLs, Spezial-Page-Felder) — so wird der HA-Zustand aufs Display gespiegelt
- **MUSS [MUST]** das **64×64-Koordinatensystem** mit Ursprung oben-links beim Positionieren beachten; Inhalte jenseits 0…63 werden abgeschnitten

### Services (Ziel: `sensor`-Entity der Integration)

- **MUSS [MUST]** für **Push-/Ad-hoc-Anzeige** den Service `divoom_pixoo.show_message` nutzen: `page_data` (eine **einzelne** Page als YAML, Pflicht) wird temporär angezeigt; optional `duration` (Sekunden, sonst `scan_interval`). `enabled`/`variables` wirken hier **nicht**
- **KANN [MAY]** `divoom_pixoo.play_buzzer` mit `buzz_cycle_time_millis` (Default 500), `idle_cycle_time_millis` (Default 500), `total_time` (Default 3000) auslösen — **Warnung:** kann das Gerät potenziell beschädigen, Nutzung auf eigene Gefahr
- **KANN [MAY]** `divoom_pixoo.restart` für einen Geräte-Neustart (mit Verzögerung) und `divoom_pixoo.update_page` zum erneuten Rendern/Senden der aktuellen Page nutzen — **Warnung:** häufiges Spammen von `update_page` kann das Gerät zum Absturz bringen
- **SOLLTE [SHOULD]** `show_message` als **temporäre Überlagerung** der Standard-Rotation verstehen: nach Ablauf der `duration` läuft die konfigurierte `pages_data`-Rotation weiter

## Akzeptanzkriterien

- [ ] Gerät ist über eine stabile lokale IP erreichbar; Integration wurde via HACS installiert und ein `divoom_pixoo`-Eintrag mit `ip_address` + `scan_interval` existiert
- [ ] Beide Entitäten (`sensor` "Current Page", `light` "Light") sind vorhanden; `light` schaltet Display an/aus und Helligkeit; bei nicht erreichbarem Gerät werden sie `unavailable`
- [ ] Eine `pages_data`-Liste mit mindestens einer `components`-Page rotiert im `scan_interval`; `duration` und `enabled` pro Page wirken in der Config
- [ ] Eine `components`-Page rendert Text (großgeschrieben), Bild (lokal/URL/Base64) und Rechteck korrekt im 64×64-Raster mit gewähltem Font/Farbe/Ausrichtung
- [ ] Mindestens eine Spezial-Page (`PV`, `progress_bar`, `fuel`) oder native Page (`channel`/`clock`/`gif`/`visualizer`) ist beispielhaft konfiguriert
- [ ] `show_message` zeigt eine Ad-hoc-Page temporär an und kehrt danach zur Rotation zurück; `play_buzzer`/`restart`/`update_page` zielen auf das `sensor`-Entity
- [ ] Jinja-Templates spiegeln einen HA-Entity-State sichtbar aufs Display (z. B. eine Sensor-Zahl in einer `text`-Komponente)
- [ ] Die Config-only-Natur von `enabled`/`duration`/`variables` ist berücksichtigt — im `show_message`-Pfad wird stattdessen mit fixen Werten bzw. HA-`variables` gearbeitet

## Offene Fragen

- ClockFace- und Visualizer-IDs sind geräte-/firmware-/app-abhängig und nicht stabil dokumentiert — soll ein projekt-lokaler ID-Katalog (per `CurClockId`-Debug-Methode ermittelt) gepflegt werden?
- Soll für die wiederkehrenden Pixoo-Pages (Countdown, Status) ein Blueprint-/Skript-Layer im `home-assistant-config`-Repo standardisiert werden, statt Pages pro Automation zu duplizieren?
- Versions-Drift: Die Spec ist gegen `gickowtf/pixoo-homeassistant` v1.23.0 verifiziert — bei künftigen Releases (neue Page-Typen, Fonts, Services) ist ein Re-Check nötig.
