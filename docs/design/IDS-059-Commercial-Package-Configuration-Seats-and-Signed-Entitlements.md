# IDS-059 — Commercial Package Configuration, Seats & Signed Entitlements

## 1. Control and authority

Status: **HUMAN ACCEPTED.**

Date: 2026-09-30.

This IDS physicalizes Human-accepted EDS-059 and remains subordinate to the Human-accepted PATCH-059 Discovery and Architecture-059.

It defines implementation design only. It does not authorize migration creation/execution, production-code implementation, database mutation, deployment, release, PATCH-059 closure or PATCH-060.

Current accepted remote baseline at IDS authoring is main commit 7e612141ca007c28effc1d47947b0daef874cb07. Current known sole Alembic head is e05800000001. Implementation preflight must re-verify both repository baseline and sole migration head; any intervening accepted change requires rebase/reconciliation before a PATCH-059 migration is authored.

Human authority remains controlling. AI remains advisory and non-authoritative.

## 2. Physical module topology

PATCH-059 shall extend existing package and authentication boundaries with bounded commercial modules:

Backend new modules:
- app/commercial_entitlements/canonical.py — strict envelope/payload canonical types and JCS boundary;
- app/commercial_entitlements/crypto.py — Ed25519 verification/trust lookup only;
- app/commercial_entitlements/state.py — effective-state and reason-code pure functions;
- app/models/commercial_entitlement.py — current state, activation history and seat assignment persistence;
- app/schemas/commercial_entitlement.py — API schemas;
- app/repositories/commercial_entitlement_repository.py;
- app/repositories/commercial_entitlement_unit_of_work.py;
- app/services/commercial_entitlement_service.py — validation/activation/status;
- app/services/commercial_seat_service.py — assign/release/retain/capacity;
- app/adapters/commercial_entitlement.py — EntitlementDecisionPort implementation;
- app/dependencies/commercial_entitlement.py — trusted deployment/commercial service wiring;
- app/api/v1/routers/commercial_entitlements.py — bounded admin/status routes.

Existing modules extended, not replaced:
- app/ports/discipline_package.py;
- app/enums/discipline_package.py only if bounded reason/state typing requires it without breaking existing enum values;
- app/services/discipline_package_service.py and existing configuration/operation call sites only at the existing entitlement seam;
- app/core/config.py;
- app/main.py router/dependency assembly;
- PATCH-058 refresh-session/step-up service consumed without creating a second auth system.

Frontend:
- OrganizationAdminPage remains the admin shell;
- add bounded CommercialEntitlementPanel and CommercialSeatsPanel components;
- package panels consume backend commercial status but do not make entitlement decisions.

No dynamic plugin loader, customer module import or parallel package registry is introduced.## 3. Canonical entitlement types

canonical.py shall define frozen/strict domain values corresponding exactly to EDS-059.

The wire envelope schema is:
{
  "schema": "satco.commercial-entitlement/v1",
  "key_id": "<bounded>",
  "payload": { ...closed payload... },
  "signature": "<unpadded-base64url>"
}

Payload fields are exactly:
schema_version=1; entitlement_id UUID; revision positive integer; organization_id UUID; deployment_id; issuer; issued_at; not_before; valid_until; grace_until; package_keys; seat_capacity; support_until nullable; baseline_release_sequence; max_release_sequence.

Pydantic API/import models use extra="forbid". Datetimes require explicit timezone and normalize to UTC before domain comparison. seat_capacity, revision and release sequences are >=1. max_release_sequence >= baseline_release_sequence. grace_until - valid_until <= 30 days.

package_keys is a non-empty unique sorted/canonical set drawn only from electrical, instrumentation, control_automation. Core is not accepted as a client package key.

entitlement_key at the existing EntitlementRequest seam remains a bounded server-owned selector; commercial evaluation shall not trust arbitrary client entitlement keys to select a different license.

## 4. JSON canonicalization and signature verification

