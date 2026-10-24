import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "competition_demo", Path(__file__).parents[1] / "scripts/competition_demo.py"
)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_wrong_core_commit_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(demo, "git", lambda *_args: "wrong")
    with pytest.raises(ValueError, match="does not match pin"):
        demo.check_core(tmp_path)


def test_dirty_core_is_rejected(monkeypatch, tmp_path):
    pin = json.loads((demo.ROOT / "core-pin.json").read_text())["commit"]
    monkeypatch.setattr(
        demo,
        "git",
        lambda _path, *args: (
            pin if args[0] == "rev-parse" else " M src/aegisland/planner.py"
        ),
    )
    with pytest.raises(ValueError, match="must be clean"):
        demo.check_core(tmp_path)


def test_cli_never_creates_output_for_bad_core(tmp_path):
    result = subprocess.run(
        [
            demo.sys.executable,
            str(Path(demo.__file__)),
            "--core",
            str(tmp_path),
            "--output",
            str(tmp_path / "evidence"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not (tmp_path / "evidence").exists()


def test_existing_output_is_preserved(monkeypatch, tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("existing evidence")
    monkeypatch.setattr(demo, "check_core", lambda _core: "pinned")
    monkeypatch.setattr(
        demo.sys,
        "argv",
        ["competition_demo", "--core", str(tmp_path / "core"), "--output", str(output)],
    )
    with pytest.raises(FileExistsError):
        demo.main()
    assert sentinel.read_text() == "existing evidence"


def test_output_cannot_change_core(monkeypatch, tmp_path):
    monkeypatch.setattr(
        demo.sys,
        "argv",
        [
            "competition_demo",
            "--core",
            str(tmp_path),
            "--output",
            str(tmp_path / "new"),
        ],
    )
    with pytest.raises(ValueError, match="outside the core"):
        demo.main()
    assert not (tmp_path / "new").exists()
