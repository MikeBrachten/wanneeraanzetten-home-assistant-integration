"""Audit owned runtime requirements and the isolated security-tool environment."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Fail on known vulnerabilities or an incomplete dependency audit."""
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--local",
            "--strict",
            "--format",
            "json",
            "--output",
            str(reports / "security-tools.json"),
            "--progress-spinner",
            "off",
        ],
        check=True,
    )
    manifest = json.loads((ROOT / "custom_components/wanneeraanzetten/manifest.json").read_text())
    requirements = manifest["requirements"]
    if not requirements:
        (reports / "integration-runtime.json").write_text(
            json.dumps(
                {
                    "dependencies": [],
                    "message": "No third-party runtime requirements are bundled by this integration. "
                    "Home Assistant platform dependencies are managed by Home Assistant.",
                },
                indent=2,
            )
            + "\n"
        )
        print("No additional integration runtime dependencies to audit.")
        return
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "requirements.txt"
        source.write_text("\n".join(requirements) + "\n")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--strict",
                "--requirement",
                str(source),
                "--format",
                "json",
                "--output",
                str(reports / "integration-runtime.json"),
                "--progress-spinner",
                "off",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
