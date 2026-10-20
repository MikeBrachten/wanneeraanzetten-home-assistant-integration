# Account linking, security, and privacy

The integration connects to `https://wanneeraanzetten.nl` using TLS. It does not open inbound
network ports, send analytics, or contact upstream electricity data providers directly.

## Credentials

- Your email and password are sent to the existing sign-in endpoint during setup.
- Authenticator and one-time recovery codes use the service's existing verification flow.
- Login cookies are isolated from the shared Home Assistant HTTP session. The temporary
  login session is logged out after token issuance.
- Home Assistant stores your account email, selected market, and a scoped integration token.
  It does not store your password or pending two-factor token.
- The token expires after one year. The server stores its hash. Expiry or revocation triggers
  Home Assistant reauthentication, which checks the linked account identity.

Keep Home Assistant configuration files and backups private because they contain the integration
access token. The integration uses Home Assistant's config-entry storage; it does not add separate
at-rest encryption or an external credential vault.

## Data read by the integration

The API returns your account identity, current spot-price metadata, and saved devices with their
names, icons, run durations, and current planning recommendations. Polling runs once a minute per
linked account. This is a cloud connection, not a local appliance protocol.

A scoped token can read only its account's integration snapshot and revoke itself. It cannot edit
devices, access billing, change your password, or mint additional tokens. No physical device state
is read, and no appliance is controlled by this component.

## Revoking access

Removing the integration revokes its own token if the service is reachable. Reloading or restarting
Home Assistant does not revoke it. Password recovery revokes existing integration tokens. If a
removal happened offline, an authenticated account session can list and revoke the remaining link
using the service's token-management API. Do not paste session cookies or bearer tokens into issues.

The service's [privacy policy](https://wanneeraanzetten.nl/privacy/) and
[terms](https://wanneeraanzetten.nl/voorwaarden/) govern use of the hosted account and API.
Report suspected vulnerabilities privately using [SECURITY.md](../SECURITY.md).
