# PATCH-058 Checkpoint D — High-Finding Human Decision Package

Status: HUMAN DECISION REQUIRED — NO EXCEPTION GRANTED
Date: 2026-09-27
Candidate HEAD: `71be9da02e12b6d4323fa07d8b31a5774ebf8a45`

## Purpose and authority boundary

This package reduces the current scanner output to distinct High-finding identities for Human review. It does **not** accept risk, create an exception, authorize signing, approve release, or advance Checkpoint E.

Current evidence contains 45 Trivy High occurrences representing 9 distinct CVE identities, plus one `pip-audit` High-process finding. `npm audit` reports zero findings. No Critical finding is present in the current Trivy report.

The vulnerability gate remains fail-closed. Any accepted High exception must satisfy the governed schema, bind to the exact candidate artifact digest, have a Human approver, a bounded approval/expiry window, compensating controls, and a passing retest.

## Application dependency finding

### PYSEC-2026-1325 / ecdsa 0.19.2

`pip-audit` reports `PYSEC-2026-1325` with no fixed release. Trivy independently reports `CVE-2024-23342` for the same installed `ecdsa==0.19.2` dependency and also reports no fixed version.

Repository evidence: `python-jose[cryptography]` pulls `ecdsa`; SATCO's configured JWT algorithm is `HS256`, and the reviewed token encode/decode surface constrains operations to `settings.ALGORITHM`. No application ECDSA signing or ECDH path has been identified in the inspected authentication surface.

Disposition for Human decision: applicability appears bounded by the current HS256-only configuration, but the finding remains High under PATCH-058 policy. AI has not accepted it.
## Base-image High identities

The exact backend artifact contains these eight additional distinct High CVE identities from Debian/runtime packages. The current Trivy evidence reports no fixed version for any of them:

- `CVE-2025-69720` — ncurses packages: `libncursesw6`, `libtinfo6`, `ncurses-base`, `ncurses-bin`.
- `CVE-2026-16742` — systemd packages: `libsystemd0`, `libudev1`.
- `CVE-2026-54369` — `libacl1`.
- `CVE-2026-76642` — util-linux family; reported across nine installed package records.
- `CVE-2026-78408` — util-linux family; reported across the same package family.
- `CVE-2026-78409` — util-linux family; reported across the same package family.
- `CVE-2026-78410` — util-linux family; reported across the same package family.
- `CVE-2026-9538` — `perl-base`.

These package-level repetitions explain why 45 Trivy High occurrences reduce to nine distinct Trivy CVE identities rather than 45 independent risk decisions.

## Required next gate

Before any Human exception is requested, each distinct base-image CVE must be reviewed for runtime reachability/applicability and available remediation against the exact candidate image. Evidence should distinguish scanner facts from repository/runtime inference.

If remediation is available without violating the accepted PATCH-058 boundary, remediate and rebuild/re-scan instead of excepting. If no remediation is available and a High remains applicable or conservatively unresolved, prepare an exact-artifact-digest-bound exception record for explicit Human approval.

Until that Human decision exists, Checkpoint D remains **NOT READY**. No signing, release approval, Checkpoint E progression, commit, push, deployment, PATCH-059, or PATCH-060 progression is authorized.
## Runtime applicability evidence

The qualified backend image runs as `satco` (`uid=999`, `gid=999`) rather than root. Runtime probing reports `CapEff=0000000000000000`.

Repository search found no application or migration execution path invoking ncurses/`infocmp`, systemd/udev administration, ACL mutation, `mount`, `nsenter`, Perl `Archive::Tar`, ECDSA, or ECDH. String matches for `mounted_on` and similar terms are engineering-domain vocabulary, not operating-system mount execution.

The image does contain several affected utilities/libraries. Presence is therefore not being treated as absence of risk. Direct runtime probes under the configured application user showed `mount` rejected for lack of superuser privilege and `nsenter` rejected with `Operation not permitted`.

The JWT surface remains configured to `HS256`; encode/decode operations use `settings.ALGORITHM`, and decode constrains accepted algorithms to that configured value. The `ecdsa` Python module remains installed/importable through the dependency graph, so scanner evidence is retained even though no reviewed SATCO ECDSA execution path was found.

These observations are compensating/applicability evidence only. They do not downgrade scanner severity and do not constitute Human risk acceptance.
## Candidate Human disposition

On the present evidence, automated remediation is not established for the remaining High findings: the current Trivy report supplies no fixed version for the nine Trivy CVE identities, and `pip-audit` supplies no fixed release for `PYSEC-2026-1325`.

The evidence supports presenting the unresolved set for explicit Human exception review rather than silently passing the gate. Any exception record must preserve the scanner identifiers and affected components, bind to the exact backend artifact digest recorded in the governed evidence, identify the Human approver, state rationale and compensating controls, and use a bounded expiry/retest window.

Recommended compensating controls for Human consideration are limited to controls already evidenced by this candidate: non-root runtime, zero effective Linux capabilities, current HS256-only JWT configuration, absence of reviewed application invocation paths for the affected privileged utilities/features, and continued fail-closed rescanning before release/retest.

No exception record has been created by this package. The next action is an explicit Human accept/reject decision on whether these unresolved High findings may receive a bounded exception for this exact candidate artifact.