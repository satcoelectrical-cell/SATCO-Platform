# EDS-049 — Project Completeness & Missing-Information Intelligence

## 1. Status and authority

**ACCEPTED / COMPLETE.** Independent EDS Review is PASS with Critical/Major/
Minor findings `0/0/0`. Human EDS Acceptance grants IDS-049 design authority
only.

This EDS translates accepted Architecture-049 into exact engineering contracts
for deterministic, explainable, read-only Project completeness intelligence.
It introduces no model-backed AI, persistence, migration, source mutation,
workflow or PATCH-050 recommendation/material direction.

## 2. Application boundary and operations

V1 exposes exactly one application operation:

```text
assess_project_completeness(
    actor: CompletenessActor,
    request: CompletenessAssessmentRequest,
    current_user: TrustedPrincipal,
) -> CompletenessAssessmentResult
```

`CompletenessActor` is constructed only by the request-scoped composition root:

| Field | Type | Rule |
|---|---|---|
| `actor_id` | positive integer | trusted authenticated User identity |
| `organization_id` | UUID | server-derived active Organization |

`CompletenessAssessmentRequest` is a frozen strict DTO:

| Field | Type | Rule |
|---|---|---|
| `project_id` | positive integer | route/context-selected Project |
| `workspace_id` | positive integer or null | optional filter inside the same Project/Organization |

There is one V1 catalog, so the caller supplies no catalog/rule-set selector,
rule IDs, classification policy, source data, Project Context result, graph
depth, continuation, prompt or arbitrary option. Unknown fields are rejected.

## 3. Fresh Project Context input contract

The completeness service depends on a narrow inward port implemented over the
public PATCH-048 application service:

```text
ProjectContextAssessmentSource.observe(
    actor: ProjectContextActor,
    request: ProjectContextRequest,
    current_user: TrustedPrincipal,
) -> ProjectContextResult
```

For every assessment the service constructs a new `ProjectContextRequest` with:

- the request Project/Workspace scope;
- all ten `CANONICAL_SECTION_ORDER` sections;
- `page_size = 100` for each section;
- no section continuation.

The same trusted actor/current User is passed through. Caller-supplied
`ProjectContextResult`, serialized context, Organization, authority decision or
continuation is forbidden. The adapter calls the PATCH-048 application service,
not its HTTP route, repositories, owner services, ORM, Session or UoW.

Upstream result translation is exact:

| `ProjectContextResult` | Completeness result |
|---|---|
| `protected_not_found` | payload-free `protected_not_found` |
| `invalid_request` | payload-free `invalid_request` |
| `unavailable` | payload-free `unavailable` |
| `success` | deterministic catalog evaluation |

## 4. Upstream observable vocabulary

EDS-049 consumes the accepted PATCH-048 vocabulary unchanged:

- section kinds: `project_basis`, `execution`, `deliverables`,
  `project_controls`, `engineering_context`, `engineering_objects`, `evidence`,
  `supporting_files`, `technical_reports`, `organizational_memory`;
- source states: `available`, `empty`, `not_established`, `not_disclosed`,
  `unavailable`;
- observation status: `complete_within_bounds` or `partial`;
- `SectionAvailable.visible_count`, items, observation time and exact
  truncation metadata;
- item `selector`, `version`, `standing` and `FactProvenance` safe fields;
- owner-approved typed section projections only.

PATCH-049 neither widens those projections nor interprets unavailable/protected
fields as empty.

## 5. Static rule catalog contract

V1 owns exactly one source-controlled catalog:

```text
catalog_id      = "project_completeness.v1"
catalog_version = 1
```

`catalog_digest` is lowercase SHA-256 over canonical UTF-8 JSON containing the
ordered complete rule definitions. Canonical JSON uses sorted object keys,
preserves array order, UTF-8 without ASCII escaping and compact separators.
The digest excludes runtime observations and rendered results.

Each frozen `CompletenessRuleV1` contains exactly:

| Field | Contract |
|---|---|
| `rule_id` | namespaced lowercase identifier matching `^[a-z0-9_.-]{1,128}$` |
| `rule_version` | positive integer; V1 inventory uses `1` |
| `category` | closed `RuleCategory` |
| `applicability` | closed typed `ApplicabilityPredicateV1` |
| `observable` | closed typed `ObservablePredicateV1` |
| `question_template` | zero or one catalog-owned template |
| `checklist_template` | zero or one catalog-owned template |
| `limitation_codes` | ordered closed codes, maximum 8 |
| `graph_requirement` | null in the accepted V1 inventory |

