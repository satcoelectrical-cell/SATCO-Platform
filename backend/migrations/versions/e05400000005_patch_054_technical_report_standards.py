"""PATCH-054 Batch-4 canonical Technical Report standards provenance.

Revision ID: e05400000005
Revises: e05400000004
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e05400000005"
down_revision = "e05400000004"
branch_labels = None
depends_on = None

_LOCATOR = """(source_type='universal_capture' AND capture_id IS NOT NULL AND capture_version IS NOT NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='evidence' AND evidence_id IS NOT NULL AND evidence_version IS NOT NULL AND capture_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_object' AND engineering_object_id IS NOT NULL AND engineering_object_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_relationship' AND engineering_relationship_id IS NOT NULL AND engineering_relationship_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='cross_discipline_assessment' AND cross_discipline_assessment_id IS NOT NULL AND cross_discipline_assessment_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='external_or_human' AND report_local_source_id IS NOT NULL AND external_reference IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='standard' AND standard_identity IS NOT NULL AND issuing_authority IS NOT NULL AND edition IS NOT NULL AND clause_or_location IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND context_id IS NULL) OR (source_type='contextual' AND context_id IS NOT NULL AND owning_context IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL)"""
_OWNER = """(source_type='universal_capture' AND source_class='canonical_material' AND owning_capability='universal_capture' AND is_material) OR (source_type='evidence' AND source_class='canonical_material' AND owning_capability='evidence' AND is_material) OR (source_type='engineering_object' AND source_class='canonical_material' AND owning_capability='engineering_object' AND is_material) OR (source_type='engineering_relationship' AND source_class='canonical_material' AND owning_capability='engineering_relationship' AND is_material) OR (source_type='cross_discipline_assessment' AND source_class='canonical_material' AND owning_capability='cross_discipline_assessment' AND is_material) OR (source_type='external_or_human' AND source_class='external_or_human_material' AND owning_capability IS NULL AND is_material) OR (source_type='standard' AND source_class='standards_material' AND owning_capability IS NULL AND is_material) OR (source_type='contextual' AND source_class='contextual_non_material' AND owning_capability IS NULL AND NOT is_material)"""
_HISTORY = """(source_class='canonical_material' AND ((canonical_snapshot_id IS NOT NULL AND minimal_historical_representation IS NULL) OR (canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL))) OR (source_class IN ('external_or_human_material','standards_material') AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL) OR (source_class='contextual_non_material' AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NULL AND integrity_algorithm IS NULL AND integrity_digest IS NULL)"""
_PATCH054_LOCATOR = """(source_type='universal_capture' AND capture_id IS NOT NULL AND capture_version IS NOT NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='evidence' AND evidence_id IS NOT NULL AND evidence_version IS NOT NULL AND capture_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_object' AND engineering_object_id IS NOT NULL AND engineering_object_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='engineering_relationship' AND engineering_relationship_id IS NOT NULL AND engineering_relationship_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='cross_discipline_assessment' AND cross_discipline_assessment_id IS NOT NULL AND cross_discipline_assessment_version IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='external_or_human' AND report_local_source_id IS NOT NULL AND external_reference IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND standard_identity IS NULL AND context_id IS NULL) OR (source_type='standard' AND (((standard_basis IS NULL AND standard_identity IS NOT NULL AND issuing_authority IS NOT NULL AND edition IS NOT NULL AND clause_or_location IS NOT NULL) OR (standard_basis IS NOT NULL AND standard_identity IS NULL AND issuing_authority IS NULL AND edition IS NULL AND clause_or_location IS NULL)) AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND context_id IS NULL)) OR (source_type='contextual' AND context_id IS NOT NULL AND owning_context IS NOT NULL AND capture_id IS NULL AND evidence_id IS NULL AND engineering_object_id IS NULL AND engineering_relationship_id IS NULL AND cross_discipline_assessment_id IS NULL AND report_local_source_id IS NULL AND standard_identity IS NULL)"""


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError("PATCH-054 report standards migration requires exact e05400000004 predecessor")
    op.execute("SET LOCAL lock_timeout='5s'")
    op.execute("SET LOCAL statement_timeout='60s'")
    for column in (
        sa.Column("standard_basis_schema_version", sa.String(40)),
        sa.Column("standard_basis", postgresql.JSONB()),
        sa.Column("standard_basis_digest", sa.String(64)),
        sa.Column("standards_basis_materiality", sa.String(24)),
        sa.Column("standard_edition_id", postgresql.UUID(as_uuid=True)),
        sa.Column("standard_source_snapshot_id", postgresql.UUID(as_uuid=True)),
        sa.Column("standard_assertion_id", postgresql.UUID(as_uuid=True)),
        sa.Column("standard_intelligence_run_id", postgresql.UUID(as_uuid=True)),
    ):
        op.add_column("technical_report_provenance_entries", column)
    for name, column, table in (
        ("fk_report_standard_basis_edition", "standard_edition_id", "standard_editions"),
        ("fk_report_standard_basis_snapshot", "standard_source_snapshot_id", "standard_source_snapshots"),
        ("fk_report_standard_basis_assertion", "standard_assertion_id", "standard_knowledge_assertions"),
        ("fk_report_standard_basis_intelligence", "standard_intelligence_run_id", "standard_intelligence_runs"),
    ):
        op.create_foreign_key(name, "technical_report_provenance_entries", table, [column], ["id"], ondelete="RESTRICT")
    for name in ("ck_technical_report_provenance_locator_shape", "ck_technical_report_provenance_owner_coherence", "ck_technical_report_provenance_historical_basis"):
        op.drop_constraint(name, "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_locator_shape", "technical_report_provenance_entries", _PATCH054_LOCATOR)
    op.create_check_constraint("ck_technical_report_provenance_owner_coherence", "technical_report_provenance_entries", _OWNER.replace("AND owning_capability IS NULL AND is_material) OR (source_type='contextual'", "AND owning_capability IS NULL AND (is_material OR standards_basis_materiality='reference_only')) OR (source_type='contextual'"))
    op.create_check_constraint("ck_technical_report_provenance_historical_basis", "technical_report_provenance_entries", _HISTORY.replace("(source_class IN ('external_or_human_material','standards_material') AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL)", "(source_class='external_or_human_material' AND canonical_snapshot_id IS NULL AND minimal_historical_representation IS NOT NULL) OR (source_class='standards_material' AND canonical_snapshot_id IS NULL AND ((standard_basis IS NULL AND minimal_historical_representation IS NOT NULL) OR (standard_basis IS NOT NULL AND minimal_historical_representation IS NULL)))"))
    op.create_check_constraint("ck_technical_report_standard_basis_exclusive", "technical_report_provenance_entries", "(source_type<>'standard' AND standard_basis_schema_version IS NULL AND standard_basis IS NULL AND standard_basis_digest IS NULL AND standards_basis_materiality IS NULL AND standard_edition_id IS NULL AND standard_source_snapshot_id IS NULL AND standard_assertion_id IS NULL AND standard_intelligence_run_id IS NULL) OR (source_type='standard' AND ((standard_basis IS NULL AND standard_basis_schema_version IS NULL AND standard_basis_digest IS NULL AND standards_basis_materiality IS NULL AND standard_edition_id IS NULL AND standard_source_snapshot_id IS NULL AND standard_assertion_id IS NULL AND standard_intelligence_run_id IS NULL) OR (standard_basis IS NOT NULL AND standard_basis_schema_version='standard_historical_basis_v1' AND standard_basis_digest ~ '^[0-9a-f]{64}$' AND standards_basis_materiality IN ('reference_only','material_support') AND standard_edition_id IS NOT NULL AND standard_source_snapshot_id IS NOT NULL)))")

    op.execute("ALTER FUNCTION public.technical_report_provenance_json_valid(jsonb) RENAME TO technical_report_provenance_pre054_json_valid")
    op.execute(r"""
    CREATE FUNCTION public.technical_report_standard_basis_valid(basis jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE keys text[]:=ARRAY['schema_version','basis_id','materiality','selection_rationale','standard_identity_id','issuer','designation','title','identity_digest','standard_edition_id','edition_designation','official_publication_identifier','publication_date','edition_digest','standing_observation_id','standing','standing_observation_digest','standing_acknowledged_by_id','standing_acknowledgement_rationale','source_snapshot_id','source_provider_id','source_location','immutable_provider_token','provider_version_digest','provider_handle_key_version','source_availability_status','byte_count','snapshot_digest','content_digest','rights_binding_id','rights_binding_version','rights_digest','rights_basis','rights_status','evaluated_capabilities','ai_processing_permission','rights_decided_at','applicability_id','applicability_revision','applicability_digest','applicability_status','applicability_role','assertion_id','assertion_kind','assertion_digest','assertion_origin','assertion_verification_status','assertion_verified_by_id','assertion_current_use_eligible','intelligence_interaction_id','intelligence_provider_id','intelligence_model','intelligence_template_digest','intelligence_input_digest','intelligence_output_digest','intelligence_processor_decision','selected_by_id','selected_at','report_revision_id','accepted_report_id','accepted_report_version','accepted_at','basis_digest']; uuid_pattern text:='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'; caps text[]:=ARRAY['content_storage','derived_current_use','derived_retention','excerpt_display','indexing','metadata_visibility','source_retrieval'];
    BEGIN RETURN jsonb_typeof(basis)='object' AND basis ?& keys AND (SELECT count(*) FROM jsonb_object_keys(basis))=cardinality(keys)
      AND basis->>'schema_version'='standard_historical_basis_v1' AND basis->>'basis_id'~uuid_pattern AND basis->>'standard_identity_id'~uuid_pattern AND basis->>'standard_edition_id'~uuid_pattern AND basis->>'standing_observation_id'~uuid_pattern AND basis->>'source_snapshot_id'~uuid_pattern AND basis->>'rights_binding_id'~uuid_pattern AND basis->>'report_revision_id'~uuid_pattern
      AND basis->>'materiality' IN ('reference_only','material_support') AND technical_report_text_valid(basis->>'selection_rationale',2000,false) AND technical_report_text_valid(basis->>'issuer',240,false) AND technical_report_text_valid(basis->>'designation',240,false) AND technical_report_text_valid(basis->>'title',500,false) AND technical_report_text_valid(basis->>'edition_designation',240,false) AND technical_report_text_valid(basis->>'source_provider_id',80,true) AND technical_report_text_valid(basis->>'source_location',500,true)
      AND (jsonb_typeof(basis->'official_publication_identifier')='null' OR (jsonb_typeof(basis->'official_publication_identifier')='string' AND technical_report_text_valid(basis->>'official_publication_identifier',240,true)))
      AND (jsonb_typeof(basis->'publication_date')='null' OR (jsonb_typeof(basis->'publication_date')='string' AND technical_report_canonical_utc_valid(basis->>'publication_date')))
      AND basis->>'identity_digest'~'^[0-9a-f]{64}$' AND basis->>'edition_digest'~'^[0-9a-f]{64}$' AND basis->>'standing_observation_digest'~'^[0-9a-f]{64}$' AND basis->>'snapshot_digest'~'^[0-9a-f]{64}$' AND basis->>'rights_digest'~'^[0-9a-f]{64}$' AND basis->>'basis_digest'~'^[0-9a-f]{64}$'
      AND basis->>'standing' IN ('current','superseded','withdrawn','unknown') AND basis->>'source_availability_status' IN ('available','temporarily_unavailable','permanently_unavailable','rights_restricted','integrity_failed') AND basis->>'rights_basis' IN ('metadata_only','customer_supplied_declared','organization_license','open_distribution','internally_authored','unknown') AND basis->>'rights_status' IN ('active','expired','revoked','unknown') AND basis->>'ai_processing_permission' IN ('prohibited','local_only','approved_processor')
      AND jsonb_typeof(basis->'rights_binding_version')='number' AND (basis->>'rights_binding_version')::numeric>=1 AND (basis->>'rights_binding_version')::numeric=trunc((basis->>'rights_binding_version')::numeric) AND jsonb_typeof(basis->'selected_by_id')='number' AND (basis->>'selected_by_id')::numeric>=1 AND (basis->>'selected_by_id')::numeric=trunc((basis->>'selected_by_id')::numeric) AND technical_report_canonical_utc_valid(basis->>'rights_decided_at') AND technical_report_canonical_utc_valid(basis->>'selected_at')
      AND jsonb_typeof(basis->'evaluated_capabilities')='object' AND basis->'evaluated_capabilities' ?& caps AND (SELECT count(*) FROM jsonb_object_keys(basis->'evaluated_capabilities'))=7 AND NOT EXISTS (SELECT 1 FROM jsonb_each(basis->'evaluated_capabilities') item WHERE jsonb_typeof(item.value)<>'boolean')
      AND ((jsonb_typeof(basis->'accepted_report_id')='null' AND jsonb_typeof(basis->'accepted_report_version')='null' AND jsonb_typeof(basis->'accepted_at')='null') OR (basis->>'accepted_report_id'~uuid_pattern AND jsonb_typeof(basis->'accepted_report_version')='number' AND (basis->>'accepted_report_version')::numeric>=1 AND (basis->>'accepted_report_version')::numeric=trunc((basis->>'accepted_report_version')::numeric) AND technical_report_canonical_utc_valid(basis->>'accepted_at')))
      AND ((jsonb_typeof(basis->'applicability_id')='null' AND jsonb_typeof(basis->'applicability_revision')='null' AND jsonb_typeof(basis->'applicability_digest')='null' AND jsonb_typeof(basis->'applicability_status')='null' AND jsonb_typeof(basis->'applicability_role')='null') OR (basis->>'applicability_id'~uuid_pattern AND jsonb_typeof(basis->'applicability_revision')='number' AND (basis->>'applicability_revision')::numeric>=1 AND (basis->>'applicability_revision')::numeric=trunc((basis->>'applicability_revision')::numeric) AND basis->>'applicability_digest'~'^[0-9a-f]{64}$' AND basis->>'applicability_status' IN ('declared_applicable','declared_not_applicable') AND basis->>'applicability_role' IN ('informative','design_basis','mandatory')))
      AND ((jsonb_typeof(basis->'assertion_id')='null' AND jsonb_typeof(basis->'assertion_kind')='null' AND jsonb_typeof(basis->'assertion_digest')='null' AND jsonb_typeof(basis->'assertion_origin')='null' AND jsonb_typeof(basis->'assertion_verification_status')='null' AND jsonb_typeof(basis->'assertion_verified_by_id')='null' AND jsonb_typeof(basis->'assertion_current_use_eligible')='null') OR (basis->>'assertion_id'~uuid_pattern AND basis->>'assertion_kind' IN ('requirement_statement','defined_term','numeric_constraint','cross_reference') AND basis->>'assertion_digest'~'^[0-9a-f]{64}$' AND basis->>'assertion_origin' IN ('human','deterministic') AND basis->>'assertion_verification_status' IN ('unverified','human_verified','rejected','stale') AND (jsonb_typeof(basis->'assertion_verified_by_id')='null' OR (jsonb_typeof(basis->'assertion_verified_by_id')='number' AND (basis->>'assertion_verified_by_id')::numeric>=1 AND (basis->>'assertion_verified_by_id')::numeric=trunc((basis->>'assertion_verified_by_id')::numeric))) AND jsonb_typeof(basis->'assertion_current_use_eligible')='boolean'))
      AND ((jsonb_typeof(basis->'intelligence_interaction_id')='null' AND jsonb_typeof(basis->'intelligence_provider_id')='null' AND jsonb_typeof(basis->'intelligence_model')='null' AND jsonb_typeof(basis->'intelligence_template_digest')='null' AND jsonb_typeof(basis->'intelligence_input_digest')='null' AND jsonb_typeof(basis->'intelligence_output_digest')='null' AND jsonb_typeof(basis->'intelligence_processor_decision')='null') OR (basis->>'intelligence_interaction_id'~uuid_pattern AND jsonb_typeof(basis->'intelligence_provider_id')='string' AND technical_report_text_valid(basis->>'intelligence_provider_id',80,true) AND jsonb_typeof(basis->'intelligence_model')='string' AND technical_report_text_valid(basis->>'intelligence_model',120,true) AND basis->>'intelligence_template_digest'~'^[0-9a-f]{64}$' AND basis->>'intelligence_input_digest'~'^[0-9a-f]{64}$' AND basis->>'intelligence_output_digest'~'^[0-9a-f]{64}$' AND jsonb_typeof(basis->'intelligence_processor_decision')='string' AND technical_report_text_valid(basis->>'intelligence_processor_decision',80,true)))
      AND ((jsonb_typeof(basis->'standing_acknowledged_by_id')='null' AND jsonb_typeof(basis->'standing_acknowledgement_rationale')='null') OR (jsonb_typeof(basis->'standing_acknowledged_by_id')='number' AND (basis->>'standing_acknowledged_by_id')::numeric>=1 AND (basis->>'standing_acknowledged_by_id')::numeric=trunc((basis->>'standing_acknowledged_by_id')::numeric) AND (basis->>'standing_acknowledged_by_id')::numeric=(basis->>'selected_by_id')::numeric AND jsonb_typeof(basis->'standing_acknowledgement_rationale')='string' AND technical_report_text_valid(basis->>'standing_acknowledgement_rationale',2000,false)))
      AND ((jsonb_typeof(basis->'immutable_provider_token')='null' AND jsonb_typeof(basis->'provider_version_digest')='null' AND jsonb_typeof(basis->'provider_handle_key_version')='null') OR (jsonb_typeof(basis->'immutable_provider_token')='string' AND octet_length(basis->>'immutable_provider_token') BETWEEN 1 AND 16384 AND basis->>'provider_version_digest'~'^[0-9a-f]{64}$' AND jsonb_typeof(basis->'provider_handle_key_version')='string' AND technical_report_text_valid(basis->>'provider_handle_key_version',40,true)))
      AND (jsonb_typeof(basis->'byte_count')='null' OR (jsonb_typeof(basis->'byte_count')='number' AND (basis->>'byte_count')::numeric BETWEEN 1 AND 8192 AND (basis->>'byte_count')::numeric=trunc((basis->>'byte_count')::numeric)))
      AND (jsonb_typeof(basis->'content_digest')='null' OR basis->>'content_digest'~'^[0-9a-f]{64}$')
      AND (basis->>'materiality'<>'material_support' OR (basis->>'source_availability_status'='available' AND jsonb_typeof(basis->'byte_count')='number' AND (basis->>'byte_count')::numeric BETWEEN 1 AND 8192 AND (basis->'evaluated_capabilities'->>'source_retrieval')::boolean AND (jsonb_typeof(basis->'content_digest')='string' OR jsonb_typeof(basis->'immutable_provider_token')='string')))
      AND (basis->>'materiality'<>'material_support' OR basis->>'rights_status'='active')
      AND (basis->>'materiality'<>'material_support' OR basis->>'standing'<>'unknown')
      AND (basis->>'materiality'<>'material_support' OR basis->>'standing' NOT IN ('superseded','withdrawn') OR (jsonb_typeof(basis->'applicability_id')='string' AND jsonb_typeof(basis->'standing_acknowledged_by_id')='number'))
      AND (basis->>'materiality'<>'material_support' OR jsonb_typeof(basis->'assertion_id')='null' OR (basis->>'assertion_verification_status'='human_verified' AND (basis->>'assertion_current_use_eligible')::boolean AND jsonb_typeof(basis->'assertion_verified_by_id')='number' AND (basis->'evaluated_capabilities'->>'derived_current_use')::boolean))
      AND encode(sha256(convert_to(technical_report_canonical_json(basis-'basis_digest'),'UTF8')),'hex')=basis->>'basis_digest'; EXCEPTION WHEN others THEN RETURN false; END $$
    """)
    op.execute(r"""
    CREATE FUNCTION public.technical_report_provenance_json_valid(entry jsonb) RETURNS boolean LANGUAGE plpgsql IMMUTABLE STRICT SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE keys text[]:=ARRAY['entry_id','ordinal','source_class','source_type','is_material','owning_capability','reliance_role','verification_status','availability_status','origin_attribution','limitations','locator','integrity_algorithm','integrity_digest']; uuid_pattern text:='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
    BEGIN
      IF entry->>'source_type'='standard' AND entry->'locator'->>'schema_version'='standard_historical_basis_v1' THEN
        IF jsonb_typeof(entry)<>'object' OR NOT entry ?& keys OR (SELECT count(*) FROM jsonb_object_keys(entry))<>cardinality(keys)
           OR entry->>'entry_id'!~uuid_pattern OR jsonb_typeof(entry->'ordinal')<>'number' OR (entry->>'ordinal')::numeric<0 OR (entry->>'ordinal')::numeric<>trunc((entry->>'ordinal')::numeric)
           OR entry->>'source_class'<>'standards_material' OR jsonb_typeof(entry->'is_material')<>'boolean' OR jsonb_typeof(entry->'owning_capability')<>'null'
           OR jsonb_typeof(entry->'reliance_role')<>'string' OR NOT technical_report_text_valid(entry->>'reliance_role',0,false)
           OR entry->>'verification_status' NOT IN ('verified','unverified') OR entry->>'availability_status' NOT IN ('available','unavailable')
           OR jsonb_typeof(entry->'origin_attribution')<>'string' OR NOT technical_report_text_valid(entry->>'origin_attribution',0,false)
           OR jsonb_typeof(entry->'limitations')<>'array'
           OR EXISTS (SELECT 1 FROM jsonb_array_elements(entry->'limitations') item WHERE jsonb_typeof(item)<>'string')
           OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(entry->'limitations') item WHERE NOT technical_report_text_valid(item,0,false))
        THEN RETURN false; END IF;
        RETURN technical_report_standard_basis_valid(entry->'locator')
          AND (entry->>'is_material')::boolean=((entry->'locator'->>'materiality')='material_support')
          AND ((entry->'locator'->>'materiality'='reference_only' AND jsonb_typeof(entry->'integrity_algorithm')='null' AND jsonb_typeof(entry->'integrity_digest')='null')
            OR (entry->'locator'->>'materiality'='material_support' AND entry->>'integrity_algorithm'='sha256' AND entry->>'integrity_digest'~'^[0-9a-f]{64}$' AND encode(sha256(convert_to(technical_report_canonical_json(entry->'locator'),'UTF8')),'hex')=entry->>'integrity_digest'));
      END IF;
      RETURN technical_report_provenance_pre054_json_valid(entry);
    EXCEPTION WHEN others THEN RETURN false; END
    $$
    """)
    op.execute(r"""
    CREATE FUNCTION public.technical_report_patch054_provenance_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE report_row public.technical_reports%ROWTYPE; basis jsonb; BEGIN
      IF (SELECT count(*) FROM public.technical_report_provenance_entries p WHERE p.technical_report_id=NEW.technical_report_id AND p.id<>NEW.id)>=32 THEN RAISE EXCEPTION 'Technical Report provenance limit exceeded' USING ERRCODE='23514'; END IF;
      IF NEW.source_type<>'standard' THEN RETURN NEW; END IF;
      SELECT * INTO report_row FROM public.technical_reports WHERE id=NEW.technical_report_id FOR UPDATE;
      IF NOT FOUND THEN RAISE EXCEPTION 'Technical Report standards basis is invalid' USING ERRCODE='23514'; END IF;
      IF NEW.standard_basis IS NULL THEN RAISE EXCEPTION 'new or updated legacy StandardLocator is prohibited' USING ERRCODE='23514'; END IF;
      basis:=NEW.standard_basis;
      IF NOT technical_report_standard_basis_valid(basis)
         OR NEW.standard_basis_schema_version<>basis->>'schema_version'
         OR NEW.standard_basis_digest<>basis->>'basis_digest'
         OR NEW.standards_basis_materiality<>basis->>'materiality'
         OR NEW.standard_edition_id::text<>basis->>'standard_edition_id'
         OR NEW.standard_source_snapshot_id::text<>basis->>'source_snapshot_id'
         OR NEW.standard_assertion_id::text IS DISTINCT FROM NULLIF(basis->>'assertion_id','')
         OR NEW.standard_intelligence_run_id::text IS DISTINCT FROM NULLIF(basis->>'intelligence_interaction_id','')
         OR report_row.project_id IS NULL
         OR basis->>'report_revision_id'<>report_row.draft_revision_id::text
         OR (basis->>'selected_by_id')::integer<>report_row.owner_id
         OR (basis->>'materiality'='material_support' AND basis->>'standing' IN ('superseded','withdrawn') AND (basis->>'standing_acknowledged_by_id')::integer<>report_row.owner_id)
         OR NEW.is_material<>((basis->>'materiality')='material_support')
         OR (NEW.is_material AND (NEW.integrity_algorithm<>'sha256' OR NEW.integrity_digest<>encode(sha256(convert_to(technical_report_canonical_json(basis),'UTF8')),'hex')))
         OR (NOT NEW.is_material AND (NEW.integrity_algorithm IS NOT NULL OR NEW.integrity_digest IS NOT NULL))
      THEN RAISE EXCEPTION 'Technical Report standards basis is invalid' USING ERRCODE='23514'; END IF;

      IF NOT EXISTS (
        SELECT 1 FROM public.standard_editions e
        JOIN public.standard_identities i ON i.id=e.standard_identity_id
        WHERE e.id=NEW.standard_edition_id
          AND i.id=(basis->>'standard_identity_id')::uuid
          AND (i.catalog_scope='global_trusted' OR i.organization_id=report_row.organization_id)
          AND i.retired_from_new_selection=false
          AND i.issuer_display=basis->>'issuer' AND i.designation=basis->>'designation'
          AND i.title=basis->>'title' AND i.identity_digest=basis->>'identity_digest'
          AND e.edition_designation=basis->>'edition_designation'
          AND e.official_publication_identifier IS NOT DISTINCT FROM basis->>'official_publication_identifier'
          AND ((e.publication_date IS NULL AND jsonb_typeof(basis->'publication_date')='null') OR e.publication_date=(basis->>'publication_date')::timestamptz)
          AND e.edition_digest=basis->>'edition_digest'
      ) THEN RAISE EXCEPTION 'Technical Report standards identity or edition is invalid' USING ERRCODE='23514'; END IF;

      IF NOT EXISTS (
        SELECT 1 FROM public.standard_edition_standing_observations standing
        WHERE standing.id=(basis->>'standing_observation_id')::uuid
          AND standing.standard_edition_id=NEW.standard_edition_id
          AND standing.is_current=true AND standing.standing=basis->>'standing'
          AND standing.observation_digest=basis->>'standing_observation_digest'
      ) THEN RAISE EXCEPTION 'Technical Report standards standing is invalid' USING ERRCODE='23514'; END IF;

      IF NOT EXISTS (
        SELECT 1 FROM public.standard_rights_bindings rights
        WHERE rights.id=(basis->>'rights_binding_id')::uuid
          AND rights.organization_id=report_row.organization_id
          AND rights.standard_edition_id=NEW.standard_edition_id
          AND rights.source_provider_id=basis->>'source_provider_id'
          AND rights.is_current=true AND rights.rights_status='active'
          AND rights.version=(basis->>'rights_binding_version')::bigint
          AND rights.rights_digest=basis->>'rights_digest'
          AND rights.rights_basis=basis->>'rights_basis'
          AND rights.rights_status=basis->>'rights_status'
          AND rights.ai_processing_permission=basis->>'ai_processing_permission'
          AND rights.effective_from<=CURRENT_TIMESTAMP
          AND (rights.effective_until IS NULL OR rights.effective_until>CURRENT_TIMESTAMP)
          AND rights.allow_metadata_visibility=(basis->'evaluated_capabilities'->>'metadata_visibility')::boolean
          AND rights.allow_content_storage=(basis->'evaluated_capabilities'->>'content_storage')::boolean
          AND rights.allow_indexing=(basis->'evaluated_capabilities'->>'indexing')::boolean
          AND rights.allow_excerpt_display=(basis->'evaluated_capabilities'->>'excerpt_display')::boolean
          AND rights.allow_source_retrieval=(basis->'evaluated_capabilities'->>'source_retrieval')::boolean
          AND rights.allow_derived_retention=(basis->'evaluated_capabilities'->>'derived_retention')::boolean
          AND rights.allow_derived_current_use=(basis->'evaluated_capabilities'->>'derived_current_use')::boolean
      ) THEN RAISE EXCEPTION 'Technical Report standards rights are invalid' USING ERRCODE='23514'; END IF;

      IF NOT EXISTS (
        SELECT 1 FROM public.standard_source_snapshots source
        WHERE source.id=NEW.standard_source_snapshot_id
          AND source.organization_id=report_row.organization_id AND source.project_id=report_row.project_id
          AND source.standard_identity_id=(basis->>'standard_identity_id')::uuid
          AND source.standard_edition_id=NEW.standard_edition_id
          AND source.source_provider_id=basis->>'source_provider_id'
          AND source.source_location=basis->>'source_location'
          AND source.availability_status=basis->>'source_availability_status'
          AND source.request_purpose=basis->>'materiality'
          AND source.snapshot_digest=basis->>'snapshot_digest'
          AND source.byte_count IS NOT DISTINCT FROM (basis->>'byte_count')::integer
          AND source.content_sha256 IS NOT DISTINCT FROM basis->>'content_digest'
          AND source.provider_version_digest IS NOT DISTINCT FROM basis->>'provider_version_digest'
          AND source.provider_handle_key_version IS NOT DISTINCT FROM basis->>'provider_handle_key_version'
          AND ((jsonb_typeof(basis->'immutable_provider_token')='null' AND source.provider_handle_ciphertext IS NULL)
               OR replace(encode(source.provider_handle_ciphertext,'base64'),E'\n','')=basis->>'immutable_provider_token')
          AND (basis->>'materiality'='reference_only' OR source.integrity_verified=true)
      ) THEN RAISE EXCEPTION 'Technical Report standards source is invalid' USING ERRCODE='23514'; END IF;

      IF jsonb_typeof(basis->'applicability_id')<>'null' AND NOT EXISTS (
        SELECT 1 FROM public.project_standard_applicability applicability
        WHERE applicability.id=(basis->>'applicability_id')::uuid
          AND applicability.organization_id=report_row.organization_id AND applicability.project_id=report_row.project_id
          AND applicability.standard_edition_id=NEW.standard_edition_id AND applicability.is_current=true
          AND applicability.revision=(basis->>'applicability_revision')::bigint
          AND applicability.applicability_digest=basis->>'applicability_digest'
          AND applicability.status=basis->>'applicability_status'
          AND applicability.applicability_role=basis->>'applicability_role'
      ) THEN RAISE EXCEPTION 'Technical Report standards applicability is invalid' USING ERRCODE='23514'; END IF;

      IF jsonb_typeof(basis->'assertion_id')<>'null' AND NOT EXISTS (
        SELECT 1 FROM public.standard_knowledge_assertions assertion
        JOIN public.standard_assertion_verification_events verification
          ON verification.id=assertion.current_verification_event_id AND verification.assertion_id=assertion.id
        WHERE assertion.id=(basis->>'assertion_id')::uuid
          AND assertion.organization_id=report_row.organization_id AND assertion.project_id=report_row.project_id
          AND assertion.standard_edition_id=NEW.standard_edition_id AND assertion.source_snapshot_id=NEW.standard_source_snapshot_id
          AND assertion.source_location=basis->>'source_location'
          AND assertion.assertion_kind=basis->>'assertion_kind' AND assertion.assertion_digest=basis->>'assertion_digest'
          AND assertion.assertion_origin=basis->>'assertion_origin'
          AND assertion.verification_status=basis->>'assertion_verification_status'
          AND assertion.retained_derived_use_eligible=(basis->>'assertion_current_use_eligible')::boolean
          AND assertion.rights_binding_id=(basis->>'rights_binding_id')::uuid
          AND assertion.rights_binding_version=(basis->>'rights_binding_version')::bigint
          AND assertion.rights_digest=basis->>'rights_digest'
          AND verification.verified_by IS NOT DISTINCT FROM (basis->>'assertion_verified_by_id')::integer
          AND verification.source_rights_binding_id=(basis->>'rights_binding_id')::uuid
          AND verification.source_rights_binding_version=(basis->>'rights_binding_version')::bigint
          AND verification.source_rights_digest=basis->>'rights_digest'
          AND verification.assertion_digest=basis->>'assertion_digest'
      ) THEN RAISE EXCEPTION 'Technical Report standards assertion is invalid' USING ERRCODE='23514'; END IF;

      IF jsonb_typeof(basis->'intelligence_interaction_id')<>'null' AND NOT EXISTS (
        SELECT 1 FROM public.standard_intelligence_runs run
        WHERE run.id=(basis->>'intelligence_interaction_id')::uuid
          AND run.organization_id=report_row.organization_id AND run.project_id=report_row.project_id
          AND run.provider_id=basis->>'intelligence_provider_id' AND run.provider_model=basis->>'intelligence_model'
          AND run.template_digest=basis->>'intelligence_template_digest'
          AND run.input_digest=basis->>'intelligence_input_digest'
          AND run.output_digest=basis->>'intelligence_output_digest'
          AND run.processor_policy_id=basis->>'intelligence_processor_decision'
      ) THEN RAISE EXCEPTION 'Technical Report standards intelligence is invalid' USING ERRCODE='23514'; END IF;

      IF (SELECT count(*) FROM public.technical_report_provenance_entries p WHERE p.technical_report_id=NEW.technical_report_id AND p.standard_basis IS NOT NULL AND p.id<>NEW.id)>=16 THEN RAISE EXCEPTION 'Technical Report standards provenance limit exceeded' USING ERRCODE='23514'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_technical_report_patch054_provenance_guard BEFORE INSERT OR UPDATE ON public.technical_report_provenance_entries FOR EACH ROW EXECUTE FUNCTION public.technical_report_patch054_provenance_guard();
    """)
    op.execute(r"""
    CREATE FUNCTION public.technical_report_patch054_root_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$ BEGIN
      IF NEW.lifecycle='accepted' AND (
        EXISTS (
          SELECT 1 FROM public.technical_report_provenance_entries p
          WHERE p.technical_report_id=NEW.id AND p.source_type='standard'
            AND p.standard_basis IS NULL
        )
        OR EXISTS (
          SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry
          WHERE entry->'locator'->>'schema_version'='standard_historical_basis_v1'
            AND (
              entry->'locator'->>'accepted_report_id'<>NEW.id::text
              OR (entry->'locator'->>'accepted_report_version')::integer<>NEW.version
              OR (entry->'locator'->>'accepted_at')::timestamptz<>NEW.accepted_at
              OR NOT EXISTS (
                SELECT 1 FROM public.technical_report_provenance_entries p
                WHERE p.technical_report_id=NEW.id
                  AND p.id::text=entry->>'entry_id'
                  AND p.standard_basis=entry->'locator'
                  AND p.standard_basis_digest=entry->'locator'->>'basis_digest'
              )
            )
        )
        OR EXISTS (
          SELECT 1 FROM public.technical_report_provenance_entries p
          WHERE p.technical_report_id=NEW.id AND p.standard_basis IS NOT NULL
            AND NOT EXISTS (
              SELECT 1 FROM jsonb_array_elements(NEW.accepted_snapshot->'provenance') entry
              WHERE entry->>'entry_id'=p.id::text
                AND entry->'locator'=p.standard_basis
                AND entry->'locator'->>'basis_digest'=p.standard_basis_digest
            )
        )
      ) THEN
        RAISE EXCEPTION 'accepted Technical Report standards basis is invalid' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_technical_report_patch054_root_guard BEFORE INSERT OR UPDATE ON public.technical_reports FOR EACH ROW EXECUTE FUNCTION public.technical_report_patch054_root_guard();
    CREATE FUNCTION public.technical_report_patch054_final_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$ DECLARE report_row public.technical_reports%ROWTYPE; basis jsonb; BEGIN IF NEW.standard_basis IS NULL THEN RETURN NEW; END IF; basis:=NEW.standard_basis; SELECT * INTO report_row FROM public.technical_reports WHERE id=NEW.technical_report_id; IF (report_row.lifecycle='draft' AND NOT (jsonb_typeof(basis->'accepted_report_id')='null' AND jsonb_typeof(basis->'accepted_report_version')='null' AND jsonb_typeof(basis->'accepted_at')='null')) OR (report_row.lifecycle='accepted' AND (basis->>'accepted_report_id'<>report_row.id::text OR (basis->>'accepted_report_version')::integer<>report_row.version OR (basis->>'accepted_at')::timestamptz<>report_row.accepted_at)) THEN RAISE EXCEPTION 'standards basis accepted_at forgery' USING ERRCODE='23514'; END IF; RETURN NEW; END $$;
    CREATE CONSTRAINT TRIGGER trg_technical_report_patch054_final_guard AFTER INSERT OR UPDATE ON public.technical_report_provenance_entries DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.technical_report_patch054_final_guard();
    """)
    for function in ("technical_report_standard_basis_valid(jsonb)", "technical_report_provenance_json_valid(jsonb)", "technical_report_patch054_provenance_guard()", "technical_report_patch054_root_guard()", "technical_report_patch054_final_guard()"):
        op.execute(f"ALTER FUNCTION public.{function} OWNER TO satco")
        op.execute(f"REVOKE ALL ON FUNCTION public.{function} FROM PUBLIC")
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_runtime') THEN REVOKE EXECUTE ON FUNCTION public.technical_report_standard_basis_valid(jsonb), public.technical_report_provenance_json_valid(jsonb), public.technical_report_patch054_provenance_guard(), public.technical_report_patch054_root_guard(), public.technical_report_patch054_final_guard() FROM satco_runtime; END IF; IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='satco_registry_installer') THEN REVOKE EXECUTE ON FUNCTION public.technical_report_standard_basis_valid(jsonb), public.technical_report_provenance_json_valid(jsonb), public.technical_report_patch054_provenance_guard(), public.technical_report_patch054_root_guard(), public.technical_report_patch054_final_guard() FROM satco_registry_installer; END IF; END $$""")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS(SELECT 1 FROM public.technical_report_provenance_entries WHERE standard_basis IS NOT NULL)")).scalar_one():
        raise RuntimeError("PATCH-054 report standards downgrade is prohibited while retained basis history exists")
    op.execute("DROP TRIGGER trg_technical_report_patch054_final_guard ON public.technical_report_provenance_entries; DROP TRIGGER trg_technical_report_patch054_root_guard ON public.technical_reports; DROP TRIGGER trg_technical_report_patch054_provenance_guard ON public.technical_report_provenance_entries; DROP FUNCTION public.technical_report_patch054_final_guard(); DROP FUNCTION public.technical_report_patch054_root_guard(); DROP FUNCTION public.technical_report_patch054_provenance_guard(); DROP FUNCTION public.technical_report_provenance_json_valid(jsonb); ALTER FUNCTION public.technical_report_provenance_pre054_json_valid(jsonb) RENAME TO technical_report_provenance_json_valid; DROP FUNCTION public.technical_report_standard_basis_valid(jsonb)")
    op.drop_constraint("ck_technical_report_standard_basis_exclusive", "technical_report_provenance_entries", type_="check")
    for name in ("ck_technical_report_provenance_locator_shape", "ck_technical_report_provenance_owner_coherence", "ck_technical_report_provenance_historical_basis"):
        op.drop_constraint(name, "technical_report_provenance_entries", type_="check")
    op.create_check_constraint("ck_technical_report_provenance_locator_shape", "technical_report_provenance_entries", _LOCATOR)
    op.create_check_constraint("ck_technical_report_provenance_owner_coherence", "technical_report_provenance_entries", _OWNER)
    op.create_check_constraint("ck_technical_report_provenance_historical_basis", "technical_report_provenance_entries", _HISTORY)
    for name in ("fk_report_standard_basis_intelligence", "fk_report_standard_basis_assertion", "fk_report_standard_basis_snapshot", "fk_report_standard_basis_edition"):
        op.drop_constraint(name, "technical_report_provenance_entries", type_="foreignkey")
    for name in ("standard_intelligence_run_id", "standard_assertion_id", "standard_source_snapshot_id", "standard_edition_id", "standards_basis_materiality", "standard_basis_digest", "standard_basis", "standard_basis_schema_version"):
        op.drop_column("technical_report_provenance_entries", name)
