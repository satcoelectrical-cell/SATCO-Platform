import copy
import datetime as dt
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "dossier", ROOT / "ops/scripts/patch058-release-dossier.py"
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
NOW = dt.datetime(2026, 9, 27, 9, 0, tzinfo=dt.timezone.utc)
REVISION = "a" * 40
DECISION_COMMIT = "b" * 40
RELEASE_ID = "p058-test"


def ev(path):
    return {"reference": str(path), "digest": M.digest(path)}


class DossierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.temporary.name)

        def write(name, data):
            path = self.path / name
            path.write_text(data if isinstance(data, str) else json.dumps(data))
            return path

        self.artifacts = {
            "backend": write("backend.tar", "backend"),
            "frontend": write("frontend.tar", "frontend"),
            "migrations": write("migrations.tar", "migrations"),
        }
        self.lock = write("lock", "lock")
        self.build_inputs = {
            name: self.lock for name in M.REQUIRED_BUILD_INPUTS
        }
        self.qualifications = {
            name: write(
                f"{name}-qualification.json",
                {"result": "PASS", "source_commit": REVISION, "gate": name},
            )
            for name in M.REQUIRED_QUALIFICATION
        }
        self.sboms = {}
        for name in ("backend", "frontend"):
            self.sboms[name] = write(
                f"{name}-sbom.json",
                {
                    "bomFormat": "CycloneDX",
                    "metadata": {
                        "properties": [
                            {
                                "name": "satco:patch058:source-revision",
                                "value": REVISION,
                            },
                            {
                                "name": "satco:patch058:artifact-digest",
                                "value": M.digest(self.artifacts[name]),
                            },
                        ]
                    },
                },
            )
        self.exceptions = write(
            "exceptions.json",
            [
                {
                    "finding_id": "CVE-TEST-1",
                    "severity": "HIGH",
                    "source": "trivy",
                    "source_revision": REVISION,
                    "status": "active",
                    "artifact_digest": M.digest(self.artifacts["backend"]),
                    "rationale": "Bounded test rationale.",
                    "compensating_controls": "Bounded test controls.",
                    "scope": "Exact test candidate only.",
                    "approver_id": "human-security-authority",
                    "approved_at": "2026-09-27T07:58:25Z",
                    "expires_at": "2026-10-27T07:58:25Z",
                    "retest_condition": "Re-evaluate on any bound identity change.",
                    "retest_reference": "PATCH-058-test-decision",
                    "retest_result": "pass",
                }
            ],
        )
        self.decision = write(
            "security-decision.json",
            {
                "schemaVersion": "PATCH-058-security-decision-v1",
                "mode": "post-build-human-decision",
                "candidateRevision": REVISION,
                "artifactDigest": M.digest(self.artifacts["backend"]),
                "exceptionEvidenceDigest": M.digest(self.exceptions),
                "decisionCommit": DECISION_COMMIT,
                "decisionRef": "refs/heads/patch-058-security-decisions",
            },
        )
        self.gate = write(
            "gate.json",
            {
                "result": "PASS",
                "blockingFindings": [],
                "sourceRevision": REVISION,
                "artifactDigest": M.digest(self.artifacts["backend"]),
                "findings": [
                    {
                        "source": item["source"],
                        "finding_id": item["finding_id"],
                        "severity": item["severity"],
                        "component": "fixture",
                        "installed_version": "1",
                    }
                    for item in json.loads(self.exceptions.read_text())
                ],
                "acceptedExceptions": json.loads(self.exceptions.read_text()),
                "securityDecision": json.loads(self.decision.read_text()),
            },
        )
        self.security = {
            name: (
                self.gate if name == "vulnerability_gate"
                else write(f"{name}.json", {"result": "PASS"})
            )
            for name in M.REQUIRED_SECURITY
        }
        provenance_evidence = {
            name.replace("_", "-"): path for name, path in self.security.items()
        }
        provenance_evidence["high-exceptions"] = self.exceptions
        provenance_evidence["security-decision"] = self.decision
        self.provenance = write(
            "provenance.json",
            {
                "_type": "https://in-toto.io/Statement/v1",
                "subject": [
                    {
                        "name": name,
                        "digest": {"sha256": M.digest(path).removeprefix("sha256:")},
                    }
                    for name, path in self.artifacts.items()
                ],
                "predicate": {
                    "buildDefinition": {
                        "externalParameters": {
                            "releaseId": RELEASE_ID,
                            "revision": REVISION,
                        },
                        "internalParameters": {
                            "governedInputs": [
                                {
                                    "name": name,
                                    "digest": {
                                        "sha256": M.digest(path).removeprefix("sha256:")
                                    },
                                }
                                for name, path in self.build_inputs.items()
                            ]
                        },
                    },
                    "satco": {
                        "sboms": [
                            {
                                "name": name,
                                "digest": {
                                    "sha256": M.digest(path).removeprefix("sha256:")
                                },
                            }
                            for name, path in self.sboms.items()
                        ],
                        "qualificationEvidence": [
                            {
                                "name": name,
                                "digest": {
                                    "sha256": M.digest(path).removeprefix("sha256:")
                                },
                            }
                            for name, path in provenance_evidence.items()
                        ],
                    },
                },
            },
        )
        self.signatures = write(
            "signature-verification.json",
            {
                "source_commit": REVISION,
                "security_decision_commit": DECISION_COMMIT,
                "artifacts": [
                    {
                        "name": name,
                        "artifact_digest": M.digest(path),
                        "verified": True,
                        "signer_identity": "patch058-sign-release.yml@refs/heads/patch-058",
                        "oidc_issuer": "https://token.actions.githubusercontent.com",
                    }
                    for name, path in self.artifacts.items()
                ],
            },
        )
        approval_payload = {
            "decision": "approved",
            "release_id": RELEASE_ID,
            "source_commit": REVISION,
            "security_decision_commit": DECISION_COMMIT,
            "artifact_digests": {
                name: M.digest(path) for name, path in self.artifacts.items()
            },
            "decided_at": "2026-09-27T08:30:00Z",
            "authority": "human-release-authority",
            "evidence_reference": "https://github.example/actions/runs/1",
        }
        self.signing_approval = write("signing-approval.json", approval_payload)
        self.release_approval = write("release-approval.json", approval_payload)
        self.dossier = {
            "schema_version": "v1",
            "release_id": RELEASE_ID,
            "source_commit": REVISION,
            "artifacts": {name: ev(path) for name, path in self.artifacts.items()},
            "build_inputs": {
                name: ev(path) for name, path in self.build_inputs.items()
            },
            "qualification_evidence": {
                name: ev(path) for name, path in self.qualifications.items()
            },
            "security_evidence": {
                name: ev(path) for name, path in self.security.items()
            },
            "exceptions": {
                "high_findings": ev(self.exceptions),
                "security_decision": ev(self.decision),
            },
            "sboms": {name: ev(path) for name, path in self.sboms.items()},
            "provenance": ev(self.provenance),
            "signature_verification": ev(self.signatures),
            "human_signing_authorization": {
                "status": "approved", **ev(self.signing_approval)
            },
            "human_release_approval": {
                "status": "approved", **ev(self.release_approval)
            },
            "created_at": "2026-09-27T08:00:00Z",
        }

    def tearDown(self):
        self.temporary.cleanup()

    def blocked(self, dossier, require_approvals=True):
        with self.assertRaises(ValueError):
            M.validate(dossier, NOW, require_approvals=require_approvals)

    def refresh(self, section, name, path):
        self.dossier[section][name] = ev(path)

    def test_valid_candidate(self):
        self.assertTrue(M.validate(self.dossier, NOW))

    def test_patch059_v3_signing_authorization_uses_source_sha_and_authenticated_approval(self):
        payload = json.loads(self.signing_approval.read_text())
        payload.pop("source_commit")
        payload.pop("decided_at")
        payload.pop("evidence_reference")
        payload.update({
            "schema": "satco.patch059-human-signing-authorization/v3",
            "source_sha": REVISION,
            "approval_event_sha256": "sha256:" + "c" * 64,
        })
        self.signing_approval.write_text(json.dumps(payload))
        self.dossier["human_signing_authorization"] = {
            "status": "approved", **ev(self.signing_approval)
        }
        self.assertTrue(M.validate(self.dossier, NOW))

        payload["source_sha"] = "d" * 40
        self.signing_approval.write_text(json.dumps(payload))
        self.dossier["human_signing_authorization"] = {
            "status": "approved", **ev(self.signing_approval)
        }
        self.blocked(self.dossier)

    def test_duplicate_high_finding_occurrences_share_one_governed_exception(self):
        gate = json.loads(self.gate.read_text())
        gate["findings"].append(dict(gate["findings"][0], component="fixture-2"))
        gate["acceptedExceptions"].append(dict(gate["acceptedExceptions"][0]))
        self.gate.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        provenance = json.loads(self.provenance.read_text())
        for item in provenance["predicate"]["satco"]["qualificationEvidence"]:
            if item["name"] == "vulnerability-gate":
                item["digest"]["sha256"] = M.digest(self.gate).removeprefix("sha256:")
        self.provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        self.dossier["provenance"] = ev(self.provenance)
        self.assertTrue(M.validate(self.dossier, NOW))

    def test_missing_duplicate_high_occurrence_exception_blocks(self):
        gate = json.loads(self.gate.read_text())
        gate["findings"].append(dict(gate["findings"][0], component="fixture-2"))
        self.gate.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        provenance = json.loads(self.provenance.read_text())
        for item in provenance["predicate"]["satco"]["qualificationEvidence"]:
            if item["name"] == "vulnerability-gate":
                item["digest"]["sha256"] = M.digest(self.gate).removeprefix("sha256:")
        self.provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        self.dossier["provenance"] = ev(self.provenance)
        self.blocked(self.dossier)

    def test_extra_duplicate_high_occurrence_exception_blocks(self):
        gate = json.loads(self.gate.read_text())
        gate["acceptedExceptions"].append(dict(gate["acceptedExceptions"][0]))
        self.gate.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        provenance = json.loads(self.provenance.read_text())
        for item in provenance["predicate"]["satco"]["qualificationEvidence"]:
            if item["name"] == "vulnerability-gate":
                item["digest"]["sha256"] = M.digest(self.gate).removeprefix("sha256:")
        self.provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        self.dossier["provenance"] = ev(self.provenance)
        self.blocked(self.dossier)

    def test_tampered_duplicate_high_occurrence_exception_blocks(self):
        gate = json.loads(self.gate.read_text())
        tampered = dict(gate["acceptedExceptions"][0])
        tampered["justification"] = "tampered"
        gate["findings"].append(dict(gate["findings"][0], component="fixture-2"))
        gate["acceptedExceptions"].append(tampered)
        self.gate.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        provenance = json.loads(self.provenance.read_text())
        for item in provenance["predicate"]["satco"]["qualificationEvidence"]:
            if item["name"] == "vulnerability-gate":
                item["digest"]["sha256"] = M.digest(self.gate).removeprefix("sha256:")
        self.provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
        self.dossier["provenance"] = ev(self.provenance)
        self.blocked(self.dossier)

    def test_missing_mandatory_evidence_blocks(self):
        dossier = copy.deepcopy(self.dossier)
        del dossier["sboms"]
        self.blocked(dossier)

    def test_all_designated_artifacts_are_mandatory(self):
        dossier = copy.deepcopy(self.dossier)
        del dossier["artifacts"]["migrations"]
        self.blocked(dossier)

    def test_substituted_evidence_blocks(self):
        self.sboms["backend"].write_text("tampered")
        self.blocked(self.dossier)

    def test_gate_artifact_mismatch_blocks(self):
        self.gate.write_text(json.dumps({
            "result": "PASS", "blockingFindings": [],
            "sourceRevision": REVISION,
            "artifactDigest": "sha256:" + "0" * 64,
            "acceptedExceptions": json.loads(self.exceptions.read_text()),
            "securityDecision": json.loads(self.decision.read_text()),
        }))
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        self.blocked(self.dossier)

    def test_blocking_finding_blocks(self):
        self.gate.write_text(json.dumps({
            "result": "FAIL", "blockingFindings": ["CVE-X"],
            "sourceRevision": REVISION,
            "artifactDigest": M.digest(self.artifacts["backend"]),
            "acceptedExceptions": json.loads(self.exceptions.read_text()),
            "securityDecision": json.loads(self.decision.read_text()),
        }))
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        self.blocked(self.dossier)

    def test_expired_exception_blocks(self):
        self.exceptions.write_text(json.dumps([{
            "status": "active",
            "artifact_digest": M.digest(self.artifacts["backend"]),
            "expires_at": "2026-09-26T00:00:00Z",
        }]))
        self.refresh("exceptions", "high_findings", self.exceptions)
        self.blocked(self.dossier)

    def test_exception_for_other_artifact_blocks(self):
        self.exceptions.write_text(json.dumps([{
            "status": "active", "artifact_digest": "sha256:" + "1" * 64,
            "expires_at": "2026-10-27T00:00:00Z",
        }]))
        self.refresh("exceptions", "high_findings", self.exceptions)
        self.blocked(self.dossier)

    def test_exception_for_other_source_revision_blocks(self):
        records = json.loads(self.exceptions.read_text())
        records[0]["source_revision"] = "c" * 40
        self.exceptions.write_text(json.dumps(records))
        self.refresh("exceptions", "high_findings", self.exceptions)
        self.blocked(self.dossier)

    def test_security_decision_commit_substitution_blocks(self):
        decision = json.loads(self.decision.read_text())
        decision["decisionCommit"] = "c" * 40
        self.decision.write_text(json.dumps(decision))
        self.refresh("exceptions", "security_decision", self.decision)
        self.blocked(self.dossier)

    def test_security_decision_exception_digest_substitution_blocks(self):
        decision = json.loads(self.decision.read_text())
        decision["exceptionEvidenceDigest"] = "sha256:" + "0" * 64
        self.decision.write_text(json.dumps(decision))
        self.refresh("exceptions", "security_decision", self.decision)
        self.blocked(self.dossier)

    def test_missing_security_decision_blocks(self):
        dossier = copy.deepcopy(self.dossier)
        del dossier["exceptions"]["security_decision"]
        self.blocked(dossier)

    def test_gate_security_decision_substitution_blocks(self):
        gate = json.loads(self.gate.read_text())
        gate["securityDecision"]["decisionCommit"] = "c" * 40
        self.gate.write_text(json.dumps(gate))
        self.refresh("security_evidence", "vulnerability_gate", self.gate)
        self.blocked(self.dossier)

    def test_signing_security_decision_substitution_blocks(self):
        signatures = json.loads(self.signatures.read_text())
        signatures["security_decision_commit"] = "c" * 40
        self.signatures.write_text(json.dumps(signatures))
        self.dossier["signature_verification"] = ev(self.signatures)
        self.blocked(self.dossier)

    def test_provenance_source_mismatch_blocks(self):
        data = json.loads(self.provenance.read_text())
        data["predicate"]["buildDefinition"]["externalParameters"]["revision"] = "b" * 40
        self.provenance.write_text(json.dumps(data))
        self.dossier["provenance"] = ev(self.provenance)
        self.blocked(self.dossier)

    def test_sbom_source_mismatch_blocks(self):
        data = json.loads(self.sboms["frontend"].read_text())
        data["metadata"]["properties"][0]["value"] = "b" * 40
        self.sboms["frontend"].write_text(json.dumps(data))
        self.refresh("sboms", "frontend", self.sboms["frontend"])
        self.blocked(self.dossier)

    def test_unsigned_designated_artifact_blocks(self):
        data = json.loads(self.signatures.read_text())
        data["artifacts"] = data["artifacts"][:-1]
        self.signatures.write_text(json.dumps(data))
        self.dossier["signature_verification"] = ev(self.signatures)
        self.blocked(self.dossier)

    def test_pending_approval_only_passes_draft_validation(self):
        dossier = copy.deepcopy(self.dossier)
        dossier["human_release_approval"] = {
            "status": "pending", "reference": "human-release-authority"
        }
        self.blocked(dossier)
        self.assertTrue(M.validate(dossier, NOW, require_approvals=False))

    def test_rejected_approval_always_blocks(self):
        dossier = copy.deepcopy(self.dossier)
        dossier["human_release_approval"] = {
            "status": "rejected", "reference": "human-release-authority"
        }
        self.blocked(dossier, require_approvals=False)

    def test_approved_human_evidence_must_bind_candidate(self):
        payload = json.loads(self.release_approval.read_text())
        payload["source_commit"] = "b" * 40
        self.release_approval.write_text(json.dumps(payload))
        self.dossier["human_release_approval"] = {
            "status": "approved", **ev(self.release_approval)
        }
        self.blocked(self.dossier)

    def test_approved_human_evidence_must_bind_security_decision(self):
        payload = json.loads(self.release_approval.read_text())
        payload["security_decision_commit"] = "c" * 40
        self.release_approval.write_text(json.dumps(payload))
        self.dossier["human_release_approval"] = {
            "status": "approved", **ev(self.release_approval)
        }
        self.blocked(self.dossier)

    def _additional_provenance_fixture(self):
        additional = {}
        for name in (
            "pre-decision-evidence",
            "pre-decision-artifact",
            "pre-decision-run",
            "pre-decision-artifact-api",
        ):
            path = self.path / f"{name}.json"
            path.write_text(json.dumps({"name": name}))
            additional[name] = path

        provenance = json.loads(self.provenance.read_text())
        evidence = provenance["predicate"]["satco"]["qualificationEvidence"]
        evidence.extend(
            {
                "name": name,
                "digest": {
                    "sha256": M.digest(path).removeprefix("sha256:")
                },
            }
            for name, path in additional.items()
        )
        self.provenance.write_text(json.dumps(provenance))
        self.dossier["provenance"] = ev(self.provenance)
        return additional

    def test_additional_provenance_evidence_exact_set_passes(self):
        additional = self._additional_provenance_fixture()
        self.assertTrue(
            M.validate(
                self.dossier,
                NOW,
                additional_provenance_evidence=additional,
            )
        )

    def test_cli_pairs_additional_provenance_descriptor_passes(self):
        additional = self._additional_provenance_fixture()
        descriptors = M.pairs(
            [f"{name}={path}" for name, path in additional.items()]
        )
        self.assertTrue(
            M.validate(
                self.dossier,
                NOW,
                additional_provenance_evidence=descriptors,
            )
        )

    def test_missing_additional_provenance_evidence_blocks(self):
        additional = self._additional_provenance_fixture()
        del additional["pre-decision-run"]
        with self.assertRaisesRegex(
            ValueError, "provenance security-evidence mismatch"
        ):
            M.validate(
                self.dossier,
                NOW,
                additional_provenance_evidence=additional,
            )

    def test_substituted_additional_provenance_evidence_blocks(self):
        additional = self._additional_provenance_fixture()
        substituted = self.path / "substituted.json"
        substituted.write_text(json.dumps({"substituted": True}))
        additional["pre-decision-run"] = substituted
        with self.assertRaisesRegex(
            ValueError, "provenance security-evidence mismatch"
        ):
            M.validate(
                self.dossier,
                NOW,
                additional_provenance_evidence=additional,
            )

    def test_unexpected_additional_provenance_evidence_blocks(self):
        additional = self._additional_provenance_fixture()
        unexpected = self.path / "unexpected.json"
        unexpected.write_text(json.dumps({"unexpected": True}))
        additional["unexpected-evidence"] = unexpected
        with self.assertRaisesRegex(
            ValueError, "provenance security-evidence mismatch"
        ):
            M.validate(
                self.dossier,
                NOW,
                additional_provenance_evidence=additional,
            )

    def test_duplicate_additional_provenance_evidence_name_blocks(self):
        additional = self._additional_provenance_fixture()
        additional["security-decision"] = self.decision
        with self.assertRaisesRegex(
            ValueError, "duplicate provenance evidence name"
        ):
            M.validate(
                self.dossier,
                NOW,
                additional_provenance_evidence=additional,
            )

    def test_release_manifest_example_tracks_required_schema_and_digest_references(self):
        schema = json.loads((ROOT / "ops/release-manifest.v1.schema.json").read_text())
        example = json.loads((ROOT / "ops/release-manifest.example.v1.json").read_text())
        self.assertEqual(set(example), set(schema["required"]))
        self.assertRegex(example["git_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(example["expected_alembic_head"], "e05800000001")
        for name in (
            "sbom_reference",
            "scan_evidence_reference",
            "signing_approver_evidence_reference",
            "release_approval_evidence_reference",
            "provenance_reference",
            "signature_verification_evidence_reference",
            "release_dossier_reference",
        ):
            self.assertRegex(example[name], r"^sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
