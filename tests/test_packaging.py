"""Verify the distributable archive, independent of the runtime tests."""

import json
import zipfile

import pytest

from scripts import build_release


def test_release_is_deterministic_and_installable():
    archive = build_release.build_release()
    first = archive.read_bytes()
    assert build_release.build_release().read_bytes() == first
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        base = "custom_components/wanneeraanzetten/"
        for path in [
            "__init__.py",
            "config_flow.py",
            "manifest.json",
            "translations/en.json",
            "translations/nl.json",
            "brand/icon.png",
            "frontend/wanneeraanzetten-price-card.js",
        ]:
            assert base + path in names
        manifest = json.loads(bundle.read(base + "manifest.json"))
        assert manifest["domain"] == "wanneeraanzetten"
        assert all(
            name.startswith(base) or name in {"LICENSE", "NOTICE", "README.md"} for name in names
        )
        assert not any("__pycache__" in name or name.endswith((".pyc", ".env")) for name in names)


def test_packager_rejects_accidental_non_component_files(tmp_path, monkeypatch):
    component = tmp_path / "custom_components" / "wanneeraanzetten"
    component.mkdir(parents=True)
    (component / "manifest.json").write_text('{"version": "0.1.0"}')
    (component / "credentials.env").write_text("example only")
    monkeypatch.setattr(build_release, "ROOT", tmp_path)
    monkeypatch.setattr(build_release, "COMPONENT", component)
    with pytest.raises(ValueError, match="Unexpected component file"):
        build_release.build_release()
