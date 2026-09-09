# PATCH-052 Context and Evidence Declaration-Binding Reconciliation

## Status, authority, and boundary

| Field | Value |
|---|---|
| Finding | `B3-052-MAJ-01` |
| Human authority | **PATCH-052 B3-052-MAJ-01 focused design/persistence reconciliation: GRANTED** |
| Result | **PASS / ACCEPTED / COMPLETE** |
| Current source Alembic head | `e05200000001` |
| Persistence verdict | **ONE BOUNDED ADDITIVE MIGRATION REQUIRED** |
| Proposed correction | `e05200000002`, `down_revision = e05200000001` |
| Production/test/migration execution authority | NOT GRANTED |
| Batch 3 | INCOMPLETE / NOT YET ACCEPTED |
| Batch 4 / PATCH-053 | NOT STARTED / NOT AUTHORIZED |

This is an append-only downstream clarification of the already accepted
PATCH-052 semantics. It preserves the historical Batch-3 failure and review.
It creates or executes no migration, changes no production or test source,
does not accept Batch 3, and introduces no Batch-4 or PATCH-053 behavior.

## Reconciled finding and root cause

The descriptor already distinguishes three related identities:

- a Context contribution `{base_id}.context`;
- an engineering input `{base_id}.input`; and
- for Evidence inputs, an Evidence requirement `{evidence_requirement_id}`.

Deliverable `required_input_ids` name engineering-input declarations. The
retained Project configuration selection already fixes the exact package
version and descriptor digest, but neither the Context owner nor the Evidence
owner retains a relation from an authorized source item to one of those exact
inputs. `source_key`, `source_reference`, `supported_fact`, owner kind/type,
row order, and current Workspace state are not declaration identity.

The withheld Context-evaluation, readiness, and package-transition routes
were therefore correct. Implementing them without a durable association would
have fabricated provenance and made later interpretation depend on mutable
current configuration.

## Options and minimum identity decision

| Option | Decision |
|---|---|
| A — store only `declaration_id` | Rejected. Declaration IDs are validated within an immutable descriptor contribution collection and can recur across package versions. An ID alone does not identify the retained descriptor selected for the Project. |
| B — put the package origin triple on Context/Evidence | Rejected. Architecture-052 and EDS-052 explicitly keep Context and Evidence independent and say consumption does not give either aggregate package origin. It would also be unable to represent multiple explicit uses without duplicating the source. |
| C — declaration plus retained configuration provenance | Accepted, expressed as an immutable association rather than aggregate origin. |
| D — reuse an existing immutable governed reference | Accepted as part of C. The existing `(project_id, configuration_revision, package_key)` Project selection is the retained reference and derives PackageVersion and DescriptorDigest. |
| E — infer from owner fields or current state | Rejected. No existing Context/Evidence field is an exact declaration reference; inference is prohibited. |

The minimum declaration target stored by both binding relations is the exact
`EngineeringInputDeclarationV1.id`. The full durable target is:

```text
(project_id,
 project_configuration_revision,
 package_key,
 input_declaration_id)
```

The first three fields are an existing restrictive reference to
`project_package_configuration_selections`. That retained row derives
PackageVersion and DescriptorDigest. The retained Project configuration
revision derives RegistryDigest and profile/combination identity. The retained
immutable descriptor derives the input version and its target declaration.
None of those derivable values is copied to a binding row.

For a Context input, the selected descriptor must contain exactly one input
whose `id=input_declaration_id`, `source_kind=context`, and whose
`input_type_id` equals exactly one Context contribution's `context_kind_id`.
That contribution is the authoritative Context declaration.

For an Evidence input, the selected descriptor must contain exactly one input
whose `id=input_declaration_id`, `source_kind=evidence`, and whose
`input_type_id` equals exactly one Evidence requirement's `id`. That
requirement is the authoritative Evidence declaration. Unknown, absent,
duplicate, cross-package, or wrong-source mappings fail closed.

