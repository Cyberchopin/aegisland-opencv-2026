#!/usr/bin/env python3
"""Build a deterministic local review archive; never publish or call AWS."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    source = ROOT / "docs/TECHNICAL_REPORT.md"
    markdown = MarkdownIt("commonmark").enable("table")
    default_fence = markdown.renderer.rules["fence"]

    def fence(tokens, index, options, env):
        if tokens[index].info.strip() == "mermaid":
            return '<figure><img src="../submission/architecture.svg" alt="Local OpenCV and undeployed cloud architecture"></figure>'
        return default_fence(tokens, index, options, env)

    markdown.renderer.rules["fence"] = fence
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>AegisLand technical report</title><style>"
        "body{max-width:1050px;margin:2rem auto;padding:0 1rem;font:16px/1.6 Arial,sans-serif;color:#182d40}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:.5rem;text-align:left}"
        "pre{white-space:pre-wrap;background:#f3f5f7;padding:1rem}img{width:100%;height:auto}"
        "@media print{body{margin:0;max-width:none}a{color:inherit}pre,figure{break-inside:avoid}}"
        "</style><main>" + markdown.render(source.read_text()) + "</main></html>"
    )
    (ROOT / "docs/TECHNICAL_REPORT.html").write_text(html)
    selected = [
        ROOT / name
        for name in ("README.md", "core-pin.json", "pytest.ini", ".gitignore")
    ]
    selected += list(ROOT.glob("requirements*.txt"))
    for folder in ("cloud", "docs", "infra", "scripts", "tests", "evidence", ".github"):
        selected += [
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and not p.name.startswith("package-build")
        ]
    selected += list((ROOT / "submission").glob("*.md"))
    selected += list((ROOT / "submission").glob("*.svg"))
    payload = {}
    for path in sorted(set(selected)):
        if path.is_symlink():
            raise ValueError(f"Symlink not permitted: {path.name}")
        name = str(path.relative_to(ROOT))
        if any(
            part in {".aws", ".git", ".venv", ".baseline", ".agents", ".codex"}
            for part in Path(name).parts
        ):
            raise ValueError("Private/tooling path in package")
        data = path.read_bytes()
        if path.suffix in {
            ".json",
            ".py",
            ".md",
            ".html",
            ".txt",
            ".yaml",
            ".yml",
            ".svg",
        }:
            text = data.decode("utf-8")
            if re.search(
                r"arn:aws[^\s\"']*:[0-9]{12}:|(?:AKIA|ASIA)[A-Z0-9]{16}", text
            ):
                raise ValueError(f"Identifier/credential-pattern review needed: {name}")
        payload[name] = data
    manifest = {
        "package_status": "LOCAL_OWNER_REVIEW_ONLY; AWS execution and final submission incomplete",
        "competition_base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "package_created_from_working_tree": True,
        "working_tree_status": subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip(),
        "core_pin": json.loads((ROOT / "core-pin.json").read_text()),
        "core_source_included": False,
        "private_configuration_and_installed_environments_included": False,
        "files": {name: digest(data) for name, data in payload.items()},
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    (ROOT / "submission/PACKAGE_MANIFEST.json").write_bytes(manifest_bytes)
    payload["submission/PACKAGE_MANIFEST.json"] = manifest_bytes
    archive = ROOT / "submission/aegisland-judge-source.zip"
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as handle:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 22, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            handle.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
        assert all(
            digest(handle.read(name)) == digest(data) for name, data in payload.items()
        )
    sha = digest(archive.read_bytes())
    archive.with_suffix(".zip.sha256").write_text(f"{sha}  {archive.name}\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "archive": str(archive.relative_to(ROOT)),
                "files": len(payload),
                "bytes": archive.stat().st_size,
                "sha256": sha,
                "published": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
