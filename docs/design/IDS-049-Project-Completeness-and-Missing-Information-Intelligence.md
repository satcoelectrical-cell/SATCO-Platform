# IDS-049 — Project Completeness & Missing-Information Intelligence

## 1. Status and authority

**ACCEPTED / COMPLETE.** This IDS implements the accepted PATCH-049,
Architecture-049 and EDS-049 boundaries as an exact design. Independent IDS
Review and focused re-review are PASS with unresolved Critical/Major/Minor
findings `0/0/0`. Human IDS Acceptance grants Implementation-Plan-049
preparation authority only.

No implementation, migration, batch, delivery, closure or PATCH-050 authority
is granted by this document.

## 2. Repository mapping and module ownership

The implementation uses the repository's existing strict Pydantic DTO,
Protocol, request-scoped dependency, thin FastAPI router, closed frontend API
result and Project Workspace panel conventions.

| Future path | Responsibility |
|---|---|
| `backend/app/schemas/project_completeness.py` | all strict enums, DTOs, rule descriptors and closed results |
| `backend/app/ports/project_completeness.py` | narrow fresh Project Context observation Protocol |
| `backend/app/services/project_completeness_service.py` | immutable catalog, evaluators, safe projection and orchestration |
| `backend/app/dependencies/project_completeness.py` | request-scoped trusted composition over the existing Project Context application |
| `backend/app/api/v1/routers/project_completeness.py` | one authenticated thin route and result serialization |
| `backend/app/main.py` | register the router once |
| `frontend/src/api/types.ts` | exact frontend result/finding DTO types |
| `frontend/src/api/client.ts` | one closed-status assessment call |
| `frontend/src/components/ProjectCompletenessPanel.tsx` | accessible read-only assessment surface |
| `frontend/src/pages/ProjectsPage.tsx` | place the panel in the existing Project Workspace page |
| `frontend/src/styles.css` | bounded responsive/direction-neutral styles only |

PATCH-049 does not modify `project_context.py` schemas, service, adapters,
owner ports or authorization rules. Composition calls its public application
service. It never imports a foreign repository, ORM model, Session or UoW.

## 3. Closed enums and shared DTO policy

Every backend DTO inherits a local `ProjectCompletenessDTO` configured with
`ConfigDict(extra="forbid", frozen=True)`. Collections are tuples. Integers
are strict where ambiguity with booleans matters. Datetimes must be timezone
aware. Text is Unicode and bounded as stated; control characters other than
tab/newline are rejected from catalog text and rendered output.

Closed enums are:

```text
CompletenessClassification =
  present | missing | indeterminate | not_disclosed | not_applicable

CompletenessObservationStatus = complete_within_bounds | partial

CompletenessAuthorityClass = derived
RuleCategory =
  project_basis | execution | deliverables |
  engineering_context | verification_evidence

EvidenceReferenceKind = visible_fact | visible_section_state
RuleApplicabilityKind = always | stage_at_least | visible_parent_exists
RulePredicateKind = true_field | nonblank_field | nonempty_tuple |
                    visible_item_exists | any_nested_item |
                    all_visible_field_present | all_visible_field_true
```

`CompletenessActor`:

| Field | Type | Constraint |
|---|---|---|
| `actor_id` | strict int | `> 0` |
| `organization_id` | UUID | server-derived |

`CompletenessAssessmentRequest`:

| Field | Type | Constraint |
|---|---|---|
| `project_id` | strict int | `> 0` |
| `workspace_id` | strict int or null | null or `> 0` |

It has no Organization, context payload, catalog selector, rule selector,
continuation, graph option, prompt or arbitrary options.

## 4. Catalog and descriptor types

`RuleCatalogDescriptorV1` contains exactly:

| Field | Type |
|---|---|
| `catalog_id` | literal `project_completeness.v1` |
| `catalog_version` | literal `1` |
| `catalog_digest` | lowercase 64-character SHA-256 |
| `rules` | tuple of exactly 14 `CompletenessRuleDescriptorV1` |

`CompletenessRuleDescriptorV1` contains:

| Field | Type / bound |
|---|---|
| `rule_id` | lowercase namespaced string, 1–128 |
| `rule_version` | literal `1` |
| `ordinal` | unique integer 1–14 |
| `category` | `RuleCategory` |
| `title` | fixed text, 1–256 |
| `description` | fixed text, 1–1024 |
| `applicability` | closed `ApplicabilityDescriptorV1`, max 8 terms |
| `required_sections` | ordered unique section kinds, 1–2 |
| `predicate` | closed `ObservablePredicateDescriptorV1`, max 8 terms |
| `question_template` | exactly one fixed template |
| `indeterminate_question_template` | exactly one fixed generic verification template |
| `checklist_template` | exactly one fixed template |
| `indeterminate_checklist_template` | exactly one fixed generic verification template |
| `limitation_codes` | ordered unique closed codes, max 8 |
| `graph_requirement` | literal null |

