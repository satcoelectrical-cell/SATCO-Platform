"""PATCH-054 Project applicability foundation correction.

Revision ID: e05400000004
Revises: e05400000003

This corrective migration closes the accepted Batch-3 persistence gap only.
It deliberately adds no API, service, package-hook, Report, or AI behavior.
"""

from alembic import op
import sqlalchemy as sa


revision = "e05400000004"
down_revision = "e05400000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError("PATCH-054 applicability correction requires exact e05400000003 predecessor")
    if bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM public.project_standard_applicability)")).scalar_one():
        raise RuntimeError("PATCH-054 applicability correction requires an empty pre-Batch-3 applicability table")

    op.execute("""
    ALTER TABLE public.project_standard_applicability
      RENAME COLUMN role TO applicability_role;
    ALTER TABLE public.project_standard_applicability
      RENAME COLUMN created_by TO declared_by;
    ALTER TABLE public.project_standard_applicability
      RENAME COLUMN version TO revision;
    ALTER TABLE public.project_standard_applicability
      ALTER COLUMN standard_edition_id DROP NOT NULL,
      ALTER COLUMN status TYPE varchar(32),
      ALTER COLUMN status DROP DEFAULT,
      ALTER COLUMN applicability_role TYPE varchar(20);
    ALTER TABLE public.project_standard_applicability
      ADD COLUMN candidate_designation_key varchar(240),
      ADD COLUMN rationale_code varchar(80) NOT NULL,
      ADD COLUMN rationale varchar(1000) NOT NULL,
      ADD COLUMN origin_reference varchar(240) NOT NULL,
      ADD COLUMN source_candidate_reference varchar(240),
      ADD COLUMN mandatory_source_kind varchar(32),
      ADD COLUMN mandatory_source_reference varchar(500),
      ADD COLUMN mandatory_source_digest char(64),
      ADD COLUMN expected_predecessor_revision bigint,
      ADD COLUMN successor_id uuid,
      ADD COLUMN is_current boolean NOT NULL DEFAULT true,
      ADD COLUMN applicability_digest char(64) NOT NULL;
    ALTER TABLE public.project_standard_applicability
      ADD CONSTRAINT fk_standard_applicability_project_scope
        FOREIGN KEY(project_id,organization_id) REFERENCES public.projects(id,organization_id) ON DELETE RESTRICT,
      ADD CONSTRAINT fk_standard_applicability_successor
        FOREIGN KEY(successor_id) REFERENCES public.project_standard_applicability(id)
        DEFERRABLE INITIALLY DEFERRED,
      ADD CONSTRAINT uq_standard_applicability_successor UNIQUE(successor_id),
      ADD CONSTRAINT ck_standard_applicability_status CHECK
        (status IN ('candidate_advisory','declared_applicable','declared_not_applicable','retired')),
      ADD CONSTRAINT ck_standard_applicability_role CHECK
        (applicability_role IN ('informative','design_basis','mandatory')),
      ADD CONSTRAINT ck_standard_applicability_digest CHECK
        (applicability_digest ~ '^[0-9a-f]{64}$'),
      ADD CONSTRAINT ck_standard_applicability_human_provenance CHECK
        (btrim(rationale_code)<>'' AND btrim(rationale)<>'' AND btrim(origin_reference)<>''),
      ADD CONSTRAINT ck_standard_applicability_candidate_shape CHECK (
        (status='candidate_advisory' AND candidate_designation_key IS NOT NULL
          AND btrim(candidate_designation_key)<>''
          AND source_candidate_reference IS NOT NULL
          AND btrim(source_candidate_reference)<>''
          AND applicability_role IN ('informative','design_basis')
          AND mandatory_source_kind IS NULL AND mandatory_source_reference IS NULL
          AND mandatory_source_digest IS NULL AND predecessor_id IS NULL
          AND successor_id IS NULL AND expected_predecessor_revision IS NULL)
        OR status<>'candidate_advisory'
      ),
      ADD CONSTRAINT ck_standard_applicability_declaration_edition CHECK
        (status='candidate_advisory' OR standard_edition_id IS NOT NULL),
      ADD CONSTRAINT ck_standard_applicability_mandatory_basis CHECK (
        (applicability_role='mandatory' AND status='declared_applicable'
          AND mandatory_source_kind IN ('contract','regulation','customer_requirement','company_policy')
          AND mandatory_source_reference IS NOT NULL AND btrim(mandatory_source_reference)<>''
          AND mandatory_source_digest ~ '^[0-9a-f]{64}$')
        OR
        (applicability_role<>'mandatory' AND mandatory_source_kind IS NULL
          AND mandatory_source_reference IS NULL AND mandatory_source_digest IS NULL)
      ),
      ADD CONSTRAINT ck_standard_applicability_retirement_shape CHECK
        (status<>'retired' OR standard_edition_id IS NOT NULL);
    CREATE UNIQUE INDEX uq_standard_applicability_current_human_head
      ON public.project_standard_applicability(project_id,standard_edition_id)
      WHERE is_current AND status IN ('declared_applicable','declared_not_applicable');
    CREATE INDEX ix_standard_applicability_project_current
      ON public.project_standard_applicability(organization_id,project_id,is_current,created_at);
    CREATE INDEX ix_standard_applicability_candidate_reference
      ON public.project_standard_applicability(organization_id,project_id,source_candidate_reference)
      WHERE source_candidate_reference IS NOT NULL;

    CREATE FUNCTION public.standards_applicability_history_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF TG_OP='DELETE' THEN
        RAISE EXCEPTION 'PATCH-054 applicability history is immutable' USING ERRCODE='55000';
      END IF;
      IF ROW(NEW.organization_id,NEW.project_id,NEW.standard_edition_id,NEW.candidate_designation_key,
             NEW.status,NEW.applicability_role,NEW.rationale_code,NEW.rationale,NEW.origin_reference,
             NEW.source_candidate_reference,NEW.mandatory_source_kind,NEW.mandatory_source_reference,
             NEW.mandatory_source_digest,NEW.expected_predecessor_revision,NEW.predecessor_id,
             NEW.applicability_digest,NEW.declared_by,NEW.created_at)
           IS DISTINCT FROM
         ROW(OLD.organization_id,OLD.project_id,OLD.standard_edition_id,OLD.candidate_designation_key,
             OLD.status,OLD.applicability_role,OLD.rationale_code,OLD.rationale,OLD.origin_reference,
             OLD.source_candidate_reference,OLD.mandatory_source_kind,OLD.mandatory_source_reference,
             OLD.mandatory_source_digest,OLD.expected_predecessor_revision,OLD.predecessor_id,
             OLD.applicability_digest,OLD.declared_by,OLD.created_at)
         OR NOT OLD.is_current OR NEW.is_current OR NEW.revision<>OLD.revision+1
         OR NEW.successor_id IS NULL THEN
        RAISE EXCEPTION 'PATCH-054 applicability history is append-only' USING ERRCODE='55000';
      END IF;
      RETURN NEW;
    END $$;

    CREATE FUNCTION public.standards_applicability_limit_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF NEW.is_current AND NEW.status IN ('declared_applicable','declared_not_applicable') THEN
        PERFORM pg_catalog.pg_advisory_xact_lock(
          pg_catalog.hashtextextended('standards-applicability:'||NEW.project_id::text,0)
        );
        IF (SELECT count(*) FROM public.project_standard_applicability
            WHERE project_id=NEW.project_id AND is_current
              AND status IN ('declared_applicable','declared_not_applicable')) >= 64 THEN
          RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED: maximum 64 current applicability declaration heads per project'
            USING ERRCODE='54000';
        END IF;
      END IF;
      RETURN NEW;
    END $$;

    CREATE FUNCTION public.standards_applicability_lineage_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE predecessor public.project_standard_applicability%ROWTYPE;
    BEGIN
      IF NEW.predecessor_id IS NULL THEN
        IF NEW.expected_predecessor_revision IS NOT NULL OR NEW.revision<>1 THEN
          RAISE EXCEPTION 'PATCH-054 applicability root revision is invalid' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
      END IF;
      SELECT * INTO predecessor FROM public.project_standard_applicability WHERE id=NEW.predecessor_id;
      IF NOT FOUND OR predecessor.organization_id<>NEW.organization_id
         OR predecessor.project_id<>NEW.project_id
         OR predecessor.standard_edition_id IS DISTINCT FROM NEW.standard_edition_id
         OR NEW.expected_predecessor_revision IS NULL
         OR NEW.revision<>NEW.expected_predecessor_revision+1
         OR predecessor.revision<>NEW.revision
         OR predecessor.is_current
         OR predecessor.successor_id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'PATCH-054 applicability predecessor/CAS lineage is invalid' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;

    CREATE TRIGGER tr_standard_applicability_immutable
      BEFORE UPDATE OR DELETE ON public.project_standard_applicability
      FOR EACH ROW EXECUTE FUNCTION public.standards_applicability_history_guard();
    CREATE TRIGGER tr_standard_applicability_limit
      BEFORE INSERT ON public.project_standard_applicability
      FOR EACH ROW EXECUTE FUNCTION public.standards_applicability_limit_guard();
    CREATE CONSTRAINT TRIGGER tr_standard_applicability_lineage
      AFTER INSERT ON public.project_standard_applicability DEFERRABLE INITIALLY DEFERRED
      FOR EACH ROW EXECUTE FUNCTION public.standards_applicability_lineage_guard();

    REVOKE ALL ON FUNCTION public.standards_applicability_history_guard() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.standards_applicability_limit_guard() FROM PUBLIC;
    REVOKE ALL ON FUNCTION public.standards_applicability_lineage_guard() FROM PUBLIC;
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON public.project_standard_applicability FROM satco_runtime;
        GRANT SELECT,INSERT ON public.project_standard_applicability TO satco_runtime;
        GRANT UPDATE(is_current,successor_id,revision) ON public.project_standard_applicability TO satco_runtime;
        REVOKE DELETE ON public.project_standard_applicability FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION public.standards_applicability_history_guard(),
          public.standards_applicability_limit_guard(), public.standards_applicability_lineage_guard()
          FROM satco_runtime;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_registry_installer') THEN
        REVOKE ALL ON public.project_standard_applicability FROM satco_registry_installer;
        REVOKE EXECUTE ON FUNCTION public.standards_applicability_history_guard(),
          public.standards_applicability_limit_guard(), public.standards_applicability_lineage_guard()
          FROM satco_registry_installer;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM public.project_standard_applicability)")).scalar_one():
        raise RuntimeError("PATCH-054 applicability correction downgrade is prohibited while retained applicability history exists")
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON public.project_standard_applicability FROM satco_runtime;
      END IF;
    END $$;
    DROP TRIGGER tr_standard_applicability_lineage ON public.project_standard_applicability;
    DROP TRIGGER tr_standard_applicability_limit ON public.project_standard_applicability;
    DROP TRIGGER tr_standard_applicability_immutable ON public.project_standard_applicability;
    DROP FUNCTION public.standards_applicability_lineage_guard();
    DROP FUNCTION public.standards_applicability_limit_guard();
    DROP FUNCTION public.standards_applicability_history_guard();
    DROP INDEX public.ix_standard_applicability_candidate_reference;
    DROP INDEX public.ix_standard_applicability_project_current;
    DROP INDEX public.uq_standard_applicability_current_human_head;
    ALTER TABLE public.project_standard_applicability
      DROP CONSTRAINT ck_standard_applicability_retirement_shape,
      DROP CONSTRAINT ck_standard_applicability_mandatory_basis,
      DROP CONSTRAINT ck_standard_applicability_declaration_edition,
      DROP CONSTRAINT ck_standard_applicability_candidate_shape,
      DROP CONSTRAINT ck_standard_applicability_human_provenance,
      DROP CONSTRAINT ck_standard_applicability_digest,
      DROP CONSTRAINT ck_standard_applicability_role,
      DROP CONSTRAINT ck_standard_applicability_status,
      DROP CONSTRAINT uq_standard_applicability_successor,
      DROP CONSTRAINT fk_standard_applicability_successor,
      DROP CONSTRAINT fk_standard_applicability_project_scope,
      DROP COLUMN applicability_digest,
      DROP COLUMN is_current,
      DROP COLUMN successor_id,
      DROP COLUMN expected_predecessor_revision,
      DROP COLUMN mandatory_source_digest,
      DROP COLUMN mandatory_source_reference,
      DROP COLUMN mandatory_source_kind,
      DROP COLUMN source_candidate_reference,
      DROP COLUMN origin_reference,
      DROP COLUMN rationale,
      DROP COLUMN rationale_code,
      DROP COLUMN candidate_designation_key;
    ALTER TABLE public.project_standard_applicability
      ALTER COLUMN standard_edition_id SET NOT NULL,
      ALTER COLUMN status TYPE varchar(24),
      ALTER COLUMN status SET DEFAULT 'declared',
      ALTER COLUMN applicability_role TYPE varchar(32);
    ALTER TABLE public.project_standard_applicability RENAME COLUMN applicability_role TO role;
    ALTER TABLE public.project_standard_applicability RENAME COLUMN revision TO version;
    ALTER TABLE public.project_standard_applicability RENAME COLUMN declared_by TO created_by;
    """)
