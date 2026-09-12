"""PATCH-054 Foundation Corrective Migration.

Revision ID: e05400000002
Revises: e05400000001

This is not the Batch-4 Technical Report integration migration.  It only
completes security and immutability invariants already assigned to the
accepted standards foundation.
"""

from alembic import op
import sqlalchemy as sa


revision = "e05400000002"
down_revision = "e05400000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError("PATCH-054 foundation correction requires exact e05400000001 predecessor")

    # Complete already-accepted tenant and provenance consistency constraints.
    op.create_unique_constraint(
        "uq_standard_editions_id_identity",
        "standard_editions",
        ["id", "standard_identity_id"],
    )
    op.create_unique_constraint(
        "uq_standard_snapshot_scope",
        "standard_source_snapshots",
        ["id", "organization_id", "project_id", "standard_edition_id"],
    )
    op.create_foreign_key(
        "fk_standard_snapshot_project_scope",
        "standard_source_snapshots",
        "projects",
        ["project_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_standard_snapshot_edition_identity",
        "standard_source_snapshots",
        "standard_editions",
        ["standard_edition_id", "standard_identity_id"],
        ["id", "standard_identity_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_standard_assertion_snapshot_scope",
        "standard_knowledge_assertions",
        "standard_source_snapshots",
        ["source_snapshot_id", "organization_id", "project_id", "standard_edition_id"],
        ["id", "organization_id", "project_id", "standard_edition_id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_standard_snapshot_availability",
        "standard_source_snapshots",
        "availability_status IN ('available','temporarily_unavailable','permanently_unavailable','rights_restricted','integrity_failed')",
    )
    op.create_check_constraint(
        "ck_standard_snapshot_receipt_shape",
        "standard_source_snapshots",
        "(availability_status='available' AND byte_count BETWEEN 1 AND 8192 AND media_type IS NOT NULL AND integrity_verified "
        "AND ((object_key IS NOT NULL AND object_version IS NOT NULL AND content_sha256 IS NOT NULL "
        "AND provider_handle_ciphertext IS NULL AND provider_handle_key_version IS NULL AND provider_version_digest IS NULL) "
        "OR (object_key IS NULL AND object_version IS NULL AND provider_handle_ciphertext IS NOT NULL "
        "AND provider_handle_key_version IS NOT NULL AND provider_version_digest IS NOT NULL))) "
        "OR (availability_status<>'available' AND object_key IS NULL AND object_version IS NULL "
        "AND provider_handle_ciphertext IS NULL AND provider_handle_key_version IS NULL "
        "AND provider_version_digest IS NULL AND content_sha256 IS NULL AND byte_count IS NULL AND media_type IS NULL)",
    )
    op.create_check_constraint(
        "ck_standard_snapshot_digests",
        "standard_source_snapshots",
        "rights_digest ~ '^[0-9a-f]{64}$' AND standing_observation_digest ~ '^[0-9a-f]{64}$' "
        "AND source_metadata_digest ~ '^[0-9a-f]{64}$' AND snapshot_digest ~ '^[0-9a-f]{64}$' "
        "AND (content_sha256 IS NULL OR content_sha256 ~ '^[0-9a-f]{64}$') "
        "AND (provider_version_digest IS NULL OR provider_version_digest ~ '^[0-9a-f]{64}$')",
    )
    op.create_check_constraint(
        "ck_standard_assertion_kind",
        "standard_knowledge_assertions",
        "assertion_kind IN ('requirement_statement','defined_term','numeric_constraint','cross_reference')",
    )
    op.create_check_constraint(
        "ck_standard_assertion_origin",
        "standard_knowledge_assertions",
        "assertion_origin IN ('human','deterministic','ai_assisted') AND "
        "((assertion_origin='ai_assisted' AND intelligence_run_id IS NOT NULL) OR "
        "(assertion_origin<>'ai_assisted' AND intelligence_run_id IS NULL))",
    )
    op.create_check_constraint(
        "ck_standard_assertion_representation",
        "standard_knowledge_assertions",
        "jsonb_typeof(canonical_representation)='object' AND octet_length(canonical_representation::text)<=8192",
    )
    op.create_check_constraint(
        "ck_standard_assertion_projection",
        "standard_knowledge_assertions",
        "verification_status IN ('unverified','human_verified','rejected','stale') AND version>=1",
    )
    op.create_check_constraint(
        "ck_standard_assertion_digests",
        "standard_knowledge_assertions",
        "source_content_digest ~ '^[0-9a-f]{64}$' AND extraction_method_digest ~ '^[0-9a-f]{64}$' "
        "AND assertion_digest ~ '^[0-9a-f]{64}$' AND rights_digest ~ '^[0-9a-f]{64}$'",
    )
    op.create_check_constraint(
        "ck_standard_verification_event_shape",
        "standard_assertion_verification_events",
        "event_kind IN ('verification_decision','eligibility_evaluation') AND status IN ('human_verified','rejected','stale') "
        "AND (status='human_verified' OR (reason IS NOT NULL AND btrim(reason)<>'')) "
        "AND (actor_kind<>'human' OR verified_by IS NOT NULL)",
    )
    op.create_index(
        "ix_standard_assertion_snapshot_count",
        "standard_knowledge_assertions",
        ["source_snapshot_id"],
    )

    op.execute("""
    CREATE FUNCTION standards_snapshot_history_immutable() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      RAISE EXCEPTION 'PATCH-054 source snapshot history is immutable' USING ERRCODE='55000';
    END $$;

    CREATE FUNCTION standards_assertion_history_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF TG_OP='DELETE' THEN
        RAISE EXCEPTION 'PATCH-054 assertion history is immutable' USING ERRCODE='55000';
      END IF;
      IF ROW(NEW.organization_id,NEW.project_id,NEW.standard_edition_id,NEW.source_snapshot_id,
             NEW.source_location,NEW.source_content_digest,NEW.assertion_kind,NEW.canonical_representation,
             NEW.assertion_origin,NEW.extraction_method_id,NEW.extraction_method_version,
             NEW.extraction_method_digest,NEW.intelligence_run_id,NEW.assertion_digest,
             NEW.rights_binding_id,NEW.rights_binding_version,NEW.rights_digest,
             NEW.predecessor_assertion_id,NEW.created_by,NEW.created_at)
         IS DISTINCT FROM
         ROW(OLD.organization_id,OLD.project_id,OLD.standard_edition_id,OLD.source_snapshot_id,
             OLD.source_location,OLD.source_content_digest,OLD.assertion_kind,OLD.canonical_representation,
             OLD.assertion_origin,OLD.extraction_method_id,OLD.extraction_method_version,
             OLD.extraction_method_digest,OLD.intelligence_run_id,OLD.assertion_digest,
             OLD.rights_binding_id,OLD.rights_binding_version,OLD.rights_digest,
             OLD.predecessor_assertion_id,OLD.created_by,OLD.created_at)
         OR NEW.version<>OLD.version+1 THEN
        RAISE EXCEPTION 'PATCH-054 assertion canonical meaning is immutable' USING ERRCODE='55000';
      END IF;
      RETURN NEW;
    END $$;

    CREATE FUNCTION standards_verification_history_immutable() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      RAISE EXCEPTION 'PATCH-054 verification history is immutable' USING ERRCODE='55000';
    END $$;

    CREATE FUNCTION standards_assertion_limit_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('standards-assertions:'||NEW.source_snapshot_id::text,0));
      IF (SELECT count(*) FROM public.standard_knowledge_assertions WHERE source_snapshot_id=NEW.source_snapshot_id)>=32 THEN
        RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED: maximum 32 assertions per snapshot' USING ERRCODE='54000';
      END IF;
      RETURN NEW;
    END $$;

    CREATE TRIGGER tr_standard_snapshot_immutable BEFORE UPDATE OR DELETE ON standard_source_snapshots
      FOR EACH ROW EXECUTE FUNCTION standards_snapshot_history_immutable();
    CREATE TRIGGER tr_standard_assertion_immutable BEFORE UPDATE OR DELETE ON standard_knowledge_assertions
      FOR EACH ROW EXECUTE FUNCTION standards_assertion_history_guard();
    CREATE TRIGGER tr_standard_verification_immutable BEFORE UPDATE OR DELETE ON standard_assertion_verification_events
      FOR EACH ROW EXECUTE FUNCTION standards_verification_history_immutable();
    CREATE TRIGGER tr_standard_assertion_limit BEFORE INSERT ON standard_knowledge_assertions
      FOR EACH ROW EXECUTE FUNCTION standards_assertion_limit_guard();

    REVOKE ALL ON FUNCTION standards_snapshot_history_immutable() FROM PUBLIC;
    REVOKE ALL ON FUNCTION standards_assertion_history_guard() FROM PUBLIC;
    REVOKE ALL ON FUNCTION standards_verification_history_immutable() FROM PUBLIC;
    REVOKE ALL ON FUNCTION standards_assertion_limit_guard() FROM PUBLIC;

    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON standard_source_snapshots,standard_knowledge_assertions,standard_assertion_verification_events FROM satco_runtime;
        GRANT INSERT(id,organization_id,project_id,standard_identity_id,standard_edition_id,source_provider_id,
          adapter_policy_id,adapter_policy_version,source_location,availability_status,request_purpose,correlation_id,
          object_key,object_version,provider_handle_ciphertext,provider_handle_key_version,provider_version_digest,
          content_sha256,byte_count,media_type,rights_binding_id,rights_binding_version,rights_digest,
          evaluated_capabilities,standing_observation_id,standing_observation_digest,source_metadata_digest,
          integrity_verified,integrity_verified_at,snapshot_digest,retrieved_at,retrieved_by)
          ON standard_source_snapshots TO satco_runtime;
        GRANT SELECT(id,organization_id,project_id,standard_identity_id,standard_edition_id,source_provider_id,
          adapter_policy_id,adapter_policy_version,source_location,availability_status,request_purpose,correlation_id,
          object_key,object_version,provider_handle_key_version,provider_version_digest,content_sha256,byte_count,
          media_type,rights_binding_id,rights_binding_version,rights_digest,evaluated_capabilities,
          standing_observation_id,standing_observation_digest,source_metadata_digest,integrity_verified,
          integrity_verified_at,snapshot_digest,retrieved_at,retrieved_by,created_at)
          ON standard_source_snapshots TO satco_runtime;
        GRANT SELECT,INSERT ON standard_knowledge_assertions,standard_assertion_verification_events TO satco_runtime;
        GRANT UPDATE(current_verification_event_id,verification_status,retained_derived_use_eligible,
          evaluated_rights_revision,successor_assertion_id,version) ON standard_knowledge_assertions TO satco_runtime;
        REVOKE DELETE ON standard_source_snapshots,standard_knowledge_assertions,standard_assertion_verification_events FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION standards_snapshot_history_immutable(),standards_assertion_history_guard(),
          standards_verification_history_immutable(),standards_assertion_limit_guard() FROM satco_runtime;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_registry_installer') THEN
        REVOKE ALL ON standard_source_snapshots,standard_knowledge_assertions,standard_assertion_verification_events FROM satco_registry_installer;
        REVOKE EXECUTE ON FUNCTION standards_snapshot_history_immutable(),standards_assertion_history_guard(),
          standards_verification_history_immutable(),standards_assertion_limit_guard() FROM satco_registry_installer;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    bind = op.get_bind()
    retained = bind.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM standard_source_snapshots) OR "
        "EXISTS(SELECT 1 FROM standard_knowledge_assertions) OR "
        "EXISTS(SELECT 1 FROM standard_assertion_verification_events)"
    )).scalar_one()
    if retained:
        raise RuntimeError("PATCH-054 foundation correction downgrade is prohibited while retained Batch-2 foundation data exists")

    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON standard_source_snapshots,standard_knowledge_assertions,standard_assertion_verification_events FROM satco_runtime;
      END IF;
    END $$;
    DROP FUNCTION standards_assertion_limit_guard() CASCADE;
    DROP FUNCTION standards_verification_history_immutable() CASCADE;
    DROP FUNCTION standards_assertion_history_guard() CASCADE;
    DROP FUNCTION standards_snapshot_history_immutable() CASCADE;
    """)
    op.drop_index("ix_standard_assertion_snapshot_count", table_name="standard_knowledge_assertions")
    for name, table in (
        ("ck_standard_verification_event_shape", "standard_assertion_verification_events"),
        ("ck_standard_assertion_digests", "standard_knowledge_assertions"),
        ("ck_standard_assertion_projection", "standard_knowledge_assertions"),
        ("ck_standard_assertion_representation", "standard_knowledge_assertions"),
        ("ck_standard_assertion_origin", "standard_knowledge_assertions"),
        ("ck_standard_assertion_kind", "standard_knowledge_assertions"),
        ("ck_standard_snapshot_digests", "standard_source_snapshots"),
        ("ck_standard_snapshot_receipt_shape", "standard_source_snapshots"),
        ("ck_standard_snapshot_availability", "standard_source_snapshots"),
    ):
        op.drop_constraint(name, table, type_="check")
    op.drop_constraint("fk_standard_assertion_snapshot_scope", "standard_knowledge_assertions", type_="foreignkey")
    op.drop_constraint("fk_standard_snapshot_edition_identity", "standard_source_snapshots", type_="foreignkey")
    op.drop_constraint("fk_standard_snapshot_project_scope", "standard_source_snapshots", type_="foreignkey")
    op.drop_constraint("uq_standard_snapshot_scope", "standard_source_snapshots", type_="unique")
    op.drop_constraint("uq_standard_editions_id_identity", "standard_editions", type_="unique")
