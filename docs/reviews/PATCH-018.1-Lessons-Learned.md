# PATCH-018.1 Lessons Learned

**Project:** SATCO Platform
**Patch:** PATCH-018.1 — Project Core Enhancement
**Date:** 2026-07-26

## 1. ORM Intent Does Not Prove Migrated State

The Project model already declared `status` as non-null, but the migration left
the legacy database column nullable. Migration validation must inspect the
actual PostgreSQL catalog and exercise critical constraints directly.

## 2. Check Constraints Do Not Replace NOT NULL

In PostgreSQL, a check expression that evaluates to unknown does not reject the
row. A status-value check alone therefore permits `NULL`. Required fields need
an explicit `NOT NULL` column contract; including `status IS NOT NULL` in the
check also makes the domain intent clear.

## 3. Partial Identifiers Are Not Unique

A partial Project Code such as `PRJ-2026` can match many Projects. Search tests
must verify inclusion of the intended result, while exact-code tests may assert
a single result because the complete code is unique.

## 4. Concurrency Tests Need Committed Shared Fixtures

Worker threads use independent PostgreSQL connections. Fixtures held inside a
test transaction are invisible to those connections. Shared prerequisite rows
must be committed explicitly, and concurrency fixtures should clean up their
own persistent rows.

## 5. Regression Tests Must Tolerate Migration Fixtures

A dedicated database used for migration preservation checks may contain
intentional legacy data. API regression tests should scope count and ordering
assertions with supported filters instead of assuming globally empty tables.

## 6. Historical Migration Gaps Must Remain Explicit

The current Alembic chain cannot reproduce the baseline from an empty database.
Representing the actual current baseline in an isolated test database allowed
PATCH-018.1 to be validated without silently expanding scope into historical
migration repair.

## 7. Safety Fingerprints Are Useful

Recording the development revision, row counts, and Project maximum before and
after validation provided direct evidence that all mutation testing remained
inside `satco_platform_patch0181_test`.