`RuleCategory` is exactly `project_basis`, `execution`, `deliverables`,
`engineering_context`, or `verification_evidence`.

Rules are immutable, unique by `(rule_id, rule_version)`, ordered
lexicographically by that pair and evaluated exactly once. Duplicate IDs,
versions, template IDs, unsupported predicates, unsafe placeholders or a
catalog digest mismatch make the service unavailable at composition/startup;
they never produce a partial catalog evaluation.

No dynamic import/evaluation, Python expression string, user script, prompt,
regular-expression rule language, database rule, customer override or
provider-generated definition is permitted.

## 6. Accepted V1 rule inventory

Every rule below has version `1`. Stage order is the accepted Project Foundation
order: `definition`, `preparation`, `execution`, `verification`,
`completion_readiness`.

| Rule ID | Category | Applicability | Observable satisfaction |
|---|---|---|---|
| `pc.project_foundation.established` | project_basis | every authorized Project | visible Project basis has `foundation_established = true` |
| `pc.project_basis.purpose` | project_basis | every authorized Project | visible trimmed `purpose` is non-empty |
| `pc.project_basis.engineering_basis` | project_basis | every authorized Project | visible trimmed `engineering_basis` is non-empty |
| `pc.project_scope.in_scope` | project_basis | every authorized Project | `ordered_in_scope` contains at least one entry |
| `pc.project_completion.basis` | project_basis | every authorized Project | visible trimmed `completion_basis` is non-empty |
| `pc.project_inputs.declared` | project_basis | every authorized Project | `required_project_inputs` contains at least one entry |
| `pc.execution.plan_established` | execution | stage is preparation or later | execution section contains one visible Plan |
| `pc.execution.activities_defined` | execution | stage is preparation or later and a Plan is visible | visible Plan contains at least one Activity |
| `pc.execution.milestones_defined` | execution | stage is preparation or later and a Plan is visible | visible Plan contains at least one Milestone |
| `pc.deliverables.register_established` | deliverables | stage is preparation or later | deliverables section contains at least one Deliverable |
| `pc.deliverables.current_revision` | deliverables | stage is execution or later and at least one Deliverable is visible | every visible Deliverable has `current_revision` |
| `pc.deliverables.representation_available` | deliverables | stage is verification or completion-readiness and at least one current revision is visible | every visible current revision has `representation_available = true` |
| `pc.engineering_context.established` | engineering_context | stage is preparation or later | engineering-context section contains at least one current context |
| `pc.verification.evidence_established` | verification_evidence | stage is verification or completion-readiness | evidence section contains at least one visible Evidence item |

The catalog deliberately has no “at least one Risk/Issue/Decision/Change,”
Technical Report or Organizational Memory rule because their absence is not a
universal completeness defect. It does not infer satisfaction of declared
free-text Project inputs because PATCH-048 exposes no canonical input-to-fact
fulfilment contract. Those exclusions prevent false missing/present claims.

Changing this inventory or a rule's meaning requires EDS/IDS review and a new
catalog/rule version. It is not a runtime configuration change.

## 7. Rule applicability semantics

Applicability predicates are limited to:

- `always`;
- current visible Project stage at-or-after a named accepted stage;
- existence of an already visible typed parent projection, used only by the
  two child Deliverable/Plan rules above.

The Project stage comes only from visible Project basis. No free text,
discipline inference, co-occurrence, tenant convention, item count outside the
visible result or graph relation establishes applicability.

Applicability evaluation is three-step:

1. If required applicability input is protected/not disclosed, classification
   is `NOT_DISCLOSED`.
2. If required applicability input is unavailable, partial, unsupported or
   truncated such that truth cannot be determined, classification is
   `INDETERMINATE`.
3. Otherwise false produces `NOT_APPLICABLE`; true proceeds to observation.