Implementation shall use RFC 8785 JCS semantics. If the repository has no proven RFC 8785 implementation, Implementation Plan must add one small pinned dependency or a reviewed bounded implementation only after dependency/security review; ad-hoc json.dumps(sort_keys=True) shall not be claimed as RFC 8785.

Import parser must reject duplicate object member names before Pydantic parsing. It must reject invalid UTF-8/non-I-JSON numeric/string forms and unknown envelope/payload members.

crypto.py accepts canonical payload bytes, key_id, signature and immutable trust-store view. Signature is unpadded base64url decoded with strict alphabet/length validation and verified using cryptography Ed25519PublicKey.verify.

The verifier never signs. No private key interface exists in runtime code.

canonical_payload_digest is lowercase sha256 hex of exact JCS payload bytes.

Golden test vectors shall freeze raw JSON input, canonical payload bytes, digest, public key, signature and expected decision.## 5. Verification trust store

New production configuration:
- SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE: required absolute/readable file in production commercial profile;
- SATCO_COMMERCIAL_ENTITLEMENT_ENABLED: explicit boolean, required true for Commercial V1 production profile.

Trust store is a closed JSON document with schema satco.commercial-entitlement-trust/v1 and keys array. Each key contains key_id, algorithm="Ed25519", public_key_base64url, not_before UTC and revoked_at nullable UTC.

Duplicate key_id, unknown fields/algorithm, malformed public key, unreadable file or empty active trust set is startup-fatal when commercial entitlement is enabled in production.

Revoked key rejects entitlement for CONFIGURE/EXECUTE when revoked_at <= authoritative evaluation time. Historical read remains independently authorized.

Trust-store replacement is deployment-governed configuration, not an ordinary browser API. Private key fields are structurally prohibited.

## 6. Persistence tables

Future PATCH-059 migration shall add three bounded tables.

commercial_entitlement_states:
- organization_id UUID FK organizations.id RESTRICT;
- deployment_id varchar bounded;
- entitlement_id UUID;
- accepted_revision bigint;
- canonical_payload_digest char(64);
- key_id varchar bounded;
- issuer varchar bounded;
- issued_at/not_before/valid_until/grace_until/support_until timestamptz;
- package_keys JSONB closed normalized array;
- seat_capacity integer;
- baseline_release_sequence bigint;
- max_release_sequence bigint;
- last_trusted_time timestamptz;
- accepted_at timestamptz;
- accepted_by_user_id integer nullable FK users.id SET NULL;
- time_untrusted_at timestamptz nullable;
- version integer;
- primary key (organization_id, deployment_id);
- checks for positive revision/capacity/sequences, release range, temporal ordering and digest format.

commercial_entitlement_activations:
- id UUID PK;
- organization_id/deployment_id;
- entitlement_id/revision/digest/key_id;
- outcome/reason_code;
- accepted_at/actor_user_id/correlation_id;
- bounded protected raw_envelope JSONB nullable only if Implementation Plan proves retention necessary;
- immutable application semantics: no update/delete service methods.

commercial_seat_assignments:
- organization_id UUID;
- deployment_id;
- user_id integer;
- state enum/string constrained to ASSIGNED, RESERVED, RETAINED;
- assigned_at/assigned_by_user_id;
- updated_at/updated_by_user_id;
- primary key (organization_id, deployment_id, user_id);
- composite FK (user_id, organization_id) -> user_organization_memberships(user_id, organization_id) RESTRICT.

Indexes support organization/deployment status, activation chronology and seat state. No table duplicates email, role, membership-enabled state, package descriptor or engineering facts.## 7. Database locking and transaction contract

CommercialEntitlementUnitOfWork owns one SQLAlchemy Session/transaction per mutation attempt, following existing explicit UoW patterns.

Every entitlement activation and seat mutation first locks commercial_entitlement_states row for the exact Organization+deployment using SELECT ... FOR UPDATE.

