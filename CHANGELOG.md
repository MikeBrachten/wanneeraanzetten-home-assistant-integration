# Changelog

## 0.2.0-beta2 — 2026-10-21

- Respect the account’s saved hourly or 15-minute electricity contract interval, with hourly prices when no interval is saved.
- Add a guided Home Assistant options flow for choosing the market and price interval, with an optional per-installation interval override.
- Improve dashboard card registration, including delayed Lovelace storage and YAML-managed setups.
- Fix the branded price card editor when its configuration is initially empty.
- Add tests for the account interval selection and dashboard-resource setup.

## 0.2.0-beta — 2026-10-21

- Fix the branded price card editor when its configuration is initially empty.
- Automatically load the card resource for config-entry installations.

## 0.2.0 — 2026-10-21

- Add an automatically registered, branded Lovelace card with a next-24-hour price graph.
- Add an estimated household price sensor based on saved Dutch tariff settings; fixed fees are excluded.
- Sync signed-in tariff settings through the account API and expose them to read-only Home Assistant links.
- Add direct tariff settings links and setup guidance in the integration and dashboard card.
- Include the bundled card in the HACS manual-install release archive.

## 0.1.1 — 2026-10-20

- Lower the minimum Home Assistant version to 2025.1.3 after full runtime testing.
- Add a four-version compatibility matrix covering 2025.1, 2025.6, 2026.3, and 2026.10.
- Improve the Dutch HACS listing description and show the logo in the README.
- Ship correctly sized 256 px and 512 px icons; document the HACS legacy-CDN display issue.
- Add Gitleaks history scanning, a service-token rule, and pip-audit dependency checks.
- Gate releases on secret and dependency scans, alongside existing CodeQL and repository protection.
- Resolve automated dependency PRs and use the updated Ruff formatter with Python 3.13 syntax.

## 0.1.0 — 2026-10-20

Initial public release.

- Link a Wanneer Aanzetten account, with authenticator or recovery-code verification.
- Display current electricity spot prices in EUR/kWh.
- Discover an appliance recommendation binary sensor for every synced device.
- Share one update per account every minute.
- Support English and Dutch, configurable electricity markets, and reauthentication.
- Mark incomplete price coverage and connection failures as unavailable.
- Distribute through a HACS custom repository or a versioned manual-install ZIP.
