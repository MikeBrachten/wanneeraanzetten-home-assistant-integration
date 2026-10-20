# Contributing

Bug reports, documentation improvements, translations, and focused pull requests are welcome.
Check existing issues before opening a new one. Describe the user-visible behavior, expected result,
and how you verified the change. Never include real credentials or account data in tests or issues.

## Local setup

Use Python 3.14, matching Home Assistant 2026.10:

```sh
python3.14 -m venv .venv
.venv/bin/pip install -r tests/requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python scripts/build_release.py
```

To run the minimum-version suite, use Python 3.13 in a separate environment and install
`tests/requirements-ha-2025.1.txt`. The other historical baselines have matching files in
`tests/`. Historical pins are intentionally excluded from automated version updates so
Dependabot does not silently replace compatibility targets. A test-only threaded DNS fixture
avoids resolver cleanup differences between old and current Home Assistant test harnesses.

The test suite is self-contained; it does not need a production account, website source, Node.js,
or external API access. Tests that exercise login cookies use a temporary localhost API fixture.

## Pull requests

Keep changes focused. Include meaningful tests for behavior changes, update translations when
setup text changes, and document user-visible changes in CHANGELOG.md. CI runs tests, lint, HACS
validation, hassfest, and a release archive check. Public API changes must remain compatible with
the hosted service. Review the security policy before reporting authentication vulnerabilities.

## Releases

1. Update `custom_components/wanneeraanzetten/manifest.json` and CHANGELOG.md.
2. Run the test suite, lint, and `python scripts/build_release.py`.
3. Push the release commit and wait for CI to pass.
4. Create a `vX.Y.Z` tag matching the manifest version.
5. The release workflow tests the tagged code, validates the version, builds the ZIP, and publishes
   the GitHub release only after secret scanning and the dependency audit pass. A checksum file accompanies the archive.

HACS downloads the component from the tagged source tree. The ZIP is for manual installation;
its root contains `custom_components/wanneeraanzetten`. No service credentials or website files
belong in this repository.
