# HA-Integration: System-Health

Status: draft

## Kontext

Home Assistant zeigt für jede Integration eine **System-Health-Seite** an — der User erreicht die aggregierte Übersicht über **Settings** -> **System** -> **Repairs** und wählt im Drei-Punkte-Menü oben rechts **System information**. Die System-Health-Plattform erlaubt Integrationen, dort Informationen bereitzustellen, die dem User helfen, den Zustand der Integration zu verstehen — etwa die Erreichbarkeit eines Endpoints, der aktuell verbundene Server oder das verbleibende Request-Kontingent.

HA implementiert das über ein `system_health.py`-Modul mit einer `async_register(hass, register)`-Funktion, die einen Info-Callback registriert. Der Callback `async_health_info(hass)` liefert ein Dict zurück, dessen Werte beliebige Typen sein dürfen — inklusive Coroutines. Für Coroutine-Werte zeigt das Frontend einen Warte-Indikator und aktualisiert das Item automatisch, sobald die Coroutine ein Ergebnis liefert. Für Konnektivitäts-Items stellt die Plattform den Helfer `system_health.async_check_can_reach_url(hass, url)` bereit.

Diese Spec grenzt sich von `ha/diagnostics` ab: System-Health ist der **At-a-Glance-Status** (kurze Werte direkt im Frontend), Diagnostics der **vollständige, herunterladbare Dump** (strukturierte JSON-Datei für Issue-Reports). Beide sind Debugging-Oberflächen, aber mit unterschiedlichem Zweck. Architektur-Kontext liefert `ha/integration-architecture`.

## Ziele

- `system_health.py` als Standard-Modul für Integrationen mit Backend-Konnektivität oder Kontingent-Limits etablieren
- Den At-a-Glance-Status klar von `ha/diagnostics` abgrenzen — kurze Werte hier, vollständiger Dump dort
- Konnektivitäts-Items über den `async_check_can_reach_url`-Helfer standardisieren statt manueller HTTP-Probes
- Coroutine-Werte für teure Checks nutzen, damit das Frontend nicht blockiert

## Nicht-Ziele

- Vollständige Diagnose-Dumps — das ist `ha/diagnostics`, mit eigener Redaction-Pflicht
- Repairs-Issues (`async_create_issue`) — eigener HA-Mechanismus, eigene Folge-Spec
- Übersetzung der Info-Keys über `strings.json` im Detail — das ist Sache der Translation-Spec; hier nur als Verweis
- Externe Monitoring-Systeme (Prometheus, Healthchecks-Endpoints) — leben außerhalb von HA-System-Health

## Anforderungen

### Zweck

- **MUSS [MUST]** System-Health ausschließlich für **At-a-Glance-Status** nutzen — kurze Werte, die der User im Frontend direkt liest (Erreichbarkeit, verbundener Server, Kontingent)
- **MUSS NICHT [MUST NOT]** System-Health als Ersatz für `ha/diagnostics` verwenden — vollständige, strukturierte Dumps gehören in den Diagnostics-Download, nicht auf die System-Health-Seite
- **KANN [MAY]** für Integrationen ohne Backend-Konnektivität oder Kontingent-Semantik entfallen — nicht jede Integration hat sinnvolle System-Health-Items

### `system_health.py`-Platform

- **MUSS [MUST]** ein `system_health.py`-Modul im `custom_components/<domain>/`-Ordner enthalten, wenn die Integration System-Health-Items bereitstellt
- **MUSS [MUST]** die Plattform-API aus `homeassistant.components.system_health` importieren (`SystemHealthRegistration` für die Type-Annotation der Registration)
- **MUSS [MUST]** das `@callback`-Decorator auf der synchronen `async_register`-Funktion führen — die Registration ist synchron, nur die Info-Erhebung ist async

### `async_register` & Info-Callback

- **MUSS [MUST]** eine `async_register(hass, register) -> None`-Funktion exportieren, die HA beim Setup der Integration aufruft
- **MUSS [MUST]** in `async_register` über `register.async_register_info(async_health_info)` den Info-Callback registrieren
- **MUSS [MUST]** einen `async_health_info(hass) -> dict`-Callback bereitstellen, der das auf der System-Health-Seite angezeigte Info-Dict zurückliefert

```python
"""Provide info to system health."""

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(async_health_info)
```