When a parent rule is visibly `MISSING`, a child rule requiring that visible
parent is `NOT_APPLICABLE`; the parent finding already states the safe gap.
When the parent cannot be observed, the child is `INDETERMINATE` or
`NOT_DISCLOSED`, never `NOT_APPLICABLE`.

## 8. Observable predicate semantics

Observable predicates are closed field-presence/list-presence/boolean/all-item
checks over the typed fields in Section 6. They cannot parse technical prose,
compare semantic meaning or execute arbitrary expressions.

For a section-level existence rule:

| Source state | Classification |
|---|---|
| available, untruncated, predicate true | `PRESENT` |
| available, untruncated, predicate false | `MISSING` |
| empty or not-established after applicability is known true | `MISSING` |
| available but truncated and predicate true is witnessed | `PRESENT` |
| available but truncated and predicate false only by absence | `INDETERMINATE` |
| unavailable | `INDETERMINATE` |
| not-disclosed | `NOT_DISCLOSED` |

For `every visible item` rules, one visible counterexample safely produces
`MISSING` even if the section is truncated. If no counterexample is visible,
`PRESENT` requires the relevant section to be untruncated; otherwise the result
is `INDETERMINATE`.

Trimmed text presence tests Unicode text after deterministic surrounding-
whitespace removal only. Content meaning, adequacy or correctness is never
inferred.

## 9. Classification precedence

Classification precedence is exact:

```text
root protected/invalid/unavailable outcome
  -> closed root result; no findings
applicability protected
  -> NOT_DISCLOSED
applicability insufficient
  -> INDETERMINATE
applicability visibly false
  -> NOT_APPLICABLE
required observation protected
  -> NOT_DISCLOSED
required observation insufficient/unavailable/truncated for absence
  -> INDETERMINATE
predicate visibly satisfied
  -> PRESENT
predicate safely false/absent within complete observable bounds
  -> MISSING
```

`MISSING` is last and requires positive proof that visibility and applicable
bounds are sufficient. `NOT_DISCLOSED` takes precedence over `INDETERMINATE`
where the reason is protected visibility. A rule never changes classification
because another rule is missing except the explicit parent-applicability rule
in Section 7.

## 10. Finding contract

Every catalog rule produces exactly one `CompletenessFindingV1`, including
`NOT_APPLICABLE` rules. The strict frozen DTO contains:

| Field | Type / limit |
|---|---|
| `rule_id` | catalog identifier, maximum 128 |
| `rule_version` | positive integer |
| `catalog_id` / `catalog_version` / `catalog_digest` | exact evaluated catalog attribution |
| `category` | `RuleCategory` |
| `classification` | closed five-value enum |
| `title` | deterministic catalog text, maximum 256 |
| `description` | deterministic catalog text, maximum 1024 |
| `applicability_basis` | ordered tuple of safe basis codes, maximum 8 |
| `evidence` | ordered safe references, maximum 4 |
| `source_observation_started_at` / `source_observation_completed_at` | copied from Project Context success |
| `limitation_codes` | ordered closed codes, maximum 8 |
| `source_truncated` / `evidence_truncated` | booleans |
| `questions` | zero or one question |
| `checklist_items` | zero or one checklist item |

`title` and `description` come from fixed catalog text. They contain no source
body, Human name/ID, raw exception, provider/model field or hidden count.

## 11. Evidence reference contract

`CompletenessEvidenceReferenceV1` is a closed union:

### Visible fact reference

- `reference_kind = "visible_fact"`;
- `owner_kind` and `item_kind`, each maximum 64;
- upstream safe `selector`, maximum 128, treated as opaque;
- optional visible `version`, `standing`, source-observed timestamp;
- upstream `observed_at`, authority class and temporal class;
- optional safe display label already disclosed by the upstream projection,
  maximum 512;
- `supported_predicate_code`, maximum 128.

### Visible section-state reference

- `reference_kind = "visible_section_state"`;
- section kind;
- state limited to `available`, `empty` or `not_established`;
- optional visible observation time;
- `truncated` boolean;
- `supported_predicate_code`.

No reference is emitted for a protected/not-disclosed source. Unavailable state
may be expressed only as a limitation code, not as a source identity. A
reference is explanatory data already disclosed in Project Context; it grants
no authorization and is not a universal resolver. Following its opaque selector
must invoke the existing canonical protected route/application read again.

