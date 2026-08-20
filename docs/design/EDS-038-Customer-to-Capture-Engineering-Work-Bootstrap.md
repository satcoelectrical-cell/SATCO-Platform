# EDS-038 — Customer-to-Capture Engineering Work Bootstrap

## 1. Status and Authority

Status: **COMPLETE — INDEPENDENT EDS REVIEW PASS / HUMAN ACCEPTANCE PENDING**.

Human PATCH-038 Architecture Acceptance and QG-M1 are PASS. The architecture
is ACCEPTED / COMPLETE and `AR038-CRIT-01` is resolved by the approved complete
legacy Customer ownership inventory. EDS-038 Design Authority is granted.

This EDS grants no IDS, migration, implementation, delivery, or PATCH-039
authority.

## 2. Bounded Product Capability

PATCH-038 provides one authenticated real-data bootstrap workflow:

`Customer → Project → Engineering Workspace → Capture → optional contextual AI Capture Assistant → Project / Engineering Command Center`.

It composes existing Project, Workspace, Capture, AI, shell, and Command Center
capabilities. Its only new canonical ownership semantic is explicit immutable
Customer Organization ownership. The frontend remains an interaction boundary,
not a source of actor, Organization, engineering, or AI authority.

## 3. Canonical Customer Semantics

### 3.1 Identity and Ownership

Customer remains the existing canonical Customer record identified by its
positive integer `id`. Each Customer has exactly one explicit non-null owning
Organization UUID referencing an existing Organization. New ownership is
derived only from the authenticated actor's active server-side Organization.
No request or browser state may supply or override it.

Customer Organization ownership is immutable in V1. It cannot be updated by a
Customer edit, Project mutation, Workspace operation, migration heuristic, or
administrative transport field. Transfer, sharing, merge/split, and
multi-Organization ownership are deferred.

Customer association never creates or establishes Project Organization.
Project retains its independently authoritative immutable Organization under
ADR-022.

### 3.2 Customer Fields and Uniqueness

PATCH-038 preserves the existing bounded Customer business fields: name,
company, phone, and email. Basic edit changes only those fields. Exact lengths,
normalization, nullability, validation, and response projections are IDS-038
obligations; Organization is never editable.

The integer primary key remains the only canonical uniqueness rule. Names,
companies, phone numbers, and email addresses are not made globally or
Organization-locally unique because no accepted business rule supports that
constraint. Selectors must disambiguate repeated names using safe authorized
presentation fields without exposing another Organization.

### 3.3 Operation Authority

Customer operations use only existing active roles and trusted active
Organization membership:

| Operation | V1 authority | Semantics |
|---|---|---|
| list/select | active `admin` or `engineer` in trusted Organization | bounded Organization-filtered choices and authorized-only count/page state |
| create | active `admin` or `engineer` in trusted Organization | create one Customer owned by that Organization; no client Organization field |
| basic edit | active `admin` or `engineer` in trusted Organization | edit only the accepted bounded fields of a Customer resolved in that Organization |
| compatibility delete | active `admin` only | not exposed by PATCH-038 UI; reject if any governed dependency exists; never cascade engineering history |

No Customer creator/owner role, approver, transfer authority, or new role is
invented. IDS must map these rows to current authenticated application
contracts and close concurrency/failure behavior without weakening them.

### 3.4 Authorization Before Disclosure

Every Customer operation starts with trusted authentication, active User,
active Organization, and enabled selected membership. Organization filtering
occurs before search, count, pagination, ordering, row materialization,
relationship validation, or Audit success.

Foreign, absent, inactive, and unauthorized Customer identities produce the
same protected non-disclosing outcome for read, edit, delete, selection, and
Project association. No response or error may reveal foreign identity, name,
fields, existence, dependency count, denial reason, or global/hidden total.
Invalid request shape is distinguishable only where it contains no protected
resource fact; dependency unavailability is payload-free.

### 3.5 Delete Compatibility

