"""PATCH-053 Batch-5 additive prerequisite completion.

Revision ID: e05300000002
Revises: e05300000001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e05300000002"
down_revision = "e05300000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError("PATCH-053 Batch-5 requires exact e05300000001 predecessor")

    op.add_column("cross_discipline_idempotency", sa.Column("handoff_key", sa.String(64)))
    op.add_column("cross_discipline_idempotency", sa.Column("project_control_idempotency_key", postgresql.UUID(as_uuid=True)))
    op.add_column("cross_discipline_idempotency", sa.Column("project_control_correlation_id", postgresql.UUID(as_uuid=True)))
    op.add_column("cross_discipline_idempotency", sa.Column("project_control_impact_id", postgresql.UUID(as_uuid=True)))
    op.add_column("cross_discipline_idempotency", sa.Column("project_control_impact_snapshot_digest", sa.String(64)))
    op.create_unique_constraint("uq_xdi_idempotency_handoff_key", "cross_discipline_idempotency", ["handoff_key"])
    op.create_check_constraint("ck_xdi_idempotency_handoff_key_digest", "cross_discipline_idempotency", "handoff_key IS NULL OR handoff_key ~ '^[0-9a-f]{64}$'")
    op.create_check_constraint("ck_xdi_idempotency_impact_snapshot_digest", "cross_discipline_idempotency", "project_control_impact_snapshot_digest IS NULL OR project_control_impact_snapshot_digest ~ '^[0-9a-f]{64}$'")
    op.create_check_constraint("ck_xdi_idempotency_handoff_identity", "cross_discipline_idempotency", "(handoff_key IS NULL AND project_control_idempotency_key IS NULL AND project_control_correlation_id IS NULL) OR (handoff_key IS NOT NULL AND project_control_idempotency_key IS NOT NULL AND project_control_correlation_id IS NOT NULL)")
    op.create_check_constraint("ck_xdi_idempotency_handoff_result", "cross_discipline_idempotency", "(project_control_impact_id IS NULL AND project_control_impact_snapshot_digest IS NULL) OR (project_control_impact_id IS NOT NULL AND project_control_impact_snapshot_digest IS NOT NULL)")

    op.add_column("technical_report_provenance_entries", sa.Column("cross_discipline_assessment_id", postgresql.UUID(as_uuid=True)))
    op.add_column("technical_report_provenance_entries", sa.Column("cross_discipline_assessment_version", sa.Integer()))
    op.create_check_constraint("ck_technical_report_provenance_xdi_assessment_version", "technical_report_provenance_entries", "cross_discipline_assessment_version IS NULL OR cross_discipline_assessment_version >= 1")
    op.create_index("ix_technical_report_provenance_xdi_assessment", "technical_report_provenance_entries", ["cross_discipline_assessment_id"], postgresql_where=sa.text("cross_discipline_assessment_id IS NOT NULL"))
    op.drop_constraint("ck_technical_report_provenance_source_type", "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_source_type", "technical_report_provenance_entries", "source_type IN ('universal_capture','evidence','engineering_object','engineering_relationship','cross_discipline_assessment','external_or_human','standard','contextual')")
    op.drop_constraint("ck_technical_report_provenance_locator_shape", "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_locator_shape", "technical_report_provenance_entries", "(source_type='universal_capture' AND capture_id IS NOT NULL AND capture_version IS NOT NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='evidence' AND evidence_id IS NOT NULL AND evidence_version IS NOT NULL AND capture_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_object' AND engineering_object_id IS NOT NULL AND engineering_object_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_relationship' AND engineering_relationship_id IS NOT NULL AND engineering_relationship_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='cross_discipline_assessment' AND cross_discipline_assessment_id IS NOT NULL AND cross_discipline_assessment_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='external_or_human' AND report_local_source_id IS NOT NULL AND external_reference IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='standard' AND standard_identity IS NOT NULL AND issuing_authority IS NOT NULL AND edition IS NOT NULL AND clause_or_location IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND context_id IS NULL) OR (source_type='contextual' AND context_id IS NOT NULL AND owning_context IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL)")
    op.drop_constraint("ck_technical_report_provenance_owner_coherence", "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_owner_coherence", "technical_report_provenance_entries", "(source_type='universal_capture' AND source_class='canonical_material' AND owning_capability='universal_capture' AND is_material) OR (source_type='evidence' AND source_class='canonical_material' AND owning_capability='evidence' AND is_material) OR (source_type='engineering_object' AND source_class='canonical_material' AND owning_capability='engineering_object' AND is_material) OR (source_type='engineering_relationship' AND source_class='canonical_material' AND owning_capability='engineering_relationship' AND is_material) OR (source_type='cross_discipline_assessment' AND source_class='canonical_material' AND owning_capability='cross_discipline_assessment' AND is_material) OR (source_type='external_or_human' AND source_class='external_or_human_material' AND owning_capability IS NULL AND is_material) OR (source_type='standard' AND source_class='standards_material' AND owning_capability IS NULL AND is_material) OR (source_type='contextual' AND source_class='contextual_non_material' AND owning_capability IS NULL AND NOT is_material)")

    op.execute("ALTER FUNCTION technical_report_historical_basis_valid(text,jsonb) RENAME TO technical_report_historical_basis_pre053_valid")
    op.execute("""
    CREATE FUNCTION technical_report_historical_basis_valid(source_type text,basis jsonb) RETURNS boolean
    LANGUAGE sql IMMUTABLE STRICT SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      SELECT CASE WHEN source_type='cross_discipline_assessment' THEN
        jsonb_typeof(basis)='object'
        AND basis ?& ARRAY['basis_schema_version','source_category','assessment_id','source_version','organization_id','project_id','workspace_id','status','snapshot_digest','definition_digest','result_digest','completed_at']
        AND (SELECT count(*) FROM jsonb_object_keys(basis))=12
        AND basis->>'basis_schema_version'='1' AND basis->>'source_category'='cross_discipline_assessment'
        AND basis->>'assessment_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        AND basis->>'organization_id' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        AND jsonb_typeof(basis->'source_version')='number' AND (basis->>'source_version')::numeric>=1
        AND jsonb_typeof(basis->'project_id')='number' AND (basis->>'project_id')::numeric>=1
        AND basis->>'status' IN ('completed_no_findings','completed_with_findings','indeterminate','unavailable')
        AND basis->>'snapshot_digest' ~ '^[0-9a-f]{64}$' AND basis->>'definition_digest' ~ '^[0-9a-f]{64}$' AND basis->>'result_digest' ~ '^[0-9a-f]{64}$'
      ELSE technical_report_historical_basis_pre053_valid(source_type,basis) END
    $$
    """)
    op.execute("REVOKE ALL ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM PUBLIC")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE EXECUTE ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM satco_runtime;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_registry_installer') THEN
        REVOKE EXECUTE ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM satco_registry_installer;
      END IF;
    END $$
    """)


