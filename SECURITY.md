# Security policy

## Supported versions

Security fixes target the latest stable release. Upgrade through HACS or install the latest
manual release before reporting a problem.

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/MikeBrachten/wanneeraanzetten-home-assistant-integration/security/advisories/new).
If that form is unavailable, email **info@mbdigitalventures.nl** with the subject
“Wanneer Aanzetten Home Assistant security”. Do not open a public issue for an authentication,
account-isolation, or token-exposure vulnerability. No specific response time is promised.

Include affected versions, reproduction steps with test data, impact, and a proposed fix if known.
Never send passwords, active tokens, two-factor secrets, recovery codes, or a full Home Assistant backup.

See [security and privacy](docs/security-and-privacy.md) for the account-link and data-access model.

## Automated checks

- CodeQL scans Python code on pull requests, main, and a weekly schedule.
- Gitleaks scans Git history in CI and before publishing a release, including a custom
  rule for the service's scoped integration tokens. GitHub secret scanning and push
  protection are also enabled.
- pip-audit checks the isolated CI security tools and every package declared in the
  integration manifest, including transitive requirements. Vulnerabilities and incomplete
  audits fail the job. JSON reports are retained as workflow artifacts.
- Dependabot proposes grouped platform-test updates and pinned action/tool updates.

The integration currently declares no additional third-party runtime packages. Home Assistant
Core dependencies belong to the installed Home Assistant platform, not this integration's
distribution. Historical compatibility environments intentionally retain upstream pins and
are not a recommendation to run an unpatched platform. Keep Home Assistant itself updated.
The platform's pinned uv installer currently has upstream advisory GHSA-hq85-5cpj-mr62; it is
not bundled or invoked by this integration. That advisory is not suppressed in an audit of
the host environment. The CI audit is isolated so platform and component ownership stay clear.
