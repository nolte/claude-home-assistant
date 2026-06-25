# HA Device: Divoom Pixoo 64 (gickowtf integration)

Status: draft

## Context

The **Divoom Pixoo 64** is a 64×64-pixel RGB matrix display with Wi-Fi connectivity. In Home Assistant it is integrated via the HACS community integration [`gickowtf/pixoo-homeassistant`](https://github.com/gickowtf/pixoo-homeassistant) (domain `divoom_pixoo`). This spec describes **how the device is connected** and **how information is displayed on it** — as a reference for config authors building pages, automations, and scripts around the Pixoo.

The key architectural point: the integration is `iot_class: local_polling` and drives the device **purely locally** through the Divoom LAN REST API (`HTTP POST http://{device_ip}/post` with JSON `Command` bodies). After a one-time device discovery, **no cloud** is required for operation. Information is displayed through a **page list** that rotates on the configured interval, plus four **services** for push-style ad-hoc display, the buzzer, restart, and re-render.

This is a **usage/reference spec** for a concrete device plus a third-party integration. It is distinct from the HA-core authoring specs under `spec/ha/` (which describe how to build *your own* integrations/cards); here the concern is the correct *use* of an existing integration. The primary source is the integration code and README at `gickowtf/pixoo-homeassistant` (`main`, v1.23.0).

Real-world anchor: the existing setup (`home-assistant-config`) has the entity `sensor.divoom_pixoo_64_current_page`; it uses, among others, the `divoom_pixoo.play_buzzer` service (blueprint `air_out/notify_window_too_long_open`) and component-based pages (`dix/example.yaml`, countdown displays).

## Goals

- Pin down the device connection (local REST API, discovery, manual IP)
- Anchor the setup and configuration path of the `divoom_pixoo` integration (IP, `scan_interval`, `pages_data`)
- Document the two device entities (`sensor` "Current Page", `light`) and their role as service target resp. brightness/on-off control
- Standardize information display via page rotation, page types, and components (text/image/rectangle/templatable) incl. fonts, colors, and templating
- Capture the four services (`show_message`, `play_buzzer`, `restart`, `update_page`) with parameters, targets, and risks
- Delimit the config-only constraints (`enabled`, `duration`, `variables`) against the service context

## Non-Goals

- Authoring a custom integration or a custom LAN-API client — this spec uses the existing `divoom_pixoo` integration, it does not rebuild it
- A complete reference of the Divoom LAN REST API beyond the commands the integration uses
- Other Divoom devices (Pixoo 16/32, Times Gate, Ditoo) — the integration supports `size ∈ {16, 32, 64}`, this spec focuses on the 64 device
- ClockFace/visualizer ID catalogs — these are device/app dependent (see the integration's `READMES/CLOCKS.md` and the `CurClockId` debug method)
- Image/GIF creation and hosting outside HA (resize to 16/32/64 px, external hosts)

## Requirements

### Connection & Network

- **MUST** make the device reachable over Wi-Fi on the same L2/L3 network as the Home Assistant host; the integration addresses it locally via `HTTP POST http://{device_ip}/post` with JSON `Command` bodies (Divoom LAN REST API)
- **MUST** give the device a **stable IP** (DHCP reservation or static) — the config persists the `ip_address`; an IP change breaks the connection until the entry is reconfigured
- **SHOULD** accept that **discovery** at add time runs through the Divoom cloud `https://app.divoom-gz.com/Device/ReturnSameLANDevice` (returns `DeviceList` with `DevicePrivateIP`/`DeviceName`); **ongoing operation** afterward is purely local and needs no cloud
- **MAY** skip discovery and enter the IP manually ("Manual IP") when cloud discovery finds nothing or is to be avoided
- **SHOULD** expect a request **timeout of 9 s** per command; an unreachable device is marked unavailable (see Availability) rather than hard-failing
- **MUST NOT** assume multiple config entries can share the same IP — the integration rejects an already-configured IP with `already_configured`

### Integration & Setup

- **MUST** install the `divoom_pixoo` integration ("Divoom Pixoo 64") via HACS (HACS default repo) and restart HA before the config flow is available
- **MUST** create the entry via *Settings → Devices & Services → Add Integration → Divoom Pixoo 64* and select a discovered device or use "Manual IP"
- **MUST** set, in the config/options flow: `ip_address` (required), `scan_interval` (seconds, 1…9999, default 15 — how long a page stays visible), and optionally `pages_data` (YAML list of the default pages)
- **SHOULD** maintain `pages_data` afterward via *Device → Configure* (options flow); changes to the entry reload the integration
- **MAY** rely on automatic migration of old entries (`CURRENT_ENTRY_VERSION = 2`, v1→v2 is detected and converted at setup) — but new configurations should be written directly in the v2 format (`page_type:` lists)

### Entities

- **MUST** know that the integration creates **two entities per device**: a `sensor` "Current Page" and a `light` "Light"; both carry `DeviceInfo` with `manufacturer: Divoom`, `model: Pixoo`
- **MUST** use the **`sensor`** ("Current Page") as the **target of all services** — its state is the current page index + 1, the attribute `TotalPages` is the page count, the `unique_id` is `current_page_<entry_id>`
- **MUST** use the **`light`** ("Light") for **display on/off and brightness**: `ColorMode.BRIGHTNESS`, on/off toggles the screen (`Channel/OnOffScreen`), brightness 0…255 maps to 0…100 % (`Channel/SetBrightness`)
- **SHOULD** understand **availability** via the `light` polling: if reading state/brightness (`Channel/GetAllConf`) fails, the device is set to `available = False`; this shared flag also pauses the `sensor`'s page rotation until the device responds again
- **MUST NOT** target service calls at the `light` entity — `show_message`, `play_buzzer`, `restart`, and `update_page` target the `sensor` entity exclusively (`domain: sensor`, `integration: divoom_pixoo`)

### Information Display — Pages & Rotation

- **MUST** define default displays as a **list of pages** under `pages_data`; each page begins with `- page_type: <type>` and the integration **rotates** through the list
- **SHOULD** control per-page display time via `duration` (integer/float seconds or template); without `duration` the global `scan_interval` applies
- **MAY** show/hide a page dynamically via `enabled` (bool or template); the rendered values `'true'`, `'yes'`, `'on'`, `'1'` count as "true" — a disabled page is skipped in the rotation
- **MUST NOT** rely on `enabled`, `duration`, and `variables` taking effect in the **service context** — these fields apply **only in the `pages_data` config**, not in `show_message`

### Page Types

- **MUST** choose the **`components`** page type for custom, data-driven displays (recommended starting point) — a free canvas of components (see next section)
- **MAY** use the prebuilt **special pages**: `PV` (photovoltaics: `power`, `storage`, `discharge`, `powerhousetotal`, `vomNetz`, `time`), `progress_bar` (`header`, `progress`, `footer` plus color/offset options), `fuel` (gas-station prices: `title`, `name1…3`, `price1…3`, `status` plus color options)
- **MAY** embed device/app-native content: `channel` (`id` 0/1/2 = custom channel 1/2/3 in the Divoom app; image cycle rate is set in the app), `clock` (`id` = ClockFace ID; catalog in `READMES/CLOCKS.md`, ID obtainable via the debug-log `CurClockId`), `visualizer` (`id` from 0), `gif` (`gif_url`)
- **MUST** for `gif` reference a GIF of **exactly** 16×16, 32×32, or 64×64 px (URL); other sizes are not rendered correctly by the device

### Components (page type `components`)

- **MUST** give each component a `type` and a `position: [x, y]` (origin top-left, grid 0…63); multiple text/image/rectangle components share a page as a canvas
- **MUST** for `type: text` set `position` and `content`; `content` supports Jinja templates and newlines; **the text is upper-cased before rendering**
- **SHOULD** for text deliberately choose `font` (default `pico_8`; valid: `pico_8`, `gicko`, `five_pix`, `eleven_pix`, `clock`, `pix24`), `color` (`[R, G, B]` or a CSS4 color name, default `white`), and `align` (`left`/`right`/`center`)
- **MUST** for `type: image` provide exactly **one** source: `image_path` (local file, e.g. `/config/img/x.png`), `image_url` (URL, also a template), or `image_data` (Base64); optionally `width`/`height` (proportional, longest side) and `resample_mode` (`box` default, else `nearest`/`pixel_art`, `bilinear`, `hamming`, `bicubic`, `lanczos`/`antialias`)
- **MUST NOT** point `image_path` at the integration's own folder `/config/custom_components/divoom_pixoo/img/` — store custom images under a stable path such as `/config/img/` (the integration folder is overwritten on updates)
- **MAY** use `type: rectangle` (`position`, `size: [w, h]`, optional `color`, `filled` as bool/template) for bars/areas and `type: templatable` (a Jinja template returning a **list of further components**) for dynamically generated pixels/components
- **MAY** define `variables:` (named templates) at the component level and reference them in component templates — config only, not in the service; in the service use HA `variables` from the automation/script instead

### Templating

- **SHOULD** bring entity states/attributes into nearly all page/component fields via **Jinja templates** (`content`, `color`, `enabled`, `duration`, image paths/URLs, special-page fields) — mirroring HA state onto the display
- **MUST** respect the **64×64 coordinate system** with origin top-left when positioning; content beyond 0…63 is clipped

### Services (target: the integration's `sensor` entity)

- **MUST** use the `divoom_pixoo.show_message` service for **push/ad-hoc display**: `page_data` (a **single** page as YAML, required) is shown temporarily; optionally `duration` (seconds, otherwise `scan_interval`). `enabled`/`variables` do **not** apply here
- **MAY** trigger `divoom_pixoo.play_buzzer` with `buzz_cycle_time_millis` (default 500), `idle_cycle_time_millis` (default 500), `total_time` (default 3000) — **warning:** this may potentially damage the device, use at your own risk
- **MAY** use `divoom_pixoo.restart` for a device restart (with a delay) and `divoom_pixoo.update_page` to re-render/re-send the current page — **warning:** spamming `update_page` heavily can crash the device
- **SHOULD** understand `show_message` as a **temporary overlay** of the default rotation: after the `duration` elapses, the configured `pages_data` rotation continues

## Acceptance Criteria

- [ ] The device is reachable over a stable local IP; the integration was installed via HACS and a `divoom_pixoo` entry with `ip_address` + `scan_interval` exists
- [ ] Both entities (`sensor` "Current Page", `light` "Light") exist; `light` toggles display on/off and brightness; when the device is unreachable they become `unavailable`
- [ ] A `pages_data` list with at least one `components` page rotates on the `scan_interval`; per-page `duration` and `enabled` take effect in the config
- [ ] A `components` page renders text (upper-cased), image (local/URL/Base64), and rectangle correctly in the 64×64 grid with the chosen font/color/alignment
- [ ] At least one special page (`PV`, `progress_bar`, `fuel`) or native page (`channel`/`clock`/`gif`/`visualizer`) is configured as an example
- [ ] `show_message` displays an ad-hoc page temporarily and then returns to the rotation; `play_buzzer`/`restart`/`update_page` target the `sensor` entity
- [ ] Jinja templates visibly mirror an HA entity state onto the display (e.g. a sensor number in a `text` component)
- [ ] The config-only nature of `enabled`/`duration`/`variables` is accounted for — in the `show_message` path fixed values resp. HA `variables` are used instead

## Open Questions

- ClockFace and visualizer IDs are device/firmware/app dependent and not stably documented — should a project-local ID catalog (obtained via the `CurClockId` debug method) be maintained?
- Should the recurring Pixoo pages (countdown, status) be standardized into a blueprint/script layer in the `home-assistant-config` repo, instead of duplicating pages per automation?
- Version drift: this spec is verified against `gickowtf/pixoo-homeassistant` v1.23.0 — future releases (new page types, fonts, services) require a re-check.
