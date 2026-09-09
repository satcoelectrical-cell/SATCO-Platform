"""PATCH-052 shared operational schema and Electrical V1 cutover.

Revision ID: e05200000001
Revises: e05100000006

The cutover is additive.  Existing owner rows retain NULL package origin and
no Engineering Identifier is inferred or backfilled.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e05200000001"
down_revision = "e05100000006"
branch_labels = None
depends_on = None


_ORIGIN_TABLES = (
    "engineering_objects",
    "engineering_relationships",
    "engineering_experience_captures",
    "engineering_deliverables",
)


def _add_origin(table: str, check_name: str, fk_name: str) -> None:
    op.add_column(table, sa.Column("origin_package_key", sa.String(64), nullable=True))
    op.add_column(
        table,
        sa.Column("origin_project_configuration_revision", sa.BigInteger(), nullable=True),
    )
    op.add_column(table, sa.Column("origin_declaration_id", sa.String(128), nullable=True))
    op.create_check_constraint(
        check_name,
        table,
        "(origin_package_key IS NULL AND origin_project_configuration_revision IS NULL "
        "AND origin_declaration_id IS NULL) OR "
        "(origin_package_key IS NOT NULL AND origin_project_configuration_revision IS NOT NULL "
        "AND origin_project_configuration_revision >= 1 AND origin_declaration_id IS NOT NULL "
        "AND char_length(origin_declaration_id) BETWEEN 1 AND 128)",
    )
    op.create_foreign_key(
        fk_name,
        table,
        "project_package_configuration_selections",
        ["project_id", "origin_project_configuration_revision", "origin_package_key"],
        ["project_id", "configuration_revision", "package_key"],
        ondelete="RESTRICT",
    )
    op.create_index(
        f"ix_{table}_origin",
        table,
        ["project_id", "origin_project_configuration_revision", "origin_package_key"],
        postgresql_where=sa.text("origin_package_key IS NOT NULL"),
    )


def upgrade() -> None:
    connection = op.get_bind()
    current = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()
    if current != down_revision:
        raise RuntimeError("PATCH-052 requires exact predecessor e05100000006")

    # No data rewrite: these checks prove the source shapes before mutation.
    expected_tables = set(_ORIGIN_TABLES) | {
        "engineering_context_subject_references",
        "project_package_configuration_selections",
        "technical_report_provenance_entries",
    }
    present = set(connection.execute(sa.text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema=current_schema()"
    )).scalars())
    if not expected_tables.issubset(present):
        raise RuntimeError("PATCH-052 predecessor schema is incomplete")

    for table, check_name, fk_name in (
        ("engineering_objects", "ck_engineering_objects_origin_all_or_none", "fk_engineering_objects_origin_selection"),
        ("engineering_relationships", "ck_engineering_relationships_origin_all_or_none", "fk_engineering_relationships_origin_selection"),
        ("engineering_experience_captures", "ck_experience_captures_origin_all_or_none", "fk_experience_captures_origin_selection"),
        ("engineering_deliverables", "ck_deliverable_origin_all_or_none", "fk_deliverable_origin_selection"),
    ):
        _add_origin(table, check_name, fk_name)

    # Only the two accepted Electrical values are added to the closed checks.
    op.drop_constraint("ck_engineering_objects_object_type", "engineering_objects", type_="check")
    op.create_check_constraint(
        "ck_engineering_objects_object_type",
        "engineering_objects",
        "object_type IN ('instrument','transmitter','analyzer','flowmeter','control_valve',"
        "'instrument_loop','junction_box','instrument_panel','motor','transformer','mcc',"
        "'switchgear','electrical_panel','electrical_cable','electrical_feeder',"
        "'electrical_power_source','plc','dcs_controller','esd_controller','control_cabinet',"
        "'io_channel','hmi','control_logic','project','vendor','requirement','standard',"
        "'datasheet','drawing','technical_decision')",
    )
    op.drop_constraint("ck_engineering_objects_family_object_type", "engineering_objects", type_="check")
    op.create_check_constraint(
        "ck_engineering_objects_family_object_type",
        "engineering_objects",
        "(family='instrumentation' AND object_type IN ('instrument','transmitter','analyzer',"
        "'flowmeter','control_valve','instrument_loop','junction_box','instrument_panel')) OR "
        "(family='electrical' AND object_type IN ('motor','transformer','mcc','switchgear',"
        "'electrical_panel','electrical_cable','electrical_feeder','electrical_power_source')) OR "
        "(family='automation' AND object_type IN ('plc','dcs_controller','esd_controller',"
        "'control_cabinet','io_channel','hmi','control_logic')) OR "
        "(family='shared' AND object_type IN ('project','vendor','requirement','standard',"
        "'datasheet','drawing','technical_decision'))",
    )

    op.add_column(
        "engineering_context_subject_references",
        sa.Column("subject_engineering_object_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_engineering_context_subject_refs_object",
        "engineering_context_subject_references",
        "engineering_objects",
        ["subject_engineering_object_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "ck_engineering_context_subject_refs_target",
        "engineering_context_subject_references",
        type_="check",
    )
    op.create_check_constraint(
        "ck_engineering_context_subject_refs_target",
        "engineering_context_subject_references",
        "(subject_kind='project' AND subject_project_id IS NOT NULL AND subject_workspace_id IS NULL "
        "AND discipline IS NULL AND subject_engineering_object_id IS NULL) OR "
        "(subject_kind='workspace' AND subject_project_id IS NULL AND subject_workspace_id IS NOT NULL "
        "AND discipline IS NULL AND subject_engineering_object_id IS NULL) OR "
        "(subject_kind='discipline' AND subject_project_id IS NULL AND subject_workspace_id IS NULL "
        "AND discipline IS NOT NULL AND subject_engineering_object_id IS NULL) OR "
        "(subject_kind='engineering_object' AND subject_project_id IS NULL AND subject_workspace_id IS NULL "
        "AND discipline IS NULL AND subject_engineering_object_id IS NOT NULL)",
    )
    op.create_index(
        "uq_engineering_context_subject_refs_object_identity",
        "engineering_context_subject_references",
        ["context_id", "subject_engineering_object_id"],
        unique=True,
        postgresql_where=sa.text("subject_kind='engineering_object'"),
    )
    op.create_index(
        "ix_engineering_context_subject_refs_object_id",
        "engineering_context_subject_references",
        ["subject_engineering_object_id"],
    )

    op.create_table(
        "engineering_identifiers",
        sa.Column("identifier_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("engineering_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("identifier_kind", sa.String(64), nullable=False),
        sa.Column("display_value", sa.String(128), nullable=False),
        sa.Column("normalized_value", sa.String(128), nullable=False),
        sa.Column("normalization_algorithm_version", sa.String(64), nullable=False),
        sa.Column("issuing_scope_kind", sa.String(32), nullable=False),
        sa.Column("issuing_scope_value", sa.String(128), nullable=False),
        sa.Column("lifecycle", sa.String(16), server_default="current", nullable=False),
        sa.Column("authority_standing", sa.String(16), server_default="draft", nullable=False),
        sa.Column("primary_role", sa.String(16), server_default="alternate", nullable=False),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("predecessor_identifier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("successor_identifier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("steward_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("origin_package_key", sa.String(64), nullable=True),
        sa.Column("origin_project_configuration_revision", sa.BigInteger(), nullable=True),
        sa.Column("origin_declaration_id", sa.String(128), nullable=True),
        sa.ForeignKeyConstraint(["engineering_object_id"], ["engineering_objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["engineering_workspaces.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["steward_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["predecessor_identifier_id"], ["engineering_identifiers.identifier_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["successor_identifier_id"], ["engineering_identifiers.identifier_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["project_id", "origin_project_configuration_revision", "origin_package_key"],
            ["project_package_configuration_selections.project_id", "project_package_configuration_selections.configuration_revision", "project_package_configuration_selections.package_key"],
            name="fk_engineering_identifier_origin_selection",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("identifier_kind IN ('tag_number','equipment_number','loop_number','cable_number','panel_number','feeder_number','system_identifier','subsystem_identifier','vendor_reference','manufacturer_model_reference','controlled_external_key')", name="ck_engineering_identifier_kind"),
        sa.CheckConstraint("char_length(display_value) BETWEEN 1 AND 128", name="ck_engineering_identifier_display"),
        sa.CheckConstraint("char_length(normalized_value) BETWEEN 1 AND 128", name="ck_engineering_identifier_normalized"),
        sa.CheckConstraint("normalization_algorithm_version='satco_identifier_nfkc_casefold_v1'", name="ck_engineering_identifier_normalizer"),
        sa.CheckConstraint("issuing_scope_kind IN ('project','workspace','external_authority')", name="ck_engineering_identifier_scope_kind"),
        sa.CheckConstraint("char_length(issuing_scope_value) BETWEEN 1 AND 128", name="ck_engineering_identifier_scope_value"),
        sa.CheckConstraint("lifecycle IN ('current','superseded','withdrawn')", name="ck_engineering_identifier_lifecycle"),
        sa.CheckConstraint("authority_standing IN ('draft','proposed','reviewed','approved','disputed','rejected')", name="ck_engineering_identifier_authority"),
        sa.CheckConstraint("primary_role IN ('primary','alternate')", name="ck_engineering_identifier_primary_role"),
        sa.CheckConstraint("version >= 1 AND updated_at >= created_at", name="ck_engineering_identifier_version_time"),
        sa.CheckConstraint("predecessor_identifier_id IS NULL OR predecessor_identifier_id<>identifier_id", name="ck_engineering_identifier_predecessor_self"),
        sa.CheckConstraint("successor_identifier_id IS NULL OR successor_identifier_id<>identifier_id", name="ck_engineering_identifier_successor_self"),
        sa.CheckConstraint("jsonb_typeof(evidence_references)='array' AND jsonb_array_length(evidence_references)<=8", name="ck_engineering_identifier_evidence_shape"),
        sa.CheckConstraint("(origin_package_key IS NULL AND origin_project_configuration_revision IS NULL AND origin_declaration_id IS NULL) OR (origin_package_key IS NOT NULL AND origin_project_configuration_revision>=1 AND origin_declaration_id IS NOT NULL AND char_length(origin_declaration_id) BETWEEN 1 AND 128)", name="ck_engineering_identifier_origin_all_or_none"),
        sa.UniqueConstraint("predecessor_identifier_id", name="uq_engineering_identifier_predecessor"),
        sa.UniqueConstraint("successor_identifier_id", name="uq_engineering_identifier_successor"),
    )
    op.create_index("uq_engineering_identifier_current_value", "engineering_identifiers", ["organization_id", "project_id", "issuing_scope_kind", "issuing_scope_value", "identifier_kind", "normalized_value"], unique=True, postgresql_where=sa.text("lifecycle='current'"))
    op.create_index("uq_engineering_identifier_current_primary", "engineering_identifiers", ["engineering_object_id"], unique=True, postgresql_where=sa.text("lifecycle='current' AND primary_role='primary'"))
    op.create_index("ix_engineering_identifier_current_set", "engineering_identifiers", ["engineering_object_id", "lifecycle", "primary_role"])
    op.create_index("ix_engineering_identifier_scope_history", "engineering_identifiers", ["organization_id", "project_id", "workspace_id", sa.text("created_at DESC"), sa.text("identifier_id DESC")])
    op.create_index("ix_engineering_identifier_origin", "engineering_identifiers", ["project_id", "origin_project_configuration_revision", "origin_package_key"], postgresql_where=sa.text("origin_package_key IS NOT NULL"))

    op.create_table(
        "engineering_identifier_idempotency",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("identifier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["identifier_id"], ["engineering_identifiers.identifier_id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("organization_id", "actor_id", "operation", "idempotency_key"),
    )
    op.create_table(
        "engineering_identifier_outbox",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("identifier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["identifier_id"], ["engineering_identifiers.identifier_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("identifier_id", "aggregate_version", name="uq_engineering_identifier_outbox_version"),
    )
    op.create_index("ix_engineering_identifier_outbox_unpublished", "engineering_identifier_outbox", ["occurred_at", "event_id"], postgresql_where=sa.text("published_at IS NULL"))

    op.execute("""
    CREATE FUNCTION satco_patch052_origin_immutable() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF ROW(OLD.origin_package_key,OLD.origin_project_configuration_revision,OLD.origin_declaration_id)
         IS DISTINCT FROM ROW(NEW.origin_package_key,NEW.origin_project_configuration_revision,NEW.origin_declaration_id) THEN
        RAISE EXCEPTION 'package origin is immutable' USING ERRCODE='55000';
      END IF;
      IF TG_TABLE_NAME='engineering_objects' AND OLD.origin_package_key IS NOT NULL
         AND (to_jsonb(OLD)->'family' IS DISTINCT FROM to_jsonb(NEW)->'family'
          OR to_jsonb(OLD)->'discipline' IS DISTINCT FROM to_jsonb(NEW)->'discipline'
          OR to_jsonb(OLD)->'object_type' IS DISTINCT FROM to_jsonb(NEW)->'object_type') THEN
        RAISE EXCEPTION 'package-origin Object classification is immutable' USING ERRCODE='55000';
      END IF;
      IF TG_TABLE_NAME='engineering_deliverables' AND OLD.origin_package_key IS NOT NULL
         AND (to_jsonb(OLD)->'discipline' IS DISTINCT FROM to_jsonb(NEW)->'discipline'
          OR to_jsonb(OLD)->'deliverable_type' IS DISTINCT FROM to_jsonb(NEW)->'deliverable_type') THEN
        RAISE EXCEPTION 'package-origin Deliverable classification is immutable' USING ERRCODE='55000';
      END IF;
      RETURN NEW;
    END $$
    """)
    for table in (*_ORIGIN_TABLES, "engineering_identifiers"):
        op.execute(f"CREATE TRIGGER trg_{table}_origin_immutable BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION satco_patch052_origin_immutable()")

    op.execute("""
    CREATE FUNCTION satco_patch052_identifier_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE obj record; predecessor record; evidence_value jsonb; visited uuid[]:=ARRAY[]::uuid[]; cursor_id uuid;
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Engineering Identifiers cannot be physically deleted' USING ERRCODE='55000'; END IF;
      SELECT organization_id,project_id,workspace_id INTO obj FROM public.engineering_objects WHERE id=NEW.engineering_object_id;
      IF NOT FOUND OR ROW(obj.organization_id,obj.project_id,obj.workspace_id) IS DISTINCT FROM ROW(NEW.organization_id,NEW.project_id,NEW.workspace_id) THEN
        RAISE EXCEPTION 'Identifier Object scope is incoherent' USING ERRCODE='23514';
      END IF;
      IF TG_OP='UPDATE' AND ROW(OLD.engineering_object_id,OLD.organization_id,OLD.project_id,OLD.workspace_id,OLD.identifier_kind,OLD.display_value,OLD.normalized_value,OLD.normalization_algorithm_version,OLD.issuing_scope_kind,OLD.issuing_scope_value,OLD.creator_id,OLD.created_at)
         IS DISTINCT FROM ROW(NEW.engineering_object_id,NEW.organization_id,NEW.project_id,NEW.workspace_id,NEW.identifier_kind,NEW.display_value,NEW.normalized_value,NEW.normalization_algorithm_version,NEW.issuing_scope_kind,NEW.issuing_scope_value,NEW.creator_id,NEW.created_at) THEN
        RAISE EXCEPTION 'immutable Identifier field changed' USING ERRCODE='55000';
      END IF;
      FOR evidence_value IN SELECT value FROM jsonb_array_elements(NEW.evidence_references) LOOP
        IF jsonb_typeof(evidence_value)<>'string' OR NOT EXISTS (
          SELECT 1 FROM public.evidence e WHERE e.id=(trim(both '"' from evidence_value::text))::uuid
          AND e.organization_id=NEW.organization_id
          AND (e.project_id IS NULL OR e.project_id=NEW.project_id)
          AND (e.workspace_id IS NULL OR e.workspace_id=NEW.workspace_id)
        ) THEN RAISE EXCEPTION 'Identifier Evidence scope is invalid' USING ERRCODE='23514'; END IF;
      END LOOP;
      IF (SELECT count(*) FROM jsonb_array_elements_text(NEW.evidence_references))<>(SELECT count(DISTINCT value) FROM jsonb_array_elements_text(NEW.evidence_references) value)
         OR NEW.evidence_references<>(SELECT COALESCE(jsonb_agg(value ORDER BY value),'[]'::jsonb) FROM jsonb_array_elements_text(NEW.evidence_references) value) THEN
        RAISE EXCEPTION 'Identifier Evidence references must be unique and ordered' USING ERRCODE='23514';
      END IF;
      IF NEW.predecessor_identifier_id IS NOT NULL THEN
        SELECT * INTO predecessor FROM public.engineering_identifiers WHERE identifier_id=NEW.predecessor_identifier_id;
        IF NOT FOUND OR ROW(predecessor.engineering_object_id,predecessor.organization_id,predecessor.project_id,predecessor.workspace_id,predecessor.issuing_scope_kind,predecessor.issuing_scope_value)
           IS DISTINCT FROM ROW(NEW.engineering_object_id,NEW.organization_id,NEW.project_id,NEW.workspace_id,NEW.issuing_scope_kind,NEW.issuing_scope_value) THEN
          RAISE EXCEPTION 'Identifier lineage scope is invalid' USING ERRCODE='23514';
        END IF;
        cursor_id:=NEW.predecessor_identifier_id;
        WHILE cursor_id IS NOT NULL LOOP
          IF cursor_id=NEW.identifier_id OR cursor_id=ANY(visited) THEN RAISE EXCEPTION 'Identifier lineage cycle' USING ERRCODE='23514'; END IF;
          visited:=array_append(visited,cursor_id);
          SELECT predecessor_identifier_id INTO cursor_id FROM public.engineering_identifiers WHERE identifier_id=cursor_id;
        END LOOP;
      END IF;
      RETURN NEW;
    END $$
    """)
    op.execute("CREATE TRIGGER trg_engineering_identifier_guard BEFORE INSERT OR UPDATE OR DELETE ON engineering_identifiers FOR EACH ROW EXECUTE FUNCTION satco_patch052_identifier_guard()")

    op.execute("""
    CREATE FUNCTION satco_patch052_identifier_cardinality() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE object_id uuid:=COALESCE(
      (to_jsonb(NEW)->>'engineering_object_id')::uuid,
      (to_jsonb(OLD)->>'engineering_object_id')::uuid,
      (to_jsonb(NEW)->>'id')::uuid,
      (to_jsonb(OLD)->>'id')::uuid
    ); current_count integer; primary_count integer; package_origin text;
    BEGIN
      SELECT count(*),count(*) FILTER (WHERE primary_role='primary') INTO current_count,primary_count
      FROM public.engineering_identifiers WHERE engineering_object_id=object_id AND lifecycle='current';
      SELECT origin_package_key INTO package_origin FROM public.engineering_objects WHERE id=object_id;
      IF current_count>16 OR primary_count>1 OR (package_origin IS NOT NULL AND primary_count<>1) THEN
        RAISE EXCEPTION 'Identifier cardinality is invalid' USING ERRCODE='23514';
      END IF;
      RETURN NULL;
    END $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER trg_engineering_identifier_cardinality AFTER INSERT OR UPDATE ON engineering_identifiers DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_patch052_identifier_cardinality()")
    op.execute("CREATE CONSTRAINT TRIGGER trg_engineering_object_identifier_cardinality AFTER INSERT OR UPDATE ON engineering_objects DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_patch052_identifier_cardinality()")

    op.execute("""
    CREATE FUNCTION satco_patch052_context_object_coherence() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF NEW.subject_kind='engineering_object' AND NOT EXISTS (
        SELECT 1 FROM public.engineering_contexts c JOIN public.engineering_objects o ON o.id=NEW.subject_engineering_object_id
        WHERE c.id=NEW.context_id AND c.project_id=o.project_id AND c.workspace_id=o.workspace_id
      ) THEN RAISE EXCEPTION 'Context Object subject scope is incoherent' USING ERRCODE='23514'; END IF;
      RETURN NEW;
    END $$
    """)
    op.execute("CREATE TRIGGER trg_context_object_coherence BEFORE INSERT OR UPDATE ON engineering_context_subject_references FOR EACH ROW EXECUTE FUNCTION satco_patch052_context_object_coherence()")

    # Retain the accepted V1 function under a stable private name, then install
    # a closed V1/V2 dispatcher.  This preserves all V1 semantics byte-for-byte.
    op.execute("ALTER FUNCTION technical_report_historical_basis_valid(text,jsonb) RENAME TO technical_report_historical_basis_v1_valid")
    op.execute("""
    CREATE FUNCTION technical_report_historical_basis_v2_valid(source_type text,basis jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE keys text[]; uuid_pattern text:='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'; item jsonb;
    BEGIN
      IF jsonb_typeof(basis)<>'object' OR basis->>'basis_schema_version'<>'2' THEN RETURN false; END IF;
      IF source_type='universal_capture' THEN
        keys:=ARRAY['basis_schema_version','source_category','capture_id','source_version','organization_id','project_id','workspace_id','origin_package_key','origin_project_configuration_revision','origin_declaration_id','discipline','engineering_object_id','source_kind','original_content','source_reference','creator_id','lifecycle','created_at'];
      ELSIF source_type='engineering_object' THEN
        keys:=ARRAY['basis_schema_version','source_category','engineering_object_id','source_version','organization_id','customer_id','project_id','workspace_id','origin_package_key','origin_project_configuration_revision','origin_declaration_id','identifiers','family','discipline','object_type','subtype','lifecycle','authority_standing','creator_id','steward_id'];
      ELSIF source_type='engineering_relationship' THEN
        keys:=ARRAY['basis_schema_version','source_category','engineering_relationship_id','source_version','organization_id','project_id','workspace_id','origin_package_key','origin_project_configuration_revision','origin_declaration_id','source_object_id','target_object_id','relationship_family','relationship_type','lifecycle','authority_standing','evidence_references','creator_id','steward_id','reviewer_id','approver_id'];
      ELSE RETURN false; END IF;
      IF NOT basis ?& keys OR (SELECT count(*) FROM jsonb_object_keys(basis))<>cardinality(keys)
         OR basis->>'source_category'<>source_type
         OR basis->>'organization_id'!~uuid_pattern
         OR jsonb_typeof(basis->'project_id')<>'number' OR (basis->>'project_id')::numeric<1
         OR jsonb_typeof(basis->'origin_project_configuration_revision')<>'number' OR (basis->>'origin_project_configuration_revision')::numeric<1
         OR jsonb_typeof(basis->'origin_package_key')<>'string' OR length(basis->>'origin_package_key') NOT BETWEEN 1 AND 64
         OR jsonb_typeof(basis->'origin_declaration_id')<>'string' OR length(basis->>'origin_declaration_id') NOT BETWEEN 1 AND 128 THEN RETURN false; END IF;
      IF source_type='engineering_object' THEN
        IF basis->>'engineering_object_id'!~uuid_pattern OR jsonb_typeof(basis->'identifiers')<>'array' OR jsonb_array_length(basis->'identifiers') NOT BETWEEN 1 AND 16
           OR (SELECT count(*) FROM jsonb_array_elements(basis->'identifiers') x WHERE x->>'primary_role'='primary')<>1 THEN RETURN false; END IF;
        FOR item IN SELECT value FROM jsonb_array_elements(basis->'identifiers') LOOP
          keys:=ARRAY['identifier_id','identifier_version','identifier_kind','display_value','normalized_value','normalization_algorithm_version','issuing_scope_kind','issuing_scope_value','lifecycle','authority_standing','primary_role','evidence_references','predecessor_identifier_id','successor_identifier_id','creator_id','steward_id','reviewer_id','approver_id','created_at','updated_at','origin_package_key','origin_project_configuration_revision','origin_declaration_id'];
          IF jsonb_typeof(item)<>'object' OR NOT item ?& keys OR (SELECT count(*) FROM jsonb_object_keys(item))<>cardinality(keys)
             OR item->>'identifier_id'!~uuid_pattern OR item->>'lifecycle'<>'current' OR jsonb_typeof(item->'successor_identifier_id')<>'null'
             OR item->>'normalization_algorithm_version'<>'satco_identifier_nfkc_casefold_v1' THEN RETURN false; END IF;
        END LOOP;
      END IF;
      RETURN true;
    EXCEPTION WHEN others THEN RETURN false;
    END $$
    """)
    op.execute("""
    CREATE FUNCTION technical_report_historical_basis_valid(source_type text,basis jsonb) RETURNS boolean
    LANGUAGE sql IMMUTABLE STRICT SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      SELECT CASE basis->>'basis_schema_version'
        WHEN '1' THEN technical_report_historical_basis_v1_valid(source_type,basis)
        WHEN '2' THEN technical_report_historical_basis_v2_valid(source_type,basis)
        ELSE false END
    $$
    """)

    op.execute("REVOKE ALL ON FUNCTION satco_patch052_origin_immutable() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION satco_patch052_identifier_guard() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION satco_patch052_identifier_cardinality() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION satco_patch052_context_object_coherence() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_historical_basis_v1_valid(text,jsonb) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_historical_basis_v2_valid(text,jsonb) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM PUBLIC")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        GRANT SELECT,INSERT,UPDATE ON engineering_identifiers TO satco_runtime;
        GRANT SELECT,INSERT,UPDATE ON engineering_identifier_idempotency TO satco_runtime;
        GRANT SELECT,INSERT ON engineering_identifier_outbox TO satco_runtime;
        GRANT UPDATE(published_at) ON engineering_identifier_outbox TO satco_runtime;
        GRANT SELECT,INSERT,UPDATE,DELETE ON engineering_context_subject_references TO satco_runtime;
        REVOKE DELETE ON engineering_identifiers FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION satco_patch052_origin_immutable() FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION satco_patch052_identifier_guard() FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION satco_patch052_identifier_cardinality() FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION satco_patch052_context_object_coherence() FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION technical_report_historical_basis_v1_valid(text,jsonb) FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION technical_report_historical_basis_v2_valid(text,jsonb) FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION technical_report_historical_basis_valid(text,jsonb) FROM satco_runtime;
      END IF;
    END $$
    """)


def downgrade() -> None:
    connection = op.get_bind()
    has_rows = connection.execute(sa.text("""
      SELECT EXISTS(SELECT 1 FROM engineering_identifiers)
          OR EXISTS(SELECT 1 FROM engineering_context_subject_references WHERE subject_kind='engineering_object')
          OR EXISTS(SELECT 1 FROM engineering_objects WHERE object_type IN ('electrical_feeder','electrical_power_source'))
          OR EXISTS(SELECT 1 FROM engineering_objects WHERE origin_package_key IS NOT NULL)
          OR EXISTS(SELECT 1 FROM engineering_relationships WHERE origin_package_key IS NOT NULL)
          OR EXISTS(SELECT 1 FROM engineering_experience_captures WHERE origin_package_key IS NOT NULL)
          OR EXISTS(SELECT 1 FROM engineering_deliverables WHERE origin_package_key IS NOT NULL)
    """)).scalar_one()
    if has_rows:
        raise RuntimeError("PATCH-052 downgrade is prohibited while PATCH-052 rows exist")

    op.execute("DROP FUNCTION technical_report_historical_basis_valid(text,jsonb)")
    op.execute("DROP FUNCTION technical_report_historical_basis_v2_valid(text,jsonb)")
    op.execute("ALTER FUNCTION technical_report_historical_basis_v1_valid(text,jsonb) RENAME TO technical_report_historical_basis_valid")
    op.execute("DROP TRIGGER trg_context_object_coherence ON engineering_context_subject_references")
    op.execute("DROP FUNCTION satco_patch052_context_object_coherence()")
    op.execute("DROP TRIGGER trg_engineering_object_identifier_cardinality ON engineering_objects")
    op.execute("DROP TRIGGER trg_engineering_identifier_cardinality ON engineering_identifiers")
    op.execute("DROP FUNCTION satco_patch052_identifier_cardinality()")
    op.execute("DROP TRIGGER trg_engineering_identifier_guard ON engineering_identifiers")
    op.execute("DROP FUNCTION satco_patch052_identifier_guard()")
    for table in (*_ORIGIN_TABLES, "engineering_identifiers"):
        op.execute(f"DROP TRIGGER trg_{table}_origin_immutable ON {table}")
    op.execute("DROP FUNCTION satco_patch052_origin_immutable()")
    op.drop_index("ix_engineering_identifier_outbox_unpublished", table_name="engineering_identifier_outbox")
    op.drop_table("engineering_identifier_outbox")
    op.drop_table("engineering_identifier_idempotency")
    op.drop_table("engineering_identifiers")
    op.drop_index("ix_engineering_context_subject_refs_object_id", table_name="engineering_context_subject_references")
    op.drop_index("uq_engineering_context_subject_refs_object_identity", table_name="engineering_context_subject_references")
    op.drop_constraint("ck_engineering_context_subject_refs_target", "engineering_context_subject_references", type_="check")
    op.create_check_constraint("ck_engineering_context_subject_refs_target", "engineering_context_subject_references", "(subject_kind='project' AND subject_project_id IS NOT NULL AND subject_workspace_id IS NULL AND discipline IS NULL) OR (subject_kind='workspace' AND subject_project_id IS NULL AND subject_workspace_id IS NOT NULL AND discipline IS NULL) OR (subject_kind='discipline' AND subject_project_id IS NULL AND subject_workspace_id IS NULL AND discipline IS NOT NULL)")
    op.drop_constraint("fk_engineering_context_subject_refs_object", "engineering_context_subject_references", type_="foreignkey")
    op.drop_column("engineering_context_subject_references", "subject_engineering_object_id")
    op.drop_constraint("ck_engineering_objects_family_object_type", "engineering_objects", type_="check")
    op.drop_constraint("ck_engineering_objects_object_type", "engineering_objects", type_="check")
    op.create_check_constraint("ck_engineering_objects_object_type", "engineering_objects", "object_type IN ('instrument','transmitter','analyzer','flowmeter','control_valve','instrument_loop','junction_box','instrument_panel','motor','transformer','mcc','switchgear','electrical_panel','electrical_cable','plc','dcs_controller','esd_controller','control_cabinet','io_channel','hmi','control_logic','project','vendor','requirement','standard','datasheet','drawing','technical_decision')")
    op.create_check_constraint("ck_engineering_objects_family_object_type", "engineering_objects", "(family='instrumentation' AND object_type IN ('instrument','transmitter','analyzer','flowmeter','control_valve','instrument_loop','junction_box','instrument_panel')) OR (family='electrical' AND object_type IN ('motor','transformer','mcc','switchgear','electrical_panel','electrical_cable')) OR (family='automation' AND object_type IN ('plc','dcs_controller','esd_controller','control_cabinet','io_channel','hmi','control_logic')) OR (family='shared' AND object_type IN ('project','vendor','requirement','standard','datasheet','drawing','technical_decision'))")
    for table, check_name, fk_name in reversed((
        ("engineering_objects", "ck_engineering_objects_origin_all_or_none", "fk_engineering_objects_origin_selection"),
        ("engineering_relationships", "ck_engineering_relationships_origin_all_or_none", "fk_engineering_relationships_origin_selection"),
        ("engineering_experience_captures", "ck_experience_captures_origin_all_or_none", "fk_experience_captures_origin_selection"),
        ("engineering_deliverables", "ck_deliverable_origin_all_or_none", "fk_deliverable_origin_selection"),
    )):
        op.drop_index(f"ix_{table}_origin", table_name=table)
        op.drop_constraint(fk_name, table, type_="foreignkey")
        op.drop_constraint(check_name, table, type_="check")
        op.drop_column(table, "origin_declaration_id")
        op.drop_column(table, "origin_project_configuration_revision")
        op.drop_column(table, "origin_package_key")
