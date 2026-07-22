# Skill: `ha-config-entry-migrate`

Status: draft

## Kontext

Ein Config-Entry speichert seine Daten unter einer `version` / `minor_version`. Wenn eine Integration die Form dessen ändert, was sie persistiert — einen Key umbenennt, einen Wert von `entry.data` nach `entry.options` verschiebt, einen Pflicht-Default ergänzt, ein Feld splittet — muss jeder Entry, der bereits auf der Platte eines Users liegt, beim Laden durch HA vorwärts migriert werden, über `async_migrate_entry(hass, config_entry)` plus einen Bump von `ConfigFlow.VERSION` (breaking) oder `MINOR_VERSION` (backward-compatible). Kein bestehender Skill besitzt das: `ha-config-flow-augment` schließt destruktive Refactorings explizit aus, und der initiale Scaffold liefert nur `VERSION = 1` ohne Migration. Die häufigen Fehler sind der vergessene Version-Bump, das Verlieren unbezogener Keys, kein Guard nach Quell-Version (sodass ein Re-Run Daten korrumpiert) und kein Ablehnen eines neueren-als-aktuellen Entrys.

Dieser Skill schließt die Lücke: Er ergänzt oder erweitert `async_migrate_entry`, um gespeicherte Config-Entries über einen Schema-Schritt zu migrieren, mit korrektem Version-Bump und einem Migrations-Test — non-destruktiv gegenüber unbezogenen Keys. Er ist die Wartungs-Schwester von `ha-config-flow-augment`, fokussiert auf den Stored-Shape-Migrationspfad.

## Scope

Ergänzung oder Erweiterung genau eines Config-Entry-Migrationsschritts pro Lauf in einer bestehenden `custom_components/<domain>/`-Integration: der `VERSION`/`MINOR_VERSION`-Bump am `ConfigFlow`, die `async_migrate_entry(hass, config_entry) -> bool`-Funktion (version-guarded, lehnt einen neueren Entry mit `False` ab, schreibt die transformierten `entry.data`/`entry.options` über `hass.config_entries.async_update_entry`), und ein Migrations-Test. Der Skill liest die aktuelle Version und Stored-Shape, entscheidet breaking vs. backward-compatible und validiert offline.

## Ziele

- Den Config-Entry-Migrationspfad (`async_migrate_entry` + Version-Bump) besitzen, der zwischen `ha-config-flow-augment` (keine destruktiven Refactorings) und dem Scaffold sitzt
- Die korrekte Version bumpen — major `VERSION` bei breaking Shape-Change, `MINOR_VERSION` bei backward-compatible
- Keys transformieren (rename / move / default / split), ohne unbezogene Keys zu verlieren, zurückgeschrieben über `async_update_entry`
- Jeden Schritt nach Quell-Version guarden, sodass die Migration idempotent und geordnet ist, und einen neueren-als-aktuellen Entry mit `False` ablehnen
- Den Version-Bump, die Migrations-Funktion und einen Migrations-Test zusammen liefern

## Nicht-Ziele

- Greenfield-Scaffold — `ha-integration-scaffold`
- Setup-Zeit-Config-Flow-Patterns (Tenant / Reauth / Reconfigure / Zeroconf / OAuth) — `ha-config-flow-augment`
- Eine neue Post-Setup-Option ergänzen ohne Migration bestehender Entries — `ha-options-flow-augment`
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „migrate the config entry to the new schema", „I renamed a config key and need a migration", „bump the config entry version"
  - „migriere den Config-Entry auf das neue Schema", „füge eine async_migrate_entry hinzu"
