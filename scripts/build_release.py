"""Build a deterministic integration archive, including its bundled dashboard card."""

import json
import zipfile
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "wanneeraanzetten"


def build_release() -> Path:
    """Include only tracked component sources, translations, and brand artwork."""
    version = json.loads((COMPONENT / "manifest.json").read_text())["version"]
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    archive = output / "wanneeraanzetten.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(COMPONENT.rglob("*")):
            if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".py", ".json", ".png", ".js"}:
                raise ValueError(f"Unexpected component file: {path.relative_to(ROOT)}")
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, path.read_bytes())
        for name in ["LICENSE", "NOTICE", "README.md"]:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, (ROOT / name).read_bytes())
    checksum = sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{checksum}  {archive.name}\n")
    print(f"Built {archive.name} for integration {version}")
    return archive


if __name__ == "__main__":
    build_release()
