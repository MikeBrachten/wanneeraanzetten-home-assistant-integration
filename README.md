<img src="https://raw.githubusercontent.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/main/custom_components/wanneeraanzetten/brand/icon.png" alt="Wanneer Aanzetten logo" width="96" height="96" align="right">

# Wanneer Aanzetten — Home Assistant integration for dynamic electricity prices

Bring **[wanneeraanzetten.nl](https://wanneeraanzetten.nl/)** into Home Assistant. See a branded **day-ahead electricity price graph**, an estimated all-in price based on your saved contract settings, and an **on/off recommendation for when to run each appliance**. Install this custom integration through **HACS** and use its card, sensors, and automation-ready entities in your dashboards.

[![HACS custom integration](https://img.shields.io/badge/HACS-Custom%20integration-41BDF5?logo=homeassistant&logoColor=white)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MikeBrachten&repository=wanneeraanzetten-home-assistant-integration&category=integration)
[![CI](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/MikeBrachten/wanneeraanzetten-home-assistant-integration)](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[Install with HACS](#install-with-hacs)** · **[Nederlandse handleiding](docs/README.nl.md)** · **[Account and appliance planner](https://wanneeraanzetten.nl/?view=account)** · **[Report a bug](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/issues/new/choose)**

## What does this Home Assistant integration do?

- **Account linking:** sign in with your existing Wanneer Aanzetten account, including authenticator or recovery-code verification.
- **Current electricity prices:** display the active day-ahead spot price in **EUR/kWh**, including negative prices. Taxes, VAT, and supplier fees are excluded.
- **Branded dashboard graph:** an automatically registered HACS card displays up to 24 hours of spot prices, uses your saved Dutch tariff to show an estimated all-in price, and links directly to tariff settings.
- **Cloud-synced tariff settings:** change your variable supplier markup, energy tax, VAT, and market in your signed-in website account and use those values in Home Assistant.
- **Appliance recommendations:** a binary sensor for each synced washing machine, dishwasher, dryer, EV charging plan, or other saved device.
- **Automatic discovery:** devices added to your online account appear on the next update; one shared poll runs every minute.
- **Automation-ready data:** inspect the recommended start/end, appliance duration, and average spot price for the selected window.
- **English and Dutch:** translated setup and entity names, with a configurable electricity market.

**A recommendation sensor is on when starting now is the cheapest available option within the device's saved delay window.** Off means a cheaper valid start is available later. Unavailable means there is insufficient price coverage or the service cannot be reached. These sensors do not measure whether an appliance is physically running.

## Install with HACS

### Requirements

- Home Assistant **2025.1.3 or newer**.
- [HACS](https://www.hacs.xyz/docs/use/) installed, or use [manual installation](#manual-installation).
- A [wanneeraanzetten.nl account](https://wanneeraanzetten.nl/?view=account) with your devices saved online.
- Internet access from Home Assistant to `wanneeraanzetten.nl`.

### Add this repository to HACS

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MikeBrachten&repository=wanneeraanzetten-home-assistant-integration&category=integration)

Or add it manually:

1. Open **HACS** in Home Assistant.
2. Open the menu and select **Custom repositories**.
3. Paste this repository URL:

   ```text
   https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration
   ```

4. Select **Integration** as the category and add the repository.
5. Find **Wanneer Aanzetten**, download the latest release, and restart Home Assistant.
6. Open **Settings → Devices & services → Add integration → Wanneer Aanzetten**.
7. Sign in, choose your electricity market, and complete two-step verification if enabled.

[![Open the integration setup in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=wanneeraanzetten)

This is a **custom repository integration**, not a default HACS catalogue listing. HACS manages updates after you add the repository.

### Manual installation

Download `wanneeraanzetten.zip` from the [latest release](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/releases/latest). Extract it into your Home Assistant configuration directory. The result must contain:

```text
config/
└── custom_components/
    └── wanneeraanzetten/
        ├── __init__.py
        ├── manifest.json
        └── ...
```

Restart Home Assistant and follow steps 6–7 above. Manual installations must be updated manually.

## Sensors for electricity prices and appliance planning

| Entity | What it tells you | Useful attributes |
| --- | --- | --- |
| Electricity spot price | Current price in EUR/kWh, excluding taxes and supplier markup | Market, data source, price-period start/end, tax exclusions |
| Estimated household price | Current Dutch marginal price calculated from the spot price and saved tariff settings | Supplier, formula, fixed-fee exclusion, tariff-settings link |
| Appliance: Recommended now | Whether now is the cheapest valid start within the saved delay settings | Best start/end, duration in minutes, average spot price |

The integration also exposes today’s and tomorrow’s available price slots on the spot-price
sensor. Its dashboard card plots the next 24 hours in the Wanneer Aanzetten brand, highlights
the current period, and marks missing price data instead of drawing it as a zero price. Home
Assistant automatically registers the card after the integration is installed; after a restart,
search for **Wanneer Aanzetten · Prijsgrafiek** under **Add card**. The card is available in
Dutch and English and follows your Home Assistant theme.

You can add the card from the visual card picker, or use YAML and replace the entity ID with your
spot-price sensor:

```yaml
type: custom:wanneeraanzetten-price-card
entity: sensor.your_electricity_spot_price
```

Each appliance is registered as its own Home Assistant device. Entity IDs depend on your language, appliance names, and existing entities. Deleted account devices become unavailable so automations do not silently switch targets.

The planner compares available prices for today and tomorrow, when published. It uses your saved appliance duration, maximum delay, delay step, and start/end delay mode. Equal-price options favor the earliest start. Plans recalculate at each poll; they are not fixed run reservations.

Price-period lengths follow the upstream data, including quarter-hour prices and hourly fallback. Dutch delivery dates use Europe/Amsterdam time, including daylight saving time. Choose the electricity market in Home Assistant. When you sign in to wanneeraanzetten.nl, your tariff settings sync to your account and are shared with linked Home Assistant installations.

## Example: get a notification when your washing machine is recommended

Replace the example entity ID with the **Recommended now** binary sensor shown in your Home Assistant installation:

```yaml
alias: Washing machine recommended now
triggers:
  - trigger: state
    entity_id: binary_sensor.wasmachine_recommended_now
    from: "off"
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      title: Wanneer Aanzetten
      message: This is a cheap time to start the washing machine.
```

The explicit `off` → `on` trigger avoids a notification when an unavailable sensor reconnects. To remotely start a compatible appliance, combine this sensor with that appliance's own Home Assistant integration. This integration does not switch appliances on or off itself.

## Plan cheaper electricity use with wanneeraanzetten.nl

[Wanneer Aanzetten](https://wanneeraanzetten.nl/) helps you compare dynamic electricity prices and find a suitable start window for your appliances. Set up a device on the website, save it to your account, and use the same recommendation in Home Assistant.

- [Electricity prices today — stroomprijzen vandaag](https://wanneeraanzetten.nl/stroomprijzen-vandaag/)
- [Electricity prices tomorrow — stroomprijzen morgen](https://wanneeraanzetten.nl/stroomprijzen-morgen/)
- [When to run your washing machine](https://wanneeraanzetten.nl/wanneer-wasmachine-aanzetten/)
- [When to run your dishwasher](https://wanneeraanzetten.nl/wanneer-vaatwasser-aanzetten/)
- [Find a cheaper EV charging window](https://wanneeraanzetten.nl/wanneer-elektrische-auto-opladen/)
- [Understand the price methodology](https://wanneeraanzetten.nl/methodologie/)

De [Nederlandse handleiding](docs/README.nl.md) legt uit hoe je dynamische stroomprijzen en apparaatadvies in Home Assistant gebruikt.

## Frequently asked questions

### Does the electricity sensor show my all-in household tariff?

The spot-price sensor reports the market price, excluding energy tax, VAT, and supplier markup. A separate **Estimated household price** sensor and the branded graph use your account's Dutch tariff settings to estimate the variable price per kWh. Fixed daily or monthly fees are excluded, and the result is an estimate based on the values you save in [tariff settings](https://wanneeraanzetten.nl/?view=settings).

### Does “on” mean my appliance is running?

No. It means the planner currently recommends starting it. Actual power state and remote start belong to your appliance or smart-plug integration.

### Why are devices or prices unavailable?

Only devices saved to your online account are visible. Prices may be unpublished or temporarily unavailable, and a complete price window must cover the whole appliance run. Missing coverage is never treated as a zero price or an off recommendation.

### Is my password stored in Home Assistant?

No. It is used during account linking in an isolated login session. Home Assistant stores a scoped read-only token, valid for one year. The service stores a hash of that token. Relink when prompted after expiry or revocation.

### How do I change the electricity market or remove access?

Use **Configure** on the integration to change the market. Removing the integration revokes its token when the service is reachable. Password recovery also revokes existing integration links. See [security and privacy](docs/security-and-privacy.md) for details.

### Why does HACS sometimes show “icon not available”?

The integration ships 256 px and 512 px brand icons, shown by Home Assistant on 2026.3 and newer. Some HACS versions still fetch list icons from the old public CDN instead of the local integration brand API. That upstream issue can leave the HACS list icon blank even when the installed integration icon works. See [HACS issue #5223](https://github.com/hacs/integration/issues/5223). The README shows the logo independently of this HACS limitation. On older Home Assistant versions, local custom-integration brand images are not supported.

### Is this an official Home Assistant integration?

It is a custom integration maintained alongside the Wanneer Aanzetten service. It is not part of Home Assistant Core and is not endorsed by the Home Assistant project.

## Support and development

Read [troubleshooting](docs/troubleshooting.md), [contributing](CONTRIBUTING.md), [security reporting](SECURITY.md), and the [changelog](CHANGELOG.md). Please do not put passwords, tokens, recovery codes, or private account details in public issues.

Every compatibility target runs the complete 23-test suite in CI:

| Home Assistant | Python | Result |
| --- | --- | --- |
| 2025.1.3 (minimum) | 3.13 | Supported |
| 2025.6.2 | 3.13 | Supported |
| 2026.3.3 | 3.14 | Supported |
| 2026.10.2 | 3.14 | Supported |

CI checks config flows, entity availability, automatic discovery, authentication, and the published API contract. It validates HACS packaging and the integration manifest with hassfest. CodeQL, Gitleaks, and pip-audit run as security checks; secret and dependency checks also gate release publication. Keep your Home Assistant platform updated; compatibility coverage is not a security recommendation to stay on an old platform.

This repository contains only the Home Assistant client. The hosted API and website are maintained separately. Code is licensed under the [MIT License](LICENSE). The Wanneer Aanzetten name and brand assets remain the property of their owner; see [NOTICE](NOTICE).
