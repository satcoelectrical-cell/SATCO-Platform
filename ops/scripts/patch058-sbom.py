#!/usr/bin/env python3
"""Bind and verify a Syft CycloneDX SBOM to exact PATCH-058 artifact bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
PROPERTY_PREFIX = "satco:patch058:"


def digest(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_sbom(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("bomFormat") != "CycloneDX" or not isinstance(data.get("components"), list):
        raise ValueError("Syft output is not a CycloneDX JSON component inventory")
    if not data.get("specVersion") or not isinstance(data.get("metadata"), dict):
        raise ValueError("CycloneDX metadata/specVersion is missing")
    return data


def expected_properties(args: argparse.Namespace) -> dict[str, str]:
    if not REVISION_RE.fullmatch(args.revision):
        raise ValueError("revision must be a full 40-character lowercase Git SHA")
    artifact = pathlib.Path(args.artifact)
    if not artifact.is_file():
        raise ValueError("artifact does not exist")
    return {
        PROPERTY_PREFIX + "artifact-digest": digest(artifact),
        PROPERTY_PREFIX + "artifact-name": args.artifact_name,
        PROPERTY_PREFIX + "source-revision": args.revision,
        PROPERTY_PREFIX + "tool": f"syft@{args.syft_version}",
    }


def bind(args: argparse.Namespace) -> int:
    data = load_sbom(pathlib.Path(args.input))
    properties = data["metadata"].setdefault("properties", [])
    if not isinstance(properties, list):
        raise ValueError("CycloneDX metadata.properties must be an array")
    properties[:] = [
        item for item in properties
        if not str(item.get("name", "")).startswith(PROPERTY_PREFIX)
    ]
    properties.extend(
        {"name": name, "value": value}
        for name, value in sorted(expected_properties(args).items())
    )
    pathlib.Path(args.output).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"sbom-bound: {digest(pathlib.Path(args.output))}")
    return 0


def verify(args: argparse.Namespace) -> int:
    data = load_sbom(pathlib.Path(args.sbom))
    properties = data["metadata"].get("properties")
    if not isinstance(properties, list):
        raise ValueError("bound CycloneDX properties are missing")
    actual = {item.get("name"): item.get("value") for item in properties}
    for name, value in expected_properties(args).items():
        if actual.get(name) != value:
            raise ValueError(f"SBOM binding mismatch: {name}")
    print(f"sbom-verified: {digest(pathlib.Path(args.sbom))}")
    return 0


def identity_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--syft-version", required=True)


def make_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    binder = commands.add_parser("bind")
    identity_arguments(binder)
    binder.add_argument("--input", required=True)
    binder.add_argument("--output", required=True)
    binder.set_defaults(handler=bind)
    verifier = commands.add_parser("verify")
    identity_arguments(verifier)
    verifier.add_argument("--sbom", required=True)
    verifier.set_defaults(handler=verify)
    return root


def main() -> int:
    args = make_parser().parse_args()
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