Initial activation where no row exists uses a deterministic PostgreSQL transaction-scoped advisory lock derived from a fixed PATCH-059 namespace plus canonical Organization UUID and deployment identifier digest, then rechecks for the row. The exact 64-bit key derivation must be frozen in implementation tests and cannot use Python hash().

Seat capacity count and insert/update occur under the same commercial-state lock. No process-local mutex is authoritative.

Activation history write and current-state advancement commit atomically. Failure rolls back both.

last_trusted_time/time_untrusted transitions that change durable security state use the same locked current-state row.

## 8. Revision, activation and raw-artifact handling

validate operation performs parse/canonical/signature/binding/temporal/package/release-range checks without changing current entitlement state and returns a bounded effect preview.

activate repeats all validation server-side inside mutation transaction; it never trusts a previous preview.

Lower revision -> ROLLBACK_DETECTED. Equal revision with same entitlement_id+digest -> idempotent no-op success. Equal revision conflict -> SAME_REVISION_CONFLICT. Higher valid revision -> atomic successor activation.

Raw envelope is not required for ordinary runtime evaluation. Preferred V1 persistence is no raw_envelope in current state; activation evidence retains only bounded normalized fields/digest/signature key reference unless an accepted Implementation Plan demonstrates a support requirement for encrypted/protected raw retention.

No API resets accepted_revision.

## 9. Trusted-time physical contract

commercial_entitlement_states.last_trusted_time is non-null after first accepted activation.

Evaluation obtains timezone-aware server UTC through an injectable server clock for deterministic tests. If now < last_trusted_time - 5 minutes, service atomically records time_untrusted_at if absent and returns UNAVAILABLE/TIME_UNTRUSTED for CONFIGURE/EXECUTE.

If backward skew is <=5 minutes, evaluation does not lower last_trusted_time. If now advances, last_trusted_time advances monotonically.

Read-heavy entitlement evaluation must not create an unbounded write on every request. Implementation shall persist last_trusted_time at bounded checkpoints: entitlement activation and at most once per configured server-side checkpoint interval, with the interval fixed in code/config and <=5 minutes. In-memory caching may optimize only after durable state has been consulted and cannot be authority across processes.

Recovery from TIME_UNTRUSTED has no ordinary application route. It is an operational recovery command/procedure requiring deployment recovery evidence and shall be separately specified in implementation/operations artifacts before PATCH-060.## 10. Seat lifecycle

ASSIGNED: membership enabled and seat executable subject to all other gates.
RESERVED: membership disabled/removed from executable authority; seat still consumes capacity.
RETAINED: explicit admin choice during over-capacity remediation; executable only if membership currently enabled.

Membership state remains canonical. Seat service re-reads UserOrganizationMembership for every mutation and entitlement execution decision; cached membership state is not authority.

Assign:
- Human admin authority;
- successful has_recent_step_up(auth.session, minutes=10);
- ACTIVE entitlement;
- enabled target membership;
- not over capacity;
- no existing assignment;
- lock state, recount capacity, insert ASSIGNED.

Disable/removal of membership does not require PATCH-059 to mutate canonical membership. At evaluation, an existing assignment with disabled membership behaves non-executable and is represented as reserved-effective. A bounded reconciliation/admin read may materialize RESERVED, but entitlement correctness cannot depend on asynchronous reconciliation.

Release:
- admin + 10-minute recent step-up;
- deletes/releases commercial seat record only;
- never alters membership.

If a previously disabled membership becomes enabled while seat row is RESERVED, it remains non-executable until explicit admin reassignment/reactivation through the accepted seat mutation path; no automatic commercial privilege restoration.

## 11. Over-capacity and retained selection

On higher-revision activation with new seat_capacity below consuming seat count, activation succeeds and state reports OVER_CAPACITY.

Immediately after such activation, no ASSIGNED seat is executable until retained selection is resolved. Admin with recent step-up submits an exact retained user-id set whose size <= capacity and whose users already have consuming seat rows.

