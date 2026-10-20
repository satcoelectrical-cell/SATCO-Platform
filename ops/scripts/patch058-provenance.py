#!/usr/bin/env python3
"""Generate and verify PATCH-058 in-toto/SLSA provenance."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from typing import Iterable

REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://slsa.dev/provenance/v1"
BUILD_TYPE = "https://satcoelectrical.ir/PATCH-058/github-actions/v1"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_pairs(values: Iterable[str]) -> dict[str, pathlib.Path]:
    pairs: dict[str, pathlib.Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"expected NAME=PATH, got {value!r}")
        name, raw_path = value.split("=", 1)
        if not name or name in pairs:
            raise ValueError(f"empty or duplicate evidence name: {name!r}")
        path = pathlib.Path(raw_path)
        if not path.is_file():
            raise ValueError(f"evidence file does not exist: {path}")
        pairs[name] = path
    return pairs


def descriptors(pairs: dict[str, pathlib.Path]) -> list[dict[str, object]]:
    return [
        {"name": name, "digest": {"sha256": sha256(path)}}
        for name, path in sorted(pairs.items())
    ]


def parse_timestamp(value: str) -> str:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("generated-at must include a timezone")
    return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def validate_identity(args: argparse.Namespace) -> None:
    if not REVISION_RE.fullmatch(args.revision):
        raise ValueError("revision must be a full 40-character lowercase Git SHA")
    if not args.repository or "/" not in args.repository:
        raise ValueError("repository must be an attributable owner/name identity")
    if not args.workflow or not args.release_id:
        raise ValueError("workflow and release-id are required")


def expected_statement(args: argparse.Namespace, generated_at: str) -> dict[str, object]:
    validate_identity(args)
    artifacts = parse_pairs(args.artifact)
    if not artifacts:
        raise ValueError("at least one artifact is required")
    sboms = parse_pairs(args.sbom)
    if not sboms:
        raise ValueError("at least one SBOM is required")
    inputs = parse_pairs(args.input)
    evidence = parse_pairs(args.evidence)
    return {
        "_type": STATEMENT_TYPE,
        "subject": descriptors(artifacts),
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "buildDefinition": {
                "buildType": BUILD_TYPE,
                "externalParameters": {
                    "releaseId": args.release_id,
                    "repository": args.repository,
                    "revision": args.revision,
                    "workflow": args.workflow,
                },
                "internalParameters": {"governedInputs": descriptors(inputs)},
                "resolvedDependencies": [
                    {
                        "uri": f"git+https://github.com/{args.repository}@{args.revision}",
                        "digest": {"gitCommit": args.revision},
                    }
                ],
            },
            "runDetails": {
                "builder": {"id": args.workflow},
                "metadata": {
                    "invocationId": args.release_id,
                    "startedOn": generated_at,
                    "finishedOn": generated_at,
                },
            },
            "satco": {
                "sboms": descriptors(sboms),
                "qualificationEvidence": descriptors(evidence),
            },
        },
    }


def command_generate(args: argparse.Namespace) -> int:
    statement = expected_statement(args, parse_timestamp(args.generated_at))
    output = pathlib.Path(args.output)
    output.write_text(json.dumps(statement, indent=2, sort_keys=True) + "\n")
    print(f"provenance-generated: sha256:{sha256(output)}")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    path = pathlib.Path(args.statement)
    actual = json.loads(path.read_text())
    try:
        generated_at = actual["predicate"]["runDetails"]["metadata"]["startedOn"]
    except (KeyError, TypeError) as exc:
        raise ValueError("statement is missing SLSA run metadata") from exc
    expected = expected_statement(args, parse_timestamp(generated_at))
    if actual != expected:
        raise ValueError("provenance does not match the exact supplied candidate evidence")
    print(f"provenance-verified: sha256:{sha256(path)}")
    return 0


def add_identity_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repository", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--sbom", action="append", default=[])
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--evidence", action="append", default=[])


def make_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate")
    add_identity_arguments(generate)
    generate.add_argument("--generated-at", required=True)
    generate.add_argument("--output", required=True)
    generate.set_defaults(handler=command_generate)
    verify = commands.add_parser("verify")
    add_identity_arguments(verify)
    verify.add_argument("--statement", required=True)
    verify.set_defaults(handler=command_verify)
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
