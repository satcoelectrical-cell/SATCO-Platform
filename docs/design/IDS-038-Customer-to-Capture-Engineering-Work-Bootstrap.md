# IDS-038 — Customer-to-Capture Engineering Work Bootstrap

## 1. Status and Executable V1

Status: **ACCEPTED / COMPLETE** after Independent Review PASS and standing
Human IDS Acceptance.

V1 operations are the existing bounded operations needed for:

- `list_customers`, `create_customer`, `update_customer`, compatibility
  `delete_customer`;
- existing `create_project`, `list_projects`, `get_project`, `update_project`;
- existing `create_workspace`, `list_project_workspaces`;
- existing `create_capture`, Project/Workspace Capture reads;
- existing `advise_capture` reached through contextual frontend handoff.

No new Report, Memory, Context/Evidence, AI, workflow, or CRM operation exists.

## 2. Trusted Context and Protected Results

All PATCH-038 backend operations use
`AuthenticatedOrganizationContext { user, organization_id: UUID }` from the
server. User is active; selected membership is enabled; Organization is active.
The client never supplies actor, role, or Organization authority.

Absent, foreign, and unauthorized Customer/Project/Workspace/Capture identities
must be indistinguishable. Existing HTTP contracts use `404`/protected response
translation; invalid request is `400` or `422`; unavailable remains
non-disclosing. Customer error messages must not contain requested foreign IDs,
names, counts, dependency types, or denial reasons. Frontend maps 401 to session
loss, 403/404 to `protected`, 400/422 to `invalid`, and 503/network failure to
`unavailable`.

## 3. Customer Contracts

### 3.1 Persistence record

`CustomerRecord`:

- `id: int`, positive, database-generated primary key;
- `organization_id: UUID`, non-null FK `organizations.id`, immutable;
- `name: str`, trimmed, 1–200 characters;
- `company: str | None`, trimmed/non-empty when present, maximum 200;
- `phone: str | None`, trimmed/non-empty when present, maximum 64;
- `email: str | None`, trimmed/non-empty when present, maximum 320;
- `created_at: datetime`, non-null server timestamp.

The response exposes `id`, name/company/phone/email, and `created_at`; it does
not expose `organization_id`. Requests use `extra="forbid"` and contain no
Organization field. `CustomerCreate` requires name. `CustomerUpdate` permits
only name/company/phone/email, requires at least one supplied field, and cannot
set name null/blank. No natural uniqueness exists.

### 3.2 Repository/service

Repository methods are no-commit collaborators:

- `list_scoped(organization_id, page, size, search) -> (items, authorized_total)`;
- `get_scoped(customer_id, organization_id) -> Customer | None`;
- `create(data, organization_id) -> Customer` using `flush`;
- `update(customer, changes) -> Customer` using `flush`;
- `has_governed_references(customer_id) -> bool` covering Projects, Contacts,
  Engineering Objects, and extant FK references;
- `delete(customer) -> None` using `flush`.

List order is `name ASC, id ASC`; page is `>=1`; size is `1..100`. Search is
trimmed, maximum 200, and applies only after Organization filtering. Total is
the filtered authorized total and never a global total.

Service authority uses only active `admin`/`engineer` for list/create/update;
compatibility delete is active `admin` only. Create/update/delete and shared
Audit commit atomically in one Session. Audit action/entity are
`CREATE|UPDATE|DELETE` / `CUSTOMER`; details contain only Organization-safe
target ID and bounded changed-field names, never phone, email, foreign IDs,
Capture content, instructions, or AI output.

Delete is not exposed by the frontend. It fails protected when unauthorized,
foreign/absent, or referenced and never cascades Project, Contact, Engineering
Object, Workspace, Capture, Report, Memory, or other history.

## 4. Migration Contract

Revision: `e03800000001`; parent: `e03400000001`; sole head after upgrade:
`e03800000001`.

Upgrade:

1. add nullable UUID `customers.organization_id`;
2. add FK `fk_customers_organization_id_organizations`, `ON DELETE RESTRICT`;
3. if Customers exist, require the exact ID set `{1,2,3,4,6}` and the exact
   Human-approved name labels, require active Organization
   `7e7c9d7a-7693-4f75-9bc5-3ef7bf528281`, then map all five;
4. if no Customers exist, perform no backfill;
5. reject missing/unexpected rows, null mappings, inactive/missing Organization,
   Project or Engineering Object Organization conflicts, or lost Contacts;
6. set `organization_id` non-null;
7. create deterministic index
   `ix_customers_organization_name_id(organization_id, name, id)`;
8. create schema-owner functions/triggers:
   `satco_customer_org_immutable()` / `trg_customers_org_immutable` and
   `satco_project_customer_org_guard()` / `trg_projects_customer_org_guard`;
9. Project trigger rejects INSERT/UPDATE when referenced Customer is absent or
   its Organization differs from `NEW.organization_id`;
10. Customer trigger rejects Organization changes; runtime cannot alter/drop
   guarded DDL/functions/triggers;
11. preserve owner `satco`, restricted `satco_runtime` DML, and no runtime DDL.

Downgrade drops only PATCH-038 triggers/functions/index/FK/column after normal
database dependency enforcement. It never deletes or remaps Customers,
Projects, Contacts, Engineering Objects, or engineering history. Upgrade,
downgrade, re-upgrade and direct-SQL negative cases are mandatory evidence.

## 5. Project/Customer Contract