Under the state lock, service validates the complete set, marks selected enabled memberships RETAINED, leaves non-selected rows ASSIGNED/RESERVED but non-executable, and commits one deterministic remediation transition.

Subsequent release may reduce consuming count. OVER_CAPACITY resolves only when consuming count <= capacity and executable seat states are unambiguous. IDS does not allow automatic oldest/newest/user-id winner selection.

New assignments remain prohibited while consuming count >= capacity or unresolved over-capacity exists.## 12. Entitlement decision adapter

CommercialEntitlementAdapter implements the existing EntitlementDecisionPort without changing EntitlementRequest shape.

It validates trusted_organization_id and trusted_deployment_id against current state, maps package_key to signed package rights, interprets EntitlementOperation and returns only existing EntitlementDecision values:
- PERMITTED;
- DENIED;
- UNAVAILABLE.

NOT_REQUIRED is prohibited when SATCO_COMMERCIAL_ENTITLEMENT_ENABLED=true.

Reason details remain internal typed CommercialEntitlementReason and are exposed only through authorized status/admin APIs and bounded audit; the narrow Core port remains stable.

HISTORICAL_READ returns PERMITTED from the commercial predicate without requiring package/seat current commercial rights, but callers must already have passed canonical historical resource authorization. This does not grant the resource.

CONFIGURE/EXECUTE require valid effective state, entitled package and seat rules defined by EDS. GRACE CONFIGURE uses a server-owned expansion classifier; arbitrary client flags cannot label an operation non-expanding.

## 13. Existing package service integration

Existing order remains: authenticated Organization context -> resource/owner authorization -> Registry/compatibility -> accepted Organization/Project configuration -> commercial entitlement predicate.

discipline_package_service/configuration/operation code shall receive the commercial adapter through existing dependency wiring. No endpoint may instantiate NonCommercialEntitlementAdapter in production commercial profile.

Organization package configuration PUT must classify requested delta against current configuration before entitlement evaluation. During GRACE, any newly enabled package/selection is denied; removal/non-expanding repair may proceed only where EDS permits.

Operational package EXECUTE must confirm package was configured before valid_until when state is GRACE. IDS requires a durable/configuration audit timestamp already owned by package configuration; if current accepted persistence cannot prove this deterministically, Implementation Plan must add the minimum bounded marker rather than infer from client data.

## 14. Release sequence contract

PATCH-059 adds a server-readable immutable SATCO_RELEASE_SEQUENCE positive integer to governed release metadata/configuration. It must be included in PATCH-058-compatible release evidence before a release can be considered for update eligibility.

At entitlement activation, current installed release sequence must be independently trusted from release metadata and satisfy baseline_release_sequence <= current_sequence <= max_release_sequence. Otherwise activation is rejected with RELEASE_SEQUENCE_OUT_OF_RANGE, except a separately governed upgrade staging flow may validate a future entitlement without activating it.

Update eligibility endpoint accepts no arbitrary trusted candidate metadata from browser. Candidate release sequence must come from server-verified PATCH-058 release evidence/artifact metadata.

Semantic version strings, image tags and filenames are display-only.## 15. API routes and authorization

New router uses existing /api/v1 prefix and these route shapes:

GET /organizations/current/commercial-entitlement
- authorized current Organization member/admin view as frozen by implementation plan;
- bounded status, no raw envelope/signature.

POST /organizations/current/commercial-entitlement/validate
- admin + recent step-up;
- accepts entitlement envelope;
- no persistence except bounded security/audit failure evidence where required;
- returns safe effect preview.

POST /organizations/current/commercial-entitlement/activate
- admin + recent step-up;
- activates after full repeat validation.

GET /organizations/current/commercial-seats
- authorized admin view;
- capacity/count/state and bounded user identifiers/display data derived from canonical User.

