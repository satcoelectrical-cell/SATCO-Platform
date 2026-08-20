# Architecture-038 — Customer-to-Capture Engineering Work Bootstrap

## 1. Status and Authority

Architecture discovery is complete within registered PATCH-038. QG-M1 and the
Focused Independent Architecture Re-review pass after the Human approved the
complete legacy Customer ownership inventory. `AR038-CRIT-01` is resolved.
Human Architecture Acceptance is PASS and the architecture is ACCEPTED /
COMPLETE. EDS-038 Design Authority is granted. This document grants no IDS,
migration, implementation, delivery, or later-PATCH authority.

## 2. Problem and Product Objective

The authenticated web application can display Projects, Workspaces, Captures,
Reports, Memory, and AI advice, but it cannot create the real Customer,
Project, Workspace, or Capture data needed to start engineering work. The
normal AI route additionally requires manual internal identifiers.

PATCH-038 supplies one bounded bootstrap journey:

`authenticated actor → active Organization → Customer → Project → Workspace → Capture → optional AI advice → Project / Command Center`.

It does not redesign the canonical Project, Workspace, Capture, or AI domains.

## 3. Current-State Evidence

- `customers` has a global integer identity, no `organization_id`, no natural
  uniqueness constraint, and globally scoped repository/service/router reads
  and mutations.
- Customer repository mutations own commits and current authenticated Customer
  operations do not derive active Organization context.
- Project has immutable accepted Organization ownership, while its Customer
  validation currently resolves a global Customer identity.
- Workspace derives Organization through its authoritative Project.
- Capture carries and validates Organization, Project, and optional Workspace
  context. PATCH-035 authorizes an exact Capture before provider disclosure.
- The frontend lists Projects, Workspaces, Captures, Reports, and Memory but
  exposes no Customer, Project, Workspace, or Capture creation flow.
- Current local data contains five Customers and seven Projects, but zero
  Workspaces, Captures, Technical Reports, or Organizational Memory records.
  Two Customers have Project references confined to one Organization; three
  Customers have no Project reference.

## 4. Canonical Customer Tenancy Decision

### 4.1 Ownership

Each Customer has exactly one explicit owning Organization in V1:

`customers.organization_id → organizations.id`.

The value is non-null in the constrained state, derived from trusted active
Organization context for new Customers, and never supplied or overridden by a
client. Customer Organization ownership governs Customer lookup, listing,
selection, creation, update, guarded legacy deletion, search/count semantics,
and Project association.

Customer does not establish, infer, replace, or transfer Project tenant
authority. Project retains its own independently authoritative immutable
`organization_id` under ADR-022.

### 4.2 Immutability and Transfer

Customer Organization ownership is immutable after creation in V1. Transfer,
shared/multi-Organization Customers, duplication across Organizations, and
merge/split semantics are deferred. If the business requires any of them, the
architecture returns to Human review rather than weakening the invariant.

### 4.3 Identity and Uniqueness

The existing Customer primary key remains the canonical identity. No accepted
evidence makes name, company, email, or phone globally or Organization-locally
unique, so PATCH-038 introduces no new natural-key uniqueness rule. An
Organization-leading lookup/index is required for bounded scoped reads; exact
index form and deterministic selector ordering belong to EDS/IDS.

## 5. Legacy Ownership and Migration Decision

The intended architecture is additive:

1. **expand** — add a nullable Customer Organization FK and supporting scoped
   index without changing current data;
2. **map** — apply a separately Human-accepted complete inventory containing
   every legacy Customer identity and exactly one existing active Organization;
3. **validate** — reject missing, duplicate, inactive, fabricated, conflicting,
   or cross-Organization mappings; verify every referencing Project and every
   Organization-scoped Engineering Object retains its existing authoritative
   Organization; and preserve Contact association under the mapped Customer
   without productizing Contacts;
4. **constrain** — make ownership non-null and immutable, install scoped
   authorization/data-integrity guards, and retain a single Alembic head;