PATCH-038 does not provide a Customer delete control in the product UI and
introduces no Customer lifecycle. The existing backend delete route may remain
only as hardened compatibility behavior:

- authorize active administrator and trusted Organization first;
- resolve the Customer inside that Organization;
- reject deletion when Project, Contact, Engineering Object, or another
  governed reference exists;
- prohibit ORM or database cascades that remove Project, Workspace, Capture,
  Evidence, Report, Memory, or other engineering history;
- map absent, foreign, and unauthorized targets to one protected outcome.

Exact dependency checks, transaction boundaries, and compatibility response
shape are IDS obligations.

## 4. Approved Legacy Inventory and Migration Semantics

The following Human-approved inventory is authoritative migration input:

| Customer ID | Recorded Customer name | Owning Organization |
|---:|---|---|
| 1 | SATCO Test Customer | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| 2 | SATCO Test Customer | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| 3 | Demo Customer | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| 4 | SATCO | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| 6 | CONTACT AUDIT CUSTOMER | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |

The mapping is keyed by immutable Customer identity; names are verification
labels, not lookup keys. Migration must stop if any listed Customer is absent,
an unexpected legacy Customer exists, the Organization is absent/inactive, a
mapping is missing/duplicated, or an existing Organization-scoped Project or
Engineering Object conflicts. Contact association is preserved beneath its
mapped Customer without productizing Contacts.

The additive migration sequence is:

1. verify the sole predecessor/head is the accepted current head
   `e03400000001`;
2. expand Customer with nullable Organization FK and scoped lookup index;
3. apply the exact approved inventory in one transaction;
4. validate all Customers, Organization activity, Project/Engineering Object
   equality, Contact preservation, and absence of unmapped/conflicting rows;
5. constrain ownership non-null and immutable;
6. enforce Project/Customer same-Organization coherence at application and
   database boundaries so direct SQL cannot create a mismatch;
7. preserve one linear Alembic head and prove upgrade, downgrade, and
   re-upgrade behavior.

No migration may infer ownership from Project, Customer name, current
Organization cardinality, User membership, creator, Contact, or timestamps.
No migration may fabricate/delete Customers or Organizations or rewrite
Project ownership. Downgrade may remove PATCH-038 schema additions only after
dependent-data safety checks; it must not delete Customer or engineering data.
Migration creation/execution remains unauthorized until later gates.

## 5. Project Bootstrap Semantics

Project create and basic edit reuse current canonical Project contracts. No new
Project aggregate, status, priority, progress, owner/assignee, code, date, or
lifecycle semantics are introduced.

For create, the browser supplies only ordinary Project data and an authorized
Customer choice. The backend derives actor and Organization, resolves Customer
inside that Organization, and then creates Project with the same independently
authoritative Organization:

`actor.organization_id == customer.organization_id == project.organization_id`.

Customer validation occurs before Customer or Project disclosure and must be
rechecked within the authoritative mutation/transaction boundary. A foreign,
absent, or unauthorized Customer cannot be distinguished. Database persistence
must independently prevent cross-Organization Project/Customer rows.

The bootstrap UI requires name and Customer and uses existing defaults for
priority and owner. It may expose description and dates. Essential edit may
expose only fields already authorized by the Project application contract;
owner/assignee, status, progress, date, transition, delete, and history rules
remain exactly canonical and are not redefined by the frontend. Project IDs and
codes are navigation identities, not authority claims.

## 6. Workspace Bootstrap Semantics

Workspace remains a Project child and derives Organization through the
authorized Project. PATCH-038 provides:

- bounded listing and selection inside Project detail;
- creation using the existing discipline, optional description, existing
  owner default, optional assignee, and current canonical authorization;
- transition into the Workspace/Capture work area.

The normal bootstrap form need not expose owner, assignee, or collaborators;
defaults remain server/application owned. Project ID from the route is an
untrusted reference and is resolved within trusted Organization before any
Workspace data or counts are disclosed.

Full collaborator administration, archive/restore, lifecycle transitions,
bulk actions, transfer, and new Workspace semantics are deferred from the UI.
Existing backend operations remain unchanged and separately authorized.

