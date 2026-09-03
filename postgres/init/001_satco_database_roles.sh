#!/bin/sh
set -eu

# PostgreSQL runs this file only when initializing a clean data directory.
# Existing environments must provision the same restricted role operationally.
: "${SATCO_RUNTIME_DATABASE_PASSWORD:?SATCO_RUNTIME_DATABASE_PASSWORD is required}"
: "${SATCO_REGISTRY_INSTALLER_DATABASE_PASSWORD:?SATCO_REGISTRY_INSTALLER_DATABASE_PASSWORD is required}"

psql --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=runtime_password="$SATCO_RUNTIME_DATABASE_PASSWORD" \
  --set=installer_password="$SATCO_REGISTRY_INSTALLER_DATABASE_PASSWORD" <<'SQL'
SELECT format(
  'CREATE ROLE satco_runtime LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS',
  :'runtime_password'
) WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'satco_runtime') \gexec
ALTER ROLE satco_runtime NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
SELECT format(
  'CREATE ROLE satco_registry_installer LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS',
  :'installer_password'
) WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'satco_registry_installer') \gexec
ALTER ROLE satco_registry_installer NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE :"DBNAME" TO satco_runtime;
GRANT USAGE ON SCHEMA public TO satco_runtime;
GRANT CONNECT ON DATABASE :"DBNAME" TO satco_registry_installer;
GRANT USAGE ON SCHEMA public TO satco_registry_installer;

-- Explicit compatibility matrix for capabilities approved before PATCH-032.
-- Missing relations are skipped during clean initialization; the PATCH-032
-- owner migration applies the same matrix after schema creation.
DO $grant$
DECLARE relation_name text;
BEGIN
  FOREACH relation_name IN ARRAY ARRAY[
    'users','customers','contacts','projects','project_code_sequences',
    'organizations','user_organization_memberships','engineering_workspaces',
    'engineering_workspace_members','engineering_contexts','engineering_context_facts',
    'engineering_context_values','engineering_context_assumptions',
    'engineering_context_subject_references','engineering_context_source_references',
    'engineering_context_relationships','interface_commitments'
  ] LOOP
    IF to_regclass('public.' || relation_name) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO satco_runtime', relation_name);
    END IF;
  END LOOP;
  FOREACH relation_name IN ARRAY ARRAY[
    'engineering_objects','engineering_relationships','evidence',
    'engineering_experience_captures'
  ] LOOP
    IF to_regclass('public.' || relation_name) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT, INSERT, UPDATE ON TABLE public.%I TO satco_runtime', relation_name);
    END IF;
  END LOOP;
  FOREACH relation_name IN ARRAY ARRAY[
    'engineering_object_outbox','engineering_object_idempotency',
    'engineering_relationship_outbox','engineering_relationship_idempotency',
    'evidence_outbox','evidence_idempotency',
    'engineering_experience_capture_outbox','engineering_experience_capture_idempotency'
  ] LOOP
    IF to_regclass('public.' || relation_name) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT, INSERT, UPDATE ON TABLE public.%I TO satco_runtime', relation_name);
    END IF;
  END LOOP;
  IF to_regclass('public.audit_logs') IS NOT NULL THEN
    REVOKE ALL ON TABLE public.audit_logs FROM satco_runtime;
    GRANT SELECT, INSERT ON TABLE public.audit_logs TO satco_runtime;
  END IF;
  FOREACH relation_name IN ARRAY ARRAY[
    'audit_logs_id_seq','contacts_id_seq','customers_id_seq',
    'engineering_context_relationships_id_seq','engineering_context_source_references_id_seq',
    'engineering_context_subject_references_id_seq','engineering_contexts_id_seq',
    'engineering_workspaces_id_seq','interface_commitments_id_seq','projects_id_seq','users_id_seq'
  ] LOOP
    IF to_regclass('public.' || relation_name) IS NOT NULL THEN
      EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE public.%I TO satco_runtime', relation_name);
    END IF;
  END LOOP;
END
$grant$;
SQL
