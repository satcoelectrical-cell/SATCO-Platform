# PATCH-051 WP051-MAJ-01 focused independent implementation re-review

## Scope

This is a fresh focused re-review of the implemented Registry-standing and descriptor-immutability correction. It reviews the actual source, M6, isolated PostgreSQL result, API/Workspace/frontend boundary, role boundary, and focused tests. It does not reopen Architecture/ADR governance, rewrite M1--M5, authorize M7, or introduce PATCH-052 scope.

## Findings

### Descriptor and digest boundaries

PASS. Immutable descriptor content excludes standing, while `DescriptorRegistrationV1` carries it as release membership. The semantic tests prove that changing only P@1.0.0 standing preserves descriptor canonical bytes and `DescriptorDigest`, changes `RegistryDigest`, and preserves SelectedSet, Profile, and Combination digests. No descriptor rehash or historical provenance rewrite is present.

### Registry and persistence

PASS. Registry assembly exposes membership standings; the installer persists them only on memberships; parity/readiness independently verify them; and compatibility/current eligibility use membership rather than descriptor state. The runtime Registry projection remains read-only. The installer-only write boundary and the fixed restricted runtime/installer role declarations were directly inspected.

### M6 and PostgreSQL proof

PASS. M6 has the accepted revision and parent, refuses non-empty or referenced state, verifies the membership standing check/immutable trigger, adds only the accepted index, and drops only descriptor standing. Fresh base through M6 bootstrap was observed on the authorized disposable database. Focused migration tests prove M5-to-M6 success on empty state, unsafe M5 and M6 failure, downgrade, and re-upgrade convergence. Final schema inspection shows membership ownership, the exact index, and no descriptor standing.

### API, effective state, and frontend

PASS. Supported package responses derive standing from current membership. Configuration and Workspace paths require executable membership for new selection/creation, while historical-read-only resolution preserves interpretation and blocks new operational behavior. Project pins and Workspace identity remain exact and unchanged. The frontend consumes server-derived effective state and passed its full test/typecheck/build suite.

### Security and authority

PASS. Standing is an eligibility predicate only; it provides no tenant visibility, data authorization, entitlement, execution authority, or Human authority. Tenant and authorization-before-disclosure vectors passed. The only database mutation was the expressly authorized disposable test database; the temporary test bootstrap owner was local to that cluster.

## Review counts

Critical: **0**

Major: **0**

Minor: **0**

Observation: **1** — the backend test image does not mount the repository `postgres/` directory, so the role-bootstrap source test is not runnable inside that image without an explicit root mount. Direct source inspection verified the assertions. This is a pre-existing test-harness limitation and does not alter the implementation verdict.

## Verdict

The actual implementation satisfies the accepted boundary and migration safety requirements. No Critical or Major finding remains, and no additional migration or Architecture/ADR change is required.

WP051-MAJ-01:
RESOLVED / CLOSED

PATCH-051 REGISTRY-STANDING REMEDIATION:
PASS / ACCEPTED / COMPLETE