Thus an input ID is package-scoped and descriptor-versioned through the
retained selection. It is not globally, release, or current-Workspace scoped.

## Context binding contract

### Owner and location

The binding belongs to a new immutable Context-owner association from an
`EngineeringContextSubjectReference` to an exact package input. It does not
belong on the Context fact/value payload and is not package origin.

The subject reference is essential. A Context aggregate may name more than
one subject, while PATCH-052 requires each Object-scoped occurrence to be
evaluated independently and forbids one Object from satisfying another. A
Context without an exact `workspace` or `engineering_object` subject reference
cannot be package-bound.

The binding relation records:

```text
context_subject_reference_id
context_version
project_id
project_configuration_revision
package_key
input_declaration_id
bound_by_id
bound_at
```

Its durable semantic identity is the subject-bound Context datum at the
recorded Context version plus the full retained input target:

```text
(context_subject_reference_id, context_version,
 project_id, project_configuration_revision,
 package_key, input_declaration_id)
```

### Eligible records and cardinality

Only an authorized, current Context whose owner storage shape, scope, exact
subject kind, subject scope, and value schema mapping satisfy the retained
descriptor can be bound. The Context and subject must belong to the same
Organization, Project, and, where applicable, Workspace as the locked package
operation.

One association binds one Context subject/version to one input. The same
subject/version may satisfy more than one input only through separate,
independently validated rows; there is no fan-out by kind or name. One input
may have multiple explicit Context rows within its descriptor bound. Workspace
inputs admit at most one eligible current occurrence. Object-scoped inputs
require at least one eligible occurrence for each applicable selected Object;
the descriptor/request bounds remain authoritative. Duplicate semantic rows
are prohibited by the binding key.

### Immutability and history

Binding rows are append-only: no update, delete, retarget, or reassignment is
permitted. A Context payload, responsibility, source, or lifecycle change that
increments the Context version makes an earlier binding ineligible for current
readiness. The updated current version requires a new explicit binding.
Withdrawal or a superseding/correcting Context never transfers a binding; the
replacement is independently authorized and bound. Earlier rows remain for
authorized historical interpretation.

General and pre-feature Context remains valid and explicitly `UNBOUND`. No
binding is inferred from Context kind, storage shape, subject, source, label,
text, current configuration, or current Workspace binding.

## Evidence binding contract

### Owner and location

The binding belongs to a new immutable Evidence-owner association from an
Evidence item/version to an exact package input. It is not a field on the
Evidence aggregate, is not package origin, and is not a second Deliverable or
Evidence fact store. Evidence lifecycle, source metadata, Human verification,
supporting-file links, and replacement remain owned by Evidence.

The binding relation records:

```text
evidence_id
evidence_version
project_id
project_configuration_revision
package_key
input_declaration_id
bound_by_id
bound_at
```

Its durable semantic identity is:

```text
(evidence_id, evidence_version,
 project_id, project_configuration_revision,
 package_key, input_declaration_id)
```

The retained input maps exactly to one Evidence requirement as specified in
the declaration-identity section.

### Eligibility, cardinality, and Human review

Only authorized Project-scoped or compatible Workspace-scoped Evidence with
`lifecycle=current`, `source_standing=current`, and owner-audited Human
verification may be bound. Organization, Project, and Workspace coherence are
mandatory. Each association binds one Evidence version to one input. One
Evidence version may satisfy multiple requirements only through separate,
independently validated binding rows; no implicit reuse occurs. One
requirement may have multiple Evidence items up to `max_occurrences=8`, and
readiness applies its declared `minimum_count` to the authorized eligible set.

The first three eligible readiness requirements retain
`evidence_kind_id=engineering_record`. The fourth remains separate:
`evidence_kind_id=human_review`, applicable only to package issue. In addition
to its exact fourth-input binding, its existing `source_reference` must be the
canonical lower-case Deliverable UUID and `source_revision` the canonical
lower-case exact revision UUID. This reconciliation does not create a parallel
Deliverable-revision link. Ready-for-review never consumes the fourth item;
issue never substitutes one of the first three.

