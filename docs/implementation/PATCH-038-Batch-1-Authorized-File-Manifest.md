# PATCH-038 Batch 1 Authorized File Manifest

Batch: Customer Tenancy and Project Integrity — S01–S03.

Authorized production files:

- MODIFY `backend/app/models/customer.py`
- MODIFY `backend/app/schemas/customer.py`
- MODIFY `backend/app/repositories/customer_repository.py`
- MODIFY `backend/app/services/customer_service.py`
- MODIFY `backend/app/api/v1/routers/customers.py`
- MODIFY `backend/app/services/project_service.py`
- CREATE `backend/migrations/versions/e03800000001_customer_organization_ownership.py`

Authorized tests:

- MODIFY `backend/tests/conftest.py` solely to keep pre-PATCH-038 direct-model
  fixtures explicit and deterministic in the test Organization; no production
  ownership default is authorized.
- MODIFY `backend/tests/test_project_core.py` solely to supply the now-required
  Organization to its direct-SQL concurrency fixture.
- MODIFY `backend/tests/test_customers.py`
- CREATE `backend/tests/test_customer_organization_migration.py`
- CREATE `backend/tests/test_customer_organization_security.py`
- MODIFY `backend/tests/test_project_organization_scope.py`
- MODIFY `backend/tests/test_technical_report_migration.py`
- MODIFY `backend/tests/test_organizational_memory_migration.py`
- MODIFY `backend/tests/test_engineering_relationship_transaction.py` solely
  to keep its legacy Project fixture coherent with canonical Customer
  Organization ownership.
- MODIFY `backend/tests/test_patch_028_1_migration.py` solely to exercise the
  PATCH-028 historical revision before restoring the current repository head.
- MODIFY `backend/tests/test_technical_report_database_roles.py` solely to
  create its adjacent Customer fixture with explicit Organization ownership.

The final three adjacent-test surfaces were reconciled during Batch 4 after
the full regression exposed stale pre-PATCH-038 fixture assumptions. They
change no production or historical migration semantics.

Only Customer tenancy/migration, Customer scoped CRUD compatibility, and
Project/Customer equality are allowed. No frontend, Contact productization,
Workspace/Capture/AI change, broad UoW redesign, or later batch behavior.

Acceptance requires focused migration/security/API/Project tests, direct-SQL
guards, role drift, adjacent migrations/Projects, one head, static/import,
scope checks and `git diff --check`. Stop for inventory mismatch, destructive
data behavior, bypassable guards, role collapse, or out-of-boundary need.
