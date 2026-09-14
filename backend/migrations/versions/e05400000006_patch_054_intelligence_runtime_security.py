"""PATCH-054 Batch-5 intelligence runtime lifecycle security.

Revision ID: e05400000006
Revises: e05400000005
"""

from alembic import op

revision = "e05400000006"
down_revision = "e05400000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE public.standard_intelligence_runs
      ADD CONSTRAINT uq_standard_intelligence_request
        UNIQUE (organization_id,project_id,created_by,request_digest),
      ADD CONSTRAINT ck_standard_intelligence_phase
        CHECK (phase_status IN ('requested','dispatched','terminal')),
      ADD CONSTRAINT ck_standard_intelligence_result
        CHECK (result_status IS NULL OR result_status IN ('completed_with_suggestions','completed_no_suggestions','not_permitted','unavailable','invalid_output')),
      ADD CONSTRAINT ck_standard_intelligence_digests
        CHECK (request_digest ~ '^[0-9a-f]{64}$' AND deterministic_result_digest ~ '^[0-9a-f]{64}$'
          AND template_digest ~ '^[0-9a-f]{64}$' AND authorized_handle_digest ~ '^[0-9a-f]{64}$'
          AND input_digest ~ '^[0-9a-f]{64}$' AND (output_digest IS NULL OR output_digest ~ '^[0-9a-f]{64}$')
          AND (suggestion_handle_digest IS NULL OR suggestion_handle_digest ~ '^[0-9a-f]{64}$')),
      ADD CONSTRAINT ck_standard_intelligence_json_bounds
        CHECK (jsonb_typeof(deterministic_result)='object' AND octet_length(deterministic_result::text)<=16384
          AND jsonb_typeof(rights_manifest)='array' AND octet_length(rights_manifest::text)<=16384
          AND (advisory_output IS NULL OR (jsonb_typeof(advisory_output)='object' AND octet_length(advisory_output::text)<=16384
            AND jsonb_typeof(advisory_output->'suggestions')='array' AND jsonb_array_length(advisory_output->'suggestions')<=12))),
      ADD CONSTRAINT ck_standard_intelligence_terminal_shape
        CHECK (
          (phase_status IN ('requested','dispatched') AND result_status IS NULL AND completed_at IS NULL)
          OR
          (phase_status='terminal' AND result_status IS NOT NULL AND completed_at IS NOT NULL
            AND ((result_status IN ('completed_with_suggestions','completed_no_suggestions') AND advisory_output IS NOT NULL AND output_digest IS NOT NULL AND suggestion_handle_digest IS NOT NULL)
              OR (result_status IN ('not_permitted','unavailable','invalid_output') AND advisory_output IS NULL AND output_digest IS NULL AND suggestion_handle_digest IS NULL)))
        );

    CREATE INDEX ix_standard_intelligence_project_created
      ON public.standard_intelligence_runs(organization_id,project_id,created_at DESC,id DESC);

    CREATE FUNCTION public.standards_intelligence_lifecycle_guard() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF TG_OP='DELETE' THEN
        RAISE EXCEPTION 'intelligence runs cannot be deleted' USING ERRCODE='55000';
      END IF;
      IF TG_OP='INSERT' THEN
        IF NEW.phase_status<>'requested' OR NEW.call_count<>0 OR NEW.version<>1
           OR NEW.result_status IS NOT NULL OR NEW.advisory_output IS NOT NULL
           OR NEW.output_digest IS NOT NULL OR NEW.suggestion_handle_digest IS NOT NULL
           OR NEW.failure_code IS NOT NULL OR NEW.dispatched_at IS NOT NULL
           OR NEW.completed_at IS NOT NULL THEN
          RAISE EXCEPTION 'invalid intelligence initial state' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
      END IF;

      IF ROW(NEW.id,NEW.organization_id,NEW.project_id,NEW.report_id,NEW.request_kind,
             NEW.purpose,NEW.correlation_id,NEW.request_digest,NEW.deterministic_result,
             NEW.deterministic_result_digest,NEW.template_id,NEW.template_version,
             NEW.template_digest,NEW.processor_policy_id,NEW.provider_id,
             NEW.provider_model,NEW.provider_version,NEW.rights_manifest,
             NEW.authorized_handle_digest,NEW.input_digest,NEW.input_byte_count,
             NEW.created_by,NEW.created_at,NEW.deadline_at)
         IS DISTINCT FROM
         ROW(OLD.id,OLD.organization_id,OLD.project_id,OLD.report_id,OLD.request_kind,
             OLD.purpose,OLD.correlation_id,OLD.request_digest,OLD.deterministic_result,
             OLD.deterministic_result_digest,OLD.template_id,OLD.template_version,
             OLD.template_digest,OLD.processor_policy_id,OLD.provider_id,
             OLD.provider_model,OLD.provider_version,OLD.rights_manifest,
             OLD.authorized_handle_digest,OLD.input_digest,OLD.input_byte_count,
             OLD.created_by,OLD.created_at,OLD.deadline_at) THEN
        RAISE EXCEPTION 'immutable intelligence provenance' USING ERRCODE='55000';
      END IF;
      IF NEW.version<>OLD.version+1 OR NEW.call_count<OLD.call_count THEN
        RAISE EXCEPTION 'invalid intelligence CAS transition' USING ERRCODE='40001';
      END IF;
      IF OLD.phase_status='requested' AND NEW.phase_status='dispatched' THEN
        IF OLD.call_count<>0 OR NEW.call_count<>1 OR NEW.dispatched_at IS NULL
           OR NEW.result_status IS NOT NULL OR NEW.completed_at IS NOT NULL
           OR NEW.advisory_output IS NOT NULL OR NEW.output_digest IS NOT NULL
           OR NEW.suggestion_handle_digest IS NOT NULL OR NEW.failure_code IS NOT NULL THEN
          RAISE EXCEPTION 'invalid intelligence dispatch transition' USING ERRCODE='23514';
        END IF;
      ELSIF OLD.phase_status='requested' AND NEW.phase_status='terminal' THEN
        IF NEW.call_count<>0 OR NEW.dispatched_at IS NOT NULL
           OR NEW.result_status NOT IN ('not_permitted','unavailable') THEN
          RAISE EXCEPTION 'invalid zero-call intelligence terminal transition' USING ERRCODE='23514';
        END IF;
      ELSIF OLD.phase_status='dispatched' AND NEW.phase_status='terminal' THEN
        IF OLD.call_count<>1 OR NEW.call_count<>1 OR NEW.dispatched_at IS DISTINCT FROM OLD.dispatched_at THEN
          RAISE EXCEPTION 'invalid intelligence finalization transition' USING ERRCODE='23514';
        END IF;
      ELSE
        RAISE EXCEPTION 'invalid intelligence lifecycle transition' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;

    CREATE TRIGGER tr_standard_intelligence_lifecycle
      BEFORE INSERT OR UPDATE OR DELETE ON public.standard_intelligence_runs
      FOR EACH ROW EXECUTE FUNCTION public.standards_intelligence_lifecycle_guard();

    REVOKE ALL ON FUNCTION public.standards_intelligence_lifecycle_guard() FROM PUBLIC;
    REVOKE ALL ON public.standard_intelligence_runs FROM PUBLIC;
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON public.standard_intelligence_runs FROM satco_runtime;
        GRANT SELECT ON public.standard_intelligence_runs TO satco_runtime;
        GRANT INSERT (id,organization_id,project_id,report_id,request_kind,purpose,correlation_id,
          request_digest,deterministic_result,deterministic_result_digest,template_id,template_version,
          template_digest,processor_policy_id,provider_id,provider_model,provider_version,rights_manifest,
          authorized_handle_digest,input_digest,input_byte_count,created_by,deadline_at)
          ON public.standard_intelligence_runs TO satco_runtime;
        GRANT UPDATE (phase_status,result_status,call_count,dispatched_at,completed_at,advisory_output,
          output_digest,suggestion_handle_digest,failure_code,version)
          ON public.standard_intelligence_runs TO satco_runtime;
        REVOKE DELETE ON public.standard_intelligence_runs FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION public.standards_intelligence_lifecycle_guard() FROM satco_runtime;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_registry_installer') THEN
        REVOKE ALL ON public.standard_intelligence_runs FROM satco_registry_installer;
        REVOKE EXECUTE ON FUNCTION public.standards_intelligence_lifecycle_guard() FROM satco_registry_installer;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON public.standard_intelligence_runs FROM satco_runtime;
      END IF;
    END $$;
    DROP TRIGGER tr_standard_intelligence_lifecycle ON public.standard_intelligence_runs;
    DROP FUNCTION public.standards_intelligence_lifecycle_guard();
    DROP INDEX public.ix_standard_intelligence_project_created;
    ALTER TABLE public.standard_intelligence_runs
      DROP CONSTRAINT ck_standard_intelligence_terminal_shape,
      DROP CONSTRAINT ck_standard_intelligence_json_bounds,
      DROP CONSTRAINT ck_standard_intelligence_digests,
      DROP CONSTRAINT ck_standard_intelligence_result,
      DROP CONSTRAINT ck_standard_intelligence_phase,
      DROP CONSTRAINT uq_standard_intelligence_request;
    """)
