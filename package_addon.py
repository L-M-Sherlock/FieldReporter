#!/usr/bin/env python3

"""
Package FieldReporter into an Anki-compatible .ankiaddon archive.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).parent.resolve()
DEFAULT_OUTPUT = PROJECT_ROOT / "dist" / "FieldReporter.ankiaddon"
DEFAULT_MANIFEST = PROJECT_ROOT / "manifest.json"

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".vscode",
    "__pycache__",
    "dist",
}

EXCLUDED_FILES = {
    ".DS_Store",
    "manifest.json",
    "package_addon.py",
}

EXCLUDED_SUFFIXES = {
    ".ankiaddon",
    ".log",
    ".pyc",
    ".pyo",
    ".swp",
    ".tmp",
}


def should_include(path: Path) -> bool:
    """Check if `path` should be part of the final package."""
    relative_parts = path.relative_to(PROJECT_ROOT).parts

    if any(part in EXCLUDED_DIRS for part in relative_parts):
        return False

    if path.name in EXCLUDED_FILES:
        return False

    if path.suffix in EXCLUDED_SUFFIXES:
        return False

    return True


def iter_project_files() -> list[Path]:
    """Collect project files that need to be bundled."""
    candidates = []
    for path in PROJECT_ROOT.rglob("*"):
        if path.is_file() and should_include(path):
            candidates.append(path)
    return sorted(
        candidates, key=lambda item: item.relative_to(PROJECT_ROOT).as_posix()
    )


def load_manifest(manifest_path: Path, override_version: str | None) -> bytes:
    """Load manifest JSON and update mutable fields (mod timestamp, optional version override)."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["mod"] = int(time.time())

    if override_version:
        manifest_data["version"] = override_version

    manifest_json = json.dumps(manifest_data, indent=2, ensure_ascii=False)
    return manifest_json.encode("utf-8")


def package_addon(output_path: Path, manifest_bytes: bytes) -> Path:
    """Create the .ankiaddon archive."""
    files = iter_project_files()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(
                file_path,
                arcname=file_path.relative_to(PROJECT_ROOT).as_posix(),
            )
        archive.writestr("manifest.json", manifest_bytes)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package FieldReporter into an Anki .ankiaddon archive."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Destination path for the generated .ankiaddon file.",
    )
    parser.add_argument(
        "-m",
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Path to the manifest.json template used for packaging.",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Optional version string to inject into the manifest.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_path = Path(args.output).expanduser().resolve()
    if output_path.suffix != ".ankiaddon":
        output_path = output_path.with_suffix(".ankiaddon")

    manifest_bytes = load_manifest(Path(args.manifest).resolve(), args.version)
    package_addon(output_path, manifest_bytes)
    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