### Info-Items (Werte & Konnektivität)

- **MUSS [MUST]** aus `async_health_info` ein Dict zurückliefern, dessen Werte beliebige Typen sein dürfen — inklusive Coroutines
- **SOLLTE [SHOULD]** teure Checks (z. B. URL-Erreichbarkeit) als **Coroutine** in das Dict setzen statt sie vorab `await`en — das Frontend zeigt dann einen Warte-Indikator und aktualisiert das Item automatisch, sobald das Ergebnis vorliegt
- **SOLLTE [SHOULD]** jeden Info-Key über die `system_health`-Sektion in `strings.json` übersetzen, damit das Frontend lesbare Beschreibungen statt roher Keys zeigt
- **KANN [MAY]** Werte wie verbleibendes Request-Kontingent, verbrauchte Requests oder den aktuell verbundenen Server als Info-Items aufnehmen

```python
async def async_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    quota_info = await config_entry.runtime_data.async_get_quota_info()

    return {
        "consumed_requests": quota_info.consumed_requests,
        "remaining_requests": quota_info.requests_remaining,
        # checking the url can take a while, so set the coroutine in the info dict
        "can_reach_server": system_health.async_check_can_reach_url(hass, ENDPOINT),
    }
```

### `async_check_can_reach_url`

- **SOLLTE [SHOULD]** für Erreichbarkeits-Items den Helfer `system_health.async_check_can_reach_url(hass, url)` verwenden statt eine eigene HTTP-Probe zu schreiben
- **MUSS [MUST]** den Helfer-Aufruf als Coroutine-Wert (ohne vorheriges `await`) in das Info-Dict legen — der Check kann dauern und soll das Frontend nicht blockieren
- **KANN [MAY]** mehrere Erreichbarkeits-Items für unterschiedliche Endpoints (z. B. API und Auth-Server) führen, jeweils über einen eigenen Helfer-Aufruf

### Wann implementieren

- **SOLLTE [SHOULD]** `system_health.py` implementieren, sobald die Integration ein Cloud- oder Netzwerk-Backend mit erreichbarkeits- oder kontingentrelevantem Zustand hat
- **KANN [MAY]** entfallen, wenn die Integration rein lokal arbeitet und keinen sinnvollen At-a-Glance-Status hat
- **MUSS NICHT [MUST NOT]** System-Health-Items mit Diagnose-Daten überladen, die in den `ha/diagnostics`-Dump gehören — die Seite ist für kurze Status-Werte, nicht für vollständige Datenstände

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/system_health.py` existiert (sofern die Integration System-Health-Items bereitstellt)
- [ ] `async_register(hass, register) -> None` ist mit `@callback` dekoriert und exportiert
- [ ] `async_register` registriert den Info-Callback über `register.async_register_info(...)`
- [ ] `async_health_info(hass) -> dict` ist als Info-Callback definiert und liefert das angezeigte Dict
- [ ] Teure Erreichbarkeits-Checks sind als Coroutine (ohne vorheriges `await`) im Info-Dict gesetzt
- [ ] Erreichbarkeits-Items nutzen `system_health.async_check_can_reach_url(hass, url)` statt manueller HTTP-Probes
- [ ] Info-Keys sind über die `system_health`-Sektion in `strings.json` übersetzt

## Offene Fragen

- **Implementierungs-Schwelle**: Ab wann verlangt die Spec `system_health.py`? Aktuell als SOLLTE für Backend-gestützte Integrationen; ein kalibrierter Trigger (z. B. „jede Integration mit Cloud-IoT-Class") fehlt.
- **Mehrere ConfigEntries**: Das Doc-Beispiel greift `async_entries(DOMAIN)[0]`. Wie soll der Callback bei mehreren Entries derselben Integration aggregieren? Aktuell nicht standardisiert.
- **Abgrenzung zu Repairs**: Erreichbarkeits-Status auf der System-Health-Seite vs. ein Repairs-Issue bei dauerhaftem Ausfall — wann eskaliert ein Konnektivitäts-Item zum Repairs-Issue? Eigene Folge-Spec.
- **Translation-Pflicht**: Ist die `strings.json`-Übersetzung der Info-Keys ein MUSS oder SOLLTE? Aktuell als SOLLTE formuliert.