POST /organizations/current/commercial-seats/{user_id}
- admin + recent step-up; assign/reactivate.

DELETE /organizations/current/commercial-seats/{user_id}
- admin + recent step-up; release.

PUT /organizations/current/commercial-seats/retained
- admin + recent step-up; exact retained set for over-capacity remediation.

GET /organizations/current/commercial-update-eligibility
- authorized admin view of current installed release and signed bounds.

No API exists for revision reset, time-untrusted clearing, trust-store mutation, private signing or raw key export.

Cookie-authenticated mutations reuse PATCH-058 CSRF protections.

## 16. Reauthentication

Sensitive PATCH-059 browser mutations require has_recent_step_up(auth.session, minutes=10), not merely has_recent_authentication. This means a fresh login without an explicit successful step-up is insufficient for entitlement activation or seat mutation.

The existing /auth/step-up flow and AuthSecurityEvent step_up_success remain authoritative. PATCH-059 creates no new credential challenge.

API error is bounded and consistent with existing PATCH-058 step-up-required semantics.

## 17. API schemas and safe reason codes

Schemas include CommercialEntitlementStatusResponse, CommercialEntitlementValidationRequest/Response, CommercialSeatResponse/ListResponse, CommercialSeatRetainedRequest and CommercialUpdateEligibilityResponse.

Safe public/admin reason vocabulary includes: entitlement_missing, invalid_signature, untrusted_key, revoked_key, organization_mismatch, deployment_mismatch, not_yet_valid, grace, expired, rollback_detected, same_revision_conflict, time_untrusted, package_not_entitled, seat_required, seat_reserved, over_capacity, release_sequence_out_of_range.

Unauthorized users receive existing authorization/protected-not-found behavior before detailed commercial reason codes. No reason code reveals another Organization's entitlement existence.

## 18. Audit integration

Use existing canonical Audit facilities for ordinary admin mutation where they satisfy attribution/correlation requirements. Security-significant signature/trust/rollback/time events may additionally use bounded AuthSecurityEvent-compatible recording.

New commercial audit payloads contain IDs/revision/digest prefix/reason only; never raw entitlement, signature, public/private key material, password/session credentials or engineering content.

Activation/rejection and seat mutation are audited transactionally or through repository-consistent post-commit semantics that cannot falsely record a rolled-back success. Implementation Plan must choose one existing audit pattern and test failure behavior.

## 19. Frontend physical design

OrganizationAdminPage adds a Commercial section.

CommercialEntitlementPanel:
- server status/effective state;
- binding, revision/digest prefix, packages, validity/grace, support/update range;
- validate upload -> effect preview -> explicit activation confirmation;
- step-up-required flow reuses existing PATCH-058 UX.

CommercialSeatsPanel:
- capacity/consuming count;
- ASSIGNED/RESERVED/RETAINED and executable status;
- assign/release;
- over-capacity exact retained selection.

Existing package configuration UI displays backend denial/status and disables obvious prohibited actions for usability, but backend remains authoritative.

No private key/signing UI is shipped. No browser computes authoritative expiry, signature validity, seat count or update eligibility.## 20. Configuration and startup readiness

Settings additions:
SATCO_COMMERCIAL_ENTITLEMENT_ENABLED bool default false for compatibility outside accepted commercial profile;
SATCO_COMMERCIAL_ENTITLEMENT_TRUST_STORE_FILE string;
SATCO_RELEASE_SEQUENCE positive integer/config-derived immutable release metadata reference as finalized by Implementation Plan;
bounded trusted-time checkpoint interval <=300 seconds if configurable.

Production Commercial V1 profile requires entitlement enabled, valid SATCO_DEPLOYMENT_ID, valid trust store, expected migration head and accepted bound entitlement before commercial readiness is green.

Static missing/malformed trust/deployment configuration is startup-fatal. Missing/invalid runtime entitlement allows bounded safe-mode historical access but readiness for commercial CONFIGURE/EXECUTE is red.