Private storage key/URL, file download token, source body, Human identity and
inaccessible provenance are forbidden. Missing optional provenance remains
absent rather than manufactured.

## 12. Clarification-question contract

`ClarificationQuestionV1` contains:

- stable `question_id = "<rule_id>.question.v<rule_version>"`;
- originating `rule_id` and `rule_version`;
- `ordinal = 1`;
- deterministic catalog-rendered `text`, maximum 512;
- `advisory = true`.

Each rule has at most one question template. Templates may substitute only a
closed visible stage or already disclosed safe Project/Deliverable label; the
template declares each placeholder. No source body, selector, hidden fact or
free-form user value is substituted.

Emission is exact:

- `MISSING`: emit the rule's question;
- `INDETERMINATE`: emit only its generic visibility/verification question;
- `PRESENT`, `NOT_APPLICABLE`, `NOT_DISCLOSED`: emit none.

Questions are deduplicated by `(question_id, rendered_safe_values)` and ordered
by source rule order then ordinal. They do not create tasks or recommend an
engineering solution.

## 13. Checklist contract

`CompletenessChecklistItemV1` contains:

- stable `checklist_id = "<rule_id>.check.v<rule_version>"`;
- originating `rule_id` and `rule_version`;
- `ordinal = 1`;
- deterministic catalog-rendered `text`, maximum 512;
- `classification` copied from its finding;
- `advisory = true`.

One checklist item is emitted for `MISSING` or `INDETERMINATE`; none is emitted
for `PRESENT`, `NOT_APPLICABLE` or `NOT_DISCLOSED`. Deduplication and ordering
match questions.

The DTO has no assignee, due date, owner, workflow state, checked state,
approval, standing, completion percentage, mutation link or automatic command.
It is regenerated on every assessment.

## 14. Exact question/checklist intent

The catalog templates are limited to these action-neutral intents:

| Rule family | Clarification intent | Checklist intent |
|---|---|---|
| Foundation/purpose/basis/scope/completion/input rules | ask the Human to identify the missing governed Project-basis information | verify that the information is established through Project Foundation |
| Plan/activity/milestone rules | ask whether the governed execution information has been established | verify it through Engineering Execution |
| Deliverable/revision/representation rules | ask whether the governed Deliverable information/reference is established | verify it through Deliverable Control or its external-authority reference |
| Engineering Context rule | ask whether current governed context has been established | verify through Engineering Context |
| Verification Evidence rule | ask whether governed verification Evidence has been established | verify through Evidence |

Templates may name the owning workflow but cannot propose technical content,
design changes, materials, vendors, priorities or solutions.

## 15. Optional EKG evidence contract

The Architecture permits one-hop evidence only when a rule explicitly requires
it. Targeted reconciliation shows every accepted initial rule in Section 6 is
decidable from existing authorized Project Context projections. Therefore:

```text
V1 catalog graph_requirement: null for every rule
maximum EKG expansion calls per assessment: 0
```

No EKG port or call is required by initial implementation. This is deliberate
scope discipline, not a weakening of PATCH-048. Adding a graph-dependent rule
requires EDS/IDS amendment that must define an authorized visible seed, exact
closed relationship kinds/direction, one `ExpandOneHopRequest`, result mapping
and cumulative bounds. It may never permit arbitrary depth, second hop,
inference, similarity, graph-wide discovery or caller continuations.

Any future permitted protected graph result maps to `NOT_DISCLOSED`; unavailable
or truncated absence maps to `INDETERMINATE`, never `MISSING`.

## 16. Observation and partiality semantics

`CompletenessObservationV1` contains:

- assessment `started_at` and `completed_at` from the completeness clock;
- upstream `source_observation_started_at` and
  `source_observation_completed_at`;
- upstream `source_observation_status`;
- catalog identity/version/digest;
- `assessment_status` of `complete_within_bounds` or `partial`;
- ordered limitation codes.

The source observation is non-transactional. The result states only what was
observed during both intervals. It never claims a globally atomic snapshot.

`assessment_status = partial` when upstream is partial, any applicable rule is
`INDETERMINATE` or `NOT_DISCLOSED`, any relevant input/evidence is truncated, or
the result carries a dependency limitation. Otherwise it is
`complete_within_bounds`. Neither value means Project approval/completion.

