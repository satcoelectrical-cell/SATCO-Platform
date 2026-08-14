"""PATCH-034 Organizational Memory credential and persistence foundation.

Revision ID: e03400000001
Revises: e03200000001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e03400000001"
down_revision: str | None = "e03200000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizational_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("projects.id", ondelete="RESTRICT")),
        sa.Column("version", sa.BigInteger(), server_default="1", nullable=False),
        sa.Column("standing", sa.String(16), server_default="active", nullable=False),
        sa.Column("source_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("technical_reports.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_accepted_version", sa.BigInteger(), nullable=False),
        sa.Column("source_snapshot_digest", sa.CHAR(64), nullable=False),
        sa.Column("projection_contract", sa.String(64), nullable=False),
        sa.Column("projection", postgresql.JSONB(), nullable=False),
        sa.Column("projection_digest", sa.CHAR(64), nullable=False),
        sa.Column("manifest", postgresql.JSONB(), nullable=False),
        sa.Column("provenance_digest", sa.CHAR(64), nullable=False),
        sa.Column("admitted_by_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admission_rationale", sa.String(2000), nullable=False),
        sa.Column("audience_actor_ids", postgresql.ARRAY(sa.BigInteger()), server_default="{}", nullable=False),
        sa.Column("reuse_restrictions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("predecessor_memory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizational_memories.id", ondelete="RESTRICT")),
        sa.Column("withdrawn_by_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
        sa.Column("withdrawal_reason", sa.String(2000)),
        sa.Column("superseded_by_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.Column("supersession_reason", sa.String(2000)),
        sa.Column("replacement_memory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizational_memories.id", ondelete="RESTRICT")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "source_report_id", "source_accepted_version", name="uq_organizational_memory_source"),
        sa.CheckConstraint("workspace_id > 0", name="ck_organizational_memories_workspace_positive"),
        sa.CheckConstraint("project_id IS NULL OR project_id > 0", name="ck_organizational_memories_project_positive"),
        sa.CheckConstraint("version > 0", name="ck_organizational_memories_version_positive"),
        sa.CheckConstraint("standing IN ('active','withdrawn','superseded')", name="ck_organizational_memories_standing"),
        sa.CheckConstraint("source_accepted_version > 0", name="ck_organizational_memories_source_version"),
        sa.CheckConstraint("source_snapshot_digest ~ '^[0-9a-f]{64}$'", name="ck_organizational_memories_source_digest"),
        sa.CheckConstraint("projection_contract = 'organizational_memory.accepted_report.v1'", name="ck_organizational_memories_projection_contract"),
        sa.CheckConstraint("projection_digest ~ '^[0-9a-f]{64}$'", name="ck_organizational_memories_projection_digest"),
        sa.CheckConstraint("provenance_digest ~ '^[0-9a-f]{64}$'", name="ck_organizational_memories_provenance_digest"),
        sa.CheckConstraint("admitted_by_id > 0", name="ck_organizational_memories_admitted_by"),
        sa.CheckConstraint("predecessor_memory_id IS NULL OR predecessor_memory_id <> id", name="ck_organizational_memories_distinct_predecessor"),
        sa.CheckConstraint("replacement_memory_id IS NULL OR replacement_memory_id <> id", name="ck_organizational_memories_distinct_replacement"),
        sa.CheckConstraint("cardinality(audience_actor_ids) <= 100 AND NOT (0 = ANY(audience_actor_ids))", name="ck_organizational_memories_audience_bound"),
        sa.CheckConstraint("jsonb_typeof(reuse_restrictions) = 'array' AND jsonb_array_length(reuse_restrictions) <= 32", name="ck_organizational_memories_restrictions_bound"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_organizational_memories_timestamp_order"),
    )
    op.create_index("ix_organizational_memories_active_order", "organizational_memories", ["organization_id", "workspace_id", "project_id", "standing", sa.text("admitted_at DESC"), sa.text("id ASC")])
    op.create_index("ix_organizational_memories_predecessor", "organizational_memories", ["predecessor_memory_id"])
    op.create_index("ix_organizational_memories_replacement", "organizational_memories", ["replacement_memory_id"])
    op.create_index("uq_organizational_memories_replacement_once", "organizational_memories", ["replacement_memory_id"], unique=True, postgresql_where=sa.text("replacement_memory_id IS NOT NULL"))

    op.create_table(
        "organizational_memory_standing_history",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("aggregate_version", sa.BigInteger(), nullable=False),
        sa.Column("from_standing", sa.String(16)),
        sa.Column("to_standing", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(2000), nullable=False),
        sa.Column("replacement_memory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizational_memories.id", ondelete="RESTRICT")),
        sa.UniqueConstraint("memory_id", "aggregate_version", name="uq_organizational_memory_history_version"),
        sa.CheckConstraint("aggregate_version > 0", name="ck_organizational_memory_history_version"),
        sa.CheckConstraint("actor_id > 0", name="ck_organizational_memory_history_actor"),
        sa.CheckConstraint("from_standing IS NULL OR from_standing = 'active'", name="ck_organizational_memory_history_from"),
        sa.CheckConstraint("to_standing IN ('active','withdrawn','superseded')", name="ck_organizational_memory_history_to"),
    )
    op.create_index("ix_organizational_memory_history_memory_version", "organizational_memory_standing_history", ["memory_id", "aggregate_version"])

    op.create_table(
        "organizational_memory_events_outbox",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizational_memories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("aggregate_version", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload_schema_version", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error_category", sa.String(64)),
        sa.UniqueConstraint("memory_id", "aggregate_version", "event_type", name="uq_organizational_memory_outbox_aggregate_event"),
        sa.CheckConstraint("aggregate_version > 0", name="ck_organizational_memory_outbox_version"),
        sa.CheckConstraint("event_type IN ('ORGANIZATIONAL_MEMORY_ADMITTED','ORGANIZATIONAL_MEMORY_WITHDRAWN','ORGANIZATIONAL_MEMORY_SUPERSEDED')", name="ck_organizational_memory_outbox_event_type"),
        sa.CheckConstraint("payload_schema_version = 1", name="ck_organizational_memory_outbox_schema_version"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_organizational_memory_outbox_attempt_count"),
        sa.CheckConstraint("last_error_category IS NULL OR (length(last_error_category) BETWEEN 1 AND 64 AND last_error_category ~ '^[a-z0-9_]+$')", name="ck_organizational_memory_outbox_error_category"),
    )
    op.create_index("ix_organizational_memory_outbox_pending", "organizational_memory_events_outbox", ["published_at", "created_at", "event_id"], postgresql_where=sa.text("published_at IS NULL"))

    op.create_table(
        "organizational_memory_idempotency",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("operation", sa.String(32), primary_key=True),
        sa.Column("idempotency_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_fingerprint", sa.CHAR(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("result_schema_version", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("safe_result", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("actor_id > 0", name="ck_organizational_memory_idempotency_actor"),
        sa.CheckConstraint("operation IN ('admit','withdraw','create_successor','supersede')", name="ck_organizational_memory_idempotency_operation"),
        sa.CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_organizational_memory_idempotency_fingerprint"),
        sa.CheckConstraint("status IN ('pending','completed')", name="ck_organizational_memory_idempotency_status"),
        sa.CheckConstraint("result_schema_version = 1", name="ck_organizational_memory_idempotency_schema_version"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_organizational_memory_idempotency_timestamp_order"),
    )

    _create_functions_and_triggers()
    _configure_role_boundary()


def _create_functions_and_triggers() -> None:
    op.execute(r"""
        CREATE FUNCTION organizational_memory_canonical_json(value jsonb) RETURNS text
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE result text;
        BEGIN
          CASE jsonb_typeof(value)
            WHEN 'object' THEN
              SELECT COALESCE('{' || string_agg(to_jsonb(key)::text || ':' || organizational_memory_canonical_json(value -> key), ',' ORDER BY key) || '}', '{}')
              INTO result FROM jsonb_object_keys(value) AS key;
            WHEN 'array' THEN
              SELECT COALESCE('[' || string_agg(organizational_memory_canonical_json(item), ',' ORDER BY ordinal) || ']', '[]')
              INTO result FROM jsonb_array_elements(value) WITH ORDINALITY AS elements(item, ordinal);
            ELSE result := value::text;
          END CASE;
          RETURN result;
        END
        $$
    """)
    op.execute(r"""
        CREATE FUNCTION organizational_memory_projection_v1_valid(value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE content jsonb; qualification jsonb; revision jsonb;
        BEGIN
          IF COALESCE(jsonb_typeof(value) <> 'object' OR octet_length(convert_to(organizational_memory_canonical_json(value),'UTF8')) > 262144
             OR (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(value) key) <> ARRAY[
               'accepted_aggregate_version','accepted_at','accepted_by_id','accepted_draft_revision_id',
               'accepted_draft_revision_number','content','organization_id','predecessor_report_id',
               'project_id','projection_contract','purpose','qualification','report_id','workspace_id']
             OR value->>'projection_contract' <> 'organizational_memory.accepted_report.v1'
             OR value->>'purpose' NOT IN ('field_experience','troubleshooting','engineering_analysis','technical_recommendation')
             OR value->>'report_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             OR value->>'organization_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             OR value->>'accepted_draft_revision_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             OR jsonb_typeof(value->'workspace_id') <> 'number' OR (value->>'workspace_id')::numeric < 1 OR (value->>'workspace_id')::numeric <> trunc((value->>'workspace_id')::numeric)
             OR NOT (jsonb_typeof(value->'project_id')='null' OR (jsonb_typeof(value->'project_id')='number' AND (value->>'project_id')::numeric>=1 AND (value->>'project_id')::numeric=trunc((value->>'project_id')::numeric)))
             OR jsonb_typeof(value->'accepted_draft_revision_number') <> 'number' OR (value->>'accepted_draft_revision_number')::numeric < 1 OR (value->>'accepted_draft_revision_number')::numeric <> trunc((value->>'accepted_draft_revision_number')::numeric)
             OR jsonb_typeof(value->'accepted_aggregate_version') <> 'number' OR (value->>'accepted_aggregate_version')::numeric < 1 OR (value->>'accepted_aggregate_version')::numeric <> trunc((value->>'accepted_aggregate_version')::numeric)
             OR jsonb_typeof(value->'accepted_by_id') <> 'number' OR (value->>'accepted_by_id')::numeric < 1 OR (value->>'accepted_by_id')::numeric <> trunc((value->>'accepted_by_id')::numeric)
             OR jsonb_typeof(value->'accepted_at') <> 'string'
             OR value->>'accepted_at' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$'
             OR to_char((value->>'accepted_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') <> value->>'accepted_at'
             OR NOT (jsonb_typeof(value->'predecessor_report_id')='null' OR value->>'predecessor_report_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'), true) THEN RETURN false;
          END IF;
          content := value->'content'; qualification := value->'qualification';
          IF COALESCE((SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(content) key) <> ARRAY['assumptions','conclusions','engineering_scope','limitations','recommendations','technical_content','uncertainty']
             OR EXISTS (SELECT 1 FROM jsonb_each(content) item WHERE item.key IN ('engineering_scope','technical_content','uncertainty','conclusions') AND (jsonb_typeof(item.value)<>'string' OR length(item.value#>>'{}') NOT BETWEEN 1 AND 10000 OR item.value#>>'{}'<>btrim(item.value#>>'{}') OR normalize(item.value#>>'{}',NFC)<>item.value#>>'{}' OR item.value#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]'))
             OR jsonb_typeof(content->'assumptions')<>'array' OR jsonb_typeof(content->'limitations')<>'array' OR jsonb_typeof(content->'recommendations')<>'array'
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(content->'assumptions') x WHERE jsonb_typeof(x)<>'string' OR length(x#>>'{}') NOT BETWEEN 1 AND 10000 OR x#>>'{}'<>btrim(x#>>'{}') OR normalize(x#>>'{}',NFC)<>x#>>'{}' OR x#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]')
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(content->'limitations') x WHERE jsonb_typeof(x)<>'string' OR length(x#>>'{}') NOT BETWEEN 1 AND 10000 OR x#>>'{}'<>btrim(x#>>'{}') OR normalize(x#>>'{}',NFC)<>x#>>'{}' OR x#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]')
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(content->'recommendations') x WHERE jsonb_typeof(x)<>'string' OR length(x#>>'{}') NOT BETWEEN 1 AND 10000 OR x#>>'{}'<>btrim(x#>>'{}') OR normalize(x#>>'{}',NFC)<>x#>>'{}' OR x#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]'), true) THEN RETURN false;
          END IF;
          IF COALESCE((SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(qualification) key) <> ARRAY['evidence_deficiencies','follow_up_requirements','is_preliminary','unresolved_issues']
             OR jsonb_typeof(qualification->'is_preliminary')<>'boolean'
             OR jsonb_typeof(qualification->'evidence_deficiencies')<>'array'
             OR jsonb_typeof(qualification->'unresolved_issues')<>'array'
             OR jsonb_typeof(qualification->'follow_up_requirements')<>'array'
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(qualification->'evidence_deficiencies') x WHERE jsonb_typeof(x)<>'string' OR length(x#>>'{}') NOT BETWEEN 1 AND 10000 OR x#>>'{}'<>btrim(x#>>'{}') OR normalize(x#>>'{}',NFC)<>x#>>'{}' OR x#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]')
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(qualification->'unresolved_issues') x WHERE jsonb_typeof(x)<>'string' OR length(x#>>'{}') NOT BETWEEN 1 AND 10000 OR x#>>'{}'<>btrim(x#>>'{}') OR normalize(x#>>'{}',NFC)<>x#>>'{}' OR x#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]')
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(qualification->'follow_up_requirements') x WHERE jsonb_typeof(x)<>'string' OR length(x#>>'{}') NOT BETWEEN 1 AND 10000 OR x#>>'{}'<>btrim(x#>>'{}') OR normalize(x#>>'{}',NFC)<>x#>>'{}' OR x#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]')
             OR (qualification->>'is_preliminary')::boolean <> (jsonb_array_length(qualification->'evidence_deficiencies')+jsonb_array_length(qualification->'unresolved_issues')+jsonb_array_length(qualification->'follow_up_requirements')>0), true) THEN RETURN false;
          END IF;
          RETURN true;
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute(r"""
        CREATE FUNCTION organizational_memory_manifest_v1_valid(value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE entries jsonb; source jsonb;
        BEGIN
          source := value->'source'; entries := value->'provenance_entries';
          IF COALESCE(jsonb_typeof(value)<>'object' OR octet_length(convert_to(organizational_memory_canonical_json(value),'UTF8'))>131072
             OR (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(value) key) <> ARRAY['admitted_projection_digest','projection_contract','provenance_digest','provenance_entries','source','source_snapshot_digest']
             OR value->>'projection_contract'<>'organizational_memory.accepted_report.v1'
             OR value->>'source_snapshot_digest' !~ '^[0-9a-f]{64}$'
             OR value->>'admitted_projection_digest' !~ '^[0-9a-f]{64}$'
             OR value->>'provenance_digest' !~ '^[0-9a-f]{64}$'
             OR (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(source) key) <> ARRAY['accepted_aggregate_version','accepted_snapshot_digest','report_id']
             OR source->>'report_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             OR jsonb_typeof(source->'accepted_aggregate_version')<>'number' OR (source->>'accepted_aggregate_version')::numeric<1 OR (source->>'accepted_aggregate_version')::numeric<>trunc((source->>'accepted_aggregate_version')::numeric)
             OR source->>'accepted_snapshot_digest'<>value->>'source_snapshot_digest'
             OR jsonb_typeof(entries)<>'array' OR jsonb_array_length(entries) NOT BETWEEN 1 AND 256
             OR value->>'provenance_digest'<>encode(sha256(convert_to(organizational_memory_canonical_json(entries),'UTF8')),'hex')
             OR EXISTS (
               SELECT 1 FROM jsonb_array_elements(entries) WITH ORDINALITY e(item,ordinal)
               WHERE COALESCE((
                      (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(item) key) <> ARRAY['entry_id','is_material','locator_digest','ordinal','owning_capability','reliance_role','source_class','source_integrity_algorithm','source_integrity_digest','source_type']
                  OR item->>'entry_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                  OR jsonb_typeof(item->'ordinal')<>'number' OR (item->>'ordinal')::numeric<>ordinal-1 OR (item->>'ordinal')::numeric<>trunc((item->>'ordinal')::numeric)
                  OR item->>'source_class'<>'canonical_material' OR jsonb_typeof(item->'is_material')<>'boolean' OR (item->>'is_material')::boolean IS NOT TRUE
                  OR item->>'source_integrity_algorithm'<>'sha256'
                  OR item->>'locator_digest' !~ '^[0-9a-f]{64}$' OR item->>'source_integrity_digest' !~ '^[0-9a-f]{64}$'
                  OR jsonb_typeof(item->'reliance_role')<>'string' OR length(item->>'reliance_role') NOT BETWEEN 1 AND 2000 OR item->>'reliance_role'<>btrim(item->>'reliance_role') OR normalize(item->>'reliance_role',NFC)<>item->>'reliance_role' OR item->>'reliance_role'~'[\x00-\x08\x0B\x0C\x0E-\x1F]'
                  OR NOT ((item->>'source_type'='universal_capture' AND item->>'owning_capability'='universal_capture') OR (item->>'source_type'='evidence' AND item->>'owning_capability'='evidence') OR (item->>'source_type'='engineering_object' AND item->>'owning_capability'='engineering_object') OR (item->>'source_type'='engineering_relationship' AND item->>'owning_capability'='engineering_relationship'))
                    ), true)
             ), true) THEN RETURN false;
          END IF;
          RETURN true;
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute(r"""
        CREATE FUNCTION organizational_memory_event_payload_v1_valid(kind text, value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        BEGIN
          RETURN COALESCE(kind IN ('ORGANIZATIONAL_MEMORY_ADMITTED','ORGANIZATIONAL_MEMORY_WITHDRAWN','ORGANIZATIONAL_MEMORY_SUPERSEDED')
             AND jsonb_typeof(value)='object' AND octet_length(convert_to(organizational_memory_canonical_json(value),'UTF8'))<=8192
             AND (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(value) key)=ARRAY['actor_id','aggregate_version','causation_id','command_id','correlation_id','memory_id','occurred_at','organization_id','predecessor_memory_id','project_id','provenance_entry_count','replacement_memory_id','source_accepted_version','source_report_id','standing','workspace_id']
             AND value->>'memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             AND value->>'organization_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             AND value->>'source_report_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             AND value->>'command_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             AND value->>'correlation_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             AND value->>'causation_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
             AND jsonb_typeof(value->'occurred_at')='string' AND value->>'occurred_at'~'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$'
             AND to_char((value->>'occurred_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') = value->>'occurred_at'
             AND jsonb_typeof(value->'aggregate_version')='number' AND (value->>'aggregate_version')::numeric>=1 AND (value->>'aggregate_version')::numeric=trunc((value->>'aggregate_version')::numeric)
             AND jsonb_typeof(value->'workspace_id')='number' AND (value->>'workspace_id')::numeric>=1 AND (value->>'workspace_id')::numeric=trunc((value->>'workspace_id')::numeric)
             AND (jsonb_typeof(value->'project_id')='null' OR (jsonb_typeof(value->'project_id')='number' AND (value->>'project_id')::numeric>=1 AND (value->>'project_id')::numeric=trunc((value->>'project_id')::numeric)))
             AND jsonb_typeof(value->'actor_id')='number' AND (value->>'actor_id')::numeric>=1 AND (value->>'actor_id')::numeric=trunc((value->>'actor_id')::numeric)
             AND jsonb_typeof(value->'source_accepted_version')='number' AND (value->>'source_accepted_version')::numeric>=1 AND (value->>'source_accepted_version')::numeric=trunc((value->>'source_accepted_version')::numeric)
             AND jsonb_typeof(value->'provenance_entry_count')='number' AND (value->>'provenance_entry_count')::numeric>=0 AND (value->>'provenance_entry_count')::numeric=trunc((value->>'provenance_entry_count')::numeric)
             AND (jsonb_typeof(value->'predecessor_memory_id')='null' OR (jsonb_typeof(value->'predecessor_memory_id')='string' AND value->>'predecessor_memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'))
             AND ((kind='ORGANIZATIONAL_MEMORY_ADMITTED' AND value->>'standing'='active' AND jsonb_typeof(value->'replacement_memory_id')='null') OR (kind='ORGANIZATIONAL_MEMORY_WITHDRAWN' AND value->>'standing'='withdrawn' AND jsonb_typeof(value->'replacement_memory_id')='null') OR (kind='ORGANIZATIONAL_MEMORY_SUPERSEDED' AND value->>'standing'='superseded' AND jsonb_typeof(value->'replacement_memory_id')='string' AND value->>'replacement_memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')), false);
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute(r"""
        CREATE FUNCTION organizational_memory_idempotency_result_v1_valid(operation_value text, value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE keys text[];
        BEGIN
          IF value IS NULL OR jsonb_typeof(value)<>'object' OR octet_length(convert_to(organizational_memory_canonical_json(value),'UTF8'))>1024 THEN RETURN false; END IF;
          SELECT array_agg(key ORDER BY key) INTO keys FROM jsonb_object_keys(value) key;
          RETURN COALESCE(CASE operation_value
            WHEN 'admit' THEN value->>'result_type'='admit.v1' AND keys=ARRAY['memory_id','result_type','source_accepted_version','source_report_id','standing','version'] AND value->>'standing'='active' AND jsonb_typeof(value->'version')='number' AND (value->>'version')::numeric=1 AND value->>'memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND value->>'source_report_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND jsonb_typeof(value->'source_accepted_version')='number' AND (value->>'source_accepted_version')::numeric>=1 AND (value->>'source_accepted_version')::numeric=trunc((value->>'source_accepted_version')::numeric)
            WHEN 'withdraw' THEN value->>'result_type'='withdraw.v1' AND keys=ARRAY['memory_id','result_type','result_version','standing','withdrawn_at'] AND value->>'standing'='withdrawn' AND value->>'memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND jsonb_typeof(value->'result_version')='number' AND (value->>'result_version')::numeric>=1 AND (value->>'result_version')::numeric=trunc((value->>'result_version')::numeric) AND value->>'withdrawn_at'~'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$' AND to_char((value->>'withdrawn_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')=value->>'withdrawn_at'
            WHEN 'create_successor' THEN value->>'result_type'='create_successor.v1' AND keys=ARRAY['memory_id','predecessor_memory_id','result_type','source_accepted_version','source_report_id','standing','version'] AND value->>'standing'='active' AND jsonb_typeof(value->'version')='number' AND (value->>'version')::numeric=1 AND value->>'memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND value->>'predecessor_memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND value->>'source_report_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND jsonb_typeof(value->'source_accepted_version')='number' AND (value->>'source_accepted_version')::numeric>=1 AND (value->>'source_accepted_version')::numeric=trunc((value->>'source_accepted_version')::numeric)
            WHEN 'supersede' THEN value->>'result_type'='supersede.v1' AND keys=ARRAY['predecessor_memory_id','predecessor_result_version','predecessor_standing','replacement_memory_id','replacement_standing','replacement_version_at_command','result_type','superseded_at'] AND value->>'predecessor_standing'='superseded' AND value->>'replacement_standing'='active' AND value->>'predecessor_memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND value->>'replacement_memory_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND jsonb_typeof(value->'predecessor_result_version')='number' AND (value->>'predecessor_result_version')::numeric>=1 AND (value->>'predecessor_result_version')::numeric=trunc((value->>'predecessor_result_version')::numeric) AND jsonb_typeof(value->'replacement_version_at_command')='number' AND (value->>'replacement_version_at_command')::numeric>=1 AND (value->>'replacement_version_at_command')::numeric=trunc((value->>'replacement_version_at_command')::numeric) AND value->>'superseded_at'~'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$' AND to_char((value->>'superseded_at')::timestamptz AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')=value->>'superseded_at'
            ELSE false END, false);
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute("ALTER TABLE organizational_memories ADD CONSTRAINT ck_organizational_memories_projection_valid CHECK (organizational_memory_projection_v1_valid(projection))")
    op.execute("ALTER TABLE organizational_memories ADD CONSTRAINT ck_organizational_memories_manifest_valid CHECK (organizational_memory_manifest_v1_valid(manifest))")
    op.execute("ALTER TABLE organizational_memories ADD CONSTRAINT ck_organizational_memories_projection_digest_coherent CHECK (projection_digest=encode(sha256(convert_to(organizational_memory_canonical_json(projection),'UTF8')),'hex'))")
    op.execute("ALTER TABLE organizational_memories ADD CONSTRAINT ck_organizational_memories_manifest_root_coherent CHECK (projection_contract=manifest->>'projection_contract' AND source_report_id::text=manifest->'source'->>'report_id' AND source_accepted_version=(manifest->'source'->>'accepted_aggregate_version')::bigint AND source_snapshot_digest=manifest->>'source_snapshot_digest' AND projection_digest=manifest->>'admitted_projection_digest' AND provenance_digest=manifest->>'provenance_digest')")
    op.execute("ALTER TABLE organizational_memory_events_outbox ADD CONSTRAINT ck_organizational_memory_outbox_payload CHECK (organizational_memory_event_payload_v1_valid(event_type,payload))")
    op.execute("ALTER TABLE organizational_memory_events_outbox ADD CONSTRAINT ck_organizational_memory_outbox_root_coherent CHECK (memory_id::text=payload->>'memory_id' AND aggregate_version=(payload->>'aggregate_version')::bigint AND occurred_at=(payload->>'occurred_at')::timestamptz)")
    op.execute("ALTER TABLE organizational_memory_idempotency ADD CONSTRAINT ck_organizational_memory_idempotency_result CHECK ((status='pending' AND safe_result IS NULL AND completed_at IS NULL) OR (status='completed' AND safe_result IS NOT NULL AND completed_at IS NOT NULL AND organizational_memory_idempotency_result_v1_valid(operation,safe_result)))")

    _create_guard_functions()


def _create_guard_functions() -> None:
    op.execute(r"""
      CREATE FUNCTION organizational_memory_lineage_guard() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE predecessor organizational_memories%ROWTYPE; replacement organizational_memories%ROWTYPE;
      BEGIN
        IF TG_OP='INSERT' AND NEW.predecessor_memory_id IS NOT NULL THEN
          SELECT * INTO predecessor FROM organizational_memories WHERE id=NEW.predecessor_memory_id FOR KEY SHARE;
          IF NOT FOUND OR predecessor.id=NEW.id OR predecessor.organization_id<>NEW.organization_id OR predecessor.workspace_id<>NEW.workspace_id OR predecessor.project_id IS DISTINCT FROM NEW.project_id
             OR (predecessor.source_report_id=NEW.source_report_id AND predecessor.source_accepted_version=NEW.source_accepted_version)
             OR NOT (cardinality(predecessor.audience_actor_ids)=0 OR (cardinality(NEW.audience_actor_ids)>0 AND NEW.audience_actor_ids <@ predecessor.audience_actor_ids)) THEN
            RAISE EXCEPTION 'invalid Organizational Memory predecessor' USING ERRCODE='23514';
          END IF;
        END IF;
        IF TG_OP='UPDATE' AND NEW.standing='superseded' THEN
          PERFORM id FROM organizational_memories
            WHERE id IN (OLD.id,NEW.replacement_memory_id) ORDER BY id FOR UPDATE;
          SELECT * INTO replacement FROM organizational_memories WHERE id=NEW.replacement_memory_id;
          IF NOT FOUND OR OLD.standing<>'active' OR replacement.standing<>'active' OR replacement.id=OLD.id OR replacement.predecessor_memory_id IS DISTINCT FROM OLD.id
             OR replacement.organization_id<>OLD.organization_id OR replacement.workspace_id<>OLD.workspace_id OR replacement.project_id IS DISTINCT FROM OLD.project_id
             OR (replacement.source_report_id=OLD.source_report_id AND replacement.source_accepted_version=OLD.source_accepted_version)
             OR NOT (cardinality(OLD.audience_actor_ids)=0 OR (cardinality(replacement.audience_actor_ids)>0 AND replacement.audience_actor_ids <@ OLD.audience_actor_ids)) THEN
            RAISE EXCEPTION 'invalid Organizational Memory replacement' USING ERRCODE='23514';
          END IF;
        END IF;
        RETURN NEW;
      END $$
    """)
    op.execute(r"""
      CREATE FUNCTION organizational_memory_root_guard() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Organizational Memory is immutable' USING ERRCODE='55000'; END IF;
        IF TG_OP='INSERT' THEN
          IF NEW.version<>1 OR NEW.standing<>'active' OR NEW.withdrawn_by_id IS NOT NULL OR NEW.withdrawn_at IS NOT NULL OR NEW.withdrawal_reason IS NOT NULL OR NEW.superseded_by_id IS NOT NULL OR NEW.superseded_at IS NOT NULL OR NEW.supersession_reason IS NOT NULL OR NEW.replacement_memory_id IS NOT NULL
             OR NEW.created_at<>NEW.admitted_at OR NEW.updated_at<>NEW.admitted_at
             OR NEW.source_report_id::text<>NEW.projection->>'report_id' OR NEW.organization_id::text<>NEW.projection->>'organization_id'
             OR NEW.workspace_id<>(NEW.projection->>'workspace_id')::bigint OR NOT ((NEW.project_id IS NULL AND jsonb_typeof(NEW.projection->'project_id')='null') OR NEW.project_id=(NEW.projection->>'project_id')::bigint)
             OR NEW.source_accepted_version<>(NEW.projection->>'accepted_aggregate_version')::bigint THEN
            RAISE EXCEPTION 'invalid Organizational Memory admission state' USING ERRCODE='23514';
          END IF;
          IF cardinality(NEW.audience_actor_ids)<>(SELECT count(DISTINCT value) FROM unnest(NEW.audience_actor_ids) value)
             OR NEW.audience_actor_ids<>(SELECT COALESCE(array_agg(value ORDER BY value),'{}'::bigint[]) FROM unnest(NEW.audience_actor_ids) value)
             OR EXISTS (SELECT 1 FROM unnest(NEW.audience_actor_ids) value WHERE value<=0)
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.reuse_restrictions) item WHERE jsonb_typeof(item)<>'string' OR length(item#>>'{}') NOT BETWEEN 1 AND 2000 OR item#>>'{}'<>btrim(item#>>'{}') OR normalize(item#>>'{}',NFC)<>item#>>'{}' OR item#>>'{}'~'[\x00-\x08\x0B\x0C\x0E-\x1F]')
             OR length(NEW.admission_rationale) NOT BETWEEN 1 AND 2000 OR NEW.admission_rationale<>btrim(NEW.admission_rationale) OR normalize(NEW.admission_rationale,NFC)<>NEW.admission_rationale OR NEW.admission_rationale~'[\x00-\x08\x0B\x0C\x0E-\x1F]' THEN
            RAISE EXCEPTION 'invalid Organizational Memory bounded text/array state' USING ERRCODE='23514';
          END IF;
          RETURN NEW;
        END IF;
        IF OLD.standing<>'active' OR NEW.version<>OLD.version+1 OR NEW.standing NOT IN ('withdrawn','superseded') OR NEW.updated_at<=OLD.updated_at
           OR (to_jsonb(NEW)-ARRAY['version','standing','withdrawn_by_id','withdrawn_at','withdrawal_reason','superseded_by_id','superseded_at','supersession_reason','replacement_memory_id','updated_at'])<>(to_jsonb(OLD)-ARRAY['version','standing','withdrawn_by_id','withdrawn_at','withdrawal_reason','superseded_by_id','superseded_at','supersession_reason','replacement_memory_id','updated_at'])
           OR (NEW.standing='withdrawn' AND (NEW.withdrawn_by_id IS NULL OR NEW.withdrawn_by_id<=0 OR NEW.withdrawn_at IS NULL OR NEW.withdrawn_at<>NEW.updated_at OR NEW.withdrawal_reason IS NULL OR length(NEW.withdrawal_reason) NOT BETWEEN 1 AND 2000 OR NEW.withdrawal_reason<>btrim(NEW.withdrawal_reason) OR normalize(NEW.withdrawal_reason,NFC)<>NEW.withdrawal_reason OR NEW.withdrawal_reason~'[\x00-\x08\x0B\x0C\x0E-\x1F]' OR NEW.superseded_by_id IS NOT NULL OR NEW.superseded_at IS NOT NULL OR NEW.supersession_reason IS NOT NULL OR NEW.replacement_memory_id IS NOT NULL))
           OR (NEW.standing='superseded' AND (NEW.superseded_by_id IS NULL OR NEW.superseded_by_id<=0 OR NEW.superseded_at IS NULL OR NEW.superseded_at<>NEW.updated_at OR NEW.supersession_reason IS NULL OR length(NEW.supersession_reason) NOT BETWEEN 1 AND 2000 OR NEW.supersession_reason<>btrim(NEW.supersession_reason) OR normalize(NEW.supersession_reason,NFC)<>NEW.supersession_reason OR NEW.supersession_reason~'[\x00-\x08\x0B\x0C\x0E-\x1F]' OR NEW.replacement_memory_id IS NULL OR NEW.withdrawn_by_id IS NOT NULL OR NEW.withdrawn_at IS NOT NULL OR NEW.withdrawal_reason IS NOT NULL)) THEN
          RAISE EXCEPTION 'invalid Organizational Memory transition' USING ERRCODE='55000';
        END IF;
        RETURN NEW;
      END $$
    """)
    op.execute(r"""
      CREATE FUNCTION organizational_memory_history_guard() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      DECLARE root organizational_memories%ROWTYPE;
      BEGIN
        IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Organizational Memory history is append-only' USING ERRCODE='55000'; END IF;
        SELECT * INTO root FROM organizational_memories WHERE id=NEW.memory_id FOR KEY SHARE;
        IF NOT FOUND OR NEW.organization_id<>root.organization_id OR NEW.aggregate_version<>root.version OR NEW.to_standing<>root.standing
           OR length(NEW.reason) NOT BETWEEN 1 AND 2000 OR NEW.reason<>btrim(NEW.reason) OR normalize(NEW.reason,NFC)<>NEW.reason OR NEW.reason~'[\x00-\x08\x0B\x0C\x0E-\x1F]'
           OR NOT (
             (NEW.aggregate_version=1 AND NEW.from_standing IS NULL AND NEW.to_standing='active' AND NEW.replacement_memory_id IS NULL AND NEW.actor_id=root.admitted_by_id AND NEW.occurred_at=root.admitted_at AND NEW.reason=root.admission_rationale)
             OR (NEW.aggregate_version>1 AND NEW.from_standing='active' AND NEW.to_standing='withdrawn' AND NEW.replacement_memory_id IS NULL AND NEW.actor_id=root.withdrawn_by_id AND NEW.occurred_at=root.withdrawn_at AND NEW.reason=root.withdrawal_reason)
             OR (NEW.aggregate_version>1 AND NEW.from_standing='active' AND NEW.to_standing='superseded' AND NEW.replacement_memory_id=root.replacement_memory_id AND NEW.actor_id=root.superseded_by_id AND NEW.occurred_at=root.superseded_at AND NEW.reason=root.supersession_reason)
           ) THEN
          RAISE EXCEPTION 'invalid Organizational Memory history' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
      END $$
    """)
    op.execute(r"""
      CREATE FUNCTION organizational_memory_side_record_guard() RETURNS trigger
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      BEGIN
        IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Organizational Memory side record is immutable' USING ERRCODE='55000'; END IF;
        IF TG_OP='UPDATE' AND TG_TABLE_NAME='organizational_memory_events_outbox' AND (to_jsonb(NEW)-ARRAY['published_at','attempt_count','last_error_category'])<>(to_jsonb(OLD)-ARRAY['published_at','attempt_count','last_error_category']) THEN RAISE EXCEPTION 'outbox identity/payload is immutable' USING ERRCODE='55000'; END IF;
        IF TG_OP='UPDATE' AND TG_TABLE_NAME='organizational_memory_idempotency' AND (OLD.status='completed' OR (to_jsonb(NEW)-ARRAY['status','result_schema_version','safe_result','updated_at','completed_at'])<>(to_jsonb(OLD)-ARRAY['status','result_schema_version','safe_result','updated_at','completed_at'])) THEN RAISE EXCEPTION 'idempotency identity/result is immutable' USING ERRCODE='55000'; END IF;
        RETURN NEW;
      END $$
    """)
    op.execute("CREATE TRIGGER a_organizational_memory_lineage_guard BEFORE INSERT OR UPDATE ON organizational_memories FOR EACH ROW EXECUTE FUNCTION organizational_memory_lineage_guard()")
    op.execute("CREATE TRIGGER b_organizational_memory_root_guard BEFORE INSERT OR UPDATE OR DELETE ON organizational_memories FOR EACH ROW EXECUTE FUNCTION organizational_memory_root_guard()")
    op.execute("CREATE TRIGGER organizational_memory_history_guard BEFORE INSERT OR UPDATE OR DELETE ON organizational_memory_standing_history FOR EACH ROW EXECUTE FUNCTION organizational_memory_history_guard()")
    op.execute("CREATE TRIGGER organizational_memory_outbox_guard BEFORE UPDATE OR DELETE ON organizational_memory_events_outbox FOR EACH ROW EXECUTE FUNCTION organizational_memory_side_record_guard()")
    op.execute("CREATE TRIGGER organizational_memory_idempotency_guard BEFORE UPDATE OR DELETE ON organizational_memory_idempotency FOR EACH ROW EXECUTE FUNCTION organizational_memory_side_record_guard()")


def _configure_role_boundary() -> None:
    signatures = (
        "organizational_memory_projection_v1_valid(jsonb)",
        "organizational_memory_manifest_v1_valid(jsonb)",
        "organizational_memory_event_payload_v1_valid(text,jsonb)",
        "organizational_memory_idempotency_result_v1_valid(text,jsonb)",
        "organizational_memory_canonical_json(jsonb)",
        "organizational_memory_lineage_guard()",
        "organizational_memory_root_guard()",
        "organizational_memory_history_guard()",
        "organizational_memory_side_record_guard()",
    )
    for signature in signatures:
        op.execute(f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC")
        op.execute(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') "
            f"THEN EXECUTE 'REVOKE ALL ON FUNCTION {signature} FROM satco_runtime'; "
            "END IF; END $$"
        )
    op.execute(r"""
      DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
          GRANT USAGE ON SCHEMA public TO satco_runtime;
          GRANT SELECT, INSERT ON organizational_memories TO satco_runtime;
          GRANT UPDATE (version,standing,withdrawn_by_id,withdrawn_at,withdrawal_reason,superseded_by_id,superseded_at,supersession_reason,replacement_memory_id,updated_at) ON organizational_memories TO satco_runtime;
          GRANT SELECT, INSERT ON organizational_memory_standing_history TO satco_runtime;
          GRANT SELECT, INSERT ON organizational_memory_events_outbox TO satco_runtime;
          GRANT UPDATE (published_at,attempt_count,last_error_category) ON organizational_memory_events_outbox TO satco_runtime;
          GRANT SELECT, INSERT ON organizational_memory_idempotency TO satco_runtime;
          GRANT UPDATE (status,result_schema_version,safe_result,updated_at,completed_at) ON organizational_memory_idempotency TO satco_runtime;
          GRANT SELECT, INSERT ON audit_logs TO satco_runtime;
          REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON organizational_memories, organizational_memory_standing_history, organizational_memory_events_outbox, organizational_memory_idempotency FROM satco_runtime;
        END IF;
      END $$
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS organizational_memory_idempotency_guard ON organizational_memory_idempotency")
    op.execute("DROP TRIGGER IF EXISTS organizational_memory_outbox_guard ON organizational_memory_events_outbox")
    op.execute("DROP TRIGGER IF EXISTS organizational_memory_history_guard ON organizational_memory_standing_history")
    op.execute("DROP TRIGGER IF EXISTS b_organizational_memory_root_guard ON organizational_memories")
    op.execute("DROP TRIGGER IF EXISTS a_organizational_memory_lineage_guard ON organizational_memories")
    op.drop_table("organizational_memory_idempotency")
    op.drop_index("ix_organizational_memory_outbox_pending", table_name="organizational_memory_events_outbox")
    op.drop_table("organizational_memory_events_outbox")
    op.drop_index("ix_organizational_memory_history_memory_version", table_name="organizational_memory_standing_history")
    op.drop_table("organizational_memory_standing_history")
    op.drop_index("uq_organizational_memories_replacement_once", table_name="organizational_memories")
    op.drop_index("ix_organizational_memories_replacement", table_name="organizational_memories")
    op.drop_index("ix_organizational_memories_predecessor", table_name="organizational_memories")
    op.drop_index("ix_organizational_memories_active_order", table_name="organizational_memories")
    op.drop_table("organizational_memories")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_side_record_guard()")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_history_guard()")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_root_guard()")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_lineage_guard()")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_idempotency_result_v1_valid(text,jsonb)")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_event_payload_v1_valid(text,jsonb)")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_manifest_v1_valid(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_projection_v1_valid(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS organizational_memory_canonical_json(jsonb)")