def downgrade() -> None:
    bind = op.get_bind()
    used = bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM cross_discipline_idempotency WHERE handoff_key IS NOT NULL) OR EXISTS(SELECT 1 FROM technical_report_provenance_entries WHERE cross_discipline_assessment_id IS NOT NULL)")).scalar_one()
    if used:
        raise RuntimeError("PATCH-053 Batch-5 downgrade is prohibited while retained handoff or assessment Report basis exists")
    op.execute("DROP FUNCTION technical_report_historical_basis_valid(text,jsonb)")
    op.execute("ALTER FUNCTION technical_report_historical_basis_pre053_valid(text,jsonb) RENAME TO technical_report_historical_basis_valid")
    op.drop_constraint("ck_technical_report_provenance_source_type", "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_source_type", "technical_report_provenance_entries", "source_type IN ('universal_capture','evidence','engineering_object','engineering_relationship','external_or_human','standard','contextual')")
    op.drop_constraint("ck_technical_report_provenance_owner_coherence", "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_owner_coherence", "technical_report_provenance_entries", "(source_type='universal_capture' AND source_class='canonical_material' AND owning_capability='universal_capture' AND is_material) OR (source_type='evidence' AND source_class='canonical_material' AND owning_capability='evidence' AND is_material) OR (source_type='engineering_object' AND source_class='canonical_material' AND owning_capability='engineering_object' AND is_material) OR (source_type='engineering_relationship' AND source_class='canonical_material' AND owning_capability='engineering_relationship' AND is_material) OR (source_type='external_or_human' AND source_class='external_or_human_material' AND owning_capability IS NULL AND is_material) OR (source_type='standard' AND source_class='standards_material' AND owning_capability IS NULL AND is_material) OR (source_type='contextual' AND source_class='contextual_non_material' AND owning_capability IS NULL AND NOT is_material)")
    op.drop_constraint("ck_technical_report_provenance_locator_shape", "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_locator_shape", "technical_report_provenance_entries", "(source_type='universal_capture' AND capture_id IS NOT NULL AND capture_version IS NOT NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='evidence' AND evidence_id IS NOT NULL AND evidence_version IS NOT NULL AND capture_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_object' AND engineering_object_id IS NOT NULL AND engineering_object_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_relationship' AND engineering_relationship_id IS NOT NULL AND engineering_relationship_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='external_or_human' AND report_local_source_id IS NOT NULL AND external_reference IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='standard' AND standard_identity IS NOT NULL AND issuing_authority IS NOT NULL AND edition IS NOT NULL AND clause_or_location IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND context_id IS NULL) OR (source_type='contextual' AND context_id IS NOT NULL AND owning_context IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL)")
    op.drop_index("ix_technical_report_provenance_xdi_assessment", table_name="technical_report_provenance_entries")
    op.drop_constraint("ck_technical_report_provenance_xdi_assessment_version", "technical_report_provenance_entries", type_="check")
    op.drop_column("technical_report_provenance_entries", "cross_discipline_assessment_version")
    op.drop_column("technical_report_provenance_entries", "cross_discipline_assessment_id")
    for name in ("ck_xdi_idempotency_handoff_result", "ck_xdi_idempotency_handoff_identity", "ck_xdi_idempotency_impact_snapshot_digest", "ck_xdi_idempotency_handoff_key_digest"):
        op.drop_constraint(name, "cross_discipline_idempotency", type_="check")
    op.drop_constraint("uq_xdi_idempotency_handoff_key", "cross_discipline_idempotency", type_="unique")
    for name in ("project_control_impact_snapshot_digest", "project_control_impact_id", "project_control_correlation_id", "project_control_idempotency_key", "handoff_key"):
        op.drop_column("cross_discipline_idempotency", name)
