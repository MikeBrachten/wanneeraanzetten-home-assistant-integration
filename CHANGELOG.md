# Changelog

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
