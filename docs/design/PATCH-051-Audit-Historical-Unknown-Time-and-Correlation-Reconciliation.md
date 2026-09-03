# PATCH-051 Audit Historical Unknown-Time and Correlation Reconciliation

## Status and authority

| Field | Value |
|---|---|
| Scope | B5-MAJ-01 legacy-data semantics only |
| Human principle | Unknown historical data remains explicitly unknown |
| Result | RECONCILED / COMPLETE |
| Production or migration authority | NOT GRANTED BY THIS RECORD |
| B5-MAJ-01 | OPEN; remediation policy resolved only |
| Batch 5 | NOT ACCEPTED / INCOMPLETE |
| Source Alembic head | `e05100000003` |

This append-only reconciliation preserves the accepted Architecture-051,
ADR-024, EDS-051, focused persistence reconciliation, IDS-051 and
Implementation-Plan-051 history. It resolves only the legacy-data semantic
gap discovered by the Batch-5 review. It creates no migration and changes no
application, database, API or frontend artifact.

## Discovered gap and factual evidence

EDS-051 requires a server-UTC `occurred_at`, a UUID `correlation_id`, and
Organization-leading indexes and pagination ordered by
`(occurred_at DESC, event_id DESC)`. IDS-051 carries those requirements into
the persistence and API contract. M1 omitted both columns and the two exact
indexes; the current API orders only by UUID `event_id`.

Read-only inspection of the authorized disposable PATCH-051 database found 68
existing package Audit rows. None has a durable event timestamp; all event IDs
are UUIDv4; PostgreSQL `track_commit_timestamp` is off; and no corresponding
generic Audit row provides a trustworthy time. Forty-six rows contain a
non-empty metadata correlation value and twenty-two do not. Migration time,
discovery time, API-read time, epoch, a sentinel timestamp, UUID order and
estimated time are not historical event time.

The controlling integrity rule is therefore:

> UNKNOWN IS NOT AN ERROR TO BE REPAIRED BY INVENTION.

## Historical and post-cutover field semantics

### `occurred_at`

For every row that exists before the corrective migration, `occurred_at` is
`NULL`. It means exactly `HISTORICAL_EVENT_TIME_UNKNOWN`. It conveys no
chronological estimate and must never be rendered, filtered or compared as a
real timestamp.

Every post-cutover event has a non-null timezone-aware UTC `occurred_at`. The
guarded operation captures it once from the trusted server clock when the
successful UoW attempt stages its Audit. All Audit rows staged by the same
atomic operation use that value; `event_id` remains the stable tie-breaker.
Retries retain the request correlation but the event time belongs to the
attempt that actually commits.

### `correlation_id`

For a pre-cutover row, M4 may copy the exact metadata `correlation_id` only if
it parses under the same accepted UUID boundary applied to new package
requests. The metadata itself remains unchanged. Empty, absent, malformed or
otherwise untrusted values produce a `NULL` column, meaning
`HISTORICAL_CORRELATION_UNKNOWN`. No event ID or generated UUID substitutes
for missing history.

All package-configuration Audit categories are produced by Human-requested
Organization configuration, Project configuration or Workspace-binding
operations. Registry installation/activation events are explicitly excluded
from this table. Consequently every post-cutover row requires one non-null
validated UUID correlation supplied through the established
`X-Correlation-ID` request boundary (or the same trusted operation boundary
for an internal invocation), frozen in the guarded identity and reused across
a whole-operation retry. It never supplies tenant or authorization authority.

## Mixed ordering and pagination

The listing consists of two explicit, non-interleaved segments:

1. `KNOWN_TIME`: rows where `occurred_at IS NOT NULL`, ordered by
   `occurred_at DESC, event_id DESC`.
2. `HISTORICAL_UNKNOWN_TIME`: rows where `occurred_at IS NULL`, returned only
   after the known-time segment and ordered by `event_id DESC` as stable
   non-temporal identity.

UUID order in the second segment is deterministic but is never described or
displayed as chronology. A first request starts in `KNOWN_TIME` when that
segment is non-empty and otherwise starts in `HISTORICAL_UNKNOWN_TIME`. Pages
do not mix segments: when the known segment is exhausted, the next cursor is
an explicit transition to the legacy segment. This may produce a short page at
the boundary and avoids assigning a historical row a fabricated temporal
position. `occurred_at: null` is the minimal truthful API representation of
unknown event time.