`ProjectService.create` and Customer-changing `update` call
`CustomerRepository.get_scoped(customer_id, organization_id)`. Failure raises
the existing related-entity protected-not-found shape without disclosing
foreign Customer state. The equality invariant is:

`actor.organization_id == project.organization_id == customer.organization_id`.

Customer is validated before Project creation/update and the database trigger
provides final persistence enforcement. Existing Project fields, owner and
assignee authority, code allocation, lifecycle, dates, priority, progress,
Audit, and response contracts remain unchanged.

Frontend create requires Customer and name; it may send description, priority,
start date and target date. Owner defaults to actor; assignee is omitted in the
normal bootstrap. Basic edit uses only the existing Project update contract.

## 6. Workspace and Capture Contracts

Workspace creation uses existing
`POST /projects/{project_id}/workspaces` with `discipline`, optional
`description`, and server defaults. Normal UI omits owner/assignee/collaborator
administration. Listing uses existing bounded Project Workspace list.

Capture creation uses existing `POST /engineering-experience-captures` with:

- `project_id` from selected Project;
- `workspace_id` from selected Workspace and required in the normal UI;
- `engineering_object_id = None` in the bootstrap UI;
- accepted `source_kind`;
- `original_content` length `1..10_000`;
- optional `source_reference` length `1..512`.

The backend independently authorizes and validates the hierarchy. The UI
renders only canonical response identity/standing/version/content. Withdrawal,
supersession, object attachment, bulk and document intake remain absent.

## 7. Contextual AI Handoff

The Capture action navigates to `/assistant` with prefilled route/query state:
`capture_id`, `project_id`, and `workspace_id`. These values are convenience
only. No Organization/actor/role value is carried. The Assistant retains the
Human instruction input and calls the existing PATCH-035 endpoint, which
independently reauthorizes exact Capture and scope before provider disclosure.

Malformed, stale, foreign, or mismatched context produces the existing
protected/invalid response. Successful output remains visibly advisory and is
not persisted or promoted. Direct manual entry fields are not part of the
normal contextual flow; a non-contextual visit presents guidance to select a
Capture from Project work rather than requesting raw IDs.

## 8. Frontend Contract

No broad Customer route is required. Existing routes remain:

- `/projects`: Customer/Project initiation, authorized Project list;
- `/projects/:projectId`: Project summary, Workspace creation/selection,
  Capture creation/display and contextual AI action;
- `/assistant`: contextual advisory request and return link;
- `/`: Command Center continuation.

Required components may be colocated or extracted but must include strict
Customer, Project, Workspace and Capture forms; canonical API adapters/types;
actionable real empty states; loading/protected/invalid/unavailable/success
states; accessible labels/errors/focus/live regions; and responsive stacking.
After mutations, state is populated only from canonical responses/refetches.
No hard-coded Customer/Project/Workspace/Capture business record or fake count
is allowed.

## 9. Request Bounds and Navigation

Initial Projects load uses existing bounded Project page plus one bounded
Customer page. Project detail uses one Project read, one Workspace page, and one
Capture page. Mutation forms make one mutation call; successful creation may
perform one bounded refresh per affected list. No polling or unbounded fan-out.

Customer, Project, Workspace, and Capture IDs may occur in routes/requests but
are never authorization evidence. Back/return links preserve only navigation
identity. Protected failures clear dependent UI and expose no count or name.

## 10. Verification Matrix

| Area | Required executable evidence |
|---|---|
| migration | exact head/parent; clean and exact-five-row upgrade; inventory/name/Organization drift rejection; downgrade/re-upgrade; no data loss |
| DB integrity | null/FK rejection; Customer Organization update rejected; Project/Customer mismatch rejected by direct SQL; exact trigger/function ownership and runtime denial |
| Customer API | active scoped create/list/update; bounded deterministic selector; foreign list/read/update/delete non-disclosure; spoofed Organization rejected/ignored; admin-only referenced-delete rejection; atomic Audit |
| Project invariant | same-Organization create/update succeeds; foreign Customer protected; direct SQL mismatch rejected; existing Project regressions |
| Workspace | create/list/select in authorized Project; foreign/denied Project protected; no collaborator/lifecycle UI |
| Capture | create/display in authorized Workspace; foreign/mismatched context protected; accepted field bounds and no correction UI |
| AI | context prefill; no raw-ID normal flow; tampered context protected; independent canonical reauthorization; advisory label/no persistence |
| UX | complete no-data progression; canonical refresh; return to Project/Command Center; loading/empty/protected/error/success states |
| quality | keyboard/focus/labels/live regions, responsive/no overflow, no fake data, no deferred routes/actions |
| closure | focused/adjacent/full regressions, migration head, frontend tests/build/typecheck, static/import, secrets/scope/prohibited patterns, `git diff --check`, QG-M1 |

## 11. Authorized Implementation Surfaces

Expected backend surfaces are Customer model/schema/repository/service/router,
Project service, one migration, and focused tests. Existing Workspace/Capture/AI
production contracts should not require modification unless IRR proves a
bounded integration gap. Expected frontend surfaces are API types/client,
Projects/Project Detail, Assistant contextual handoff, styles, and focused
tests. `main.py` needs no new route registration.

## 12. Deferred Boundary

All EDS-038 deferments remain exact. In particular no Reports/Memory mutation,
broad CRM/Contacts, Organization administration, Customer transfer/sharing,
full Workspace administration, Capture correction, Context/Evidence/document
workbench, persistent/autonomous AI, semantic/vector retrieval, BPM/tasks/ERP,
PLC generation, customer communication, or PATCH-039 capability is executable.