Binding is append-only. A lifecycle transition changes Evidence version and
makes the earlier row ineligible for current readiness. Withdrawal,
supersession, or replacement does not transfer binding. Replacement Evidence
must reach the accepted owner state and receive a new explicit binding.
Existing and general Evidence remains valid and explicitly `UNBOUND`.

## DTO and API contract

Existing canonical Context and Evidence create/update APIs remain the only
owners of source facts. PATCH-052 adds binding operations; it does not clone
the owner creation DTOs. A caller may create a general source through its
owner route and then explicitly bind it. Failure to bind leaves a truthful
unbound source and does not roll back or reclassify that owner record.

All mutation models use `extra=forbid`. `Idempotency-Key` and the existing
trusted correlation/actor context are headers, not body fields. Field order is
frozen as follows.

### `PackageContextBindingRequest`

```text
input_declaration_id
context_id
context_subject_reference_id
expected_context_version
expected_configuration_revision
rationale
```

### `PackageEvidenceBindingRequest`

```text
input_declaration_id
evidence_id
expected_evidence_version
expected_configuration_revision
rationale
```

`expected_configuration_revision` is only an optimistic stale-request
precondition. It never supplies configuration authority. PackageKey,
PackageVersion, descriptor/Registry digest, Organization, Project, Workspace,
standing, subject type, authorization, actor, Human verification, binding
provenance, and timestamps are server-derived from the authorized route scope,
locked Workspace/configuration, and owner records.

Binding responses return, in this exact order, the authorized source ID,
source version, subject-reference ID when Context, Project/Workspace IDs,
server-derived PackageKey, PackageVersion, DescriptorDigest, Project
configuration revision, input declaration ID, derived Context-contribution or
Evidence-requirement ID, and `bound_at`. No full descriptor or protected source
value is returned.

### Evaluation request selectors

`PackageContextEvaluationRequest` fields are:

```text
expected_configuration_revision
object_ids
```

`object_ids` is sorted, unique, and contains 0..64 UUIDs. The Workspace route
supplies Project and Workspace. Context IDs are never accepted as declaration
authority; the server resolves eligible bindings by exact subject.

`PackageReadinessRequest` fields are:

```text
expected_configuration_revision
object_ids
evidence_ids
```

`object_ids` is sorted/unique 0..64. `evidence_ids` is sorted/unique 0..24 for
ready-for-review and 0..8 for issue. These are candidate owner handles only;
the server verifies their immutable bindings and does not trust their order or
claimed meaning. The Deliverable/revision route supplies their identities.

The closed `PackageTransitionRequest` fields are:

```text
target_standing
expected_deliverable_version
expected_revision_version
expected_configuration_revision
object_ids
evidence_ids
rationale
```

`target_standing` is only `ready_for_review` or `issued`. The former requires
the `draft` source state and ready-for-review gate; the latter requires the
exact `reviewed` revision and fourth-Evidence gate. The owner Deliverable
service alone performs the transition after a PASS in the same transaction.

### Exact evaluation responses

`PackageContextEvaluationResponse` field order is:

```text
project_id
workspace_id
package_key
package_version
descriptor_digest
project_configuration_revision
status
object_ids
required_input_ids
context_results
findings
limitations
observation_started_at
observation_completed_at
source_version_digest
```

Each `context_results` row is ordered by input ordinal, subject kind, subject
UUID/ID, Context ID, and Context version and contains:

```text
input_declaration_id
context_declaration_id
context_kind_id
subject_kind
subject_id
required
context_id
context_version
status
reason_code
```

`PackageReadinessResponse` field order is:

