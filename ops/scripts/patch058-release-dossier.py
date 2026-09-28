#!/usr/bin/env python3
"""Fail-closed PATCH-058 release-dossier generator and validator."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
REV = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_ARTIFACTS = {"backend", "frontend", "migrations"}
REQUIRED_SBOMS = {"backend", "frontend"}
REQUIRED_BUILD_INPUTS = {
    "backend-production-lock", "backend-uv-lock",
    "frontend-package-lock", "migration-set",
}
REQUIRED_QUALIFICATION = {"backend", "frontend", "migration"}
REQUIRED_SECURITY = {
    "pip-audit", "npm-audit", "semgrep", "gitleaks", "trivy",
    "vulnerability_gate",
}
REQUIRED_EXCEPTIONS = {"high_findings", "security_decision"}
SECURITY_DECISION_REF = "refs/heads/patch-058-security-decisions"
REQUIRED_EXCEPTION_KEYS = {
    "finding_id", "severity", "source", "source_revision",
    "artifact_digest", "rationale", "compensating_controls", "scope",
    "approver_id", "approved_at", "expires_at", "retest_condition",
    "retest_reference", "retest_result", "status",
}


def digest(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(dt.timezone.utc)


def pairs(values):
    output = {}
    for value in values:
        if "=" not in value:
            raise ValueError("expected NAME=PATH")
        name, raw = value.split("=", 1)
        path = pathlib.Path(raw)
        if not name or name in output or not path.is_file():
            raise ValueError(f"invalid evidence: {value}")
        output[name] = {"reference": raw, "digest": digest(path)}
    return output


def approval(raw):
    status, reference = raw.split("=", 1)
    if status not in {"pending", "approved", "rejected"}:
        raise ValueError("invalid approval status")
    item = {"status": status, "reference": reference}
    if status == "approved":
        path = pathlib.Path(reference)
        if not path.is_file():
            raise ValueError("approved evidence file missing")
        item["digest"] = digest(path)
    return item


def verify_evidence(name, item):
    if set(item) - {"reference", "digest", "status"}:
        raise ValueError(f"unexpected evidence fields: {name}")
    reference = item.get("reference")
    expected = item.get("digest")
    if not reference or not SHA.fullmatch(expected or ""):
        raise ValueError(f"invalid evidence descriptor: {name}")
    path = pathlib.Path(reference)
    if not path.is_file() or digest(path) != expected:
        raise ValueError(f"missing or substituted evidence: {name}")


def load_evidence(name, item):
    verify_evidence(name, item)
    try:
        return json.loads(pathlib.Path(item["reference"]).read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON evidence: {name}") from error


def named_digests(items):
    return {item["name"]: "sha256:" + item["digest"]["sha256"] for item in items}


def validate_approval(name, item, dossier, security_decision_commit,
                      require_approvals):
    status = item.get("status")
    if status not in {"pending", "approved", "rejected"} or not item.get("reference"):
        raise ValueError(f"invalid {name}")
    if status == "rejected":
        raise ValueError(f"{name} is rejected")
    if require_approvals and status != "approved":
        raise ValueError(f"{name} is not approved")
    if status != "approved":
        return

    evidence = load_evidence(name, item)
    if evidence.get("decision") != "approved":
        raise ValueError(f"{name} decision is not approved")
    if evidence.get("release_id") != dossier["release_id"]:
        raise ValueError(f"{name} release mismatch")
    if evidence.get("source_commit") != dossier["source_commit"]:
        raise ValueError(f"{name} source mismatch")
    if evidence.get("security_decision_commit") != security_decision_commit:
        raise ValueError(f"{name} security-decision mismatch")
    if evidence.get("artifact_digests") != {
        key: value["digest"] for key, value in dossier["artifacts"].items()
    }:
        raise ValueError(f"{name} artifact mismatch")
    timestamp(evidence["decided_at"])
    if not evidence.get("authority") or not evidence.get("evidence_reference"):
        raise ValueError(f"{name} is not attributable")


def validate(dossier, now, require_approvals=True):
    required = {
        "schema_version", "release_id", "source_commit", "artifacts",
        "build_inputs", "qualification_evidence", "security_evidence",
        "exceptions", "sboms", "provenance", "signature_verification",
        "human_signing_authorization", "human_release_approval", "created_at",
    }
    if set(dossier) != required:
        raise ValueError(
            f"dossier keys mismatch: missing={sorted(required-set(dossier))} "
            f"extra={sorted(set(dossier)-required)}"
        )
    if (
        dossier["schema_version"] != "v1"
        or not dossier["release_id"]
        or not REV.fullmatch(dossier["source_commit"])
    ):
        raise ValueError("invalid dossier identity")
    timestamp(dossier["created_at"])

    for section in (
        "artifacts", "build_inputs", "qualification_evidence",
        "security_evidence", "exceptions", "sboms",
    ):
        if not isinstance(dossier[section], dict) or not dossier[section]:
            raise ValueError(f"{section} must be non-empty")
        for name, item in dossier[section].items():
            verify_evidence(section + "." + name, item)
    if set(dossier["artifacts"]) != REQUIRED_ARTIFACTS:
        raise ValueError("backend, frontend and migrations artifacts are mandatory")
    if set(dossier["sboms"]) != REQUIRED_SBOMS:
        raise ValueError("backend and frontend SBOMs are mandatory")
    if set(dossier["build_inputs"]) != REQUIRED_BUILD_INPUTS:
        raise ValueError("governed build-input evidence is incomplete")
    if set(dossier["qualification_evidence"]) != REQUIRED_QUALIFICATION:
        raise ValueError("backend, frontend and migration qualification is mandatory")
    if set(dossier["security_evidence"]) != REQUIRED_SECURITY:
        raise ValueError("mandatory scanner/security evidence is incomplete")
    if set(dossier["exceptions"]) != REQUIRED_EXCEPTIONS:
        raise ValueError("High exceptions and security-decision evidence are mandatory")

    provenance = load_evidence("provenance", dossier["provenance"])
    external = provenance.get("predicate", {}).get("buildDefinition", {}).get(
        "externalParameters", {}
    )
    if external.get("revision") != dossier["source_commit"]:
        raise ValueError("provenance source mismatch")
    if external.get("releaseId") != dossier["release_id"]:
        raise ValueError("provenance release mismatch")
    if named_digests(provenance.get("subject", [])) != {
        key: value["digest"] for key, value in dossier["artifacts"].items()
    }:
        raise ValueError("provenance artifact mismatch")
    provenance_inputs = named_digests(
        provenance.get("predicate", {}).get("buildDefinition", {}).get(
            "internalParameters", {}
        ).get("governedInputs", [])
    )
    if provenance_inputs != {
        key: value["digest"] for key, value in dossier["build_inputs"].items()
    }:
        raise ValueError("provenance build-input mismatch")
    provenance_sboms = named_digests(
        provenance.get("predicate", {}).get("satco", {}).get("sboms", [])
    )
    if provenance_sboms != {
        key: value["digest"] for key, value in dossier["sboms"].items()
    }:
        raise ValueError("provenance SBOM mismatch")
    provenance_evidence = named_digests(
        provenance.get("predicate", {}).get("satco", {}).get(
            "qualificationEvidence", []
        )
    )
    dossier_evidence = {
        key.replace("_", "-"): value["digest"]
        for key, value in dossier["security_evidence"].items()
    }
    dossier_evidence["high-exceptions"] = dossier["exceptions"]["high_findings"]["digest"]
    dossier_evidence["security-decision"] = dossier["exceptions"]["security_decision"]["digest"]
    if provenance_evidence != dossier_evidence:
        raise ValueError("provenance security-evidence mismatch")

    for name, descriptor in dossier["qualification_evidence"].items():
        qualification = load_evidence("qualification_evidence." + name, descriptor)
        if (
            qualification.get("result") != "PASS"
            or qualification.get("source_commit") != dossier["source_commit"]
            or qualification.get("gate") != name
        ):
            raise ValueError(f"{name} qualification mismatch")

    for name in REQUIRED_SBOMS:
        sbom = load_evidence("sboms." + name, dossier["sboms"][name])
        properties = {
            item.get("name"): item.get("value")
            for item in sbom.get("metadata", {}).get("properties", [])
        }
        if properties.get("satco:patch058:source-revision") != dossier["source_commit"]:
            raise ValueError(f"{name} SBOM source mismatch")
        if properties.get("satco:patch058:artifact-digest") != dossier["artifacts"][name]["digest"]:
            raise ValueError(f"{name} SBOM artifact mismatch")

    gate = load_evidence(
        "security_evidence.vulnerability_gate",
        dossier["security_evidence"]["vulnerability_gate"],
    )
    if gate.get("result") != "PASS" or gate.get("blockingFindings"):
        raise ValueError("vulnerability gate is not PASS with zero blockers")
    backend = dossier["artifacts"]["backend"]["digest"]
    if gate.get("sourceRevision") != dossier["source_commit"]:
        raise ValueError("vulnerability gate source mismatch")
    if gate.get("artifactDigest") != backend:
        raise ValueError("vulnerability gate artifact mismatch")

    decision = load_evidence(
        "exceptions.security_decision", dossier["exceptions"]["security_decision"]
    )
    required_decision = {
        "schemaVersion", "mode", "candidateRevision", "artifactDigest",
        "exceptionEvidenceDigest", "decisionCommit", "decisionRef",
    }
    if set(decision) != required_decision:
        raise ValueError("security-decision evidence fields mismatch")
    if (
        decision.get("schemaVersion") != "PATCH-058-security-decision-v1"
        or decision.get("mode") != "post-build-human-decision"
        or decision.get("candidateRevision") != dossier["source_commit"]
        or decision.get("artifactDigest") != backend
        or decision.get("exceptionEvidenceDigest")
        != dossier["exceptions"]["high_findings"]["digest"]
        or not REV.fullmatch(decision.get("decisionCommit") or "")
        or decision.get("decisionRef") != SECURITY_DECISION_REF
    ):
        raise ValueError("security-decision identity mismatch")
    if gate.get("securityDecision") != decision:
        raise ValueError("vulnerability gate security-decision mismatch")

    exceptions = load_evidence(
        "exceptions.high_findings", dossier["exceptions"]["high_findings"]
    )
    if not isinstance(exceptions, list):
        raise ValueError("High-finding exception evidence must be a list")
    for exception in exceptions:
        if (
            not isinstance(exception, dict)
            or set(exception) != REQUIRED_EXCEPTION_KEYS
            or exception.get("status") != "active"
            or exception.get("severity") != "HIGH"
            or exception.get("source_revision") != dossier["source_commit"]
            or exception.get("artifact_digest") != backend
            or timestamp(exception["expires_at"]) <= now
        ):
            raise ValueError("inactive, mismatched or expired High exception")
    accepted = {
        (item.get("source", "").lower(), item.get("finding_id")): item
        for item in gate.get("acceptedExceptions", [])
        if isinstance(item, dict)
    }
    expected_exceptions = {
        (item["source"].lower(), item["finding_id"]): item for item in exceptions
    }
    if (
        len(accepted) != len(gate.get("acceptedExceptions", []))
        or len(expected_exceptions) != len(exceptions)
        or accepted != expected_exceptions
    ):
        raise ValueError("vulnerability gate accepted-exception mismatch")

    signatures = load_evidence("signature_verification", dossier["signature_verification"])
    if signatures.get("source_commit") != dossier["source_commit"]:
        raise ValueError("signature verification source mismatch")
    if signatures.get("security_decision_commit") != decision["decisionCommit"]:
        raise ValueError("signature verification security-decision mismatch")
    verified = {
        item.get("name"): item.get("artifact_digest")
        for item in signatures.get("artifacts", [])
        if item.get("verified") is True
        and item.get("signer_identity")
        and item.get("oidc_issuer")
    }
    if verified != {
        key: value["digest"] for key, value in dossier["artifacts"].items()
    }:
        raise ValueError("signature verification artifact/trust mismatch")

    validate_approval(
        "human_signing_authorization",
        dossier["human_signing_authorization"], dossier,
        decision["decisionCommit"], require_approvals,
    )
    validate_approval(
        "human_release_approval",
        dossier["human_release_approval"], dossier,
        decision["decisionCommit"], require_approvals,
    )
    return True


def make_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--release-id", required=True)
    generate.add_argument("--source-commit", required=True)
    generate.add_argument("--created-at", required=True)
    generate.add_argument("--output", required=True)
    for flag in (
        "artifact", "build-input", "qualification-evidence",
        "security-evidence", "exception", "sbom",
    ):
        generate.add_argument("--" + flag, action="append", default=[])
    generate.add_argument("--provenance", required=True)
    generate.add_argument("--signature-verification", required=True)
    generate.add_argument("--human-signing-authorization", required=True)
    generate.add_argument("--human-release-approval", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--dossier", required=True)
    verify.add_argument("--now", required=True)
    verify.add_argument("--allow-pending-approvals", action="store_true")
    return root


def main():
    args = make_parser().parse_args()
    try:
        if args.command == "generate":
            dossier = {
                "schema_version": "v1",
                "release_id": args.release_id,
                "source_commit": args.source_commit,
                "artifacts": pairs(args.artifact),
                "build_inputs": pairs(args.build_input),
                "qualification_evidence": pairs(args.qualification_evidence),
                "security_evidence": pairs(args.security_evidence),
                "exceptions": pairs(args.exception),
                "sboms": pairs(args.sbom),
                "provenance": pairs(["x=" + args.provenance])["x"],
                "signature_verification": pairs(
                    ["x=" + args.signature_verification]
                )["x"],
                "human_signing_authorization": approval(
                    args.human_signing_authorization
                ),
                "human_release_approval": approval(args.human_release_approval),
                "created_at": timestamp(args.created_at).isoformat().replace(
                    "+00:00", "Z"
                ),
            }
            pathlib.Path(args.output).write_text(
                json.dumps(dossier, indent=2, sort_keys=True) + "\n"
            )
            print("dossier-generated", digest(args.output))
            return 0
        dossier = json.loads(pathlib.Path(args.dossier).read_text())
        validate(
            dossier, timestamp(args.now),
            require_approvals=not args.allow_pending_approvals,
        )
        print("dossier-verified", digest(args.dossier))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print("BLOCK:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