5. **rollback** — remove only PATCH-038 additions after safe dependency checks;
   rollback never deletes Customers or rewrites Project ownership.

Project association is useful consistency evidence but is not sufficient
Human business authority for migration. The current single-Organization
topology is also not authority to assign unreferenced Customers. The Human has
therefore approved this complete authoritative inventory:

| Legacy Customer | Approved immutable owning Organization |
|---|---|
| `1` — SATCO Test Customer | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| `2` — SATCO Test Customer | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| `3` — Demo Customer | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| `4` — SATCO | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |
| `6` — CONTACT AUDIT CUSTOMER | `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281` |

The Human confirms that all five belong to this existing active Organization,
none requires multi-Organization ownership, and ownership is immutable in V1.
Transfer, sharing, merge/split, and multi-Organization ownership remain
deferred. No migration is created or executed here.

## 6. Authorization Before Disclosure

All Customer operations begin with trusted authenticated actor and active
server-derived Organization context.

- **list/select/search/count:** filter by Organization before count,
  pagination, search, ordering, or materialization; never expose global or
  hidden totals;
- **read:** query by Customer identity plus Organization; foreign and absent
  identities collapse to the same protected-not-found behavior;
- **create:** derive Organization server-side; accept no Organization field;
- **update:** lock/query in Organization scope, apply the existing bounded
  Customer fields only, and never permit Organization change;
- **delete compatibility:** not exposed by the PATCH-038 product UI; the
  existing backend route must become Organization-scoped, administrator-only,
  and fail closed when any Project, Contact, Engineering Object, or other
  governed reference exists. Cascade deletion of engineering history is
  prohibited.

Active existing `admin` and `engineer` roles may list/select/create and perform
the minimal correction operation already allowed by the Customer contract;
delete is administrator-only compatibility behavior. EDS must close the exact
operation matrix without inventing roles or a Customer owner concept.
Protected errors must not distinguish absent, foreign, unauthorized, or
relationship-mismatch identities.

## 7. Project/Customer Association Invariant

Project Organization remains derived from trusted actor context. Before
Project create or Customer reassignment, the canonical Customer read must
resolve within that same Organization:

`project.organization_id == customer.organization_id == actor.organization_id`.

The validation occurs before Customer or Project disclosure. A mismatched,
foreign, absent, or unauthorized Customer produces the same protected result.
Customer identity is a required association; it is never a source of Project
Organization authority.

PATCH-038 reuses existing Project code, status, priority, progress,
owner/assignee, and date semantics. The bootstrap UI requires name, authorized
Customer, and existing defaults; it may expose description, priority, and
dates. Owner defaults to the actor and assignee is optional. No new lifecycle,
status taxonomy, transfer, or deletion behavior is introduced.

## 8. Trusted Bootstrap Hierarchy

| Transition | Authoritative parent/context | Authorization and protected outcome | Navigation identity |
|---|---|---|---|
| actor → Organization | authenticated selected active membership | server authentication and active membership; failure reveals no Organization data | no client Organization input |
| Organization → Customer | Customer immutable owning Organization | scoped Customer application operation; absent/foreign/denied collapse | Customer ID carried internally |
| Customer → Project | Project immutable Organization plus same-Organization Customer check | Project create/update authority after scoped Customer validation | Project ID/route |
| Project → Workspace | Project is authoritative parent; Workspace derives Organization | canonical Workspace operation in trusted Project scope | Workspace ID carried by Project UI |
| Workspace → Capture | authorized Project/Workspace context | canonical Capture create authorization before content persistence/disclosure | Capture UUID returned to UI |
| Capture → AI | exact currently authorized Capture plus server-trusted scope | PATCH-035 reauthorizes before provider disclosure; failures remain protected | contextual route/state, never an authority claim |

Internal IDs remain valid transport/navigation identifiers, but the normal
user journey never requires manual entry of Organization, Customer, Project,
Workspace, or Capture identifiers already known to the application.

## 9. Workspace and Capture Productization