## 17. Exact bounds and response behavior

V1 bounds are:

| Boundary | Maximum |
|---|---:|
| catalog rules/evaluated rules/findings | 14 / 14 / 14 |
| predicates or applicability terms per rule | 8 |
| questions per finding / total | 1 / 14 |
| checklist items per finding / total | 1 / 14 |
| applicability-basis codes per finding | 8 |
| limitation codes per finding | 8 |
| evidence references per finding / total | 4 / 56 |
| Project Context section calls | one logical all-ten-section request |
| upstream page size per section | 100 |
| maximum visible input items scanned | 1,000 across ten sections |
| optional EKG expansions | 0 |
| serialized response | 131,072 UTF-8 bytes |

The 14-rule catalog is evaluated wholly; rule truncation and pagination are
forbidden. Findings use catalog order, and questions/checklists inherit rule
order. Evidence references are ordered by section canonical order, item kind,
opaque selector and predicate code.

Upstream truncation remains explicit and changes absence-dependent results to
`INDETERMINATE`. No hidden remainder total is returned. Catalog validation must
prove fixed template/output bounds. An unexpected response-size breach returns
payload-free `unavailable` and safe operational logging; it does not silently
drop findings.

## 18. Closed result/error contract

`CompletenessAssessmentResult` is a discriminated union:

| Outcome | Payload |
|---|---|
| `success` | observation with `complete_within_bounds`, exactly 14 findings and derived questions/checklist |
| `partial_success` | observation with `partial`, exactly 14 findings and derived questions/checklist |
| `protected_not_found` | discriminator only |
| `invalid_request` | discriminator only |
| `unavailable` | discriminator only |

No separate not-found/forbidden outcome exists. Domain validation messages,
denial reasons, exception text, source identity and counts are not serialized.

`invalid_request` covers malformed Project/Workspace identifiers and strict DTO
failure. `unavailable` covers upstream unavailability, invalid catalog,
unexpected owner-contract mismatch, response-bound breach and safe dependency
failure. Rule-level source unavailability inside a valid Project Context success
produces `partial_success` with `INDETERMINATE`, not a root failure.

## 19. Authorization and non-disclosure

1. Authentication constructs `CompletenessActor`; transport cannot override it.
2. Organization is server-derived and absent from request payload/query.
3. PATCH-048 reauthorizes Project/Workspace and every source before disclosure.
4. Actor/current-user mismatch fails protected.
5. Cross-Organization and cross-Project references are discarded protected,
   never evaluated or logged.
6. `NOT_DISCLOSED` names only a public static rule/category; it contains no
   hidden instance, identity, count, standing or denial reason.
7. Visible counts are used only internally for predicates and cannot imply a
   hidden/global/authorized total.
8. Evidence/reference DTOs carry no Human identity or private storage detail.
9. Operational logs may contain request correlation ID, actor/Organization/
   Project scope, catalog version/digest, safe outcome, elapsed time and returned
   classification counts. They must not contain source bodies, selectors,
   labels, question/checklist text, hidden counts, tokens or exception details.
10. Metrics are aggregate operational metrics and cannot be tenant/source
    disclosure channels.

No model/provider receives Project data because PATCH-049 makes no AI call.

## 20. Authority and provenance

Every success response declares:

```text
authority_class = "derived"
advisory = true
authoritative = false
```

Finding provenance is the catalog attribution plus safe visible evidence and
observation intervals. It is not canonical Evidence and cannot be admitted to
Organizational Memory by implication.

No operation accepts, approves, rejects or resolves a finding. Human action is
external to PATCH-049 and uses canonical owners. UI/transport wording must not
represent a result as engineering approval, Project approval, readiness
certification, professional sign-off or completeness certification.

## 21. Frontend-observable semantics

The later IDS must support these exact observable states:

| State | Required presentation meaning |
|---|---|
| loading | assessment is being freshly authorized/evaluated |
| available | complete-within-bounds observation; findings grouped by classification/category |
| no applicable rules | all 14 findings are `NOT_APPLICABLE`; explicitly not Project approval |
| no actionable gaps | no `MISSING`, `INDETERMINATE` or `NOT_DISCLOSED`; explicitly not Project approval |
| missing | visibly distinct established absence |
| indeterminate | visibly distinct insufficient observation/uncertainty |
| not disclosed | generic protected state without identity/reason/count |
| partial | source/rule uncertainty or truncation is prominent |
| invalid/protected/unavailable | truthful payload-safe result boundary |
| truncated source/evidence | explicit limitation; no hidden remainder total |

