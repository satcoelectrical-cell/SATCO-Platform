import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE = ROOT / "ops/scripts/patch058-vulnerability-gate.py"
PROVENANCE = ROOT / "ops/scripts/patch058-provenance.py"
SBOM = ROOT / "ops/scripts/patch058-sbom.py"
EXCEPTION_VALIDATOR = ROOT / "ops/scripts/validate-high-exceptions.sh"
ARTIFACT_DIGEST = "sha256:" + "a" * 64
SOURCE_REVISION = "1" * 40
DECISION_COMMIT = "2" * 40
EVALUATED_AT = "2026-09-27T00:00:00Z"


class SupplyChainTests(unittest.TestCase):
    def write_reports(self, directory, trivy=None, pip=None):
        trivy_path = directory / "trivy.json"
        pip_path = directory / "pip-audit.json"
        trivy_path.write_text(json.dumps({"Results": trivy or []}))
        pip_path.write_text(json.dumps({"dependencies": pip or []}))
        npm_path = directory / "npm-audit.json"
        npm_path.write_text(json.dumps({"vulnerabilities": {}}))
        return trivy_path, pip_path, npm_path

    def exception(self, **overrides):
        record = {
            "finding_id": "PYSEC-TEST-1",
            "severity": "HIGH",
            "source": "pip-audit",
            "source_revision": SOURCE_REVISION,
            "artifact_digest": ARTIFACT_DIGEST,
            "rationale": "No affected algorithm is reachable.",
            "compensating_controls": "HS256-only configuration and regression tests.",
            "scope": "Exact backend candidate artifact only.",
            "approver_id": "human-security-authority",
            "approved_at": "2026-09-26T00:00:00Z",
            "expires_at": "2026-09-28T00:00:00Z",
            "retest_condition": "Dependency or algorithm use changes.",
            "retest_reference": "PATCH-058-D-test",
            "retest_result": "pass",
            "status": "active",
        }
        record.update(overrides)
        return record

    def run_gate(self, trivy=None, pip=None, exceptions=None, omit=None,
                 source_revision=SOURCE_REVISION,
                 expected_decision_commit=None, decision_overrides=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = pathlib.Path(temporary.name)
        trivy_path, pip_path, npm_path = self.write_reports(directory, trivy, pip)
        output = directory / "gate.json"
        exception_path = directory / "exceptions.json"
        exception_records = exceptions or []
        exception_path.write_text(json.dumps(exception_records))
        external_decision = bool(exception_records)
        decision = {
            "schemaVersion": "PATCH-058-security-decision-v1",
            "mode": "post-build-human-decision" if external_decision else "none",
            "candidateRevision": source_revision,
            "artifactDigest": ARTIFACT_DIGEST,
            "exceptionEvidenceDigest": "sha256:" + hashlib.sha256(
                exception_path.read_bytes()
            ).hexdigest(),
            "decisionCommit": DECISION_COMMIT if external_decision else None,
            "decisionRef": "refs/heads/patch-058-security-decisions",
        }
        decision.update(decision_overrides or {})
        decision_path = directory / "security-decision.json"
        decision_path.write_text(json.dumps(decision))
        supplied_commit = (
            DECISION_COMMIT if external_decision else ""
        ) if expected_decision_commit is None else expected_decision_commit
        command = [
            "python3", str(GATE),
            "--trivy-json", str(directory / "missing.json" if omit == "trivy" else trivy_path),
            "--pip-audit-json", str(directory / "missing.json" if omit == "pip" else pip_path),
            "--npm-audit-json", str(directory / "missing.json" if omit == "npm" else npm_path),
            "--source-revision", source_revision,
            "--artifact-digest", ARTIFACT_DIGEST,
            "--exceptions", str(exception_path),
            "--security-decision-evidence", str(
                directory / "missing-decision.json" if omit == "decision" else decision_path
            ),
            "--security-decision-commit", supplied_commit,
            "--evaluated-at", EVALUATED_AT,
            "--output", str(output),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        return result, json.loads(output.read_text())

    @staticmethod
    def trivy_finding(severity="HIGH"):
        return [{"Target": "candidate", "Vulnerabilities": [{
            "VulnerabilityID": "CVE-TEST-1", "Severity": severity,
            "PkgName": "pkg", "InstalledVersion": "1.0",
        }]}]

    @staticmethod
    def pip_finding():
        return [{"name": "ecdsa", "version": "0.19.2", "vulns": [{"id": "PYSEC-TEST-1"}]}]

    def test_clean_reports_pass_and_emit_bound_evidence(self):
        result, evidence = self.run_gate()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(evidence["result"], "PASS")
        self.assertEqual(evidence["artifactDigest"], ARTIFACT_DIGEST)
        self.assertEqual(
            {item["source"] for item in evidence["reports"]},
            {"npm-audit", "pip-audit", "trivy"},
        )

    def test_critical_is_never_excepted(self):
        exception = self.exception(source="trivy", finding_id="CVE-TEST-1")
        result, evidence = self.run_gate(self.trivy_finding("CRITICAL"), exceptions=[exception])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(evidence["blockingFindings"][0]["severity"], "CRITICAL")

    def test_high_without_exception_fails_closed(self):
        result, evidence = self.run_gate(pip=self.pip_finding())
        self.assertEqual(result.returncode, 3)
        self.assertEqual(evidence["result"], "BLOCK")

    def test_exact_high_exception_passes(self):
        result, evidence = self.run_gate(pip=self.pip_finding(), exceptions=[self.exception()])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(evidence["acceptedExceptions"]), 1)

    def test_exception_for_another_digest_fails(self):
        result, _ = self.run_gate(
            pip=self.pip_finding(),
            exceptions=[self.exception(artifact_digest="sha256:" + "b" * 64)],
        )
        self.assertEqual(result.returncode, 2)

    def test_exception_for_another_source_fails(self):
        result, _ = self.run_gate(
            pip=self.pip_finding(),
            exceptions=[self.exception(source_revision="3" * 40)],
        )
        self.assertEqual(result.returncode, 2)

    def test_exception_for_another_scanner_or_finding_fails(self):
        for override in ({"source": "trivy"}, {"finding_id": "PYSEC-OTHER"}):
            with self.subTest(override=override):
                result, _ = self.run_gate(
                    pip=self.pip_finding(), exceptions=[self.exception(**override)]
                )
                self.assertEqual(result.returncode, 2)

    def test_exception_severity_substitution_fails(self):
        result, _ = self.run_gate(
            pip=self.pip_finding(),
            exceptions=[self.exception(severity="CRITICAL")],
        )
        self.assertEqual(result.returncode, 2)

    def test_wrong_security_decision_commit_fails(self):
        result, evidence = self.run_gate(
            pip=self.pip_finding(), exceptions=[self.exception()],
            expected_decision_commit="3" * 40,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("security-decision commit mismatch", evidence["error"])

    def test_missing_security_decision_evidence_fails(self):
        result, _ = self.run_gate(
            pip=self.pip_finding(), exceptions=[self.exception()], omit="decision"
        )
        self.assertEqual(result.returncode, 2)

    def test_exception_digest_substitution_fails(self):
        result, _ = self.run_gate(
            pip=self.pip_finding(), exceptions=[self.exception()],
            decision_overrides={"exceptionEvidenceDigest": "sha256:" + "0" * 64},
        )
        self.assertEqual(result.returncode, 2)

    def test_exception_schema_and_shell_policy_require_exact_source_revision(self):
        schema = json.loads(
            (ROOT / "ops/high-vulnerability-exceptions.v1.schema.json").read_text()
        )
        self.assertIn("source_revision", schema["items"]["required"])
        self.assertEqual(
            schema["items"]["properties"]["source_revision"]["pattern"],
            "^[0-9a-f]{40}$",
        )
        record = self.exception(expires_at="2026-10-27T07:58:25Z")
        self.assertEqual(set(record), set(schema["items"]["required"]))
        with tempfile.TemporaryDirectory() as raw:
            path = pathlib.Path(raw) / "exceptions.json"
            path.write_text(json.dumps([record]))
            environment = os.environ | {
                "SATCO_HIGH_EXCEPTION_FILE": str(path),
                "SATCO_ARTIFACT_DIGEST": ARTIFACT_DIGEST,
                "SATCO_SOURCE_REVISION": SOURCE_REVISION,
            }
            accepted = subprocess.run(
                ["sh", str(EXCEPTION_VALIDATOR)], env=environment,
                text=True, capture_output=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            environment["SATCO_SOURCE_REVISION"] = "3" * 40
            rejected = subprocess.run(
                ["sh", str(EXCEPTION_VALIDATOR)], env=environment,
                text=True, capture_output=True,
            )
            self.assertNotEqual(rejected.returncode, 0)

    def test_expired_or_failed_retest_exception_fails(self):
        expired, _ = self.run_gate(
            pip=self.pip_finding(), exceptions=[self.exception(expires_at="2026-09-27T00:00:00Z")]
        )
        failed, _ = self.run_gate(
            pip=self.pip_finding(), exceptions=[self.exception(retest_result="fail")]
        )
        self.assertEqual((expired.returncode, failed.returncode), (2, 2))

    def test_missing_mandatory_scanner_report_fails(self):
        for scanner in ("trivy", "pip", "npm"):
            with self.subTest(scanner=scanner):
                result, evidence = self.run_gate(omit=scanner)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(evidence["result"], "BLOCK")

    def test_workflows_bind_and_revalidate_human_high_exceptions(self):
        security = (ROOT / ".github/workflows/patch058-security.yml").read_text()
        signing = (ROOT / ".github/workflows/patch058-sign-release.yml").read_text()
        exception_path = "resolved-high-exceptions.json"
        self.assertIn(f"--exceptions {exception_path}", security)
        self.assertIn(f"--evidence high-exceptions={exception_path}", security)
        self.assertIn("--evidence security-decision=security-decision.json", security)
        self.assertIn("source_revision", (ROOT / "ops/high-vulnerability-exceptions.v1.schema.json").read_text())
        self.assertIn("high-exception-validation.exit", security)
        self.assertIn('test "$(cat high-exception-validation.exit)" = "0"', security)
        self.assertIn("SATCO_HIGH_EXCEPTION_FILE=evidence/resolved-high-exceptions.json", signing)
        self.assertIn("--evidence high-exceptions=evidence/resolved-high-exceptions.json", signing)
        self.assertIn("--evidence security-decision=evidence/security-decision.json", signing)

    def test_push_cannot_silently_consume_external_human_exceptions(self):
        security = (ROOT / ".github/workflows/patch058-security.yml").read_text()
        self.assertIn('if [ "$GITHUB_EVENT_NAME" != "workflow_dispatch" ]', security)
        self.assertIn('test -z "$decision_commit"', security)
        self.assertIn('test "$GITHUB_REF" = "refs/heads/patch-058"', security)
        self.assertIn("printf '[]\\n' > resolved-high-exceptions.json", security)
        self.assertNotIn(
            "--exceptions ops/security/patch058-high-exceptions.json", security
        )
        self.assertIn(
            "refs/heads/patch-058-security-decisions", security
        )
        self.assertIn("git merge-base --is-ancestor", security)

    def provenance_command(self, command, directory, statement=None):
        artifact = directory / "artifact.tar"
        sbom = directory / "sbom.cdx.json"
        lock = directory / "lock"
        scan = directory / "scan.json"
        for path, value in ((artifact, "artifact"), (sbom, "sbom"), (lock, "lock"), (scan, "scan")):
            if not path.exists():
                path.write_text(value)
        args = [
            "python3", str(PROVENANCE), command,
            "--repository", "satcoelectrical-cell/SATCO-Platform",
            "--revision", "1" * 40,
            "--workflow", "patch058-security.yml",
            "--release-id", "patch058-test-1",
            "--artifact", f"backend={artifact}",
            "--sbom", f"backend={sbom}",
            "--input", f"backend-lock={lock}",
            "--evidence", f"container-scan={scan}",
        ]
        if command == "generate":
            args += ["--generated-at", EVALUATED_AT, "--output", str(directory / "provenance.json")]
        else:
            args += ["--statement", str(statement or directory / "provenance.json")]
        return subprocess.run(args, cwd=ROOT, text=True, capture_output=True), artifact, sbom

    def test_provenance_is_in_toto_slsa_and_verifies_exact_bytes(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = pathlib.Path(raw)
            generated, artifact, _ = self.provenance_command("generate", directory)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            statement = json.loads((directory / "provenance.json").read_text())
            self.assertEqual(statement["_type"], "https://in-toto.io/Statement/v1")
            self.assertEqual(statement["predicateType"], "https://slsa.dev/provenance/v1")
            self.assertEqual(
                statement["subject"][0]["digest"],
                {"sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()},
            )
            verified, _, _ = self.provenance_command("verify", directory)
            self.assertEqual(verified.returncode, 0, verified.stderr)

    def test_provenance_rejects_changed_artifact_or_sbom(self):
        for changed_name in ("artifact.tar", "sbom.cdx.json"):
            with self.subTest(changed_name=changed_name), tempfile.TemporaryDirectory() as raw:
                directory = pathlib.Path(raw)
                generated, _, _ = self.provenance_command("generate", directory)
                self.assertEqual(generated.returncode, 0)
                (directory / changed_name).write_text("changed")
                verified, _, _ = self.provenance_command("verify", directory)
                self.assertEqual(verified.returncode, 2)

    def test_sbom_binding_rejects_changed_artifact(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = pathlib.Path(raw)
            artifact = directory / "artifact.tar"
            artifact.write_text("artifact")
            source = directory / "raw.cdx.json"
            source.write_text(json.dumps({
                "bomFormat": "CycloneDX", "specVersion": "1.6",
                "metadata": {"timestamp": EVALUATED_AT}, "components": [],
            }))
            bound = directory / "bound.cdx.json"
            identity = [
                "--artifact", str(artifact), "--artifact-name", "backend",
                "--revision", "1" * 40, "--syft-version", "1.33.0",
            ]
            bind = subprocess.run(
                ["python3", str(SBOM), "bind", *identity,
                 "--input", str(source), "--output", str(bound)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(bind.returncode, 0, bind.stderr)
            verify = subprocess.run(
                ["python3", str(SBOM), "verify", *identity, "--sbom", str(bound)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr)
            artifact.write_text("changed")
            mismatch = subprocess.run(
                ["python3", str(SBOM), "verify", *identity, "--sbom", str(bound)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(mismatch.returncode, 2)

    def test_workflows_pin_actions_and_minimize_permissions(self):
        workflow_paths = sorted((ROOT / ".github/workflows").glob("patch058-*.yml"))
        self.assertEqual(len(workflow_paths), 3)
        for path in workflow_paths:
            text = path.read_text()
            self.assertNotRegex(text, r"uses:\s+[^\s]+@v\d")
            self.assertNotIn("permissions: write-all", text)
        quality = (ROOT / ".github/workflows/patch058-quality.yml").read_text()
        security = (ROOT / ".github/workflows/patch058-security.yml").read_text()
        signing = (ROOT / ".github/workflows/patch058-sign-release.yml").read_text()
        self.assertNotIn("id-token: write", quality + security)
        self.assertIn("id-token: write", signing)

    def test_quality_workflow_isolates_migrations_from_real_database(self):
        text = (ROOT / ".github/workflows/patch058-quality.yml").read_text()
        self.assertIn("alembic upgrade head", text)
        self.assertIn("127.0.0.1:55432", text)
        self.assertNotIn('ports: ["5432:5432"]', text)
        self.assertNotIn("satco-postgres", text)

    def test_security_workflow_has_all_mandatory_d_tools_and_digest_pins(self):
        text = (ROOT / ".github/workflows/patch058-security.yml").read_text()
        toolchain = (ROOT / "ops/security/toolchain.env").read_text()
        for token in ("pip-audit", "npm audit", "semgrep", "gitleaks", "trivy", "syft", "cyclonedx-json"):
            self.assertIn(token, text.lower())
        self.assertGreaterEqual(len(re.findall(r"@sha256:[0-9a-f]{64}", text + toolchain)), 3)
        self.assertIn("patch058-vulnerability-gate.py", text)
        self.assertIn("patch058-provenance.py generate", text)
        self.assertIn("patch058-provenance.py verify", text)

    def test_security_workflow_provisions_pinned_oci_capable_builder(self):
        text = (ROOT / ".github/workflows/patch058-security.yml").read_text()
        self.assertIn(
            "docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069",
            text,
        )
        self.assertIn('version: "v0.35.0"', text)
        self.assertIn("driver: docker-container", text)
        self.assertIn(
            "image=moby/buildkit@sha256:"
            "6c2fa84a6b61ccd72899dde4239f8d5717f05f9a8ca6f3cad185fb1a95a94de3",
            text,
        )
        self.assertIn("BUILDX_DRIVER: ${{ steps.buildx.outputs.driver }}", text)
        self.assertIn('test "$BUILDX_DRIVER" = "docker-container"', text)
        self.assertIn("docker buildx inspect --bootstrap", text)
        self.assertIn(
            'source_epoch="$(git show -s --format=%ct "$GITHUB_SHA")"',
            text,
        )
        self.assertIn('export SOURCE_DATE_EPOCH="$source_epoch"', text)
        self.assertIn('--build-arg SOURCE_DATE_EPOCH="$source_epoch"', text)
        dockerfile = (ROOT / "backend/Dockerfile.production").read_text()
        self.assertIn("ARG SOURCE_DATE_EPOCH", dockerfile)
        self.assertIn(
            '/etc /etc/passwd /etc/passwd- /etc/group /etc/group-',
            dockerfile,
        )
        self.assertIn(
            "--output type=oci,dest=backend-image.oci.tar,"
            "rewrite-timestamp=true backend",
            text,
        )
        dockerignore = (ROOT / "backend/.dockerignore").read_text()
        for pattern in (
            "**/__pycache__/",
            "**/*.py[cod]",
            ".pytest_cache/",
            ".venv/",
        ):
            self.assertIn(pattern, dockerignore)
        self.assertLess(
            text.index("Set up pinned OCI-capable Buildx builder"),
            text.index("Build exact backend and frontend artifacts"),
        )

    def test_signing_workflow_is_human_protected_and_identity_constrained(self):
        text = (ROOT / ".github/workflows/patch058-sign-release.yml").read_text()
        self.assertIn("environment: patch058-protected-release", text)
        self.assertIn('rule.get("type") == "required_reviewers"', text)
        self.assertIn('prevent_self_review") is True', text)
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("\n  push:", text)
        self.assertIn("cosign sign-blob", text)
        self.assertIn("cosign attest-blob", text)
        self.assertIn("cosign verify-blob", text)
        self.assertIn("cosign verify-blob-attestation", text)
        self.assertIn("--certificate-identity-regexp", text)
        self.assertIn("--certificate-oidc-issuer", text)
        self.assertNotIn("COSIGN_PASSWORD", text)
        # Negative signing-authorization contract: no automatic trigger or unprotected OIDC authority.
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("\n  push:", text)
        self.assertIn("permissions: {}", text)
        self.assertEqual(text.count("id-token: write"), 1)
        self.assertIn("environment: patch058-protected-release", text)
        # Negative identity/digest contract: exact source/artifact and signer identity are re-verified.
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXPECTED_SOURCE_SHA"', text)
        self.assertIn('test "$actual_digest" = "$EXPECTED_BACKEND_DIGEST"', text)
        self.assertIn("security_decision_commit:", text)
        self.assertIn("EXPECTED_SECURITY_DECISION_COMMIT", text)
        self.assertIn("git merge-base --is-ancestor", text)
        self.assertIn("evidence/security-decision.json", text)
        self.assertIn('--certificate-github-workflow-sha "$GITHUB_SHA"', text)
        self.assertIn('--certificate-identity-regexp "$identity"', text)
        # Every artifact named by provenance and the dossier contract is signed,
        # attested and verified under the same protected trust boundary.
        for artifact in (
            "backend-image.oci.tar",
            "frontend-dist.tar",
            "migration-set.tar",
        ):
            self.assertIn(artifact, text)
        self.assertIn("signature-verification-summary.json", text)
        self.assertIn("human-signing-authorization.json", text)
        self.assertIn("GitHub protected Environment: patch058-protected-release", text)


if __name__ == "__main__":
    unittest.main()