Descriptors contain data only. Evaluators are explicit named functions in a
closed tuple alongside descriptors. No reflection, dynamic import, `eval`,
expression language, plugin, script, regex rule engine, prompt or database
catalog exists.

## 5. Canonical catalog serialization and digest

`CATALOG_RULES_V1` is a module-level tuple in ordinal order. Startup/import
validation requires exactly 14 rules, ordinals `1..14`, unique IDs, all
versions `1`, lexicographic `(rule_id, rule_version)` order, null graph
requirements and safe bounded templates.

The digest input is the JSON projection of every descriptor field in the field
order above, excluding `ordinal` only if the published fixture explicitly
retains array position; V1 **includes `ordinal`** to avoid ambiguity. It uses:

```python
json.dumps(
    catalog_payload,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

`catalog_digest = hashlib.sha256(bytes).hexdigest()`. IDS implementation must
publish a golden canonical JSON byte vector and digest in contract tests.
Descriptor construction or digest mismatch fails composition and yields
payload-free `unavailable`; partial catalog evaluation is forbidden.

## 6. Exact fourteen-rule catalog

All rules have version `1`, `graph_requirement = null`, and the fixed
lexicographic ordinal shown. The following metadata is part of the canonical
serialized descriptor; the later prose closes each rule's conditions,
evidence and templates.

| Ordinal | Rule ID | Fixed title | Fixed description | Applicability code | Predicate code | Required section(s) |
|---:|---|---|---|---|---|---|
| 1 | `pc.deliverables.current_revision` | Current Deliverable revision | Every applicable visible Deliverable must have a governed current revision. | `stage_execution_and_visible_deliverable` | `all_visible_field_present:current_revision` | Project Basis, Deliverables |
| 2 | `pc.deliverables.register_established` | Deliverable register | An applicable Project must have at least one governed visible Deliverable. | `stage_preparation` | `visible_item_exists:deliverable` | Project Basis, Deliverables |
| 3 | `pc.deliverables.representation_available` | Deliverable representation | Every applicable current Deliverable revision must have an available governed representation. | `stage_verification_and_visible_current_revision` | `all_visible_field_true:current_revision.representation_available` | Project Basis, Deliverables |
| 4 | `pc.engineering_context.established` | Engineering Context | Applicable current governed Engineering Context must be established. | `stage_preparation` | `visible_item_exists:engineering_context` | Project Basis, Engineering Context |
| 5 | `pc.execution.activities_defined` | Execution activities | An applicable governed execution plan must define at least one Activity. | `stage_preparation_and_visible_plan` | `any_nested_item:activities` | Project Basis, Execution |
| 6 | `pc.execution.milestones_defined` | Execution milestones | An applicable governed execution plan must define at least one Milestone. | `stage_preparation_and_visible_plan` | `any_nested_item:milestones` | Project Basis, Execution |
| 7 | `pc.execution.plan_established` | Execution plan | An applicable Project must have a governed execution plan. | `stage_preparation` | `visible_item_exists:execution` | Project Basis, Execution |
| 8 | `pc.project_basis.engineering_basis` | Engineering basis | The governed Project engineering basis must be stated. | `always` | `nonblank_field:engineering_basis` | Project Basis |
| 9 | `pc.project_basis.purpose` | Project purpose | The governed Project purpose must be stated. | `always` | `nonblank_field:purpose` | Project Basis |
| 10 | `pc.project_completion.basis` | Completion basis | The governed Project completion basis must be stated. | `always` | `nonblank_field:completion_basis` | Project Basis |
| 11 | `pc.project_foundation.established` | Project Foundation | The canonical Project Foundation must be established. | `always` | `true_field:foundation_established` | Project Basis |
| 12 | `pc.project_inputs.declared` | Required Project inputs | At least one required governed Project input must be declared. | `always` | `nonempty_tuple:required_project_inputs` | Project Basis |
| 13 | `pc.project_scope.in_scope` | In-scope work | At least one governed in-scope Project statement must be established. | `always` | `nonempty_tuple:ordered_in_scope` | Project Basis |
| 14 | `pc.verification.evidence_established` | Verification Evidence | An applicable Project must have governed visible verification Evidence. | `stage_verification` | `visible_item_exists:evidence` | Project Basis, Evidence |

The exact predicate/applicability code strings above are closed literals in V1.
“Complete” below means the required section is observable without
absence-affecting truncation. Protected/unavailable/truncated precedence is
defined in Section 9 and overrides every stated missing condition.

### 6.1 Project basis rules

#### `pc.project_basis.engineering_basis`
   - category/order: `project_basis`, 8;
   - purpose: determine whether the governed engineering basis is stated;
   - applicability: `always`;
   - section/type/field: Project Basis / `ProjectBasisItem.engineering_basis`;
   - PRESENT: one visible scoped basis item has nonblank trimmed value;
   - MISSING: exactly one complete visible basis item has null/blank value;
   - evidence: basis item visible-fact reference when PRESENT; section-state
     reference plus basis item selector when safely MISSING;
   - question: “What governed engineering basis must be established for this Project?”;
   - checklist: “Establish the engineering basis through Project Foundation.”

#### `pc.project_basis.purpose`
   - category/order: `project_basis`, 9;
   - purpose: determine whether Project purpose is stated;
   - applicability: `always`;
   - field: Project Basis / `ProjectBasisItem.purpose`;
   - PRESENT/MISSING/evidence: same nonblank/complete semantics as rule 1;
   - question: “What governed purpose must be established for this Project?”;
   - checklist: “Establish the Project purpose through Project Foundation.”

#### `pc.project_completion.basis`
   - category/order: `project_basis`, 10;
   - purpose: determine whether completion basis is stated;
   - applicability: `always`;
   - field: Project Basis / `ProjectBasisItem.completion_basis`;
   - PRESENT/MISSING/evidence: same nonblank/complete semantics;
   - question: “What governed completion basis must be established for this Project?”;
   - checklist: “Establish the completion basis through Project Foundation.”

#### `pc.project_foundation.established`
   - category/order: `project_basis`, 11;
   - purpose: determine whether canonical Foundation is established;
   - applicability: `always`;
   - field: Project Basis / `ProjectBasisItem.foundation_established`;
   - PRESENT: value is true; MISSING: complete value is false;
   - evidence: basis visible-fact or safe Project Basis section-state;
   - question: “Has the governed Project Foundation been established?”;
   - checklist: “Establish the Project Foundation through its canonical workflow.”

#### `pc.project_inputs.declared`
   - category/order: `project_basis`, 12;
   - purpose: determine whether required Project inputs are declared;
   - applicability: `always`;
   - field: Project Basis / `ProjectBasisItem.required_project_inputs`;
   - PRESENT: tuple length `>= 1`; MISSING: complete tuple is empty;
   - evidence: safe basis fact/section state only, never input body text;
   - question: “Which required governed Project inputs must be declared?”;
   - checklist: “Declare required Project inputs through Project Foundation.”

#### `pc.project_scope.in_scope`
   - category/order: `project_basis`, 13;
   - purpose: determine whether in-scope work is declared;
   - applicability: `always`;
   - field: Project Basis / `ProjectBasisItem.ordered_in_scope`;
   - PRESENT: tuple length `>= 1`; MISSING: complete tuple is empty;
   - evidence: safe basis fact/section state; scope entry text is not copied;
   - question: “What governed in-scope Project work must be established?”;
   - checklist: “Establish in-scope work through Project Foundation.”

### 6.2 Execution rules

#### `pc.execution.activities_defined`
   - category/order: `execution`, 5;
   - applicability: visible stage `preparation+` and visible Plan exists;
   - section/type/field: Execution / `ExecutionPlanItem.activities`;
   - PRESENT: visible Plan has at least one Activity; MISSING: complete visible
     Plan has zero Activities;
   - evidence: Plan visible-fact; no Activity title/ID is required;
   - question: “Which governed execution activities must be defined?”;
   - checklist: “Define execution activities through Engineering Execution.”

#### `pc.execution.milestones_defined`
   - category/order: `execution`, 6;
   - applicability: visible stage `preparation+` and visible Plan exists;
   - field: Execution / `ExecutionPlanItem.milestones`;
   - PRESENT: at least one Milestone; MISSING: complete Plan has none;
   - evidence: Plan visible-fact;
   - question: “Which governed execution milestones must be defined?”;
   - checklist: “Define milestones through Engineering Execution.”

#### `pc.execution.plan_established`
   - category/order: `execution`, 7;
   - applicability: visible stage `preparation+`;
   - section/type: Execution / `ExecutionPlanItem`;
   - PRESENT: one visible Plan; MISSING: complete section is empty or
     not-established;
   - evidence: Plan visible-fact or safe Execution section-state;
   - question: “Has the governed execution plan been established?”;
   - checklist: “Establish the plan through Engineering Execution.”

### 6.3 Deliverable rules

#### `pc.deliverables.current_revision`
   - category/order: `deliverables`, 1;
   - applicability: visible stage `execution+` and at least one visible
     Deliverable;
   - section/type/field: Deliverables / `DeliverableItem.current_revision`;
   - PRESENT: every visible Deliverable has a current revision and the section
     is complete; MISSING: any visible Deliverable lacks one, including under
     truncation because the counterexample is visible;
   - evidence: up to four counterexample Deliverable references for MISSING;
     otherwise up to four supporting references;
   - question: “Which governed Deliverable requires a current revision?”;
   - checklist: “Establish the current revision through Deliverable Control.”

#### `pc.deliverables.register_established`
   - category/order: `deliverables`, 2;
   - applicability: visible stage `preparation+`;
   - section/type: Deliverables / `DeliverableItem`;
   - PRESENT: at least one visible Deliverable; MISSING: complete section empty
     or not-established;
   - evidence: Deliverable reference or safe section-state;
   - question: “Which governed Deliverables must be established?”;
   - checklist: “Establish the Deliverable register through Deliverable Control.”

#### `pc.deliverables.representation_available`
   - category/order: `deliverables`, 3;
   - applicability: visible stage `verification+` and at least one visible
     current revision;
   - field: `DeliverableItem.current_revision.representation_available`;
   - PRESENT: all visible current revisions true and section complete;
   - MISSING: any visible false, even under truncation;
   - evidence/question/checklist: up to four counterexamples; “Which current
     governed Deliverable revision requires an available representation?” /
     “Establish its representation through Deliverable Control or the governed
     external-authority reference.”

### 6.4 Engineering context and verification rules

#### `pc.engineering_context.established`
   - category/order: `engineering_context`, 4;
   - applicability: visible stage `preparation+`;
   - section/type: Engineering Context / `EngineeringContextProjection`;
   - PRESENT: at least one visible current context; MISSING: complete section
     empty/not-established;
   - evidence: safe Engineering Context reference or section-state;
   - question: “What governed Engineering Context must be established?”;
   - checklist: “Establish current context through Engineering Context.”

#### `pc.verification.evidence_established`
   - category/order: `verification_evidence`, 14;
   - applicability: visible stage `verification+`;
   - section/type: Evidence / `EvidenceItem`;
   - PRESENT: at least one visible Evidence item; MISSING: complete section
     empty/not-established;
   - evidence: safe Evidence reference or section-state; `safe_source_reference`
     is not copied;
   - question: “What governed verification Evidence must be established?”;
   - checklist: “Establish verification Evidence through Evidence.”

For every rule, protected required applicability/observation yields
`NOT_DISCLOSED`; unavailable, unsupported, insufficient or absence-affecting
truncation yields `INDETERMINATE`; visibly false applicability yields
`NOT_APPLICABLE`. Indeterminate templates ask only that visibility/establishment
be verified through the named owner. `NOT_DISCLOSED` emits neither question nor
checklist.

## 7. Ten-section-to-rule closure matrix

| Canonical section | Allowed observations | Rules |
|---|---|---|
| Project Basis | exactly one `ProjectBasisItem`; stage, foundation flag, purpose, basis, in-scope tuple, completion basis, input tuple | applicability for 1–7 and 14; predicates 8–13 |
| Execution | `ExecutionPlanItem`, activities, milestones | 5–7 |
| Deliverables | `DeliverableItem.current_revision` and representation flag | 1–3 |
| Project Controls | state/partiality only; no initial rule predicate | none |
| Engineering Context | existence of current `EngineeringContextProjection` | 4 |
| Engineering Objects | state/partiality only | none |
| Evidence | existence of `EvidenceItem` | 14 |
| Supporting Files | state/partiality only | none |
| Technical Reports | state/partiality only | none |
| Organizational Memory | state/partiality only | none |

All ten sections are requested and contribute to assessment-level partiality.
Only the typed fields above influence classifications. Capture, Journal,
Interface Commitment, graph, raw provenance and foreign data are forbidden.

## 8. Stage normalization and applicability

The only accepted stage values are repository Project Foundation stages mapped
exactly to rank:

```text
definition=0, preparation=1, execution=2, verification=3,
completion_readiness=4
```

Unknown/null stage is insufficient, not false. `stage_at_least` therefore
yields `INDETERMINATE` unless Project Basis is protected, in which case it
yields `NOT_DISCLOSED`. An untruncated visible stage below threshold yields
`NOT_APPLICABLE`.

`visible_parent_exists` is evaluated only after stage applicability. A complete
section with no parent makes the child rule `NOT_APPLICABLE`. A visibly missing
parent finding does not cause a second missing child finding. Protected,
unavailable or truncated-to-absence parent observation yields protected or
indeterminate respectively.

## 9. Exact classification algorithm

The evaluator indexes exactly one section of each canonical kind and rejects a
missing/duplicate/out-of-order section or item/type mismatch as root
`unavailable`. It evaluates each rule independently in this order:

1. If any required applicability source state is `not_disclosed`, return
   `NOT_DISCLOSED`.
2. If applicability needs a source that is unavailable, unsupported, missing
   from the response, or truncated such that the fact is not witnessed, return
   `INDETERMINATE`.
3. If all applicability facts are visible and the predicate is false, return
   `NOT_APPLICABLE`.
4. If any required observation source is `not_disclosed`, return
   `NOT_DISCLOSED`.
5. If required observation is unavailable/unsupported, return
   `INDETERMINATE`.
6. Evaluate positive witnesses. A visible witness satisfying an existential
   rule returns `PRESENT` even if the section is truncated.
7. Evaluate visible counterexamples. For an all-item rule, one visible
   counterexample returns `MISSING` even if truncated.
8. If absence or all-item satisfaction depends on unseen candidates and the
   relevant section is truncated, return `INDETERMINATE`.
9. If the complete authorized observation satisfies the predicate, return
   `PRESENT`; otherwise return `MISSING`.

For multiple inputs, the most protective result wins:
`NOT_DISCLOSED > INDETERMINATE > NOT_APPLICABLE`, before observation. No empty,
false, null or zero value can establish missingness unless its enclosing
required section is sufficiently visible and complete.

## 10. Finding and observation DTOs

`CompletenessObservationV1`:

| Field | Type |
|---|---|
| `started_at`, `completed_at` | aware datetime, ordered |
| `source_observation_started_at`, `source_observation_completed_at` | copied aware datetimes |
| `source_observation_status` | upstream closed status |
| `catalog` | catalog ID/version/digest projection |
| `assessment_status` | `complete_within_bounds` or `partial` |
| `authority_class` | literal `derived` |
| `advisory` | literal true |
| `authoritative` | literal false |
| `limitation_codes` | ordered unique tuple, max 8 |
| `findings` | exactly 14 ordered findings |

`CompletenessFindingV1` fields are exactly the EDS fields: rule/catalog
attribution, category, classification, fixed title/description, safe
applicability basis (max 8), evidence (max 4), copied source observation times,
limitation codes (max 8), source/evidence truncation flags, zero-or-one question
and zero-or-one checklist item. It has no source body, Human identity, score,
priority, recommendation, workflow, provider or model field.

`ApplicabilityBasisCode` is closed to:

```text
always_applicable, stage_definition, stage_preparation, stage_execution,
stage_verification, stage_completion_readiness, visible_plan,
visible_deliverable, visible_current_revision
```

`LimitationCode` is closed to:

```text
source_partial, source_unavailable, source_not_disclosed, source_truncated,
applicability_indeterminate, observation_indeterminate,
evidence_reference_truncated, non_atomic_observation
```

## 11. Safe evidence projection

`VisibleFactReferenceV1`:

| Field | Type / rule |
|---|---|
| `reference_kind` | literal `visible_fact` |
| `owner_kind`, `item_kind` | bounded 1–64 |
| `selector` | copied opaque safe selector, 1–128 |
| `version` | positive int or null |
| `standing` | bounded string or null |
| `source_observed_at` | copied aware datetime or null |
| `observed_at` | copied aware datetime |
| `authority_class`, `temporal_class` | copied closed upstream enums |
| `display_label` | optional already-disclosed label, max 512 |
| `supported_predicate_code` | closed rule predicate code, max 128 |

Permitted display labels are Project name, Deliverable code/title and safe
catalog-owned section label. Engineering Context purpose/payload, Evidence
source reference, Supporting File filename/storage identity, Technical Report
content, Memory provenance and all Human data are never projected.

`VisibleSectionStateReferenceV1` contains literal kind, canonical section kind,
state limited to `available|empty|not_established`, optional visible
`observed_at`, truncation flag and predicate code. Protected/unavailable
sections create limitation codes, not evidence identities.

References are deduplicated by canonical JSON bytes and sorted by canonical
section ordinal, item kind, opaque selector, predicate code. First four remain
per finding; `evidence_truncated=true` records safe projection truncation. The
global first 56 in rule/evidence order are permitted, although 14×4 already
proves the bound. References confer no navigation authority; any UI link uses
an already supported route and reauthorizes.

## 12. Questions and checklist items

`ClarificationQuestionV1` contains `question_id`, rule ID/version, literal
ordinal `1`, bounded text and literal `advisory=true`.
`CompletenessChecklistItemV1` adds copied classification and otherwise follows
the same shape with `checklist_id`.

Stable IDs are `<rule_id>.question.v1` and `<rule_id>.check.v1`. Missing uses
the fixed rule template. Indeterminate uses the fixed generic visibility
template. Only closed visible stage or disclosed Deliverable label placeholders
are accepted; V1 templates use no free source placeholder, so rendering is a
constant lookup.

Emit one of each for `MISSING` and `INDETERMINATE`; emit none for `PRESENT`,
`NOT_APPLICABLE`, `NOT_DISCLOSED`. Deduplicate by stable ID plus rendered text
and order by rule ordinal. There are no task/workflow fields.

## 13. Fresh Project Context port and service flow

`ProjectContextAssessmentSource` Protocol exposes one method:

```text
observe(
  *, actor: ProjectContextActor,
  request: ProjectContextRequest,
  current_user: ProjectContextPrincipal
) -> ProjectContextResult
```

`ProjectContextAssessmentAdapter` wraps the existing
`ProjectContextService.assemble_project_context` and nothing else. It does not
expose owner calls, graph, repositories or continuation.

`ProjectCompletenessService.assess_project_completeness` executes:

1. reject actor/current-user mismatch protected;
2. validate strict request and positive Project/Workspace selectors;
3. construct Project Context actor from the same actor ID/Organization;
4. construct all ten canonical section requests in canonical order, each with
   page size 100 and null continuation;
5. call `observe` exactly once;
6. translate upstream protected/invalid/unavailable exactly;
7. validate ten sections, types, scope coherence and at most 1,000 recursively
   inspected visible inputs;
8. validate immutable catalog/digest;
9. evaluate all 14 rules once in ordinal order;
10. project bounded safe evidence;
11. generate deterministic questions/checklists;
12. compute observation partiality and limitations;
13. construct the closed result and serialize exactly with
    `result.model_dump_json().encode("utf-8")`;
14. if UTF-8 response exceeds 131,072 bytes, return payload-free unavailable;
15. return success or partial-success.

Clock reads occur immediately before the source call and after evaluation. No
state is written and no transaction boundary is introduced.

## 14. Authorization composition and scope validation

`ProjectCompletenessApplication` is a frozen request-scoped object containing
service, trusted actor and current user. `get_project_completeness_application`
depends on `AuthenticatedOrganizationContext`, calls
`get_project_context_application` with the same request Session and context,
and wraps only its public service.

The completeness layer does not recreate Project/Workspace or owner policy.
PATCH-048 is authoritative. After success it nevertheless fail-closes malformed
public output:

- exactly one Project Basis item must identify the requested Project;
- every emitted item with `project_id` must equal the request Project;
- when Workspace is specified, every non-null item `workspace_id` must equal it;
- actor Organization never comes from transport;
- a scope/type mismatch returns protected-not-found when it could reveal a
  foreign identity, otherwise unavailable for structural owner-contract drift.

No source is re-resolved. Safe logging may contain correlation ID, actor,
Organization, requested Project/Workspace, catalog attribution, root outcome,
duration and returned classification counts only. It excludes source data,
selectors, labels, questions, evidence, denials, tokens and exceptions.

## 15. Closed result union and transport mapping

Backend results are a discriminator union on `status`:

```text
CompletenessSuccess(status="success", observation=complete observation)
CompletenessPartialSuccess(status="partial_success", observation=partial)
CompletenessProtectedNotFound(status="protected_not_found")
CompletenessInvalidRequest(status="invalid_request")
CompletenessUnavailable(status="unavailable")
```

Protected, invalid and unavailable DTOs contain only the discriminator.
Validation error text and exceptions are caught before serialization.

The only route is:

```text
GET /projects/{project_id}/completeness?workspace_id={optional-positive-int}
```

It has `response_model=CompletenessAssessmentResult`, uses the authenticated
dependency, constructs only the strict request, and calls the application
service once. Like Project Context, closed domain outcomes use HTTP 200 and the
status discriminator; framework-level unauthenticated requests retain the
existing auth response. No request body, Organization parameter, catalog/rule
query, continuation, rule management or mutation route exists.

The router owns no policy, repository, Session, UoW, catalog or evaluator.
`backend/app/main.py` registers it once.

## 16. Bounds and failure enforcement

| Bound | Enforcement |
|---|---|
| catalog rules/findings = 14 | import/startup catalog validator and result DTO |
| terms/rule <= 8 | descriptor DTO |
| questions <= 14, one/finding | generator and result DTO |
| checklist <= 14, one/finding | generator and result DTO |
| evidence <= 4/finding and 56 total | projector and DTO validators |
| applicability/limitation codes <= 8/finding | DTO validators |
| ten sections, 100 items/section, <=1,000 total | constructed request and input validator |
| Project Context calls = 1 | adapter/service contract test |
| EKG calls = 0 | no graph dependency/import and prohibited-pattern test |
| response <=131,072 UTF-8 bytes | service serialization before return |

One visible input is each top-level section item plus each nested Activity,
Milestone and current-revision object whose fields an evaluator inspects.
Uninspected nested dependency/progress data is not traversed or counted. The
counter increments before inspection; reaching 1,001 returns payload-free
`unavailable`, never a truncated assessment or a false absence.

Catalog/result structural overflow is unavailable, never silent truncation.
Evidence above per-finding bound is deterministically truncated with an
explicit flag because it does not affect classification. Upstream truncation
changes absence-dependent classification to indeterminate. No total other than
the visible bounded output length is disclosed.

## 17. Overall partiality

The result is `partial_success` and assessment status `partial` if any of:

- upstream observation status is partial;
- any of ten sections is unavailable or not-disclosed;
- any available section is truncated;
- any finding is indeterminate or not-disclosed;
- any dependency/observation limitation applies.

Otherwise it is `success`/`complete_within_bounds`. A result may have no
actionable gaps while still being partial; the frontend must show both facts.
All 14 findings are returned for either success variant.

## 18. Frontend contracts and placement

`frontend/src/api/types.ts` adds exact string unions/interfaces mirroring the
backend. It uses no `[key:string]: unknown` escape hatch for completeness DTOs.
`api.projectCompleteness(projectId, workspaceId?)` calls the single route via
`closedStatusResult`; it maps success and partial-success as data-bearing
success states so the panel can render partial findings. Protected/invalid/
unavailable map to existing safe states without payload.

`ProjectCompletenessPanel` is rendered immediately before
`ProjectEngineeringContextPanel` in `ProjectWorkspacePage` and receives only
the current Project ID and selected Workspace ID. It provides an explicit
refresh button; mount and scope changes obtain fresh data.

Presentation rules:

- semantic section heading “Project Completeness” and derived/advisory notice;
- visible observation status/catalog version and limitation summary;
- findings grouped by category then fixed rule order;
- distinct text and badge semantics for all five classifications;
- missing is never styled/labeled as uncertainty or protected;
- evidence references display only safe labels/type/standing and do not expose
  raw selectors; supported links use canonical routes and reauthorize;
- questions/checklists are read-only lists, not controls or completion state;
- explicit no-applicable-rules when all findings are not-applicable;
- explicit no-actionable-gaps when none are missing/indeterminate/not-disclosed;
- partial/truncation notice remains visible with either empty state;
- loading uses existing LoadingState; protected uses ProtectedState;
  invalid/unavailable use payload-safe existing states;
- refresh restores focus to the panel status/heading without trapping focus;
- `aria-live="polite"` announces only safe status, not all findings;
- headings/list semantics, keyboard-operable links, visible focus, non-color
  text labels, 44px target where applicable, responsive single-column stacking,
  CSS logical properties and RTL/text expansion are required.

No percentage, score, progress ring, AI/chat wording, recommendation CTA,
editable checklist, task creation or fake production data is permitted.

## 19. Authority, provenance and PATCH-050 firewall

Every success response fixes `authority_class="derived"`, `advisory=true`, and
`authoritative=false`. Catalog digest/rule versions and visible evidence explain
the result. Findings do not mutate or approve owners and cannot be treated as
canonical Evidence or Organizational Memory.

Catalog templates may ask what required governed information must be
established and name its owning workflow. They cannot suggest engineering
content, solutions, design changes, materials, BOMs, vendors, optimization,
priority, readiness or professional judgment. Static scan tests forbid
solution-oriented catalog phrases and any model/provider/AI import.

## 20. Exact implementation file map

### Create

- `backend/app/schemas/project_completeness.py`
- `backend/app/ports/project_completeness.py`
- `backend/app/services/project_completeness_service.py`
- `backend/app/dependencies/project_completeness.py`
- `backend/app/api/v1/routers/project_completeness.py`
- `backend/tests/test_project_completeness_contracts.py`
- `backend/tests/test_project_completeness_catalog.py`
- `backend/tests/test_project_completeness_service.py`
- `backend/tests/test_project_completeness_security.py`
- `backend/tests/test_project_completeness_api.py`
- `frontend/src/components/ProjectCompletenessPanel.tsx`
- `frontend/src/test/project-completeness.test.tsx`

### Modify

- `backend/app/main.py` — router registration only;
- `frontend/src/api/types.ts` — exact DTO types only;
- `frontend/src/api/client.ts` — one read method only;
- `frontend/src/pages/ProjectsPage.tsx` — place panel only;
- `frontend/src/styles.css` — scoped accessible/responsive styles only.

No schema owner, migration, repository, ORM, Project Context contract, graph,
AI, Audit, outbox or idempotency file is required.

## 21. Verification matrix

| Evidence | Required focused proof |
|---|---|
| DTO closure | extra fields, invalid enum/type/optionality/cardinality rejected |
| catalog integrity | exactly 14, ordinals/order/IDs/versions unique, stable canonical bytes/digest |
| every rule | PRESENT and MISSING; INDETERMINATE/NOT_DISCLOSED; NOT_APPLICABLE for conditional rules |
| critical precedence | protected/unavailable/truncated/unsupported never maps to MISSING |
| stage/parent | unknown stage and invisible parent fail conservatively; missing visible parent prevents duplicate child missingness |
| all-item rules | visible counterexample missing; truncated no-counterexample indeterminate |
| sections | exactly ten, correct typed item fields only; no forbidden source |
| evidence | safe field allow-list, deterministic dedup/order, 4/56 bounds, no Human/storage/protected fields |
| questions/checklist | stable IDs/text, one/finding, correct emission/dedup/order, no workflow fields |
| service | one fresh Project Context call, all-ten request/page100/no continuation, observation times |
| result mapping | exact protected/invalid/unavailable and success/partial unions |
| security | actor mismatch, cross-Organization/Project/Workspace protected, no disclosure/log leakage |
| bounds | 14/14/14/14/56/1,000/0/131,072 exact positive and failure vectors |
| no graph/AI/write | import/prohibited-pattern checks and no EKG calls |
| transport | authentication, server-derived Organization, one route/call, payload-free outcomes, no extra OpenAPI surface |
| frontend | all states, distinct classifications, safe evidence, no-applicable/no-actionable/partial coexistence |
| accessibility | semantic groups, keyboard/focus/live status, non-color labels, responsive/RTL-ready |
| real data/firewall | no sample/demo production fallback, no score/AI/recommendation/task semantics |
| regression | focused PATCH-048 contract/security/API plus Project Workspace frontend adjacent tests |

Implementation batches run only their focused and smallest adjacent evidence;
final validation scope is assigned by the later accepted Plan.

## 22. Recommended implementation batches

### Batch 1 — Contracts, catalog and evaluator

Schemas, immutable catalog, canonical digest, typed evaluator, safe evidence and
question/checklist generators plus contract/catalog/service-unit tests. No
composition, transport or frontend.

### Batch 2 — Fresh composition, application service and transport

Public Project Context adapter/port, request-scoped composition, orchestration,
one route, main registration, security/API/service integration evidence. No
frontend and no owner/persistence changes.

### Batch 3 — Frontend and final focused evidence

Frontend types/client/panel/page/styles/tests, frontend accessibility/responsive
evidence, focused backend/frontend integration, PATCH-048 adjacent regression,
static/no-AI/no-persistence/no-PATCH-050 scope evidence and final review package.

Each batch requires an authorized manifest, implementation authority,
independent review, remediation/re-review and Human acceptance before the next.

## 23. Migration and reliability assessment

PATCH-049 is a pure read. It owns no database state, transaction, UoW, cache,
Audit, outbox, idempotency, task, persisted assessment or history. No migration
is created or modified. Alembic sole head remains `e04700000001`.

If implementation requires persistence, a new owner field/authorization port,
graph evidence, source mutation, saved assessment, background execution or
dynamic catalog, stop and return to Architecture/EDS rather than widening IDS.

## 24. Implementation stop conditions

Stop before implementation or the affected batch if any of these becomes
necessary: guessing a missing canonical field; bypassing the public PATCH-048
service; foreign repository/ORM/Session/UoW access; client Organization;
classification from hidden/unavailable data; EKG call; dynamic rule execution;
output scoring; source mutation; persistence/migration; model/provider call;
solution recommendation; PATCH-050 behavior; or a file outside an accepted
batch manifest.