```text
project_id
workspace_id
deliverable_id
revision_id
deliverable_version
revision_version
package_key
package_version
descriptor_digest
project_configuration_revision
status
required_input_ids
context_results
evidence_results
transition_allowed
findings
limitations
observation_started_at
observation_completed_at
rule_hook_id
rule_hook_version
source_version_digest
```

Each `evidence_results` row is ordered by input/requirement ordinal and
Evidence UUID and contains:

```text
input_declaration_id
evidence_requirement_id
evidence_kind_id
minimum_count
evidence_id
evidence_version
status
reason_code
```

Top-level `status` is exactly `PASS`, `FINDINGS`, or `INDETERMINATE`.
Per-row status is exactly `SATISFIED`, `MISSING`, `STALE`, or
`INDETERMINATE`. `transition_allowed` is true only for top-level PASS and the
exact requested owner transition.

Safe reason codes are closed to:

```text
required_binding_missing
binding_configuration_mismatch
binding_source_version_stale
binding_declaration_mismatch
source_not_current
human_verification_unproven
human_review_revision_mismatch
configuration_stale
retained_descriptor_unavailable
source_partial_or_truncated
protected_source_unavailable
resource_limit_exceeded
rule_unavailable
```

Protected-source results never include a source ID, declaration ID, count, or
package fact. Externally indistinguishable protected/not-found cases retain the
accepted protected response rather than exposing the reason code.

## Server resolution and transaction contract

For binding or evaluation, the server performs this order:

1. derive actor and Organization from trusted context;
2. authorize route Project, Workspace, owner aggregate, subject, and every
   selected Object/Evidence/Deliverable before resolving package metadata;
3. enter the shared PATCH-052 UoW and lock current Registry/configuration,
   Project head/revision/selection, then Workspace and owner rows in the
   accepted lock order;
4. compare `expected_configuration_revision` as a stale-request precondition;
5. derive PackageKey and exact selection from the locked Workspace; resolve
   retained PackageVersion/DescriptorDigest and current execution eligibility;
6. resolve `input_declaration_id` only inside that exact descriptor and
   validate the exact Context-contribution or Evidence-requirement mapping;
7. validate source version, state, scope, subject, storage shape, Human
   verification, cardinality, and bounds;
8. insert the immutable binding and transactional Audit/outbox/idempotency
   result, or build the bounded immutable evaluation envelope; and
9. recheck fresh authority and commit once for mutation. Evaluation remains
   read-only. A transition commits the gate and owner transition atomically.

Replay occurs only after fresh authority and configuration checks. Binding
Audit records safe association identity and derived package/version/digest,
Registry digest for current execution, actor/correlation/causation, outcome,
and source version, never protected values or a descriptor body.

## Deterministic readiness and historical behavior

For each exact Deliverable declaration, the server resolves only its ordered
`required_input_ids`. A Context input is satisfied only by a current Context
version with a matching subject/version binding to the locked selection. An
Evidence input is satisfied only by a selected, authorized, current,
Human-verified Evidence version whose binding maps that exact input to that
exact retained requirement. Counts and results are stable and bounded; there
is no fuzzy, free-text, type-only, ordering, or current-state match.

The ordered union rule for package readiness remains unchanged: only Evidence
inputs named by requested Deliverables control ready-for-review. The fourth
Human-review requirement controls only issue of its exact reviewed revision.
No universal Evidence gate is introduced.

Visible absence, a visible stale source version, or a visible binding from a
different Project configuration yields `FINDINGS` with the applicable closed
reason. Hidden/partially authorized sources, missing required retained
descriptor material, truncation, incoherent persisted identity, or rule
unavailability yields `INDETERMINATE`. It is never converted to `MISSING`.

Workspace rebind, Project reconfiguration, Registry release/standing change,
or package upgrade never rewrites a binding. Current operational evaluation
accepts only bindings to the locked current Project selection. Old bindings
remain owner-authorized historical records resolved through their exact
retained Project selection and descriptor. Historical-only standing permits
interpretation but not new binding, rule execution, or transition. Missing
retained history fails closed; current Workspace state is never substituted.

