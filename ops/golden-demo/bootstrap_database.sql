\set ON_ERROR_STOP on

-- Golden Demo only: preserve the production role boundary while making a
-- disposable migration-owner database reproducible.  Run once before Alembic
-- (to create the NOLOGIN owner used by historical migrations), and once after
-- Alembic (to align the PATCH-032 tables/functions with the same NOLOGIN
-- migration owner expected by the runtime boundary).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'satco') THEN
        CREATE ROLE satco NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

ALTER ROLE satco NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;

DO $$
BEGIN
    IF to_regclass('public.technical_reports') IS NOT NULL THEN
        ALTER TABLE public.technical_reports OWNER TO satco;
    END IF;
    IF to_regclass('public.technical_report_provenance_entries') IS NOT NULL THEN
        ALTER TABLE public.technical_report_provenance_entries OWNER TO satco;
    END IF;
    IF to_regclass('public.technical_report_outbox') IS NOT NULL THEN
        ALTER TABLE public.technical_report_outbox OWNER TO satco;
    END IF;
    IF to_regclass('public.technical_report_idempotency') IS NOT NULL THEN
        ALTER TABLE public.technical_report_idempotency OWNER TO satco;
    END IF;
END
$$;

DO $$
BEGIN
    IF to_regprocedure('public.technical_report_canonical_json(jsonb)') IS NOT NULL THEN
        ALTER FUNCTION public.technical_report_canonical_json(jsonb) OWNER TO satco;
    END IF;
    IF to_regprocedure('public.technical_report_historical_basis_valid(text,jsonb)') IS NOT NULL THEN
        ALTER FUNCTION public.technical_report_historical_basis_valid(text,jsonb) OWNER TO satco;
    END IF;
    IF to_regprocedure('public.technical_report_provenance_json_valid(jsonb)') IS NOT NULL THEN
        ALTER FUNCTION public.technical_report_provenance_json_valid(jsonb) OWNER TO satco;
    END IF;
    IF to_regprocedure('public.technical_report_root_accepted_immutable()') IS NOT NULL THEN
        ALTER FUNCTION public.technical_report_root_accepted_immutable() OWNER TO satco;
    END IF;
    IF to_regprocedure('public.technical_report_provenance_accepted_immutable()') IS NOT NULL THEN
        ALTER FUNCTION public.technical_report_provenance_accepted_immutable() OWNER TO satco;
    END IF;
END
$$;
