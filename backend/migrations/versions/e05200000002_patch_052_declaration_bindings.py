"""PATCH-052 immutable Context/Evidence declaration bindings.

Revision ID: e05200000002
Revises: e05200000001

The correction is additive and creates no binding rows. Legacy/general
Context and Evidence remain explicitly unbound.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e05200000002"
down_revision = "e05200000001"
branch_labels = None
depends_on = None


def _binding_columns(source_name: str, source_type, version_name: str):
    return (
        sa.Column(source_name, source_type, nullable=False),
        sa.Column(version_name, sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("project_configuration_revision", sa.BigInteger(), nullable=False),
        sa.Column("package_key", sa.String(64), nullable=False),
        sa.Column("input_declaration_id", sa.String(128), nullable=False),
        sa.Column("bound_by_id", sa.Integer(), nullable=False),
        sa.Column("bound_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    connection = op.get_bind()
    current = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    if current != down_revision:
        raise RuntimeError("PATCH-052 binding correction requires exact predecessor e05200000001")
    required = {
        "engineering_contexts", "engineering_context_subject_references", "evidence",
        "project_package_configuration_revisions",
        "project_package_configuration_selections", "users",
    }
    present = set(connection.execute(sa.text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema=current_schema()"
    )).scalars())
    if not required <= present or {
        "engineering_context_package_input_bindings", "evidence_package_input_bindings",
    } & present:
        raise RuntimeError("PATCH-052 binding predecessor schema is not exact")

    op.drop_constraint(
        "ck_engineering_context_subject_refs_kind",
        "engineering_context_subject_references",
        type_="check",
    )
    op.create_check_constraint(
        "ck_engineering_context_subject_refs_kind",
        "engineering_context_subject_references",
        "subject_kind IN ('project','workspace','discipline','engineering_object')",
    )

    op.create_table(
        "engineering_context_package_input_bindings",
        *_binding_columns("context_subject_reference_id", sa.Integer(), "context_version"),
        sa.PrimaryKeyConstraint(
            "context_subject_reference_id", "context_version", "project_id",
            "project_configuration_revision", "package_key", "input_declaration_id",
            name="pk_engineering_context_package_input_bindings",
        ),
        sa.ForeignKeyConstraint(
            ["context_subject_reference_id"], ["engineering_context_subject_references.id"],
            name="fk_context_input_binding_subject", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "project_configuration_revision", "package_key"],
            ["project_package_configuration_selections.project_id",
             "project_package_configuration_selections.configuration_revision",
             "project_package_configuration_selections.package_key"],
            name="fk_context_input_binding_selection", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["bound_by_id"], ["users.id"], name="fk_context_input_binding_actor",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "context_version >= 1 AND project_configuration_revision >= 1 "
            "AND char_length(package_key) BETWEEN 1 AND 64 "
            "AND input_declaration_id ~ '^[a-z][a-z0-9_.-]*$'",
            name="ck_context_input_binding_values",
        ),
    )
    op.create_index(
        "ix_context_input_binding_readiness",
        "engineering_context_package_input_bindings",
        ["project_id", "project_configuration_revision", "package_key",
         "input_declaration_id", "context_subject_reference_id", "context_version"],
    )

    op.create_table(
        "evidence_package_input_bindings",
        *_binding_columns("evidence_id", postgresql.UUID(as_uuid=True), "evidence_version"),
        sa.PrimaryKeyConstraint(
            "evidence_id", "evidence_version", "project_id",
            "project_configuration_revision", "package_key", "input_declaration_id",
            name="pk_evidence_package_input_bindings",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["evidence.id"], name="fk_evidence_input_binding_evidence",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "project_configuration_revision", "package_key"],
            ["project_package_configuration_selections.project_id",
             "project_package_configuration_selections.configuration_revision",
             "project_package_configuration_selections.package_key"],
            name="fk_evidence_input_binding_selection", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["bound_by_id"], ["users.id"], name="fk_evidence_input_binding_actor",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "evidence_version >= 1 AND project_configuration_revision >= 1 "
            "AND char_length(package_key) BETWEEN 1 AND 64 "
            "AND input_declaration_id ~ '^[a-z][a-z0-9_.-]*$'",
            name="ck_evidence_input_binding_values",
        ),
    )
    op.create_index(
        "ix_evidence_input_binding_readiness", "evidence_package_input_bindings",
        ["project_id", "project_configuration_revision", "package_key",
         "input_declaration_id", "evidence_id", "evidence_version"],
    )

    op.execute("""
    CREATE FUNCTION satco_patch052_binding_coherent() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE source_project integer; source_workspace integer; workspace_project integer;
            source_org uuid;
            source_version integer; revision_org uuid; subject_kind text;
            subject_workspace integer; object_workspace integer;
    BEGIN
      SELECT r.organization_id INTO revision_org
        FROM project_package_configuration_revisions r
       WHERE r.project_id=NEW.project_id
         AND r.configuration_revision=NEW.project_configuration_revision;
      IF TG_TABLE_NAME='engineering_context_package_input_bindings' THEN
        SELECT c.project_id,c.workspace_id,p.organization_id,c.version,
               s.subject_kind,s.subject_workspace_id,o.workspace_id
          INTO source_project,source_workspace,source_org,source_version,
               subject_kind,subject_workspace,object_workspace
          FROM engineering_context_subject_references s
          JOIN engineering_contexts c ON c.id=s.context_id
          JOIN projects p ON p.id=c.project_id
          LEFT JOIN engineering_objects o ON o.id=s.subject_engineering_object_id
         WHERE s.id=NEW.context_subject_reference_id;
        IF source_project IS DISTINCT FROM NEW.project_id
           OR source_org IS DISTINCT FROM revision_org
           OR source_version IS DISTINCT FROM NEW.context_version
           OR subject_kind NOT IN ('workspace','engineering_object')
           OR (subject_kind='workspace' AND subject_workspace IS DISTINCT FROM source_workspace)
           OR (subject_kind='engineering_object' AND object_workspace IS DISTINCT FROM source_workspace)
        THEN RAISE EXCEPTION 'Context input binding is incoherent' USING ERRCODE='23514'; END IF;
      ELSIF TG_TABLE_NAME='evidence_package_input_bindings' THEN
        SELECT e.project_id,e.workspace_id,e.organization_id,e.version
          INTO source_project,source_workspace,source_org,source_version
          FROM evidence e WHERE e.id=NEW.evidence_id;
        IF source_project IS NULL OR source_project IS DISTINCT FROM NEW.project_id
           OR source_org IS DISTINCT FROM revision_org
           OR source_version IS DISTINCT FROM NEW.evidence_version
        THEN RAISE EXCEPTION 'Evidence input binding is incoherent' USING ERRCODE='23514'; END IF;
      ELSE RAISE EXCEPTION 'Unsupported binding table' USING ERRCODE='23514';
      END IF;
      IF source_workspace IS NOT NULL THEN
        SELECT w.project_id INTO workspace_project
          FROM engineering_workspaces w WHERE w.id=source_workspace;
        IF workspace_project IS DISTINCT FROM source_project
        THEN RAISE EXCEPTION 'Binding Workspace is incoherent' USING ERRCODE='23514'; END IF;
      END IF;
      RETURN NEW;
    END $$
    """)
    op.execute("""
    CREATE FUNCTION satco_patch052_binding_immutable() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      RAISE EXCEPTION 'Package input bindings are immutable' USING ERRCODE='23514';
    END $$
    """)
    for table in (
        "engineering_context_package_input_bindings", "evidence_package_input_bindings",
    ):
        op.execute(f"CREATE TRIGGER trg_{table}_coherent BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION satco_patch052_binding_coherent()")
        op.execute(f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION satco_patch052_binding_immutable()")

    op.execute("REVOKE ALL ON FUNCTION satco_patch052_binding_coherent() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION satco_patch052_binding_immutable() FROM PUBLIC")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        GRANT SELECT,INSERT ON engineering_context_package_input_bindings TO satco_runtime;
        GRANT SELECT,INSERT ON evidence_package_input_bindings TO satco_runtime;
        REVOKE UPDATE,DELETE,TRUNCATE ON engineering_context_package_input_bindings FROM satco_runtime;
        REVOKE UPDATE,DELETE,TRUNCATE ON evidence_package_input_bindings FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION satco_patch052_binding_coherent() FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION satco_patch052_binding_immutable() FROM satco_runtime;
      END IF;
    END $$
    """)
    counts = connection.execute(sa.text(
        "SELECT (SELECT count(*) FROM engineering_context_package_input_bindings),"
        "       (SELECT count(*) FROM evidence_package_input_bindings)"
    )).one()
    if tuple(counts) != (0, 0):
        raise RuntimeError("PATCH-052 binding migration must not fabricate rows")