Non-production NOT_REQUIRED adapter is allowed only through explicit non-production dependency wiring and tests. Environment misclassification must not silently downgrade production enforcement.

## 21. Migration design

Planned migration identifier: e05900000001, subject to implementation preflight verifying sole parent e05800000001. If sole head differs, this identifier/parent plan must be reconciled before authoring; no branch head is permitted.

Upgrade creates the three bounded tables, constraints, indexes and FKs only. It does not fabricate entitlement or seat rows and does not mutate existing package/engineering facts.

Downgrade may drop PATCH-059 tables only in disposable/non-production qualification. Operational production rollback after commercial activation is prohibited unless a separately accepted recovery plan preserves anti-rollback evidence; migration downgrade is not a licensing rollback mechanism.

Migration qualification uses disposable PostgreSQL only, never real production satco-postgres.

## 22. Implementation file plan

Expected new backend files:
commercial_entitlements package modules; commercial entitlement model/schema/repository/UoW/services/adapter/dependency/router; migration e059...; focused tests.

Expected modified backend files:
core/config.py; main.py; discipline package dependency/service/configuration/operation integration; model exports only where repository conventions require; release metadata/readiness code where release_sequence belongs.

Expected frontend files:
OrganizationAdminPage integration; new commercial panels/API types/client helpers; focused tests.

Expected docs/evidence:
Implementation Plan-059, migration/qualification evidence, security negative vectors, release-sequence evidence update and final review artifacts.

Implementation Plan must enumerate exact files after fresh baseline inventory; IDS does not authorize edits yet.

## 23. Deterministic test inventory

Backend unit vectors:
JCS/Ed25519 golden vector; duplicate keys; unknown fields; invalid base64/signature; trust key lifecycle; time boundaries/skew; revision conflict; package rights; seat state machine; release range.

DB/service vectors:
fresh migration/sole head; first activation advisory lock; concurrent activation; concurrent last-seat assignment; reserved membership; explicit reactivation; capacity reduction/retained selection; audit rollback; trusted-time persistence.

API/security vectors:
tenant/role negatives; protected-not-found; step-up required; CSRF; entitlement validate vs activate repeat validation; safe reason codes/redaction; no reset/trust mutation endpoints.

Integration vectors:
all seven non-empty E/I/C combinations; ACTIVE/GRACE/EXPIRED/INVALID/TIME_UNTRUSTED; GRACE pre-existing configuration proof; historical read without seat; entitlement cannot override canonical denial; production no NOT_REQUIRED fallback.

Frontend:
status rendering; server-time display; upload preview/confirm; step-up UX; seat remediation; backend denial remains authoritative.

Release/recovery:
below/at/above sequence; rollback entitlement; same revision conflict; clock rollback; restored DB older than recovery anchor blocks execution.

## 24. Acceptance and implementation gates

IDS acceptance requires independent review showing no open Critical/Major finding and explicit Human IDS acceptance.

Only after IDS acceptance may a separate Implementation Plan-059 be authored. Implementation Plan acceptance is required before production-code or migration edits.

Implementation must use an isolated worktree/branch from verified current origin/main, preserve unrelated dirty work, use disposable DB qualification and never mutate real port-5432 satco-postgres.

Implementation completion does not itself close PATCH-059. Deterministic qualification, security review, Human acceptance and closure remain separate gates.

PATCH-060 remains NOT STARTED / NOT AUTHORIZED.

## 25. Governance disposition

Independent IDS Review completed with Critical 0 / Major 0 / Minor 0.

On 2026-09-30, the Human Authority explicitly accepted IDS-059. This acceptance authorizes progression to a separately governed Implementation Plan-059 candidate only. It does not authorize migration creation/execution, product-code implementation, deployment, release, closure or PATCH-060.

Human authority remains controlling. AI remains advisory and non-authoritative.

**IDS-059: HUMAN ACCEPTED.**