The Project detail surface lists authorized Workspaces and permits creation
using the accepted discipline, optional description, and existing ownership
defaults. Full collaborator administration, archive/restore, and general
lifecycle management are not required for bootstrap.

Within a selected Workspace, the engineer may create one real Capture using
the accepted source kind, original content, and optional source reference. The
trusted Project and Workspace context is supplied by application navigation,
then independently validated by the backend. Engineering Object attachment,
withdrawal, supersession, bulk capture, document analysis, and new Capture
semantics are deferred.

The resulting Capture is displayed with its canonical standing and permitted
actions. It remains usable without AI.

## 10. Contextual AI Handoff

An authorized Capture may offer an optional “Request AI assistance” action.
The frontend carries Capture/Project/Workspace navigation context to the
existing Assistant surface and preselects the exact Capture. It does not carry
actor or Organization authority and cannot bypass PATCH-035 reauthorization.

The assistant preserves explicit Human instruction, bounded single-Capture
context, advisory attribution, uncertainty/limitations, provider protection,
and non-authoritative output. No output is silently written back, accepted,
published, admitted to Memory, or treated as engineering truth.

## 11. Frontend Composition and First Use

PATCH-038 extends two primary product surfaces rather than creating a broad
administration application:

1. **Projects / work-initiation surface:** actionable no-Customer/no-Project
   state, authorized Customer selection with inline creation, and Project
   creation. A standalone CRM/Customer area is not required.
2. **Project detail / engineering work area:** Workspace creation/selection,
   Capture creation and display, optional contextual AI action, and return to
   Project/Command Center.

Existing shell, design tokens, API-result conventions, protected states,
responsive behavior, accessibility, and Command Center composition are reused.
No fake or seeded production records are introduced.

Truthful progression is: no Customer → create Customer; Customer but no
Project → create Project; Project but no Workspace → create Workspace;
Workspace but no Capture → create Capture; Capture → continue work or
optionally request AI assistance.

## 12. Security and Reliability Principles

- deny by default and authorize before existence, identity, fields, counts, or
  relationship disclosure;
- scope every Customer query and Project association by trusted Organization;
- keep Project, Workspace, Capture, and AI authorization independently active;
- preserve Audit requirements and accepted transaction ownership; EDS/IDS
  shall resolve exact Customer mutation/UoW behavior rather than inherit the
  current repository-owned commits by accident;
- reject client Organization fields and cross-Organization selectors;
- never turn navigation state into authorization evidence;
- preserve real data, migration rollback safety, accessibility, and
  non-disclosing error equivalence.

## 13. Risks and Downstream EDS Obligations

EDS-038, if later authorized, must close:

- the Human-approved complete legacy Customer ownership inventory, validation
  against Project/Engineering Object references, inherited Contact handling,
  and secure migration input/audit record;
- exact Customer aggregate ownership, operation authority, protected outcomes,
  schemas, repository/UoW transaction behavior, Audit behavior, and deletion
  compatibility;
- scoped list/search/count/pagination, deterministic selector ordering, indexes,
  FK/immutability constraints, migration validation, rollback, and one-head
  sequencing from `e03400000001`;
- same-Organization Project association sequencing and race/failure behavior;
- exact UI/API workflow contracts, contextual navigation integrity, request
  bounds, accessibility, responsiveness, and negative/security verification;
- preservation tests for Project, Workspace, Capture, AI, Dashboard, and all
  explicit deferments.

EDS-038 Design Authority is granted by the subsequent Human Architecture
Acceptance. IDS, migration, and implementation authority remain not granted.

## 14. Explicit Deferred Boundary

Technical Report and Memory mutation UI; broad Customer/CRM/Contact activity;
Organization administration; Customer transfer/sharing/merge; full Workspace
administration; Capture correction lifecycle; broad Context/Evidence/document
workbenches; autonomous or persistent AI; search/ranking/vector/graph
expansion; workflow/task/ERP/PLC/customer-communication capability; PATCH-039
and all other unregistered scope remain deferred.