## Persistence decision and exact `e05200000002` scope

One linear additive migration is necessary and sufficient:

```text
revision:      e05200000002
down_revision: e05200000001
```

It may do only the following:

1. preflight exact head `e05200000001`, required owner/configuration tables,
   roles, and absence of conflicting tables/functions;
2. create `engineering_context_package_input_bindings` with the eight columns
   frozen above and its constraints/indexes;
3. create `evidence_package_input_bindings` with the eight columns frozen
   above and its constraints/indexes;
4. add restrictive FKs from source/subject and actor IDs and the exact
   `(project_id, project_configuration_revision, package_key)` selection FK;
5. add database coherence guards that reject cross-Organization,
   cross-Project, cross-Workspace, or source-version-incoherent rows;
6. add one private immutable-binding trigger function and BEFORE UPDATE OR
   DELETE triggers on both tables;
7. grant `satco_runtime` only `SELECT, INSERT` on the two tables and no UPDATE,
   DELETE, TRUNCATE, trigger-function execution, or projection-install
   authority; and
8. verify both tables are empty, constraints/indexes/triggers/grants are exact,
   and the graph still has one head.

The exact additive columns are:

| Table | Column | SQL type / nullability |
|---|---|---|
| `engineering_context_package_input_bindings` | `context_subject_reference_id` | `INTEGER NOT NULL` |
|  | `context_version` | `INTEGER NOT NULL` |
|  | `project_id` | `INTEGER NOT NULL` |
|  | `project_configuration_revision` | `BIGINT NOT NULL` |
|  | `package_key` | `VARCHAR(64) NOT NULL` |
|  | `input_declaration_id` | `VARCHAR(128) NOT NULL` |
|  | `bound_by_id` | `INTEGER NOT NULL` |
|  | `bound_at` | `TIMESTAMPTZ NOT NULL`, server time default |
| `evidence_package_input_bindings` | `evidence_id` | `UUID NOT NULL` |
|  | `evidence_version` | `INTEGER NOT NULL` |
|  | `project_id` | `INTEGER NOT NULL` |
|  | `project_configuration_revision` | `BIGINT NOT NULL` |
|  | `package_key` | `VARCHAR(64) NOT NULL` |
|  | `input_declaration_id` | `VARCHAR(128) NOT NULL` |
|  | `bound_by_id` | `INTEGER NOT NULL` |
|  | `bound_at` | `TIMESTAMPTZ NOT NULL`, server time default |

The stable primary keys are, in order:

```text
pk_engineering_context_package_input_bindings
  (context_subject_reference_id, context_version, project_id,
   project_configuration_revision, package_key, input_declaration_id)

pk_evidence_package_input_bindings
  (evidence_id, evidence_version, project_id,
   project_configuration_revision, package_key, input_declaration_id)
```

The stable restrictive FKs are:

```text
fk_context_input_binding_subject
  context_subject_reference_id -> engineering_context_subject_references.id
fk_context_input_binding_selection
  (project_id, project_configuration_revision, package_key)
    -> project_package_configuration_selections
       (project_id, configuration_revision, package_key)
fk_context_input_binding_actor
  bound_by_id -> users.id

fk_evidence_input_binding_evidence
  evidence_id -> evidence.id
fk_evidence_input_binding_selection
  (project_id, project_configuration_revision, package_key)
    -> project_package_configuration_selections
       (project_id, configuration_revision, package_key)
fk_evidence_input_binding_actor
  bound_by_id -> users.id
```

`ck_context_input_binding_values` and `ck_evidence_input_binding_values`
require positive source/configuration versions, non-empty bounded PackageKey,
and `input_declaration_id` matching `^[a-z][a-z0-9_.-]*$`.

