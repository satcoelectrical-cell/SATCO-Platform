"""PATCH-054 Batch-1 standards foundation.

Revision ID: e05400000001
Revises: e05300000002
"""

from alembic import op
import sqlalchemy as sa


revision = "e05400000001"
down_revision = "e05300000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError("PATCH-054 requires exact e05300000002 predecessor")
    # All retained historical rows are UUID-addressed. Project is the existing integer-keyed aggregate.
    op.execute("""
    CREATE TABLE standard_identities (
      id uuid PRIMARY KEY, catalog_scope varchar(32) NOT NULL,
      organization_id uuid NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      issuer_key varchar(240) NOT NULL, issuer_display varchar(240) NOT NULL,
      designation varchar(240) NOT NULL, designation_key varchar(240) NOT NULL,
      title varchar(500) NOT NULL, language varchar(24), jurisdiction jsonb NOT NULL DEFAULT '{}'::jsonb,
      normalization_version varchar(64) NOT NULL, metadata_source_reference varchar(500) NOT NULL,
      identity_digest char(64) NOT NULL, predecessor_id uuid NULL UNIQUE REFERENCES standard_identities(id) ON DELETE RESTRICT,
      retired_from_new_selection boolean NOT NULL DEFAULT false, created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_standard_identity_scope CHECK (catalog_scope IN ('global_trusted','organization_private')),
      CONSTRAINT ck_standard_identity_scope_org CHECK ((catalog_scope='global_trusted' AND organization_id IS NULL) OR (catalog_scope='organization_private' AND organization_id IS NOT NULL)),
      CONSTRAINT ck_standard_identity_digest CHECK (identity_digest ~ '^[0-9a-f]{64}$'),
      CONSTRAINT uq_standard_identity_scope_key UNIQUE(catalog_scope,organization_id,issuer_key,designation_key)
    );
    CREATE INDEX ix_standard_identity_catalog ON standard_identities(catalog_scope,organization_id,issuer_key,designation_key);
    CREATE TABLE standard_editions (
      id uuid PRIMARY KEY, standard_identity_id uuid NOT NULL REFERENCES standard_identities(id) ON DELETE RESTRICT,
      edition_designation varchar(240) NOT NULL, edition_key varchar(240) NOT NULL, edition_disambiguator varchar(120) NOT NULL DEFAULT '',
      official_publication_identifier varchar(240), publication_date timestamptz, effective_date timestamptz, language varchar(24), jurisdiction jsonb NOT NULL DEFAULT '{}'::jsonb,
      metadata_source_reference varchar(500) NOT NULL, predecessor_id uuid NULL UNIQUE REFERENCES standard_editions(id) ON DELETE RESTRICT,
      edition_digest char(64) NOT NULL, created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_standard_edition_digest CHECK (edition_digest ~ '^[0-9a-f]{64}$'),
      CONSTRAINT uq_standard_edition_identity_key UNIQUE(standard_identity_id,edition_key,edition_disambiguator)
    );
    CREATE INDEX ix_standard_edition_identity ON standard_editions(standard_identity_id,created_at);
    CREATE TABLE standard_edition_standing_observations (
      id uuid PRIMARY KEY, standard_edition_id uuid NOT NULL REFERENCES standard_editions(id) ON DELETE RESTRICT,
      standing varchar(16) NOT NULL, superseded_by_edition_id uuid NULL REFERENCES standard_editions(id) ON DELETE RESTRICT,
      observed_effective_at timestamptz NOT NULL, source_reference varchar(500) NOT NULL, source_digest char(64) NOT NULL,
      actor_kind varchar(24) NOT NULL DEFAULT 'human', created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      predecessor_id uuid NULL UNIQUE REFERENCES standard_edition_standing_observations(id) ON DELETE RESTRICT,
      observation_digest char(64) NOT NULL, is_current boolean NOT NULL DEFAULT true, version bigint NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_standard_standing_value CHECK (standing IN ('current','superseded','withdrawn','unknown')),
      CONSTRAINT ck_standard_standing_successor CHECK ((standing='superseded' AND superseded_by_edition_id IS NOT NULL) OR (standing<>'superseded' AND superseded_by_edition_id IS NULL)),
      CONSTRAINT ck_standard_standing_digest CHECK (source_digest ~ '^[0-9a-f]{64}$' AND observation_digest ~ '^[0-9a-f]{64}$'),
      CONSTRAINT ck_standard_standing_version CHECK (version >= 1)
    );
    CREATE UNIQUE INDEX uq_standard_standing_current ON standard_edition_standing_observations(standard_edition_id) WHERE is_current;
    CREATE INDEX ix_standard_standing_edition ON standard_edition_standing_observations(standard_edition_id,observed_effective_at);
    CREATE TABLE standard_rights_bindings (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
      standard_edition_id uuid NOT NULL REFERENCES standard_editions(id) ON DELETE RESTRICT, source_provider_id varchar(80) NOT NULL,
      rights_basis varchar(40) NOT NULL, rights_status varchar(16) NOT NULL,
      allow_metadata_visibility boolean NOT NULL DEFAULT false, allow_content_storage boolean NOT NULL DEFAULT false,
      allow_indexing boolean NOT NULL DEFAULT false, allow_excerpt_display boolean NOT NULL DEFAULT false,
      allow_source_retrieval boolean NOT NULL DEFAULT false, allow_derived_retention boolean NOT NULL DEFAULT false, allow_derived_current_use boolean NOT NULL DEFAULT false,
      ai_processing_permission varchar(24) NOT NULL DEFAULT 'prohibited', approved_processor_policy_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
      effective_from timestamptz NOT NULL, effective_until timestamptz, rights_authority_reference varchar(500) NOT NULL, rights_authority_digest char(64) NOT NULL,
      predecessor_id uuid NULL UNIQUE REFERENCES standard_rights_bindings(id) ON DELETE RESTRICT, reason_code varchar(80) NOT NULL, reason varchar(500),
      is_current boolean NOT NULL DEFAULT true, version bigint NOT NULL DEFAULT 1, rights_digest char(64) NOT NULL,
      created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT ck_standard_rights_basis CHECK (rights_basis IN ('metadata_only','customer_supplied_declared','organization_license','open_distribution','internally_authored','unknown')),
      CONSTRAINT ck_standard_rights_status CHECK (rights_status IN ('active','expired','revoked','unknown')),
      CONSTRAINT ck_standard_rights_ai CHECK (ai_processing_permission IN ('prohibited','local_only','approved_processor')),
      CONSTRAINT ck_standard_rights_time CHECK (effective_until IS NULL OR effective_from < effective_until),
      CONSTRAINT ck_standard_rights_provider CHECK (btrim(source_provider_id)<>''),
      CONSTRAINT ck_standard_rights_digests CHECK (rights_authority_digest ~ '^[0-9a-f]{64}$' AND rights_digest ~ '^[0-9a-f]{64}$'),
      CONSTRAINT ck_standard_rights_policies CHECK (jsonb_typeof(approved_processor_policy_ids)='array' AND ((ai_processing_permission='approved_processor' AND jsonb_array_length(approved_processor_policy_ids)>0) OR (ai_processing_permission<>'approved_processor' AND jsonb_array_length(approved_processor_policy_ids)=0))),
      CONSTRAINT ck_standard_rights_fail_closed CHECK ((rights_basis NOT IN ('metadata_only','unknown') AND rights_status='active') OR NOT (allow_content_storage OR allow_indexing OR allow_excerpt_display OR allow_source_retrieval OR allow_derived_retention OR allow_derived_current_use))
    );
    CREATE UNIQUE INDEX uq_standard_rights_current ON standard_rights_bindings(organization_id,standard_edition_id,source_provider_id) WHERE is_current;
    CREATE INDEX ix_standard_rights_tuple ON standard_rights_bindings(organization_id,standard_edition_id,source_provider_id,created_at DESC);
    CREATE TABLE project_standard_applicability (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT, project_id integer NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
      standard_edition_id uuid NOT NULL REFERENCES standard_editions(id) ON DELETE RESTRICT, role varchar(32) NOT NULL, status varchar(24) NOT NULL DEFAULT 'declared',
      predecessor_id uuid NULL UNIQUE REFERENCES project_standard_applicability(id) ON DELETE RESTRICT, version bigint NOT NULL DEFAULT 1, created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE standard_source_snapshots (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT, project_id integer NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
      standard_identity_id uuid NOT NULL REFERENCES standard_identities(id) ON DELETE RESTRICT, standard_edition_id uuid NOT NULL REFERENCES standard_editions(id) ON DELETE RESTRICT,
      source_provider_id varchar(80) NOT NULL, adapter_policy_id varchar(80) NOT NULL, adapter_policy_version varchar(40) NOT NULL, source_location varchar(500) NOT NULL,
      availability_status varchar(32) NOT NULL, request_purpose varchar(80) NOT NULL, correlation_id uuid NOT NULL, object_key varchar(500), object_version varchar(240), provider_handle_ciphertext bytea,
      provider_handle_key_version varchar(40), provider_version_digest char(64), content_sha256 char(64), byte_count integer, media_type varchar(120),
      rights_binding_id uuid NOT NULL REFERENCES standard_rights_bindings(id) ON DELETE RESTRICT, rights_binding_version bigint NOT NULL, rights_digest char(64) NOT NULL,
      evaluated_capabilities jsonb NOT NULL, standing_observation_id uuid NOT NULL REFERENCES standard_edition_standing_observations(id) ON DELETE RESTRICT, standing_observation_digest char(64) NOT NULL,
      source_metadata_digest char(64) NOT NULL, integrity_verified boolean NOT NULL, integrity_verified_at timestamptz NOT NULL, snapshot_digest char(64) NOT NULL,
      retrieved_at timestamptz NOT NULL, retrieved_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE standard_knowledge_assertions (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT, project_id integer NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
      standard_edition_id uuid NOT NULL REFERENCES standard_editions(id) ON DELETE RESTRICT, source_snapshot_id uuid NOT NULL REFERENCES standard_source_snapshots(id) ON DELETE RESTRICT,
      source_location varchar(500) NOT NULL, source_content_digest char(64) NOT NULL, assertion_kind varchar(32) NOT NULL, canonical_representation jsonb NOT NULL,
      assertion_origin varchar(20) NOT NULL, extraction_method_id varchar(80) NOT NULL, extraction_method_version varchar(40) NOT NULL, extraction_method_digest char(64) NOT NULL,
      intelligence_run_id uuid NULL, assertion_digest char(64) NOT NULL, verification_status varchar(24) NOT NULL DEFAULT 'unverified', current_verification_event_id uuid NULL,
      rights_binding_id uuid NOT NULL REFERENCES standard_rights_bindings(id) ON DELETE RESTRICT, rights_binding_version bigint NOT NULL, rights_digest char(64) NOT NULL,
      retained_derived_use_eligible boolean NOT NULL DEFAULT false, evaluated_rights_revision bigint NOT NULL, predecessor_assertion_id uuid NULL REFERENCES standard_knowledge_assertions(id) ON DELETE RESTRICT,
      successor_assertion_id uuid NULL REFERENCES standard_knowledge_assertions(id) ON DELETE RESTRICT, version bigint NOT NULL DEFAULT 1, created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT uq_standard_assertion_unique UNIQUE(project_id,source_snapshot_id,source_location,assertion_kind,assertion_digest)
    );
    CREATE TABLE standard_assertion_verification_events (
      id uuid PRIMARY KEY, assertion_id uuid NOT NULL REFERENCES standard_knowledge_assertions(id) ON DELETE RESTRICT, event_kind varchar(32) NOT NULL, status varchar(24) NOT NULL,
      reason varchar(1000), source_rights_binding_id uuid NOT NULL REFERENCES standard_rights_bindings(id) ON DELETE RESTRICT, source_rights_binding_version bigint NOT NULL,
      source_rights_digest char(64) NOT NULL, assertion_digest char(64) NOT NULL, basis_human_verification_event_id uuid NULL REFERENCES standard_assertion_verification_events(id) ON DELETE RESTRICT,
      actor_kind varchar(24) NOT NULL, verified_by integer NULL REFERENCES users(id) ON DELETE RESTRICT, verified_at timestamptz NOT NULL DEFAULT now(), CONSTRAINT uq_standard_assertion_event UNIQUE(assertion_id,id)
    );
    CREATE TABLE standard_intelligence_runs (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT, project_id integer NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
      report_id uuid NULL, request_kind varchar(40) NOT NULL, purpose varchar(500) NOT NULL, correlation_id uuid NOT NULL, request_digest char(64) NOT NULL,
      deterministic_result jsonb NOT NULL, deterministic_result_digest char(64) NOT NULL, template_id varchar(80) NOT NULL, template_version varchar(40) NOT NULL, template_digest char(64) NOT NULL,
      processor_policy_id varchar(80) NOT NULL, provider_id varchar(80) NOT NULL, provider_model varchar(120) NOT NULL, provider_version varchar(80), result_status varchar(40), phase_status varchar(24) NOT NULL DEFAULT 'requested',
      call_count smallint NOT NULL DEFAULT 0, rights_manifest jsonb NOT NULL, authorized_handle_digest char(64) NOT NULL, input_digest char(64) NOT NULL, input_byte_count integer NOT NULL,
      advisory_output jsonb, output_digest char(64), suggestion_handle_digest char(64), failure_code varchar(64), created_by integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      created_at timestamptz NOT NULL DEFAULT now(), dispatched_at timestamptz, completed_at timestamptz, deadline_at timestamptz NOT NULL, version bigint NOT NULL DEFAULT 1,
      CONSTRAINT ck_standard_intelligence_call_count CHECK (call_count BETWEEN 0 AND 1), CONSTRAINT ck_standard_intelligence_input_limit CHECK (input_byte_count BETWEEN 0 AND 32768)
    );
    CREATE TABLE standards_idempotency (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT, actor_id integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      operation varchar(80) NOT NULL, idempotency_key varchar(160) NOT NULL, request_digest char(64) NOT NULL, state varchar(16) NOT NULL DEFAULT 'pending',
      resource_type varchar(80), resource_id uuid, response_status smallint, response_body jsonb, created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, expires_at timestamptz NOT NULL, version bigint NOT NULL DEFAULT 1,
      CONSTRAINT uq_standards_idempotency_key UNIQUE(organization_id,actor_id,operation,idempotency_key), CONSTRAINT ck_standards_idempotency_state CHECK (state IN ('pending','completed')),
      CONSTRAINT ck_standards_idempotency_expiry CHECK (expires_at > created_at), CONSTRAINT ck_standards_idempotency_digest CHECK (request_digest ~ '^[0-9a-f]{64}$')
    );
    CREATE INDEX ix_standards_idempotency_expiry ON standards_idempotency(expires_at);
    CREATE TABLE standards_outbox (
      id uuid PRIMARY KEY, organization_id uuid NULL REFERENCES organizations(id) ON DELETE RESTRICT, aggregate_type varchar(80) NOT NULL, aggregate_id uuid NOT NULL,
      event_id varchar(80) NOT NULL, event_version integer NOT NULL DEFAULT 1, payload jsonb NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz,
      CONSTRAINT uq_standards_outbox_event UNIQUE(aggregate_type,aggregate_id,event_id,event_version),
      CONSTRAINT ck_standards_outbox_event CHECK (event_id IN ('standards.identity.registered','standards.edition.registered','standards.edition.standing_observed','standards.rights.created','standards.rights.replaced','standards.rights.expired','standards.rights.revoked','standards.applicability.candidate_recorded','standards.applicability.declared','standards.applicability.retired','standards.source.retrieval_succeeded','standards.source.retrieval_unavailable','standards.source.snapshot_created','standards.assertion.created','standards.assertion.human_verified','standards.assertion.rejected','standards.assertion.stale','standards.intelligence.requested','standards.intelligence.completed','standards.intelligence.unavailable')),
      CONSTRAINT ck_standards_outbox_payload CHECK (jsonb_typeof(payload)='object' AND octet_length(payload::text)<=16384 AND event_version=1)
    );
    CREATE INDEX ix_standards_outbox_unpublished ON standards_outbox(published_at,occurred_at) WHERE published_at IS NULL;
    ALTER TABLE standard_knowledge_assertions ADD CONSTRAINT fk_standard_assertion_run FOREIGN KEY(intelligence_run_id) REFERENCES standard_intelligence_runs(id) ON DELETE RESTRICT;
    ALTER TABLE standard_knowledge_assertions ADD CONSTRAINT fk_standard_assertion_event FOREIGN KEY(current_verification_event_id) REFERENCES standard_assertion_verification_events(id) DEFERRABLE INITIALLY DEFERRED;
    """)
    op.execute("""
    CREATE FUNCTION standards_edition_limit_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN IF (SELECT count(*) FROM public.standard_editions WHERE standard_identity_id=NEW.standard_identity_id) >= 64 THEN RAISE EXCEPTION 'RESOURCE_LIMIT_EXCEEDED'; END IF; RETURN NEW; END $$;
    CREATE FUNCTION standards_immutable_history_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    BEGIN
      IF TG_TABLE_NAME='standard_editions' THEN RAISE EXCEPTION 'immutable edition'; END IF;
      IF TG_TABLE_NAME='standard_identities' THEN
        IF NEW.retired_from_new_selection AND NOT OLD.retired_from_new_selection AND NEW.id=OLD.id AND NEW.catalog_scope=OLD.catalog_scope AND NEW.organization_id IS NOT DISTINCT FROM OLD.organization_id AND NEW.issuer_key=OLD.issuer_key AND NEW.designation_key=OLD.designation_key AND NEW.identity_digest=OLD.identity_digest THEN RETURN NEW; END IF;
        RAISE EXCEPTION 'immutable identity';
      END IF;
      IF NEW.is_current=false AND OLD.is_current=true AND NEW.version=OLD.version+1 THEN RETURN NEW; END IF;
      RAISE EXCEPTION 'append-only history';
    END $$;
    CREATE TRIGGER tr_standard_edition_limit BEFORE INSERT ON standard_editions FOR EACH ROW EXECUTE FUNCTION standards_edition_limit_guard();
    CREATE TRIGGER tr_standard_identity_immutable BEFORE UPDATE ON standard_identities FOR EACH ROW EXECUTE FUNCTION standards_immutable_history_guard();
    CREATE TRIGGER tr_standard_edition_immutable BEFORE UPDATE OR DELETE ON standard_editions FOR EACH ROW EXECUTE FUNCTION standards_immutable_history_guard();
    CREATE TRIGGER tr_standard_standing_immutable BEFORE UPDATE OR DELETE ON standard_edition_standing_observations FOR EACH ROW EXECUTE FUNCTION standards_immutable_history_guard();
    CREATE TRIGGER tr_standard_rights_immutable BEFORE UPDATE OR DELETE ON standard_rights_bindings FOR EACH ROW EXECUTE FUNCTION standards_immutable_history_guard();
    REVOKE ALL ON FUNCTION standards_edition_limit_guard() FROM PUBLIC;
    REVOKE ALL ON FUNCTION standards_immutable_history_guard() FROM PUBLIC;
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON standard_identities,standard_editions,standard_edition_standing_observations,standard_rights_bindings,project_standard_applicability,standard_source_snapshots,standard_knowledge_assertions,standard_assertion_verification_events,standard_intelligence_runs,standards_idempotency,standards_outbox FROM satco_runtime;
        GRANT SELECT,INSERT ON standard_identities,standard_editions,standard_edition_standing_observations,standard_rights_bindings,standards_idempotency,standards_outbox TO satco_runtime;
        GRANT UPDATE(retired_from_new_selection) ON standard_identities TO satco_runtime;
        GRANT UPDATE(is_current,version) ON standard_edition_standing_observations,standard_rights_bindings TO satco_runtime;
        GRANT UPDATE(state,resource_type,resource_id,response_status,response_body,completed_at,version) ON standards_idempotency TO satco_runtime;
        GRANT UPDATE(published_at) ON standards_outbox TO satco_runtime;
        REVOKE DELETE ON standard_identities,standard_editions,standard_edition_standing_observations,standard_rights_bindings,standards_idempotency,standards_outbox FROM satco_runtime;
        REVOKE EXECUTE ON FUNCTION standards_edition_limit_guard(), standards_immutable_history_guard() FROM satco_runtime;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_registry_installer') THEN REVOKE ALL ON standard_identities,standard_editions,standard_edition_standing_observations,standard_rights_bindings,project_standard_applicability,standard_source_snapshots,standard_knowledge_assertions,standard_assertion_verification_events,standard_intelligence_runs,standards_idempotency,standards_outbox FROM satco_registry_installer; REVOKE EXECUTE ON FUNCTION standards_edition_limit_guard(), standards_immutable_history_guard() FROM satco_registry_installer; END IF;
    END $$;
    """)


def downgrade() -> None:
    bind = op.get_bind()
    tables = ("standard_identities","standard_editions","standard_edition_standing_observations","standard_rights_bindings","project_standard_applicability","standard_source_snapshots","standard_knowledge_assertions","standard_assertion_verification_events","standard_intelligence_runs","standards_idempotency","standards_outbox")
    used = bind.execute(sa.text("SELECT " + " OR ".join(f"EXISTS(SELECT 1 FROM {table})" for table in tables))).scalar_one()
    if used: raise RuntimeError("PATCH-054 downgrade is prohibited while retained standards data exists")
    op.execute("DROP TABLE standards_outbox, standards_idempotency, standard_assertion_verification_events, standard_knowledge_assertions, standard_intelligence_runs, standard_source_snapshots, project_standard_applicability, standard_rights_bindings, standard_edition_standing_observations, standard_editions, standard_identities CASCADE")
    op.execute("DROP FUNCTION standards_edition_limit_guard(); DROP FUNCTION standards_immutable_history_guard()")