## 7. Capture Bootstrap Semantics

Within an authorized selected Workspace, the engineer may create one canonical
Capture using the accepted PATCH-028 contract:

- source kind;
- original content;
- optional source reference;
- trusted Project and Workspace context;
- no required Engineering Object attachment in the bootstrap UI.

The UI requires a Workspace for the normal PATCH-038 flow even though the
canonical backend continues to support its accepted optional Workspace
contract elsewhere. Project and Workspace identities are derived from current
navigation and treated as untrusted references; the Capture application must
independently validate actor, Organization, Project, Workspace, membership,
discipline/context compatibility, and operation authority before persistence or
disclosure.

After success, the canonical Capture is displayed with its exact identity,
standing, version, source kind, and permitted current actions from the accepted
response. The Capture remains useful without AI. PATCH-038 adds no Capture
edit, withdrawal, supersession, bulk intake, document parsing, Evidence,
Engineering Object, or lifecycle semantics.

## 8. Contextual AI Handoff

An authorized created or selected Capture may expose an optional contextual
“Request AI assistance” action. The frontend may carry Capture, Project, and
Workspace navigation values to the existing PATCH-035 Assistant surface and
prefill them. The normal user is not required to type a Capture UUID or numeric
Project/Workspace/Organization identifier already known to the product.

Navigation state is untrusted. The existing AI application boundary must again
derive actor and Organization server-side, resolve and authorize the exact
current Capture, prove Project/Workspace equality, minimize provider context,
and fail closed before provider disclosure. Direct/deep links with stale,
foreign, malformed, or mismatched context disclose nothing.

The Human supplies the instruction and explicitly invokes AI. Output remains
ephemeral, attributable, uncertainty-aware, visibly advisory, and
non-authoritative. It is never silently persisted to Capture, accepted as a
Technical Report, admitted to Memory, communicated externally, or treated as
engineering approval.

## 9. Frontend Composition and Navigation Continuity

PATCH-038 extends existing surfaces rather than creating a broad CRM:

1. **Projects / work initiation:** authorized Customer selector, inline
   Customer creation, Project creation, and truthful Customer/Project empty
   states. Basic Customer correction may use the same bounded interaction;
   there is no general CRM workspace.
2. **Project detail / engineering work:** Project summary, Workspace
   list/creation/selection, Capture list/creation/display, optional contextual
   AI action, and explicit return to Project/Command Center.
3. **Existing Assistant:** accepts context-prefill navigation while preserving
   manual deep-link fail-closed behavior and PATCH-035 result presentation.

Successful creation updates or refetches canonical data; the frontend must not
invent optimistic canonical IDs, standing, counts, timestamps, or success.
Refresh/back navigation reconstructs state from authorized APIs rather than
browser-owned engineering data. Raw internal IDs may appear in URLs or
diagnostic detail where already accepted, but normal actions use selections and
context, never manual ID entry.

## 10. Truthful First-Use and Result States

The UI progression is deterministic and real-data-only:

- no Customer → create Customer;
- Customer but no Project → create Project;
- Project but no Workspace → create Workspace;
- Workspace but no Capture → create Capture;
- Capture → continue engineering work or optionally request AI assistance.

No fixture, generated demonstration record, local hard-coded business entity,
fake KPI, placeholder count, or synthetic success may enter production paths.
Loading, empty, invalid, protected, unavailable, conflict, and success states
remain visually distinct where disclosure permits. Protected states do not
name a denied entity, expose counts, or explain authorization. Retriable errors
must not imply that a mutation did or did not commit unless the canonical result
establishes it.

## 11. Accessibility and Responsive Semantics

All new interactions reuse PATCH-036/037 design primitives and must provide:

- programmatic labels, instructions, validation association, and required-state
  indication;
- keyboard-complete selection, dialogs/forms, submission, cancellation, and
  return navigation with visible focus and logical focus restoration;