One private `satco_patch052_binding_coherent()` BEFORE INSERT trigger function
serves table-specific branches. For Context it joins subject -> Context and
requires the recorded current Context version plus exact Project/Organization/
Workspace coherence. For Evidence it requires a non-null matching Evidence
Project, the recorded current Evidence version, and exact Project/
Organization/Workspace coherence. Both compare the retained Project revision's
Organization. `satco_patch052_binding_immutable()` rejects every UPDATE or
DELETE on either table. Both functions are `SECURITY DEFINER` with a fixed
`pg_catalog, public` search path, are owned by the schema owner, and grant no
PUBLIC or runtime EXECUTE.

Each table has a composite primary/unique semantic key over its source
subject/ID, source version, Project revision, PackageKey, and input declaration
ID. Checks require source version and configuration revision >= 1, non-empty
bounded PackageKey/input ID, and canonical declaration-ID syntax. FKs are
`ON DELETE RESTRICT`. The coherence guard resolves the source's owning Context
or Evidence and its Project/Workspace/Organization; it does not parse free
text or infer a declaration.

Each table additionally has one readiness index:

```text
ix_context_input_binding_readiness
  (project_id, project_configuration_revision, package_key,
   input_declaration_id, context_subject_reference_id, context_version)

ix_evidence_input_binding_readiness
  (project_id, project_configuration_revision, package_key,
   input_declaration_id, evidence_id, evidence_version)
```

The composite primary key supplies the reverse source-history lookup. No
additional version/digest/Registry/current-Workspace index or copied package
fact is required.

There is no backfill. Every pre-existing Context/Evidence row remains unbound,
and both new tables are empty immediately after upgrade. Migration code must
not inspect names, types, text, source references, Deliverables, current
configuration, or Workspace binding to manufacture rows. Downgrade may drop
the two empty tables and their private guards only when no binding rows exist;
after use it fails closed and recovery is forward-only.

The migration must not modify `e05200000001`, any existing row, Context or
Evidence owner schema, origin triples, descriptor JSON, Project configuration,
Report/Memory bytes, or Registry state. No second corrective migration is
needed for this contract.

## Ownership, upstream impact, and governance outcome

This is a shared PATCH-052 correction implemented once as the minimum Batch-3
blocker remediation and reused unchanged by Batch 4. It does not redesign
batch boundaries or start Batch 4.

- **ADR-025:** no amendment. It governs Identifier ownership and is unaffected.
- **Architecture-052:** no amendment. Association rows preserve its explicit
  Context/Evidence non-origin rule and reuse its retained-selection derivation.
- **EDS-052:** no amendment. Its exact input/requirement mappings, selected
  Evidence rule, fourth-Evidence revision reference, and historical semantics
  are preserved.
- **IDS-052:** no semantic amendment. This downstream reconciliation supplies
  the DTO and association detail omitted from the named route contracts.
- **Implementation-Plan-052:** no semantic amendment. A separately authorized
  Batch-3 remediation addendum must include this one migration, the two owner
  association seams, DTO/routes, readiness/transition completion, and proofs.

No accepted upstream contract is contradictory. No Human product choice or
upstream reconciliation is required. The Post-PATCH-051 roadmap freeze is
preserved: PATCH-052 stays open, Batch 4 stays unauthorized, and PATCH-053 is
not started.

PATCH-052 CONTEXT / EVIDENCE DECLARATION-BINDING RECONCILIATION:
**PASS / ACCEPTED / COMPLETE**

B3-052-MAJ-01:
**OPEN / REMEDIATION PATH RESOLVED**

CORRECTIVE `e05200000002`:
**ELIGIBLE FOR SEPARATE HUMAN AUTHORITY**

PATCH-052 BATCH-3:
**INCOMPLETE / NOT YET ACCEPTED**

PATCH-052 BATCH-4:
**NOT STARTED / NOT AUTHORIZED**

PATCH-053:
**NOT STARTED / NOT AUTHORIZED**
