# EDS-024 — EngineeringObject Persistence Migration

## Status

Accepted

## Objective

Define an exact, additive persistence design for the already approved
EngineeringObject model without changing Domain semantics.

## Inputs

- approved PATCH-024;
- AR-024 PASS;
- approved PATCH-022.3 model contract;
- current EngineeringObject SQLAlchemy metadata;
- Alembic head `b2022c0202f2`.

## Table Contract

The migration shall create `engineering_objects` with exactly these columns:

| Column | Database type | Nullability | Database default | Key/reference |
|---|---|---|---|---|
| `id` | PostgreSQL UUID | NOT NULL | none | primary key |
| `organization_id` | PostgreSQL UUID | NOT NULL | none | none |
| `customer_id` | Integer | NULL | none | `customers.id`, ON DELETE RESTRICT |
| `project_id` | Integer | NOT NULL | none | `projects.id`, ON DELETE RESTRICT |
| `workspace_id` | Integer | NOT NULL | none | `engineering_workspaces.id`, ON DELETE RESTRICT |
| `family` | String(32) | NOT NULL | none | controlled by checks |
| `discipline` | String(32) | NOT NULL | none | controlled by checks |
| `object_type` | String(64) | NOT NULL | none | controlled by checks |
| `subtype` | String(64) | NULL | none | constrained to NULL in v1 |
| `lifecycle` | String(16) | NOT NULL | `proposed` | controlled by check |
| `authority_standing` | String(16) | NOT NULL | `draft` | controlled by check |
| `version` | Integer | NOT NULL | `1` | positive check |
| `creator_id` | Integer | NOT NULL | none | `users.id`, ON DELETE RESTRICT |
| `steward_id` | Integer | NOT NULL | none | `users.id`, ON DELETE RESTRICT |
| `created_at` | timestamp with time zone | NOT NULL | `now()` | none |
| `updated_at` | timestamp with time zone | NOT NULL | `now()` | none |

The model's Python UUID generation and `updated_at` ORM `onupdate` behavior are
not database defaults or triggers and shall not be invented by the migration.

## Controlled Values and Constraints

Controlled values remain string-backed. The migration shall reproduce the
model's named checks for:

- approved family values;
- approved discipline values;
- approved object-type values;
- family-to-discipline compatibility;
- family-to-object-type compatibility;
- `subtype IS NULL` for Blueprint v1.0;
- approved lifecycle values;
- approved authority-standing values;
- `version >= 1`;
- `updated_at >= created_at`.

The migration shall reproduce the model's five named foreign keys for Customer,
Project, Workspace, Creator, and Steward. No Organization foreign key exists.

## Indexes

The migration shall create only:

- `ix_engineering_objects_organization_project` on
  (`organization_id`, `project_id`);
- `ix_engineering_objects_project_workspace` on
  (`project_id`, `workspace_id`);
- `ix_engineering_objects_classification` on
  (`family`, `discipline`, `object_type`);
- `ix_engineering_objects_lifecycle_authority` on
  (`lifecycle`, `authority_standing`).

The primary-key index is provided by PostgreSQL. No additional index is
authorized.

## Upgrade and Downgrade

Upgrade creates the table with its table constraints, then the four named
indexes. Downgrade drops the four named indexes and then drops only the table.
The implementation shall follow current Alembic conventions and shall not
inspect or mutate application data.

## Validation

Validation requires static revision review, model/DDL comparison, isolated
upgrade, schema inspection, constraint and foreign-key checks, downgrade,
re-upgrade, one-head verification, focused tests, and regression tests.

## Stop Conditions

Stop for any model mismatch, missing referenced table, second Alembic head,
need for data migration, new field or constraint, non-isolated execution, or
change outside the single authorized migration file.

## Acceptance

EDS-024 is accepted. Its design is a strict persistence representation of the
current approved model.