- **MUSS NICHT [MUST NOT]** für Greenfield-Scaffold (`ha-integration-scaffold`), Setup-Zeit-Config-Flow-Patterns (`ha-config-flow-augment`) oder das Ergänzen einer neuen Option (`ha-options-flow-augment`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und `change` (die Schema-Änderung in Prosa — welche Keys rename / move / split / default)
- **KANN [MAY]** erfassen: `breaking` (sonst abgeleitet und bestätigt) — breaking (major `VERSION`) vs. backward-compatible (`MINOR_VERSION`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo mit sauberem Working-Tree ist und `config_flow.py` + `__init__.py` existieren; `domain`, die aktuelle `VERSION`/`MINOR_VERSION` und die Stored-`entry.data`/`entry.options`-Form lesen
- **MUSS [MUST]** `breaking` (ableiten + bestätigen) und die konkreten Key-Transforms vor der Generierung auflösen

### Generierungs-Regeln

- **MUSS [MUST]** `ConfigFlow.VERSION` bei einem breaking Shape-Change und `MINOR_VERSION` bei einem backward-compatible bumpen, und angeben, welches und warum
- **MUSS [MUST]** `async_migrate_entry(hass, config_entry) -> bool` ergänzen oder erweitern, das `False` zurückgibt, wenn `config_entry.version` neuer ist als der laufende Major (ein Downgrade, das der Code nicht handhaben kann)
- **MUSS [MUST]** Keys explizit transformieren (rename / move / default / split) und über `hass.config_entries.async_update_entry(entry, data=…, options=…, version=…, minor_version=…)` zurückschreiben; unbezogene Keys werden verbatim übernommen und **kein** Key wird still verworfen
- **MUSS [MUST]** jeden Schritt nach Quell-Version guarden (`if entry.version == 1: …`), sodass ein Re-Run idempotent ist und Multi-Step-Upgrades geordnet anwenden
- **MUSS [MUST]** einen Migrations-Test (`tests/test_init.py` oder `tests/test_migration.py`) ergänzen, der einen Alt-Versions-`MockConfigEntry` seedet, Setup ausführt und assertet, dass der Entry auf die neue `version`/`minor_version` mit den transformierten Keys migriert ist
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: die Version ist gebumpt; `async_migrate_entry` ist vorhanden, version-guarded, gibt bei einem neueren Entry `False` zurück, schreibt über `async_update_entry` und verwirft keinen Key; der Migrations-Test ist vorhanden
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an diese Akzeptanzkriterien plus die geänderten Datei-Pfade anknüpft

### Verbote

- **MUSS NICHT [MUST NOT]** über mehr als einen Version-Schritt pro Lauf migrieren ohne die Zwischen-Guards
- **MUSS NICHT [MUST NOT]** unbezogene Keys verwerfen oder einen neueren-als-aktuellen Entry korrumpieren
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] `ConfigFlow.VERSION` (breaking) oder `MINOR_VERSION` (backward-compatible) ist gebumpt, mit angegebener Begründung
- [ ] `async_migrate_entry` ist version-guarded, gibt bei einem neueren Entry `False` zurück und schreibt über `async_update_entry`
- [ ] Key-Transforms sind explizit; unbezogene Keys werden übernommen; kein Key wird still verworfen
- [ ] Ein Migrations-Test seedet einen Alt-Versions-Entry und assertet die migrierte `version`/`minor_version` und transformierte Keys
- [ ] Der Bericht benennt die geänderten Datei-Pfade

## Offene Fragen

- **Multi-Step-Ketten**: Ein Lauf migriert einen Version-Schritt. Wenn eine Integration mehrere Versionen überspringt, wird eine geguardete Kette in einem Lauf generiert oder ein Skill-Lauf pro Schritt?
- **`minor_version`-Support-Floor**: `MINOR_VERSION` existiert in neueren HA-Cores. Erkennt der Skill den HA-Versions-Floor, bevor er es nutzt, oder nimmt er an, dass es verfügbar ist?
- **Options-vs-Data-Moves**: Einen Key von `entry.data` nach `entry.options` zu verschieben ist eine häufige Migration. Gibt es einen kodifizierbaren Default, welche Keys wohin gehören?