- live-region status for bounded loading/success/error feedback without
  announcing protected details;
- non-color-only status and action affordances;
- responsive composition without horizontal page overflow, clipped controls,
  overlapping text, or loss of action order;
- reduced-motion compatibility and existing shell/sidebar behavior.

Desktop may present Customer/Project initiation beside contextual guidance;
narrow layouts stack it in workflow order. Responsive changes do not remove
authorization, validation, Human/AI labels, or protected-state semantics.

## 12. Audit, Transactions, and Failure Semantics

Customer create, basic edit, and compatibility delete use the existing shared
Audit capability. Project, Workspace, Capture, and AI operations retain their
accepted Audit requirements. Audit must identify actor, Organization,
operation, safe target identity where permitted, outcome/category, and bounded
changed-field metadata. Phone, email, Capture content, Human instruction, AI
output, credentials, tokens, and protected foreign identity must not be added
to Audit plaintext by PATCH-038.

No success may be returned before its canonical transaction succeeds.
Customer mutation and its required Audit record must be transactionally
coherent; the current repository-owned commit behavior is not automatically an
accepted transaction design. Project/Customer equality is rechecked within the
Project mutation boundary. Failure rolls back the primary mutation and maps to
a stable non-disclosing outcome. Exact UoW signatures, concurrency control,
idempotency applicability, rollback sequencing, and Audit failure handling are
IDS-038 obligations aligned with current repository foundations.

## 13. Security and Request Bounds

- Authentication and active Organization membership precede all operations.
- Client Organization, actor, role, ownership, and authorization claims are
  ignored/rejected.
- Customer selectors are bounded and Organization-filtered before counts.
- Each bootstrap step makes only the canonical calls required for the visible
  state; no polling or unbounded fan-out is introduced.
- Cross-Organization IDs, altered navigation state, stale links, and mismatched
  hierarchy fail closed.
- Frontend caches/local storage hold no Customer, Project, Workspace, Capture,
  authorization, or AI payload as authoritative state.
- Existing CSRF/CORS/token/session and secret-handling boundaries remain in
  force; no provider credential or production business fixture is committed.

Exact page sizes, call bounds, request/result schemas, status mappings, and
security verification belong to IDS-038.

## 14. Explicit Deferred Boundary

PATCH-038 excludes Technical Report authoring/revision/acceptance UI;
Organizational Memory admission/lifecycle UI; Customer transfer/sharing,
merge/split, lifecycle, contacts, activities, sales pipeline, CRM automation,
billing, or customer communication; Organization invitation/selection,
entitlements, or administration; full Workspace collaboration/lifecycle;
Capture correction lifecycle; broad Context, Evidence, graph, or document
analysis; persistent/autonomous AI, conversations, automated report creation,
semantic/vector search, ranking, BPM/tasks/ERP, PLC generation, PATCH-039, and
all other unregistered capability.

## 15. IDS-038 Obligations

IDS-038 must define, without changing this EDS:

- exact Customer actor/context/request/result DTOs, field types, normalization,
  operation authority matrix, protected outcomes, pagination, deterministic
  ordering, concurrency, Audit, UoW, and dependency-safe delete contracts;
- exact schema/model/index/FK/immutability and cross-row Project/Customer guard;
- the additive migration, exact inventory validation, upgrade/downgrade,
  role/ownership, rollback, one-head, and direct-SQL verification contracts;
- exact Project create/edit UI projection and same-Organization validation
  sequencing using current Project application boundaries;
- exact Workspace and Capture selection/create DTO mappings and canonical call
  bounds;
- contextual AI route/state contract, mismatch behavior, independent
  reauthorization, and protected translation;
- frontend route/component/API ownership, form validation, state transitions,
  accessibility, responsive breakpoints, and navigation restoration;
- executable positive, negative, cross-Organization, enumeration, migration,
  transaction, Audit, concurrency, fake-data, regression, and end-to-end
  real-data bootstrap evidence.

IDS must stop rather than invent a canonical boundary that the repository does
not supply.
