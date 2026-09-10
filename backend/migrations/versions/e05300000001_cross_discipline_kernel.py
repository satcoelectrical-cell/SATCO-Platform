"""PATCH-053 Batch-1 governed cross-discipline kernel.

Revision ID: e05300000001
Revises: e05200000002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e05300000001"
down_revision = "e05200000002"
branch_labels = None
depends_on = None


def _digest(name):
    return sa.CheckConstraint(
        f"char_length({name})=64 AND {name} ~ '^[0-9a-f]{{64}}$'",
        name=f"ck_xdi_{name}",
    )


def _scope_columns():
    return (
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
    )


def _scope_fk(name):
    return sa.ForeignKeyConstraint(
        ["organization_id", "project_id", "assessment_id"],
        ["cross_discipline_assessments.organization_id", "cross_discipline_assessments.project_id", "cross_discipline_assessments.id"],
        name=name, ondelete="RESTRICT",
    )


def upgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError("PATCH-053 requires exact e05200000002 predecessor")

    op.create_table(
        "cross_discipline_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("purpose", sa.String(48), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("combination_id", sa.String(128), nullable=False),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.Column("scope_digest", sa.String(64), nullable=False),
        sa.Column("status", sa.String(48), nullable=False),
        sa.Column("reason_code", sa.String(64)),
        sa.Column("aggregate_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], name="fk_xdi_root_project_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "project_id", "id", name="uq_xdi_root_scope"),
        sa.UniqueConstraint("organization_id", "project_id", "actor_id", "idempotency_key", name="uq_xdi_assessment_idempotency"),
        sa.CheckConstraint("aggregate_version>=1", name="ck_xdi_assessment_version"),
        sa.CheckConstraint("purpose IN ('interface_assessment','current_handoff_gate','explicit_change_impact')", name="ck_xdi_assessment_purpose"),
        sa.CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 4000", name="ck_xdi_assessment_rationale"),
        sa.CheckConstraint("status IN ('completed_no_findings','completed_with_findings','indeterminate','unavailable')", name="ck_xdi_assessment_status"),
        sa.CheckConstraint("(status IN ('indeterminate','unavailable') AND reason_code IS NOT NULL) OR (status IN ('completed_no_findings','completed_with_findings') AND reason_code IS NULL)", name="ck_xdi_assessment_status_reason"),
        _digest("request_digest"), _digest("scope_digest"),
    )
    op.create_index("ix_xdi_assessment_project_time", "cross_discipline_assessments", ["organization_id", "project_id", "completed_at", "id"])
    op.create_index("ix_xdi_assessment_status_combination", "cross_discipline_assessments", ["organization_id", "project_id", "status", "combination_id"])

    op.create_table(
        "cross_discipline_assessment_snapshots",
        *_scope_columns(),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("registry_digest", sa.String(64), nullable=False),
        sa.Column("definition_digest", sa.String(64), nullable=False),
        sa.Column("source_manifest_digest", sa.String(64), nullable=False),
        sa.Column("finding_set_digest", sa.String(64), nullable=False),
        sa.Column("snapshot_digest", sa.String(64), nullable=False),
        sa.Column("result_digest", sa.String(64), nullable=False),
        sa.Column("observed_through", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        _scope_fk("fk_xdi_snapshot_root_scope"),
        sa.PrimaryKeyConstraint("assessment_id"),
        sa.CheckConstraint("octet_length(payload::text)<=2097152", name="ck_xdi_snapshot_size"),
        *(_digest(name) for name in ("registry_digest", "definition_digest", "source_manifest_digest", "finding_set_digest", "snapshot_digest", "result_digest")),
    )
    op.create_table(
        "cross_discipline_assessment_workspaces",
        *_scope_columns(),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("package_key", sa.String(64), nullable=False),
        sa.Column("discipline_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("binding_revision", sa.BigInteger(), nullable=False),
        sa.Column("binding_digest", sa.String(64), nullable=False),
        _scope_fk("fk_xdi_workspace_root_scope"),
        sa.ForeignKeyConstraint(["workspace_id", "project_id"], ["engineering_workspaces.id", "engineering_workspaces.project_id"], name="fk_xdi_workspace_project_scope", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("assessment_id", "workspace_id", "package_key"),
        sa.UniqueConstraint("assessment_id", "workspace_id", name="uq_xdi_workspace_participant"),
        sa.UniqueConstraint("assessment_id", "role", name="uq_xdi_workspace_role"),
        sa.CheckConstraint("binding_revision>=1", name="ck_xdi_workspace_binding_revision"),
        _digest("binding_digest"),
    )
    op.create_table(
        "cross_discipline_source_projections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_scope_columns(),
        sa.Column("projection_id", sa.String(128), nullable=False),
        sa.Column("owner_kind", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("revision_kind", sa.String(32), nullable=False),
        sa.Column("revision", sa.String(128), nullable=False),
        sa.Column("schema_id", sa.String(128), nullable=False),
        sa.Column("adapter_capability_id", sa.String(128), nullable=False),
        sa.Column("sensitivity", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("projection_digest", sa.String(64), nullable=False),
        _scope_fk("fk_xdi_projection_root_scope"),
        sa.UniqueConstraint("assessment_id", "id", name="uq_xdi_projection_root"),
        sa.UniqueConstraint("assessment_id", "projection_id", name="uq_xdi_projection_id"),
        sa.UniqueConstraint("assessment_id", "owner_kind", "owner_id", "revision_kind", "revision", "projection_id", name="uq_xdi_projection_owner"),
        sa.CheckConstraint("revision_kind IN ('aggregate_version','snapshot_digest')", name="ck_xdi_projection_revision_kind"),
        sa.CheckConstraint("octet_length(payload::text)<=262144", name="ck_xdi_projection_size"),
        _digest("projection_digest"),
    )
    op.create_index("ix_xdi_projection_owner", "cross_discipline_source_projections", ["assessment_id", "owner_kind", "owner_id", "revision"])
    op.create_table(
        "cross_discipline_completeness_attestations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_scope_columns(),
        sa.Column("owner_kind", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("selector_digest", sa.String(64), nullable=False),
        sa.Column("observed_cardinality", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("non_truncated", sa.Boolean(), nullable=False),
        sa.Column("negative_result", sa.Boolean(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("attestation_digest", sa.String(64), nullable=False),
        _scope_fk("fk_xdi_attestation_root_scope"),
        sa.UniqueConstraint("assessment_id", "id", name="uq_xdi_attestation_root"),
        sa.UniqueConstraint("assessment_id", "attestation_digest", name="uq_xdi_attestation_digest"),
        sa.CheckConstraint("observed_cardinality>=0 AND page_count>=0", name="ck_xdi_attestation_counts"),
        _digest("selector_digest"), _digest("attestation_digest"),
    )
    op.create_table(
        "cross_discipline_interface_occurrences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_scope_columns(),
        sa.Column("occurrence_key", sa.String(64), nullable=False),
        sa.Column("interface_definition_id", sa.String(128), nullable=False),
        sa.Column("provider_workspace_id", sa.Integer(), nullable=False),
        sa.Column("consumer_workspace_id", sa.Integer(), nullable=False),
        sa.Column("commitment_id", sa.Integer()),
        sa.Column("commitment_version", sa.Integer()),
        sa.Column("applicability", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurrence_digest", sa.String(64), nullable=False),
        _scope_fk("fk_xdi_occurrence_root_scope"),
        sa.ForeignKeyConstraint(["assessment_id", "provider_workspace_id"], ["cross_discipline_assessment_workspaces.assessment_id", "cross_discipline_assessment_workspaces.workspace_id"], name="fk_xdi_occurrence_provider_workspace", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assessment_id", "consumer_workspace_id"], ["cross_discipline_assessment_workspaces.assessment_id", "cross_discipline_assessment_workspaces.workspace_id"], name="fk_xdi_occurrence_consumer_workspace", ondelete="RESTRICT"),
        sa.UniqueConstraint("assessment_id", "occurrence_key", name="uq_xdi_occurrence_key"),
        sa.UniqueConstraint("assessment_id", "id", name="uq_xdi_occurrence_root"),
        sa.CheckConstraint("(commitment_id IS NULL)=(commitment_version IS NULL)", name="ck_xdi_occurrence_commitment"),
        _digest("occurrence_key"), _digest("occurrence_digest"),
    )
    op.create_table(
        "cross_discipline_occurrence_sources",
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("projection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id", "occurrence_id"], ["cross_discipline_interface_occurrences.assessment_id", "cross_discipline_interface_occurrences.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assessment_id", "projection_id"], ["cross_discipline_source_projections.assessment_id", "cross_discipline_source_projections.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("assessment_id", "occurrence_id", "projection_id"),
    )
    op.create_table(
        "cross_discipline_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_scope_columns(),
        sa.Column("occurrence_id", postgresql.UUID(as_uuid=True)),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.String(128), nullable=False),
        sa.Column("rule_version", sa.String(16), nullable=False),
        sa.Column("rule_digest", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("subcode", sa.String(128), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("recurrence_key", sa.String(64), nullable=False),
        sa.Column("affected_selector", sa.String(256), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        _scope_fk("fk_xdi_finding_root_scope"),
        sa.ForeignKeyConstraint(["assessment_id", "occurrence_id"], ["cross_discipline_interface_occurrences.assessment_id", "cross_discipline_interface_occurrences.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("assessment_id", "id", name="uq_xdi_finding_root"),
        sa.UniqueConstraint("assessment_id", "fingerprint", name="uq_xdi_finding_fingerprint"),
        sa.UniqueConstraint("assessment_id", "ordinal", name="uq_xdi_finding_ordinal"),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 255", name="ck_xdi_finding_ordinal"),
        sa.CheckConstraint("category IN ('missing','inconsistent','stale','disputed','unfulfilled_commitment','dependency','potential_change_impact','incomplete_handoff')", name="ck_xdi_finding_category"),
        sa.CheckConstraint("severity IN ('info','warning','major','critical')", name="ck_xdi_finding_severity"),
        *(_digest(name) for name in ("rule_digest", "fingerprint", "recurrence_key")),
    )
    op.create_index("ix_xdi_finding_order", "cross_discipline_findings", ["assessment_id", "ordinal"])
    op.create_index("ix_xdi_finding_recurrence", "cross_discipline_findings", ["recurrence_key"])
    for table, target, role_name in (
        ("cross_discipline_finding_sources", "cross_discipline_source_projections", "projection"),
        ("cross_discipline_finding_attestations", "cross_discipline_completeness_attestations", "attestation"),
    ):
        target_column = role_name + "_id"
        op.create_table(
            table,
            sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(target_column, postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("role", sa.String(64), nullable=False),
            sa.ForeignKeyConstraint(["assessment_id", "finding_id"], ["cross_discipline_findings.assessment_id", "cross_discipline_findings.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["assessment_id", target_column], [f"{target}.assessment_id", f"{target}.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("assessment_id", "finding_id", target_column, "role"),
        )
    op.create_table(
        "cross_discipline_finding_dispositions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_scope_columns(),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resulting_view_state", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_role", sa.String(32), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("expected_assessment_version", sa.Integer(), nullable=False),
        sa.Column("expected_view_version", sa.Integer(), nullable=False),
        sa.Column("resulting_view_version", sa.Integer(), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("causation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("disposition_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        _scope_fk("fk_xdi_disposition_root_scope"),
        sa.ForeignKeyConstraint(["assessment_id", "finding_id"], ["cross_discipline_findings.assessment_id", "cross_discipline_findings.id"], name="fk_xdi_disposition_finding_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("assessment_id", "id", name="uq_xdi_disposition_root"),
        sa.UniqueConstraint("assessment_id", "sequence", name="uq_xdi_disposition_sequence"),
        sa.UniqueConstraint("organization_id", "project_id", "actor_id", "idempotency_key", name="uq_xdi_disposition_idempotency"),
        sa.CheckConstraint("sequence>=1 AND resulting_view_version=expected_view_version+1", name="ck_xdi_disposition_versions"),
        sa.CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 4000", name="ck_xdi_disposition_rationale"),
        _digest("disposition_digest"),
    )
    op.create_index("ix_xdi_disposition_order", "cross_discipline_finding_dispositions", ["assessment_id", "finding_id", "sequence"])
    op.create_table(
        "cross_discipline_finding_current",
        *_scope_columns(),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("projection_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latest_disposition_id", postgresql.UUID(as_uuid=True)),
        sa.Column("latest_action", sa.String(64)),
        sa.Column("current_state", sa.String(64), nullable=False, server_default="open"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        _scope_fk("fk_xdi_current_root_scope"),
        sa.ForeignKeyConstraint(["assessment_id", "finding_id"], ["cross_discipline_findings.assessment_id", "cross_discipline_findings.id"], name="fk_xdi_current_finding_scope", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assessment_id", "latest_disposition_id"], ["cross_discipline_finding_dispositions.assessment_id", "cross_discipline_finding_dispositions.id"], name="fk_xdi_current_disposition_scope", ondelete="RESTRICT"),
        sa.CheckConstraint("projection_version>=0", name="ck_xdi_current_version"),
    )
    op.create_index("ix_xdi_current_category_state", "cross_discipline_finding_current", ["organization_id", "project_id", "current_state"])
    op.create_table(
        "cross_discipline_assessment_lineage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("predecessor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("successor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("scope_family_digest", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("replacement_operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id", "project_id", "predecessor_id"], ["cross_discipline_assessments.organization_id", "cross_discipline_assessments.project_id", "cross_discipline_assessments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id", "project_id", "successor_id"], ["cross_discipline_assessments.organization_id", "cross_discipline_assessments.project_id", "cross_discipline_assessments.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("predecessor_id<>successor_id", name="ck_xdi_lineage_not_self"),
        sa.CheckConstraint("kind IN ('reassessment_of','supersedes')", name="ck_xdi_lineage_kind"),
        sa.UniqueConstraint("kind", "predecessor_id", "replacement_operation_id", name="uq_xdi_lineage_operation"),
        _digest("scope_family_digest"),
    )
    op.create_index("ix_xdi_lineage_predecessor", "cross_discipline_assessment_lineage", ["organization_id", "project_id", "predecessor_id"])
    op.create_index("ix_xdi_lineage_successor", "cross_discipline_assessment_lineage", ["organization_id", "project_id", "successor_id"])
    op.create_index("uq_xdi_lineage_supersedes", "cross_discipline_assessment_lineage", ["predecessor_id"], unique=True, postgresql_where=sa.text("kind='supersedes'"))
    op.create_table(
        "cross_discipline_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.Column("response_json", postgresql.JSONB()),
        sa.Column("response_digest", sa.String(64)),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cross_discipline_assessments.id", ondelete="RESTRICT")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id", "organization_id"], ["projects.id", "projects.organization_id"], name="fk_xdi_idempotency_project_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "project_id", "actor_id", "operation", "idempotency_key", name="uq_xdi_idempotency_scope"),
        sa.CheckConstraint("(completed_at IS NULL AND response_digest IS NULL) OR (completed_at IS NOT NULL AND response_digest IS NOT NULL)", name="ck_xdi_idempotency_completion"),
        _digest("request_digest"),
    )
    op.create_table(
        "cross_discipline_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cross_discipline_assessments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", name="uq_xdi_outbox_event"),
    )
    op.create_index("ix_xdi_outbox_unpublished", "cross_discipline_outbox", ["published_at", "created_at"])

    op.execute("""
    CREATE FUNCTION satco_cross_discipline_immutable() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      RAISE EXCEPTION 'cross-discipline history is immutable' USING ERRCODE='23514';
    END $$;
    CREATE FUNCTION satco_cross_discipline_root_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'cross-discipline roots cannot be deleted' USING ERRCODE='23514'; END IF;
      IF to_jsonb(NEW)-'aggregate_version' IS DISTINCT FROM to_jsonb(OLD)-'aggregate_version'
         OR NEW.aggregate_version<>OLD.aggregate_version+1 THEN
        RAISE EXCEPTION 'cross-discipline root update is not a version increment' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE FUNCTION satco_cross_discipline_current_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'current projection cannot be deleted' USING ERRCODE='23514'; END IF;
      IF TG_OP='UPDATE' AND (
        NEW.organization_id IS DISTINCT FROM OLD.organization_id OR
        NEW.project_id IS DISTINCT FROM OLD.project_id OR
        NEW.assessment_id IS DISTINCT FROM OLD.assessment_id OR
        NEW.finding_id IS DISTINCT FROM OLD.finding_id OR
        NEW.projection_version<>OLD.projection_version+1
      ) THEN RAISE EXCEPTION 'invalid current projection update' USING ERRCODE='23514'; END IF;
      RETURN NEW;
    END $$;
    CREATE FUNCTION satco_cross_discipline_lineage_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF EXISTS (
        WITH RECURSIVE descendants(id,depth) AS (
          SELECT NEW.successor_id, 1
          UNION
          SELECT l.successor_id, d.depth+1 FROM public.cross_discipline_assessment_lineage l
          JOIN descendants d ON l.predecessor_id=d.id
          WHERE d.depth<33
        ) SELECT 1 FROM descendants WHERE id=NEW.predecessor_id OR depth>32
      ) THEN RAISE EXCEPTION 'cross-discipline lineage cycle' USING ERRCODE='23514'; END IF;
      RETURN NEW;
    END $$;
    CREATE FUNCTION satco_cross_discipline_scope_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE root_id uuid; root_status text; workspace_count integer; projection_count integer;
      attestation_count integer; occurrence_count integer; finding_count integer;
      disposition_count integer; finding_disposition_count integer;
    BEGIN
      root_id := COALESCE(
        (to_jsonb(NEW)->>'assessment_id')::uuid,
        (to_jsonb(NEW)->>'id')::uuid
      );
      SELECT status INTO root_status FROM public.cross_discipline_assessments WHERE id=root_id;
      SELECT count(*) INTO workspace_count FROM public.cross_discipline_assessment_workspaces WHERE assessment_id=root_id;
      SELECT count(*) INTO projection_count FROM public.cross_discipline_source_projections WHERE assessment_id=root_id;
      SELECT count(*) INTO attestation_count FROM public.cross_discipline_completeness_attestations WHERE assessment_id=root_id;
      SELECT count(*) INTO occurrence_count FROM public.cross_discipline_interface_occurrences WHERE assessment_id=root_id;
      SELECT count(*) INTO finding_count FROM public.cross_discipline_findings WHERE assessment_id=root_id;
      SELECT count(*) INTO disposition_count FROM public.cross_discipline_finding_dispositions WHERE assessment_id=root_id;
      SELECT COALESCE(max(n),0) INTO finding_disposition_count FROM (
        SELECT count(*) n FROM public.cross_discipline_finding_dispositions
        WHERE assessment_id=root_id GROUP BY finding_id
      ) counts;
      IF workspace_count NOT BETWEEN 1 AND 12 OR projection_count>256 OR attestation_count>128 OR occurrence_count>128 OR finding_count>256 OR disposition_count>4096 OR finding_disposition_count>64 THEN
        RAISE EXCEPTION 'cross-discipline resource/coherence limit' USING ERRCODE='23514';
      END IF;
      IF (root_status='completed_no_findings' AND finding_count<>0) OR (root_status IN ('indeterminate','unavailable') AND finding_count<>0) OR (root_status='completed_with_findings' AND finding_count=0) THEN
        RAISE EXCEPTION 'cross-discipline status/finding mismatch' USING ERRCODE='23514';
      END IF;
      IF (SELECT count(*) FROM public.cross_discipline_assessment_snapshots WHERE assessment_id=root_id)<>1 THEN
        RAISE EXCEPTION 'cross-discipline snapshot cardinality' USING ERRCODE='23514';
      END IF;
      RETURN NULL;
    END $$;
    """)
    immutable_tables = (
        "cross_discipline_assessment_snapshots", "cross_discipline_assessment_workspaces",
        "cross_discipline_source_projections", "cross_discipline_completeness_attestations",
        "cross_discipline_interface_occurrences", "cross_discipline_occurrence_sources",
        "cross_discipline_findings", "cross_discipline_finding_sources",
        "cross_discipline_finding_attestations", "cross_discipline_finding_dispositions",
        "cross_discipline_assessment_lineage",
    )
    for table in immutable_tables:
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION satco_cross_discipline_immutable()")
    op.execute("CREATE TRIGGER trg_xdi_root_guard BEFORE UPDATE OR DELETE ON cross_discipline_assessments FOR EACH ROW EXECUTE FUNCTION satco_cross_discipline_root_guard()")
    op.execute("CREATE TRIGGER trg_xdi_current_guard BEFORE UPDATE OR DELETE ON cross_discipline_finding_current FOR EACH ROW EXECUTE FUNCTION satco_cross_discipline_current_guard()")
    op.execute("CREATE TRIGGER trg_xdi_lineage_guard BEFORE INSERT ON cross_discipline_assessment_lineage FOR EACH ROW EXECUTE FUNCTION satco_cross_discipline_lineage_guard()")
    for table in ("cross_discipline_assessments", "cross_discipline_assessment_snapshots", "cross_discipline_assessment_workspaces", "cross_discipline_source_projections", "cross_discipline_completeness_attestations", "cross_discipline_interface_occurrences", "cross_discipline_findings", "cross_discipline_finding_dispositions"):
        op.execute(f"CREATE CONSTRAINT TRIGGER trg_{table}_scope AFTER INSERT ON {table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_cross_discipline_scope_guard()")
    op.execute("""
    REVOKE ALL ON FUNCTION satco_cross_discipline_immutable(), satco_cross_discipline_root_guard(),
      satco_cross_discipline_current_guard(), satco_cross_discipline_lineage_guard(),
      satco_cross_discipline_scope_guard() FROM PUBLIC;
    REVOKE ALL ON TABLE cross_discipline_assessments, cross_discipline_assessment_snapshots,
      cross_discipline_assessment_workspaces, cross_discipline_source_projections,
      cross_discipline_completeness_attestations, cross_discipline_interface_occurrences,
      cross_discipline_occurrence_sources, cross_discipline_findings,
      cross_discipline_finding_sources, cross_discipline_finding_attestations,
      cross_discipline_finding_dispositions, cross_discipline_finding_current,
      cross_discipline_assessment_lineage, cross_discipline_idempotency,
      cross_discipline_outbox FROM satco_runtime;
    GRANT SELECT,INSERT ON cross_discipline_assessments, cross_discipline_assessment_snapshots,
      cross_discipline_assessment_workspaces, cross_discipline_source_projections,
      cross_discipline_completeness_attestations, cross_discipline_interface_occurrences,
      cross_discipline_occurrence_sources, cross_discipline_findings,
      cross_discipline_finding_sources, cross_discipline_finding_attestations,
      cross_discipline_finding_dispositions, cross_discipline_assessment_lineage,
      cross_discipline_idempotency, cross_discipline_outbox TO satco_runtime;
    GRANT SELECT,INSERT,UPDATE(projection_version,latest_disposition_id,latest_action,current_state,updated_at)
      ON cross_discipline_finding_current TO satco_runtime;
    GRANT UPDATE(aggregate_version) ON cross_discipline_assessments TO satco_runtime;
    GRANT UPDATE(published_at) ON cross_discipline_outbox TO satco_runtime;
    """)


def downgrade():
    bind = op.get_bind()
    retained = bind.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM cross_discipline_assessments)"
    )).scalar()
    if retained:
        raise RuntimeError("PATCH-053 downgrade would discard retained assessments")
    tables = (
        "cross_discipline_outbox", "cross_discipline_idempotency",
        "cross_discipline_finding_current", "cross_discipline_finding_dispositions",
        "cross_discipline_finding_attestations", "cross_discipline_finding_sources",
        "cross_discipline_findings", "cross_discipline_occurrence_sources",
        "cross_discipline_interface_occurrences", "cross_discipline_completeness_attestations",
        "cross_discipline_source_projections", "cross_discipline_assessment_workspaces",
        "cross_discipline_assessment_snapshots", "cross_discipline_assessment_lineage",
        "cross_discipline_assessments",
    )
    for table in tables:
        op.drop_table(table)
    for function in (
        "satco_cross_discipline_scope_guard", "satco_cross_discipline_lineage_guard",
        "satco_cross_discipline_current_guard", "satco_cross_discipline_root_guard",
        "satco_cross_discipline_immutable",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}()")