def downgrade() -> None:
    connection = op.get_bind()
    has_object_subjects = connection.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM engineering_context_subject_references "
        "WHERE subject_kind='engineering_object')"
    )).scalar_one()
    if has_object_subjects:
        raise RuntimeError(
            "PATCH-052 binding downgrade is prohibited while engineering_object "
            "Context subjects exist"
        )
    has_rows = connection.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM engineering_context_package_input_bindings) "
        "OR EXISTS(SELECT 1 FROM evidence_package_input_bindings)"
    )).scalar_one()
    if has_rows:
        raise RuntimeError("PATCH-052 binding downgrade is prohibited while bindings exist")
    for table in (
        "evidence_package_input_bindings", "engineering_context_package_input_bindings",
    ):
        op.execute(f"DROP TRIGGER trg_{table}_immutable ON {table}")
        op.execute(f"DROP TRIGGER trg_{table}_coherent ON {table}")
    op.execute("DROP FUNCTION satco_patch052_binding_immutable()")
    op.execute("DROP FUNCTION satco_patch052_binding_coherent()")
    op.drop_index("ix_evidence_input_binding_readiness", table_name="evidence_package_input_bindings")
    op.drop_table("evidence_package_input_bindings")
    op.drop_index("ix_context_input_binding_readiness", table_name="engineering_context_package_input_bindings")
    op.drop_table("engineering_context_package_input_bindings")
    op.drop_constraint(
        "ck_engineering_context_subject_refs_kind",
        "engineering_context_subject_references",
        type_="check",
    )
    op.create_check_constraint(
        "ck_engineering_context_subject_refs_kind",
        "engineering_context_subject_references",
        "subject_kind IN ('project','workspace','discipline')",
    )
