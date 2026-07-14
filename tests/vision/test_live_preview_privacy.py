from pathlib import Path


def test_preview_and_overlay_code_has_no_persistence_or_base64_path():
    root = Path(__file__).resolve().parents[2] / "src" / "lina"
    paths = (
        root / "interfaces" / "qt" / "camera_preview.py",
        root / "interfaces" / "qt" / "monitoring_overlay.py",
        root / "interfaces" / "qt" / "camera_source.py",
        root / "vision" / "live" / "controller.py",
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths).casefold()
    for forbidden in ("tempfile", "namedtemporaryfile", "b64encode", "base64", "sqlite", "write_bytes"):
        assert forbidden not in combined
