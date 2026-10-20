# Troubleshooting

## The integration does not appear in Home Assistant

Download it in HACS, restart Home Assistant, and refresh the browser. In a manual installation,
check that `manifest.json` is at `config/custom_components/wanneeraanzetten/manifest.json`.
Do not put an extra release directory between `custom_components` and `wanneeraanzetten`.

## Cannot connect or sign in

Verify that Home Assistant can reach `https://wanneeraanzetten.nl`, and confirm your credentials
on the website. Complete authenticator verification, or select the recovery-code checkbox if
using a recovery code. A pending two-factor session expires after five minutes; cancel and restart
account linking if it expires. Rate limiting and service outages are temporary connection failures.

## Devices are missing

Only devices synced to your online account are available. Sign in on the website and save your
browser's devices to the account. Allow a minute for discovery. A deleted device's existing Home
Assistant entity becomes unavailable; remove that old entity manually if it is no longer needed.

## Prices differ from the website

The sensor reports spot prices in EUR/kWh, excluding energy tax, VAT, and supplier fees. The website
can display all-in estimates from browser-local settings. Check the selected electricity market,
price period, and quarter-hour/hour resolution before comparing. Negative spot prices are valid
and do not necessarily mean your household's all-in tariff is negative.

## Recommendations or prices are unavailable

Missing or unpublished data must not become a false zero or off state. A recommended appliance
window needs price coverage for its full duration. Tomorrow's prices may not be published yet.
A temporary connection failure marks entities unavailable until a successful refresh.

## A recommendation changed after an update

The planner recalculates from the current time. A recommendation is not a reservation, physical
power-state measurement, or record of whether an appliance has already started. Use the appliance's
own integration for run state and remote-start controls.

## Change market or reconnect

Use the integration's Configure action to select a different market. If Home Assistant requests
reauthentication, sign in with the originally linked account. Tokens expire after one year and may
also be revoked by account recovery or manual revocation.

## Report a bug

Open the [bug report form](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/issues/new?template=bug_report.yml).
Include Home Assistant and integration versions, the selected market, expected behavior, and a
minimal reproduction. Redact passwords, tokens, email addresses, recovery codes, and private device
names from logs. Report security issues privately through [SECURITY.md](../SECURITY.md).

## HACS says “icon not available”

The package includes `brand/icon.png` (256×256) and `brand/icon@2x.png` (512×512).
Home Assistant serves local integration branding from 2026.3 onward. Some HACS list views
still use the legacy CDN and do not display inline icons, including for installed integrations.
That UI limitation does not affect sensors or installation. See [the upstream HACS issue](https://github.com/hacs/integration/issues/5223).
