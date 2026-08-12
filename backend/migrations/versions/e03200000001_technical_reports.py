"""PATCH-032 Technical Report credential and persistence foundation.

Revision ID: e03200000001
Revises: e02800000001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e03200000001"
down_revision: str | None = "e02800000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "technical_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("engineering_scope", sa.Text(), nullable=False),
        sa.Column("draft_content", sa.Text(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("conclusions", sa.Text(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("is_preliminary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("evidence_deficiencies", sa.JSON(), nullable=False),
        sa.Column("unresolved_issues", sa.JSON(), nullable=False),
        sa.Column("follow_up_requirements", sa.JSON(), nullable=False),
        sa.Column("draft_revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("draft_revision_number", sa.Integer(), nullable=False),
        sa.Column("lifecycle", sa.String(16), server_default="draft", nullable=False),
        sa.Column("predecessor_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("technical_reports.id", ondelete="RESTRICT")),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("accepted_snapshot", postgresql.JSONB()),
        sa.Column("accepted_snapshot_digest", sa.String(64)),
        sa.Column("accepted_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("accepted_draft_revision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("accepted_aggregate_version", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("purpose IN ('field_experience','troubleshooting','engineering_analysis','technical_recommendation')", name="ck_technical_reports_purpose"),
        sa.CheckConstraint("lifecycle IN ('draft','accepted')", name="ck_technical_reports_lifecycle"),
        sa.CheckConstraint("version >= 1", name="ck_technical_reports_version"),
        sa.CheckConstraint("draft_revision_number >= 1", name="ck_technical_reports_draft_revision_number"),
        sa.CheckConstraint("predecessor_report_id IS NULL OR predecessor_report_id <> id", name="ck_technical_reports_distinct_predecessor"),
        sa.CheckConstraint(
            "(lifecycle='draft' AND accepted_snapshot IS NULL AND accepted_snapshot_digest IS NULL AND accepted_by_id IS NULL AND accepted_at IS NULL AND accepted_draft_revision_id IS NULL AND accepted_aggregate_version IS NULL) OR "
            "(lifecycle='accepted' AND accepted_snapshot IS NOT NULL AND accepted_snapshot_digest IS NOT NULL AND accepted_by_id IS NOT NULL AND accepted_at IS NOT NULL AND accepted_draft_revision_id IS NOT NULL AND accepted_aggregate_version IS NOT NULL AND accepted_aggregate_version=version)",
            name="ck_technical_reports_acceptance_coherence",
        ),
        sa.CheckConstraint("NOT is_preliminary OR json_array_length(evidence_deficiencies)+json_array_length(unresolved_issues)+json_array_length(follow_up_requirements)>0", name="ck_technical_reports_preliminary_basis"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_technical_reports_timestamp_order"),
        sa.CheckConstraint("accepted_snapshot_digest IS NULL OR accepted_snapshot_digest ~ '^[0-9a-f]{64}$'", name="ck_technical_reports_snapshot_digest"),
    )
    op.create_index("ix_technical_reports_workspace_order", "technical_reports", ["organization_id", "workspace_id", "lifecycle", sa.text("updated_at DESC"), sa.text("id DESC")])
    op.create_index("ix_technical_reports_project_order", "technical_reports", ["organization_id", "project_id", "lifecycle", sa.text("updated_at DESC"), sa.text("id DESC")])
    op.create_index("ix_technical_reports_owner_lifecycle", "technical_reports", ["organization_id", "owner_id", "lifecycle"])
    op.create_index("ix_technical_reports_predecessor", "technical_reports", ["predecessor_report_id"])

    op.create_table(
        "technical_report_provenance_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("technical_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("technical_reports.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("source_class", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("is_material", sa.Boolean(), nullable=False),
        sa.Column("owning_capability", sa.String(40)),
        sa.Column("reliance_role", sa.Text(), nullable=False),
        sa.Column("verification_status", sa.String(16), nullable=False),
        sa.Column("availability_status", sa.String(16), nullable=False),
        sa.Column("origin_attribution", sa.Text(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("integrity_algorithm", sa.String(16)),
        sa.Column("integrity_digest", sa.String(64)),
        sa.Column("minimal_historical_representation", sa.JSON()),
        sa.Column("capture_id", postgresql.UUID(as_uuid=True)),
        sa.Column("capture_version", sa.Integer()),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True)),
        sa.Column("evidence_version", sa.Integer()),
        sa.Column("engineering_object_id", postgresql.UUID(as_uuid=True)),
        sa.Column("engineering_object_version", sa.Integer()),
        sa.Column("engineering_relationship_id", postgresql.UUID(as_uuid=True)),
        sa.Column("engineering_relationship_version", sa.Integer()),
        sa.Column("canonical_snapshot_id", postgresql.UUID(as_uuid=True)),
        sa.Column("report_local_source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("external_reference", sa.Text()),
        sa.Column("submitted_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("standard_identity", sa.Text()),
        sa.Column("issuing_authority", sa.Text()),
        sa.Column("edition", sa.Text()),
        sa.Column("clause_or_location", sa.Text()),
        sa.Column("context_id", postgresql.UUID(as_uuid=True)),
        sa.Column("owning_context", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("technical_report_id", "ordinal", name="uq_technical_report_provenance_ordinal"),
        sa.CheckConstraint("source_class IN ('canonical_material','external_or_human_material','standards_material','contextual_non_material')", name="ck_technical_report_provenance_source_class"),
        sa.CheckConstraint("source_type IN ('universal_capture','evidence','engineering_object','engineering_relationship','external_or_human','standard','contextual')", name="ck_technical_report_provenance_source_type"),
        sa.CheckConstraint("verification_status IN ('verified','unverified')", name="ck_technical_report_provenance_verification"),
        sa.CheckConstraint("availability_status IN ('available','unavailable')", name="ck_technical_report_provenance_availability"),
        sa.CheckConstraint("ordinal >= 0", name="ck_technical_report_provenance_ordinal"),
        sa.CheckConstraint("capture_version IS NULL OR capture_version >= 1", name="ck_technical_report_provenance_capture_version"),
        sa.CheckConstraint("evidence_version IS NULL OR evidence_version >= 1", name="ck_technical_report_provenance_evidence_version"),
        sa.CheckConstraint("engineering_object_version IS NULL OR engineering_object_version >= 1", name="ck_technical_report_provenance_object_version"),
        sa.CheckConstraint("engineering_relationship_version IS NULL OR engineering_relationship_version >= 1", name="ck_technical_report_provenance_relationship_version"),
        sa.CheckConstraint(
            "(source_type='universal_capture' AND capture_id IS NOT NULL AND capture_version IS NOT NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='evidence' AND evidence_id IS NOT NULL AND evidence_version IS NOT NULL AND capture_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='engineering_object' AND engineering_object_id IS NOT NULL AND engineering_object_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='engineering_relationship' AND engineering_relationship_id IS NOT NULL AND engineering_relationship_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='external_or_human' AND report_local_source_id IS NOT NULL AND external_reference IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR "
            "(source_type='standard' AND standard_identity IS NOT NULL AND issuing_authority IS NOT NULL AND edition IS NOT NULL AND clause_or_location IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND context_id IS NULL) OR "
            "(source_type='contextual' AND context_id IS NOT NULL AND owning_context IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL)",
            name="ck_technical_report_provenance_locator_shape",
        ),
        sa.CheckConstraint(
            "(source_type='universal_capture' AND source_class='canonical_material' AND owning_capability='universal_capture' AND is_material) OR "
            "(source_type='evidence' AND source_class='canonical_material' AND owning_capability='evidence' AND is_material) OR "
            "(source_type='engineering_object' AND source_class='canonical_material' AND owning_capability='engineering_object' AND is_material) OR "
            "(source_type='engineering_relationship' AND source_class='canonical_material' AND owning_capability='engineering_relationship' AND is_material) OR "
            "(source_type='external_or_human' AND source_class='external_or_human_material' AND owning_capability IS NULL AND is_material) OR "
            "(source_type='standard' AND source_class='standards_material' AND owning_capability IS NULL AND is_material) OR "
            "(source_type='contextual' AND source_class='contextual_non_material' AND owning_capability IS NULL AND NOT is_material)",
            name="ck_technical_report_provenance_owner_coherence",
        ),
        sa.CheckConstraint("NOT is_material OR (integrity_algorithm='sha256' AND integrity_digest IS NOT NULL)", name="ck_technical_report_provenance_material_integrity"),
        sa.CheckConstraint("integrity_digest IS NULL OR integrity_digest ~ '^[0-9a-f]{64}$'", name="ck_technical_report_provenance_digest_format"),
        sa.CheckConstraint(
            "(source_class='canonical_material' AND ((canonical_snapshot_id IS NOT NULL AND minimal_historical_representation IS NULL) OR (canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL))) OR "
            "(source_class IN ('external_or_human_material','standards_material') AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL) OR "
            "(source_class='contextual_non_material' AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NULL AND integrity_algorithm IS NULL AND integrity_digest IS NULL)",
            name="ck_technical_report_provenance_historical_basis",
        ),
    )
    op.create_index("ix_technical_report_provenance_report", "technical_report_provenance_entries", ["technical_report_id", "ordinal"])
    op.create_index("ix_technical_report_provenance_capture", "technical_report_provenance_entries", ["capture_id"], postgresql_where=sa.text("capture_id IS NOT NULL"))
    op.create_index("ix_technical_report_provenance_evidence", "technical_report_provenance_entries", ["evidence_id"], postgresql_where=sa.text("evidence_id IS NOT NULL"))
    op.create_index("ix_technical_report_provenance_object", "technical_report_provenance_entries", ["engineering_object_id"], postgresql_where=sa.text("engineering_object_id IS NOT NULL"))
    op.create_index("ix_technical_report_provenance_relationship", "technical_report_provenance_entries", ["engineering_relationship_id"], postgresql_where=sa.text("engineering_relationship_id IS NOT NULL"))

    op.create_table(
        "technical_report_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("technical_reports.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_technical_report_outbox_event"),
        sa.UniqueConstraint("aggregate_id", "aggregate_version", "event_type", name="uq_technical_report_outbox_aggregate_event"),
        sa.CheckConstraint("aggregate_version >= 1", name="ck_technical_report_outbox_version"),
        sa.CheckConstraint("schema_version = 1", name="ck_technical_report_outbox_schema_version"),
    )
    op.create_index("ix_technical_report_outbox_unpublished", "technical_report_outbox", ["published_at", "occurred_at"])

    op.create_table(
        "technical_report_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("command_type", sa.String(128), nullable=False),
        sa.Column("idempotency_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("technical_reports.id", ondelete="RESTRICT")),
        sa.Column("result", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "actor_id", "command_type", "idempotency_id", name="uq_technical_report_idempotency_scope"),
        sa.CheckConstraint("status IN ('pending','completed')", name="ck_technical_report_idempotency_status"),
    )
    op.create_index("ix_technical_report_idempotency_lookup", "technical_report_idempotency", ["organization_id", "actor_id", "command_type", "idempotency_id"])

    op.execute("""
        CREATE FUNCTION technical_report_canonical_json(value jsonb) RETURNS text
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE result text;
        BEGIN
          CASE jsonb_typeof(value)
            WHEN 'object' THEN
              SELECT COALESCE('{' || string_agg(to_jsonb(key)::text || ':' || technical_report_canonical_json(value -> key), ',' ORDER BY key) || '}', '{}')
              INTO result FROM jsonb_object_keys(value) AS key;
            WHEN 'array' THEN
              SELECT COALESCE('[' || string_agg(technical_report_canonical_json(item), ',' ORDER BY ordinal) || ']', '[]')
              INTO result FROM jsonb_array_elements(value) WITH ORDINALITY AS elements(item, ordinal);
            ELSE result := value::text;
          END CASE;
          RETURN result;
        END
        $$
    """)
    op.execute("""
        CREATE FUNCTION technical_report_canonical_utc_valid(value text) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE parsed timestamptz;
        BEGIN
          IF value !~ '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{6}Z$' THEN RETURN false; END IF;
          parsed := value::timestamptz;
          RETURN to_char(parsed AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') = value;
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute("""
        CREATE FUNCTION technical_report_text_valid(value text, maximum integer, single_line boolean) RETURNS boolean
        LANGUAGE sql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
          SELECT value = btrim(value,
                 chr(9) || chr(10) || chr(11) || chr(12) || chr(13)
              || chr(28) || chr(29) || chr(30) || chr(31) || chr(32)
              || chr(133) || chr(160) || chr(5760)
              || chr(8192) || chr(8193) || chr(8194) || chr(8195)
              || chr(8196) || chr(8197) || chr(8198) || chr(8199)
              || chr(8200) || chr(8201) || chr(8202)
              || chr(8232) || chr(8233) || chr(8239) || chr(8287)
              || chr(12288))
             AND value = normalize(value, NFC)
             AND length(value) >= 1
             AND (maximum = 0 OR length(value) <= maximum)
             AND translate(value, chr(10) || chr(9), '') !~ '[[:cntrl:]]'
             AND (NOT single_line OR value !~ E'[\\n\\r]')
        $$
    """)
    op.execute("""
        CREATE FUNCTION technical_report_historical_basis_valid(source_type text, basis jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE keys text[]; uuid_pattern text := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
        BEGIN
          IF jsonb_typeof(basis) <> 'object' THEN RETURN false; END IF;
          IF source_type = 'universal_capture' THEN
            keys := ARRAY['basis_schema_version','source_category','capture_id','source_version','organization_id','project_id','workspace_id','discipline','engineering_object_id','source_kind','original_content','source_reference','creator_id','lifecycle','created_at'];
            RETURN basis ?& keys AND (SELECT count(*) FROM jsonb_object_keys(basis))=cardinality(keys)
              AND jsonb_typeof(basis->'basis_schema_version')='number' AND (basis->>'basis_schema_version')::numeric=1
              AND basis->>'source_category'='universal_capture' AND basis->>'capture_id'~uuid_pattern AND basis->>'organization_id'~uuid_pattern
              AND jsonb_typeof(basis->'source_version')='number' AND (basis->>'source_version')::numeric>=1 AND (basis->>'source_version')::numeric=trunc((basis->>'source_version')::numeric)
              AND jsonb_typeof(basis->'project_id')='number' AND (basis->>'project_id')::numeric>=1 AND (basis->>'project_id')::numeric=trunc((basis->>'project_id')::numeric)
              AND (jsonb_typeof(basis->'workspace_id')='null' OR (jsonb_typeof(basis->'workspace_id')='number' AND (basis->>'workspace_id')::numeric>=1 AND (basis->>'workspace_id')::numeric=trunc((basis->>'workspace_id')::numeric)))
              AND (jsonb_typeof(basis->'discipline')='null' OR basis->>'discipline' IN ('instrumentation','electrical','industrial_automation','shared_engineering'))
              AND (jsonb_typeof(basis->'engineering_object_id')='null' OR basis->>'engineering_object_id'~uuid_pattern)
              AND basis->>'source_kind' IN ('observation','question','assumption','rationale','discussion_note','correspondence_note','field_note','review_note','outcome','lesson_candidate','external_record_note')
              AND jsonb_typeof(basis->'original_content')='string' AND technical_report_text_valid(basis->>'original_content',10000,false)
              AND (jsonb_typeof(basis->'source_reference')='null' OR (jsonb_typeof(basis->'source_reference')='string' AND technical_report_text_valid(basis->>'source_reference',512,true)))
              AND jsonb_typeof(basis->'creator_id')='number' AND (basis->>'creator_id')::numeric>=1 AND (basis->>'creator_id')::numeric=trunc((basis->>'creator_id')::numeric)
              AND basis->>'lifecycle' IN ('captured','withdrawn','superseded')
              AND jsonb_typeof(basis->'created_at')='string' AND technical_report_canonical_utc_valid(basis->>'created_at');
          ELSIF source_type = 'evidence' THEN
            keys := ARRAY['basis_schema_version','source_category','evidence_id','source_version','organization_id','project_id','workspace_id','lifecycle','source_kind','source_reference','source_revision','source_standing','effective_at','supported_fact','creator_id'];
            RETURN basis ?& keys AND (SELECT count(*) FROM jsonb_object_keys(basis))=cardinality(keys)
              AND jsonb_typeof(basis->'basis_schema_version')='number' AND (basis->>'basis_schema_version')::numeric=1
              AND basis->>'source_category'='evidence' AND basis->>'evidence_id'~uuid_pattern AND basis->>'organization_id'~uuid_pattern
              AND jsonb_typeof(basis->'source_version')='number' AND (basis->>'source_version')::numeric>=1 AND (basis->>'source_version')::numeric=trunc((basis->>'source_version')::numeric)
              AND (jsonb_typeof(basis->'project_id')='null' OR (jsonb_typeof(basis->'project_id')='number' AND (basis->>'project_id')::numeric>=1 AND (basis->>'project_id')::numeric=trunc((basis->>'project_id')::numeric)))
              AND (jsonb_typeof(basis->'workspace_id')='null' OR (jsonb_typeof(basis->'workspace_id')='number' AND (basis->>'workspace_id')::numeric>=1 AND (basis->>'workspace_id')::numeric=trunc((basis->>'workspace_id')::numeric)))
              AND basis->>'lifecycle' IN ('proposed','current','withdrawn','superseded','rejected')
              AND basis->>'source_kind' IN ('engineering_record','external_reference','human_review','technical_decision','standard_reference','inspection_record','commissioning_record')
              AND jsonb_typeof(basis->'source_reference')='string' AND technical_report_text_valid(basis->>'source_reference',512,true)
              AND jsonb_typeof(basis->'source_revision')='string' AND technical_report_text_valid(basis->>'source_revision',128,true)
              AND basis->>'source_standing' IN ('draft','current','withdrawn','superseded')
              AND (jsonb_typeof(basis->'effective_at')='null' OR (jsonb_typeof(basis->'effective_at')='string' AND technical_report_canonical_utc_valid(basis->>'effective_at')))
              AND jsonb_typeof(basis->'supported_fact')='string' AND technical_report_text_valid(basis->>'supported_fact',2000,false)
              AND jsonb_typeof(basis->'creator_id')='number' AND (basis->>'creator_id')::numeric>=1 AND (basis->>'creator_id')::numeric=trunc((basis->>'creator_id')::numeric);
          ELSIF source_type = 'engineering_object' THEN
            keys := ARRAY['basis_schema_version','source_category','engineering_object_id','source_version','organization_id','customer_id','project_id','workspace_id','family','discipline','object_type','subtype','lifecycle','authority_standing','creator_id','steward_id'];
            RETURN basis ?& keys AND (SELECT count(*) FROM jsonb_object_keys(basis))=cardinality(keys)
              AND jsonb_typeof(basis->'basis_schema_version')='number' AND (basis->>'basis_schema_version')::numeric=1
              AND basis->>'source_category'='engineering_object' AND basis->>'engineering_object_id'~uuid_pattern AND basis->>'organization_id'~uuid_pattern
              AND jsonb_typeof(basis->'source_version')='number' AND (basis->>'source_version')::numeric>=1 AND (basis->>'source_version')::numeric=trunc((basis->>'source_version')::numeric)
              AND (jsonb_typeof(basis->'customer_id')='null' OR (jsonb_typeof(basis->'customer_id')='number' AND (basis->>'customer_id')::numeric>=1 AND (basis->>'customer_id')::numeric=trunc((basis->>'customer_id')::numeric)))
              AND jsonb_typeof(basis->'project_id')='number' AND (basis->>'project_id')::numeric>=1 AND (basis->>'project_id')::numeric=trunc((basis->>'project_id')::numeric)
              AND jsonb_typeof(basis->'workspace_id')='number' AND (basis->>'workspace_id')::numeric>=1 AND (basis->>'workspace_id')::numeric=trunc((basis->>'workspace_id')::numeric)
              AND basis->>'family' IN ('instrumentation','electrical','automation','shared')
              AND basis->>'discipline' IN ('instrumentation','electrical','industrial_automation','shared_engineering')
              AND basis->>'object_type' IN ('instrument','transmitter','analyzer','flowmeter','control_valve','instrument_loop','junction_box','instrument_panel','motor','transformer','mcc','switchgear','electrical_panel','electrical_cable','plc','dcs_controller','esd_controller','control_cabinet','io_channel','hmi','control_logic','project','vendor','requirement','standard','datasheet','drawing','technical_decision')
              AND jsonb_typeof(basis->'subtype')='null' AND basis->>'lifecycle' IN ('proposed','active','superseded','withdrawn','retired')
              AND basis->>'authority_standing' IN ('draft','proposed','reviewed','approved','disputed','rejected')
              AND jsonb_typeof(basis->'creator_id')='number' AND (basis->>'creator_id')::numeric>=1 AND (basis->>'creator_id')::numeric=trunc((basis->>'creator_id')::numeric)
              AND jsonb_typeof(basis->'steward_id')='number' AND (basis->>'steward_id')::numeric>=1 AND (basis->>'steward_id')::numeric=trunc((basis->>'steward_id')::numeric);
          ELSIF source_type = 'engineering_relationship' THEN
            keys := ARRAY['basis_schema_version','source_category','engineering_relationship_id','source_version','organization_id','project_id','workspace_id','source_object_id','target_object_id','relationship_family','relationship_type','lifecycle','authority_standing','evidence_references','creator_id','steward_id','reviewer_id','approver_id'];
            RETURN basis ?& keys AND (SELECT count(*) FROM jsonb_object_keys(basis))=cardinality(keys)
              AND jsonb_typeof(basis->'basis_schema_version')='number' AND (basis->>'basis_schema_version')::numeric=1
              AND basis->>'source_category'='engineering_relationship' AND basis->>'engineering_relationship_id'~uuid_pattern AND basis->>'organization_id'~uuid_pattern
              AND basis->>'source_object_id'~uuid_pattern AND basis->>'target_object_id'~uuid_pattern AND basis->>'source_object_id'<>basis->>'target_object_id'
              AND jsonb_typeof(basis->'source_version')='number' AND (basis->>'source_version')::numeric>=1 AND (basis->>'source_version')::numeric=trunc((basis->>'source_version')::numeric)
              AND jsonb_typeof(basis->'project_id')='number' AND (basis->>'project_id')::numeric>=1 AND (basis->>'project_id')::numeric=trunc((basis->>'project_id')::numeric)
              AND jsonb_typeof(basis->'workspace_id')='number' AND (basis->>'workspace_id')::numeric>=1 AND (basis->>'workspace_id')::numeric=trunc((basis->>'workspace_id')::numeric)
              AND basis->>'relationship_family' IN ('structural','physical','electrical','instrumentation','automation','dependency')
              AND basis->>'relationship_type' IN ('part_of','belongs_to_system','belongs_to_subsystem','belongs_to_package','grouped_with','installed_in','located_in','connected_to','mounted_on','connected_through','mechanically_coupled_to','terminated_at','routed_through','shares_enclosure_with','powered_by','protected_by','isolated_by','earthed_through','connected_to_busbar','controlled_by_feeder','backed_up_by_ups','measures','transmits_to','receives_process_input_from','connected_to_loop','connected_to_io_channel','actuates','positioned_by','monitored_by','provides_feedback_to','compensated_by','calibrated_against','controlled_by','commands','receives_signal_from','sends_signal_to','implemented_in','interlocked_with','trips','initiates','inhibits','participates_in_sequence','generates_alarm_for','executes_logic_for','depends_on','affects','enables','prevents','constrains','replaces','supersedes','derived_from')
              AND basis->>'lifecycle' IN ('proposed','current','superseded','withdrawn','rejected') AND basis->>'authority_standing' IN ('draft','proposed','reviewed','approved','disputed','rejected')
              AND jsonb_typeof(basis->'evidence_references')='array' AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(basis->'evidence_references') x WHERE jsonb_typeof(x)<>'string' OR trim(both '"' from x::text)!~uuid_pattern)
              AND (SELECT count(*) FROM jsonb_array_elements(basis->'evidence_references'))=(SELECT count(DISTINCT x::text) FROM jsonb_array_elements(basis->'evidence_references') x)
              AND jsonb_typeof(basis->'creator_id')='number' AND (basis->>'creator_id')::numeric>=1 AND (basis->>'creator_id')::numeric=trunc((basis->>'creator_id')::numeric)
              AND jsonb_typeof(basis->'steward_id')='number' AND (basis->>'steward_id')::numeric>=1 AND (basis->>'steward_id')::numeric=trunc((basis->>'steward_id')::numeric)
              AND (jsonb_typeof(basis->'reviewer_id')='null' OR (jsonb_typeof(basis->'reviewer_id')='number' AND (basis->>'reviewer_id')::numeric>=1 AND (basis->>'reviewer_id')::numeric=trunc((basis->>'reviewer_id')::numeric)))
              AND (jsonb_typeof(basis->'approver_id')='null' OR (jsonb_typeof(basis->'approver_id')='number' AND (basis->>'approver_id')::numeric>=1 AND (basis->>'approver_id')::numeric=trunc((basis->>'approver_id')::numeric)));
          END IF;
          RETURN false;
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute("""
        CREATE FUNCTION technical_report_provenance_json_valid(entry jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE keys text[] := ARRAY['entry_id','ordinal','source_class','source_type','is_material','owning_capability','reliance_role','verification_status','availability_status','origin_attribution','limitations','locator','integrity_algorithm','integrity_digest']; st text; sc text; locator jsonb; uuid_pattern text := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'; locator_keys text[];
        BEGIN
          IF jsonb_typeof(entry)<>'object' OR NOT entry ?& keys OR (SELECT count(*) FROM jsonb_object_keys(entry))<>cardinality(keys) THEN RETURN false; END IF;
          st:=entry->>'source_type'; sc:=entry->>'source_class'; locator:=entry->'locator';
          IF entry->>'entry_id'!~uuid_pattern OR jsonb_typeof(entry->'ordinal')<>'number' OR (entry->>'ordinal')::numeric<0 OR (entry->>'ordinal')::numeric<>trunc((entry->>'ordinal')::numeric)
             OR jsonb_typeof(entry->'is_material')<>'boolean' OR jsonb_typeof(entry->'reliance_role')<>'string' OR NOT technical_report_text_valid(entry->>'reliance_role',0,false)
             OR entry->>'verification_status' NOT IN ('verified','unverified') OR entry->>'availability_status' NOT IN ('available','unavailable')
             OR jsonb_typeof(entry->'origin_attribution')<>'string' OR NOT technical_report_text_valid(entry->>'origin_attribution',0,false) OR jsonb_typeof(entry->'limitations')<>'array'
             OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(entry->'limitations') x WHERE NOT technical_report_text_valid(x,0,false))
             OR EXISTS (SELECT 1 FROM jsonb_array_elements(entry->'limitations') x WHERE jsonb_typeof(x)<>'string') THEN RETURN false; END IF;
          IF st IN ('universal_capture','evidence','engineering_object','engineering_relationship') THEN
            RETURN sc='canonical_material' AND entry->>'owning_capability'=st AND (entry->>'is_material')::boolean
              AND entry->>'integrity_algorithm'='sha256' AND entry->>'integrity_digest'~'^[0-9a-f]{64}$'
              AND technical_report_historical_basis_valid(st,locator)
              AND encode(sha256(convert_to(technical_report_canonical_json(locator),'UTF8')),'hex')=entry->>'integrity_digest';
          ELSIF st='external_or_human' THEN
            locator_keys:=ARRAY['report_local_source_id','external_reference','submitted_by_id','observed_at','retrieved_at','submitted_at','minimal_representation'];
            RETURN sc='external_or_human_material' AND jsonb_typeof(entry->'owning_capability')='null' AND (entry->>'is_material')::boolean
              AND entry->>'integrity_algorithm'='sha256' AND entry->>'integrity_digest'~'^[0-9a-f]{64}$' AND jsonb_typeof(locator)='object' AND locator ?& locator_keys AND (SELECT count(*) FROM jsonb_object_keys(locator))=cardinality(locator_keys)
              AND locator->>'report_local_source_id'~uuid_pattern AND jsonb_typeof(locator->'external_reference')='string' AND technical_report_text_valid(locator->>'external_reference',512,true)
              AND (jsonb_typeof(locator->'submitted_by_id')='null' OR (jsonb_typeof(locator->'submitted_by_id')='number' AND (locator->>'submitted_by_id')::numeric>=1 AND (locator->>'submitted_by_id')::numeric=trunc((locator->>'submitted_by_id')::numeric)))
              AND (jsonb_typeof(locator->'observed_at')='null' OR (jsonb_typeof(locator->'observed_at')='string' AND technical_report_canonical_utc_valid(locator->>'observed_at')))
              AND (jsonb_typeof(locator->'retrieved_at')='null' OR (jsonb_typeof(locator->'retrieved_at')='string' AND technical_report_canonical_utc_valid(locator->>'retrieved_at')))
              AND (jsonb_typeof(locator->'submitted_at')='null' OR (jsonb_typeof(locator->'submitted_at')='string' AND technical_report_canonical_utc_valid(locator->>'submitted_at')))
              AND (jsonb_typeof(locator->'observed_at')='string' OR jsonb_typeof(locator->'retrieved_at')='string' OR jsonb_typeof(locator->'submitted_at')='string')
              AND jsonb_typeof(locator->'minimal_representation')='string' AND technical_report_text_valid(locator->>'minimal_representation',10000,false)
              AND encode(sha256(convert_to(technical_report_canonical_json(locator),'UTF8')),'hex')=entry->>'integrity_digest';
          ELSIF st='standard' THEN
            locator_keys:=ARRAY['standard_identity','issuing_authority','edition','clause_or_location','minimal_representation','retrieved_at'];
            RETURN sc='standards_material' AND jsonb_typeof(entry->'owning_capability')='null' AND (entry->>'is_material')::boolean
              AND entry->>'integrity_algorithm'='sha256' AND entry->>'integrity_digest'~'^[0-9a-f]{64}$' AND jsonb_typeof(locator)='object' AND locator ?& locator_keys AND (SELECT count(*) FROM jsonb_object_keys(locator))=cardinality(locator_keys)
              AND jsonb_typeof(locator->'standard_identity')='string' AND technical_report_text_valid(locator->>'standard_identity',512,true)
              AND jsonb_typeof(locator->'issuing_authority')='string' AND technical_report_text_valid(locator->>'issuing_authority',512,true)
              AND jsonb_typeof(locator->'edition')='string' AND technical_report_text_valid(locator->>'edition',512,true)
              AND jsonb_typeof(locator->'clause_or_location')='string' AND technical_report_text_valid(locator->>'clause_or_location',512,true)
              AND jsonb_typeof(locator->'minimal_representation')='string' AND technical_report_text_valid(locator->>'minimal_representation',10000,false)
              AND (jsonb_typeof(locator->'retrieved_at')='null' OR (jsonb_typeof(locator->'retrieved_at')='string' AND technical_report_canonical_utc_valid(locator->>'retrieved_at')))
              AND encode(sha256(convert_to(technical_report_canonical_json(locator),'UTF8')),'hex')=entry->>'integrity_digest';
          ELSIF st='contextual' THEN
            locator_keys:=ARRAY['context_id','owning_context'];
            RETURN sc='contextual_non_material' AND jsonb_typeof(entry->'owning_capability')='null' AND NOT (entry->>'is_material')::boolean
              AND jsonb_typeof(entry->'integrity_algorithm')='null' AND jsonb_typeof(entry->'integrity_digest')='null'
              AND jsonb_typeof(locator)='object' AND locator ?& locator_keys AND (SELECT count(*) FROM jsonb_object_keys(locator))=cardinality(locator_keys)
              AND locator->>'context_id'~uuid_pattern AND jsonb_typeof(locator->'owning_context')='string' AND technical_report_text_valid(locator->>'owning_context',128,true);
          END IF;
          RETURN false;
        EXCEPTION WHEN others THEN RETURN false;
        END
        $$
    """)
    op.execute("""
        CREATE FUNCTION technical_report_root_accepted_immutable() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE expected_keys text[] := ARRAY[
          'report_id','purpose','organization_id','workspace_id','project_id',
          'content','qualification','provenance','accepted_draft_revision',
          'accepted_aggregate_version','accepted_by_id','accepted_at','predecessor_report_id'
        ];
        BEGIN
            IF TG_OP <> 'INSERT' AND OLD.lifecycle = 'accepted' THEN
                RAISE EXCEPTION 'accepted Technical Report is immutable' USING ERRCODE = '55000';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            IF TG_OP = 'INSERT' AND NEW.lifecycle = 'accepted' THEN
                RAISE EXCEPTION 'Technical Report must enter accepted state through a draft transition' USING ERRCODE = '23514';
            END IF;
            IF NEW.lifecycle = 'accepted' THEN
                IF jsonb_typeof(NEW.accepted_snapshot) <> 'object'
                   OR NOT NEW.accepted_snapshot ?& expected_keys
                   OR (SELECT count(*) FROM jsonb_object_keys(NEW.accepted_snapshot)) <> cardinality(expected_keys)
                   OR jsonb_typeof(NEW.accepted_snapshot->'content') <> 'object'
                   OR NOT (NEW.accepted_snapshot->'content') ?& ARRAY['engineering_scope','technical_content','assumptions','uncertainty','limitations','conclusions','recommendations']
                   OR (SELECT count(*) FROM jsonb_object_keys(NEW.accepted_snapshot->'content')) <> 7
                   OR jsonb_typeof(NEW.accepted_snapshot->'qualification') <> 'object'
                   OR NOT (NEW.accepted_snapshot->'qualification') ?& ARRAY['is_preliminary','evidence_deficiencies','unresolved_issues','follow_up_requirements']
                   OR (SELECT count(*) FROM jsonb_object_keys(NEW.accepted_snapshot->'qualification')) <> 4
                   OR jsonb_typeof(NEW.accepted_snapshot->'accepted_draft_revision') <> 'object'
                   OR NOT (NEW.accepted_snapshot->'accepted_draft_revision') ?& ARRAY['revision_id','revision_number']
                   OR (SELECT count(*) FROM jsonb_object_keys(NEW.accepted_snapshot->'accepted_draft_revision')) <> 2
                   OR jsonb_typeof(NEW.accepted_snapshot->'provenance') <> 'array'
                   OR jsonb_array_length(NEW.accepted_snapshot->'provenance') = 0
                   OR (SELECT count(DISTINCT (entry->>'ordinal')::integer) FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry) <> jsonb_array_length(NEW.accepted_snapshot->'provenance')
                   OR (SELECT min((entry->>'ordinal')::integer) FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry) <> 0
                   OR (SELECT max((entry->>'ordinal')::integer) FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry) <> jsonb_array_length(NEW.accepted_snapshot->'provenance')-1
                   OR jsonb_typeof(NEW.accepted_snapshot->'workspace_id') <> 'number'
                   OR (NEW.accepted_snapshot->>'workspace_id')::numeric < 1
                   OR (NEW.accepted_snapshot->>'workspace_id')::numeric <> trunc((NEW.accepted_snapshot->>'workspace_id')::numeric)
                   OR NOT (jsonb_typeof(NEW.accepted_snapshot->'project_id')='null' OR (jsonb_typeof(NEW.accepted_snapshot->'project_id')='number' AND (NEW.accepted_snapshot->>'project_id')::numeric>=1 AND (NEW.accepted_snapshot->>'project_id')::numeric=trunc((NEW.accepted_snapshot->>'project_id')::numeric)))
                   OR jsonb_typeof(NEW.accepted_snapshot->'accepted_aggregate_version') <> 'number'
                   OR (NEW.accepted_snapshot->>'accepted_aggregate_version')::numeric < 1
                   OR (NEW.accepted_snapshot->>'accepted_aggregate_version')::numeric <> trunc((NEW.accepted_snapshot->>'accepted_aggregate_version')::numeric)
                   OR jsonb_typeof(NEW.accepted_snapshot->'accepted_by_id') <> 'number'
                   OR (NEW.accepted_snapshot->>'accepted_by_id')::numeric < 1
                   OR (NEW.accepted_snapshot->>'accepted_by_id')::numeric <> trunc((NEW.accepted_snapshot->>'accepted_by_id')::numeric)
                   OR jsonb_typeof(NEW.accepted_snapshot->'accepted_at') <> 'string'
                   OR NOT technical_report_canonical_utc_valid(NEW.accepted_snapshot->>'accepted_at')
                   OR NOT (jsonb_typeof(NEW.accepted_snapshot->'predecessor_report_id')='null' OR NEW.accepted_snapshot->>'predecessor_report_id'~'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry WHERE NOT technical_report_provenance_json_valid(entry))
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry WHERE entry->>'source_type' IN ('universal_capture','evidence','engineering_object','engineering_relationship') AND entry->'locator'->>'organization_id'<>NEW.organization_id::text)
                   OR (SELECT count(*) FROM technical_report_provenance_entries p WHERE p.technical_report_id=NEW.id) <> jsonb_array_length(NEW.accepted_snapshot->'provenance')
                   OR EXISTS (
                     SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry
                     WHERE NOT EXISTS (
                       SELECT 1 FROM technical_report_provenance_entries p
                       WHERE p.technical_report_id=NEW.id AND p.id::text=entry->>'entry_id'
                         AND p.ordinal=(entry->>'ordinal')::integer AND p.source_class=entry->>'source_class'
                         AND p.source_type=entry->>'source_type' AND p.is_material=(entry->>'is_material')::boolean
                         AND p.integrity_digest IS NOT DISTINCT FROM entry->>'integrity_digest'
                     )
                   )
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'engineering_scope')<>'string' OR NOT technical_report_text_valid(NEW.accepted_snapshot->'content'->>'engineering_scope',10000,false)
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'technical_content')<>'string' OR NOT technical_report_text_valid(NEW.accepted_snapshot->'content'->>'technical_content',10000,false)
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'uncertainty')<>'string' OR NOT technical_report_text_valid(NEW.accepted_snapshot->'content'->>'uncertainty',10000,false)
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'conclusions')<>'string' OR NOT technical_report_text_valid(NEW.accepted_snapshot->'content'->>'conclusions',10000,false)
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'assumptions')<>'array' OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'content'->'assumptions') x WHERE jsonb_typeof(x)<>'string') OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.accepted_snapshot->'content'->'assumptions') x WHERE NOT technical_report_text_valid(x,10000,false))
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'limitations')<>'array' OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'content'->'limitations') x WHERE jsonb_typeof(x)<>'string') OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.accepted_snapshot->'content'->'limitations') x WHERE NOT technical_report_text_valid(x,10000,false))
                   OR jsonb_typeof(NEW.accepted_snapshot->'content'->'recommendations')<>'array' OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'content'->'recommendations') x WHERE jsonb_typeof(x)<>'string') OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.accepted_snapshot->'content'->'recommendations') x WHERE NOT technical_report_text_valid(x,10000,false))
                   OR jsonb_typeof(NEW.accepted_snapshot->'qualification'->'is_preliminary')<>'boolean'
                   OR jsonb_typeof(NEW.accepted_snapshot->'qualification'->'evidence_deficiencies')<>'array'
                   OR jsonb_typeof(NEW.accepted_snapshot->'qualification'->'unresolved_issues')<>'array'
                   OR jsonb_typeof(NEW.accepted_snapshot->'qualification'->'follow_up_requirements')<>'array'
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'qualification'->'evidence_deficiencies') x WHERE jsonb_typeof(x)<>'string')
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.accepted_snapshot->'qualification'->'evidence_deficiencies') x WHERE NOT technical_report_text_valid(x,0,false))
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'qualification'->'unresolved_issues') x WHERE jsonb_typeof(x)<>'string')
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.accepted_snapshot->'qualification'->'unresolved_issues') x WHERE NOT technical_report_text_valid(x,0,false))
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'qualification'->'follow_up_requirements') x WHERE jsonb_typeof(x)<>'string')
                   OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.accepted_snapshot->'qualification'->'follow_up_requirements') x WHERE NOT technical_report_text_valid(x,0,false))
                   OR ((NEW.accepted_snapshot->'qualification'->>'is_preliminary')::boolean <> (jsonb_array_length(NEW.accepted_snapshot->'qualification'->'evidence_deficiencies')+jsonb_array_length(NEW.accepted_snapshot->'qualification'->'unresolved_issues')+jsonb_array_length(NEW.accepted_snapshot->'qualification'->'follow_up_requirements')>0))
                   OR jsonb_typeof(NEW.accepted_snapshot->'accepted_draft_revision'->'revision_id')<>'string'
                   OR NEW.accepted_snapshot->'accepted_draft_revision'->>'revision_id' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                   OR jsonb_typeof(NEW.accepted_snapshot->'accepted_draft_revision'->'revision_number')<>'number'
                   OR (NEW.accepted_snapshot->'accepted_draft_revision'->>'revision_number')::numeric<1
                   OR (NEW.accepted_snapshot->'accepted_draft_revision'->>'revision_number')::numeric<>trunc((NEW.accepted_snapshot->'accepted_draft_revision'->>'revision_number')::numeric)
                   OR NEW.accepted_snapshot->>'report_id' <> NEW.id::text
                   OR NEW.accepted_snapshot->>'organization_id' <> NEW.organization_id::text
                   OR (NEW.accepted_snapshot->>'workspace_id')::integer <> NEW.workspace_id
                   OR NOT ((NEW.project_id IS NULL AND jsonb_typeof(NEW.accepted_snapshot->'project_id')='null') OR (NEW.project_id IS NOT NULL AND (NEW.accepted_snapshot->>'project_id')::integer=NEW.project_id))
                   OR NEW.accepted_snapshot->>'purpose' <> NEW.purpose
                   OR (NEW.accepted_snapshot->>'accepted_by_id')::integer <> NEW.accepted_by_id
                   OR (NEW.accepted_snapshot->>'accepted_aggregate_version')::integer <> NEW.version
                   OR NEW.accepted_snapshot->'accepted_draft_revision'->>'revision_id' <> NEW.accepted_draft_revision_id::text
                   OR (NEW.accepted_snapshot->'accepted_draft_revision'->>'revision_number')::integer <> NEW.draft_revision_number
                   OR (NEW.accepted_snapshot->>'accepted_at')::timestamptz <> NEW.accepted_at
                   OR NOT ((NEW.predecessor_report_id IS NULL AND jsonb_typeof(NEW.accepted_snapshot->'predecessor_report_id')='null') OR (NEW.predecessor_report_id IS NOT NULL AND NEW.accepted_snapshot->>'predecessor_report_id'=NEW.predecessor_report_id::text))
                   OR NEW.accepted_snapshot->'content'->>'engineering_scope' <> NEW.engineering_scope
                   OR NEW.accepted_snapshot->'content'->>'technical_content' <> NEW.draft_content
                   OR NEW.accepted_snapshot->'content'->'assumptions' <> to_jsonb(NEW.assumptions)
                   OR NEW.accepted_snapshot->'content'->>'uncertainty' <> NEW.uncertainty
                   OR NEW.accepted_snapshot->'content'->'limitations' <> to_jsonb(NEW.limitations)
                   OR NEW.accepted_snapshot->'content'->>'conclusions' <> NEW.conclusions
                   OR NEW.accepted_snapshot->'content'->'recommendations' <> to_jsonb(NEW.recommendations)
                   OR (NEW.accepted_snapshot->'qualification'->>'is_preliminary')::boolean <> NEW.is_preliminary
                   OR NEW.accepted_snapshot->'qualification'->'evidence_deficiencies' <> to_jsonb(NEW.evidence_deficiencies)
                   OR NEW.accepted_snapshot->'qualification'->'unresolved_issues' <> to_jsonb(NEW.unresolved_issues)
                   OR NEW.accepted_snapshot->'qualification'->'follow_up_requirements' <> to_jsonb(NEW.follow_up_requirements)
                   OR NEW.accepted_snapshot_digest !~ '^[0-9a-f]{64}$'
                   OR encode(sha256(convert_to(technical_report_canonical_json(NEW.accepted_snapshot), 'UTF8')), 'hex') <> NEW.accepted_snapshot_digest THEN
                    RAISE EXCEPTION 'accepted Technical Report snapshot is invalid' USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_technical_reports_accepted_immutable
        BEFORE INSERT OR UPDATE OR DELETE ON technical_reports
        FOR EACH ROW EXECUTE FUNCTION technical_report_root_accepted_immutable()
    """)
    op.execute("""
        CREATE FUNCTION technical_report_provenance_accepted_immutable() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE report_lifecycle text; report_organization uuid; report_project integer; report_workspace integer; basis jsonb;
        BEGIN
            SELECT lifecycle, organization_id, project_id, workspace_id
            INTO report_lifecycle, report_organization, report_project, report_workspace FROM public.technical_reports
            WHERE id = COALESCE(NEW.technical_report_id, OLD.technical_report_id) FOR UPDATE;
            IF report_lifecycle = 'accepted' THEN
                RAISE EXCEPTION 'accepted Technical Report provenance is immutable' USING ERRCODE = '55000';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            IF NEW.source_class = 'canonical_material' AND NEW.canonical_snapshot_id IS NULL
            THEN
                basis := NEW.minimal_historical_representation::jsonb;
                IF NOT technical_report_historical_basis_valid(NEW.source_type, basis)
                   OR NEW.integrity_digest <> encode(sha256(convert_to(technical_report_canonical_json(basis), 'UTF8')), 'hex')
                   OR basis->>'organization_id' <> report_organization::text
                   OR (NEW.source_type='universal_capture' AND (report_project IS NULL OR (basis->>'project_id')::integer<>report_project OR NOT (jsonb_typeof(basis->'workspace_id')='null' OR (basis->>'workspace_id')::integer=report_workspace) OR basis->>'capture_id'<>NEW.capture_id::text OR (basis->>'source_version')::integer<>NEW.capture_version))
                   OR (NEW.source_type='evidence' AND (NOT (jsonb_typeof(basis->'project_id')='null' OR (report_project IS NOT NULL AND (basis->>'project_id')::integer=report_project)) OR NOT (jsonb_typeof(basis->'workspace_id')='null' OR (basis->>'workspace_id')::integer=report_workspace) OR basis->>'evidence_id'<>NEW.evidence_id::text OR (basis->>'source_version')::integer<>NEW.evidence_version))
                   OR (NEW.source_type='engineering_object' AND (report_project IS NULL OR (basis->>'project_id')::integer<>report_project OR basis->>'engineering_object_id'<>NEW.engineering_object_id::text OR (basis->>'source_version')::integer<>NEW.engineering_object_version OR (basis->>'workspace_id')::integer<>report_workspace))
                   OR (NEW.source_type='engineering_relationship' AND (report_project IS NULL OR (basis->>'project_id')::integer<>report_project OR basis->>'engineering_relationship_id'<>NEW.engineering_relationship_id::text OR (basis->>'source_version')::integer<>NEW.engineering_relationship_version OR (basis->>'workspace_id')::integer<>report_workspace)) THEN
                    RAISE EXCEPTION 'canonical historical fallback is invalid' USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_technical_report_provenance_accepted_immutable
        BEFORE INSERT OR UPDATE OR DELETE ON technical_report_provenance_entries
        FOR EACH ROW EXECUTE FUNCTION technical_report_provenance_accepted_immutable()
    """)
    op.execute("REVOKE ALL ON FUNCTION technical_report_root_accepted_immutable() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_provenance_accepted_immutable() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_canonical_json(jsonb) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_provenance_json_valid(jsonb) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_canonical_utc_valid(text) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_text_valid(text,integer,boolean) FROM PUBLIC")
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
            GRANT USAGE ON SCHEMA public TO satco_runtime;
            GRANT SELECT, INSERT, UPDATE, DELETE ON
              users, customers, contacts, projects, project_code_sequences,
              organizations, user_organization_memberships, engineering_workspaces,
              engineering_workspace_members, engineering_contexts, engineering_context_facts,
              engineering_context_values, engineering_context_assumptions,
              engineering_context_subject_references, engineering_context_source_references,
              engineering_context_relationships, interface_commitments
              TO satco_runtime;
            GRANT SELECT, INSERT, UPDATE ON
              engineering_objects, engineering_relationships, evidence,
              engineering_experience_captures,
              engineering_object_outbox, engineering_object_idempotency,
              engineering_relationship_outbox, engineering_relationship_idempotency,
              evidence_outbox, evidence_idempotency,
              engineering_experience_capture_outbox, engineering_experience_capture_idempotency
              TO satco_runtime;
            GRANT USAGE, SELECT ON SEQUENCE
              audit_logs_id_seq, contacts_id_seq, customers_id_seq,
              engineering_context_relationships_id_seq,
              engineering_context_source_references_id_seq,
              engineering_context_subject_references_id_seq,
              engineering_contexts_id_seq, engineering_workspaces_id_seq,
              interface_commitments_id_seq, projects_id_seq, users_id_seq
              TO satco_runtime;
            GRANT SELECT, INSERT ON technical_reports TO satco_runtime;
            GRANT UPDATE (engineering_scope, draft_content, assumptions, uncertainty, limitations,
              conclusions, recommendations, is_preliminary, evidence_deficiencies, unresolved_issues,
              follow_up_requirements, draft_revision_id, draft_revision_number, lifecycle, version,
              accepted_snapshot, accepted_snapshot_digest, accepted_by_id, accepted_at,
              accepted_draft_revision_id, accepted_aggregate_version, updated_at)
              ON technical_reports TO satco_runtime;
            GRANT SELECT, INSERT, UPDATE, DELETE ON technical_report_provenance_entries TO satco_runtime;
            GRANT SELECT, INSERT ON technical_report_outbox TO satco_runtime;
            GRANT UPDATE (published_at) ON technical_report_outbox TO satco_runtime;
            GRANT SELECT, INSERT ON technical_report_idempotency TO satco_runtime;
            GRANT UPDATE (status, aggregate_id, result, updated_at) ON technical_report_idempotency TO satco_runtime;
            REVOKE ALL ON audit_logs FROM satco_runtime;
            GRANT SELECT, INSERT ON audit_logs TO satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_root_accepted_immutable() FROM satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_provenance_accepted_immutable() FROM satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_canonical_json(jsonb) FROM satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_provenance_json_valid(jsonb) FROM satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_canonical_utc_valid(text) FROM satco_runtime;
            REVOKE EXECUTE ON FUNCTION technical_report_text_valid(text,integer,boolean) FROM satco_runtime;
          END IF;
        END $$
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_technical_report_provenance_accepted_immutable ON technical_report_provenance_entries")
    op.execute("DROP TRIGGER IF EXISTS trg_technical_reports_accepted_immutable ON technical_reports")
    op.execute("DROP FUNCTION IF EXISTS technical_report_provenance_accepted_immutable()")
    op.execute("DROP FUNCTION IF EXISTS technical_report_root_accepted_immutable()")
    op.execute("DROP FUNCTION IF EXISTS technical_report_provenance_json_valid(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS technical_report_historical_basis_valid(text,jsonb)")
    op.execute("DROP FUNCTION IF EXISTS technical_report_text_valid(text,integer,boolean)")
    op.execute("DROP FUNCTION IF EXISTS technical_report_canonical_utc_valid(text)")
    op.execute("DROP FUNCTION IF EXISTS technical_report_canonical_json(jsonb)")
    op.drop_index("ix_technical_report_idempotency_lookup", table_name="technical_report_idempotency")
    op.drop_table("technical_report_idempotency")
    op.drop_index("ix_technical_report_outbox_unpublished", table_name="technical_report_outbox")
    op.drop_table("technical_report_outbox")
    op.drop_table("technical_report_provenance_entries")
    op.drop_table("technical_reports")