Keyset predicates are exact:

- known continuation: `occurred_at < :time OR
  (occurred_at = :time AND event_id < :event_id)`, with
  `occurred_at IS NOT NULL`;
- legacy continuation: `event_id < :event_id`, with
  `occurred_at IS NULL`.

The opaque cursor position includes an explicit segment discriminator:

- `KNOWN_TIME`, UTC timestamp and event ID;
- `HISTORICAL_UNKNOWN_TIME` and event ID; or
- a segment-transition marker with no fabricated timestamp.

The existing HMAC signature, 15-minute expiry and binding to Organization,
filter/category and page limit remain mandatory. Timestamp parsing must be
strict UTC and round-trip canonical. Wrong segment shape, malformed values,
signature failure, expiry, tenant mismatch or filter/limit mismatch fails with
the existing safe cursor error after authentication and Organization
derivation. Correlation ID is not part of cursor scope and cannot become a
disclosure key.

## Index and database-enforcement reconciliation

The corrective schema uses the two accepted indexes, with explicit NULL
placement:

```text
(organization_id, occurred_at DESC NULLS LAST, event_id DESC)
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC)
```

These remain tenant-leading and timestamp-leading for known rows. Equality on
`occurred_at IS NULL` also provides the deterministic legacy `event_id` access
path, so no speculative third legacy index is required. The obsolete
single-column Organization index may be replaced by the first accepted index.
Actual M4 validation must inspect PostgreSQL definitions and demonstrate the
authorized 100-event known-time query plan; it must not claim production SLO
evidence.

Both new columns remain physically nullable because truthful legacy values are
unknown. Database enforcement distinguishes legacy from current rows without
a fabricated marker:

- M4 adds the nullable columns in one locked transaction;
- only trustworthy historical correlation metadata is copied;
- all historical `occurred_at` values remain `NULL`;
- a narrowly scoped `BEFORE INSERT` guard rejects every new row whose
  `occurred_at` or `correlation_id` is null;
- the existing immutable-row trigger continues to reject update/delete after
  migration completion.

The migration may temporarily suspend only the package-Audit immutability
trigger while it populates the newly added correlation column. It must lock
the table, change no pre-existing column, compare before/after row counts and
checksums over the original columns, restore the trigger before commit, and
fail atomically on any invalid state. Broad trigger bypass is prohibited.
The null itself is the minimum historical provenance representation; no
status column or sentinel is needed.

## Migration and compatibility implications

One forward corrective M4 from `e05100000003` can now be designed. It may add
only the two nullable columns, the exact two indexes, the current-row insert
guard and the validated historical correlation copy; update the model,
staging/UoW and Audit cursor/API; and add the focused migration, security,
pagination and query-plan evidence required by B5-MAJ-01.

A downgrade may remove M4 only before any post-cutover Audit row exists. Once
a current row uses the new fields, accepted recovery is forward-only because
downgrade would discard authoritative event time/correlation. This record does
not authorize that migration or its execution.

Architecture-051 and ADR-024 already require truthful immutable history,
stable Audit identity, tenant minimization and transactional Audit; they need
no amendment. This record is the narrow controlling overlay for the EDS/IDS
assumption that every Audit row could satisfy the newer non-null temporal
contract. Known-time current behavior remains authoritative; the only legacy
exception is explicit NULL uncertainty and segmented non-chronological access.

## Governance outcome

The policy is truthful, deterministic, implementable, tenant-safe and
compatible with PATCH-051 architecture. B5-MAJ-01 remains open until a
separately authorized M4 and implementation pass focused regression and
re-review. Batch 5 and PATCH-051 remain open; PATCH-052 has not started.

PATCH-051 AUDIT HISTORICAL UNKNOWN-DATA RECONCILIATION:
PASS / ACCEPTED / COMPLETE

B5-MAJ-01:
OPEN / REMEDIATION POLICY RESOLVED

Corrective migration:
ELIGIBLE FOR SEPARATE HUMAN AUTHORITY

Batch 5:
NOT YET ACCEPTED

PATCH-051:
OPEN