There is no score, percentage, progress ring, “AI analysis,” chat treatment,
anthropomorphic language, recommendation CTA or automatic workflow button.
Questions and checklist prompts link only to already supported canonical product
surfaces and require Human action.

Semantic headings/lists/status text, non-color-only classification, keyboard
operation, visible focus, restrained live announcements, responsive stacking,
text expansion and direction-neutral/RTL-ready layout are mandatory. Detailed
component/transport field mappings remain IDS obligations.

## 22. Backward compatibility and legacy truth

PATCH-049 is additive and changes no PATCH-048 or owner contract. Sparse legacy
Projects are evaluated with the same truth table:

- explicit visible absence may be `MISSING`;
- false applicability is `NOT_APPLICABLE`;
- insufficient observation is `INDETERMINATE`;
- protected input is `NOT_DISCLOSED`.

No rule assumes records existed historically. There is no backfill, synthetic
Foundation/Plan/Deliverable/Context/Evidence, saved assessment or fabricated
percentage.

## 23. PATCH-050 firewall

Finding, question, checklist and description templates may identify required
information or the owning workflow through which a Human can establish it.
They must not produce:

- engineering recommendations or proposed solutions;
- design changes, optimizations or preferred approaches;
- material/equipment selection or preliminary BOM direction;
- vendor recommendation;
- Project-health/priority advice;
- model-generated content.

Those solution-oriented capabilities remain PATCH-050 or later. Any template
that answers “what should the engineering solution/material be?” is invalid.

## 24. Persistence, migration and reliability assessment

The rule catalog is immutable version-controlled application data and every
assessment is request-time only. No repository, table, cache, background job,
transaction, UoW, outbox, idempotency record, persisted review or assessment
history is required. PATCH-049 introduces **no migration** and Alembic remains
at `e04700000001`.

Ordinary shared access logging may apply under Section 19 but is not a PATCH-049
domain write. Dependency failure is fail-closed and cannot leave partial state
because the capability owns no state.

## 25. Explicit implementation invariants

1. No AI/model/provider call.
2. No caller-supplied Project Context or Organization authority.
3. One fresh PATCH-048 context observation per request.
4. No source mutation, persistence, migration, task/workflow or accepted state.
5. No foreign repository/ORM/Session/UoW access.
6. Protected/unavailable/partial/truncated absence never becomes `MISSING`.
7. Exactly 14 source-controlled rules, evaluated once in canonical order.
8. Every finding carries exact catalog/rule attribution.
9. No inferred edge, arbitrary traversal, EKG call or second hop in initial V1.
10. No hidden totals, Human identity, storage detail or inaccessible provenance.
11. No completeness score/percentage or Project approval claim.
12. No engineering/material/vendor/optimization recommendation.
13. All outputs and inputs remain within the fixed bounds in Section 17.
14. Legacy absence is never backfilled or fabricated.
15. Existing PATCH-048 and AI/provider-neutral seams remain unchanged.

## 26. IDS-049 obligations and stop conditions

IDS-049 must close:

- exact Python/transport enum, DTO and Protocol names/types;
- canonical catalog JSON field serialization and published digest test vector;
- the 14 concrete immutable rule/template definitions and safe text;
- predicate evaluator functions without arbitrary dispatch/eval;
- exact limitation/applicability/predicate code enums;
- safe reference extraction per upstream item type;
- strict result serialization and transport status mapping;
- request-scoped composition and frontend API/component state mapping;
- deterministic unit vectors for all classification precedence cases;
- security/non-disclosure, bounds, byte-size, legacy, accessibility, responsive,
  no-AI/no-persistence/no-PATCH-050 and adjacent PATCH-048 regression evidence.

Stop and return to Architecture if IDS requires a new owner field/port,
arbitrary caller context, EKG evidence, rule persistence/configuration,
assessment history, model-backed AI, source mutation, a score/percentage or
PATCH-050 guidance.
