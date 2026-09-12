"""PATCH-054 protected provider-handle resolver correction.

Revision ID: e05400000003
Revises: e05400000002

This migration adds only the protected ciphertext-resolution function already
required by the accepted PATCH-054 persistence contract.  It is not Batch-2
retrieval, provider, assertion, or opaque-handle implementation.
"""

from alembic import op
import sqlalchemy as sa


revision = "e05400000003"
down_revision = "e05400000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() != down_revision:
        raise RuntimeError(
            "PATCH-054 provider-handle correction requires exact e05400000002 predecessor"
        )

    op.execute("""
    CREATE FUNCTION public.resolve_standard_provider_handle(
      requested_snapshot_id uuid,
      requested_organization_id uuid,
      requested_actor_id integer,
      requested_purpose text
    ) RETURNS bytea
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
      SELECT snapshot.provider_handle_ciphertext
      FROM public.standard_source_snapshots AS snapshot
      JOIN public.standard_rights_bindings AS rights
        ON rights.id = snapshot.rights_binding_id
       AND rights.organization_id = snapshot.organization_id
       AND rights.standard_edition_id = snapshot.standard_edition_id
       AND rights.source_provider_id = snapshot.source_provider_id
      JOIN public.user_organization_memberships AS membership
        ON membership.user_id = requested_actor_id
       AND membership.organization_id = snapshot.organization_id
      JOIN public.users AS actor
        ON actor.id = membership.user_id
      JOIN public.organizations AS organization
        ON organization.id = membership.organization_id
      WHERE snapshot.id = requested_snapshot_id
        AND snapshot.organization_id = requested_organization_id
        AND snapshot.availability_status = 'available'
        AND snapshot.integrity_verified
        AND snapshot.object_key IS NULL
        AND snapshot.object_version IS NULL
        AND snapshot.provider_handle_ciphertext IS NOT NULL
        AND snapshot.provider_handle_key_version IS NOT NULL
        AND snapshot.provider_version_digest IS NOT NULL
        AND membership.is_enabled
        AND actor.is_active
        AND organization.is_active
        AND rights.is_current
        AND rights.version = snapshot.rights_binding_version
        AND rights.rights_digest = snapshot.rights_digest
        AND rights.rights_status = 'active'
        AND rights.effective_from <= pg_catalog.now()
        AND (rights.effective_until IS NULL OR rights.effective_until > pg_catalog.now())
        AND (
          (requested_purpose = 'display'
           AND rights.allow_excerpt_display
           AND snapshot.evaluated_capabilities->>'excerpt_display' = 'true')
          OR
          (requested_purpose = 'retrieval'
           AND rights.allow_source_retrieval
           AND snapshot.evaluated_capabilities->>'source_retrieval' = 'true')
        )
    $$;

    ALTER FUNCTION public.resolve_standard_provider_handle(uuid,uuid,integer,text)
      OWNER TO satco;
    REVOKE ALL ON FUNCTION public.resolve_standard_provider_handle(uuid,uuid,integer,text)
      FROM PUBLIC;

    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_runtime') THEN
        GRANT EXECUTE ON FUNCTION public.resolve_standard_provider_handle(uuid,uuid,integer,text)
          TO satco_runtime;
      END IF;
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_registry_installer') THEN
        REVOKE ALL ON FUNCTION public.resolve_standard_provider_handle(uuid,uuid,integer,text)
          FROM satco_registry_installer;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    bind = op.get_bind()
    retained = bind.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM public.standard_source_snapshots "
        "WHERE provider_handle_ciphertext IS NOT NULL)"
    )).scalar_one()
    if retained:
        raise RuntimeError(
            "PATCH-054 provider-handle correction downgrade is prohibited while retained provider handles exist"
        )

    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='satco_runtime') THEN
        REVOKE ALL ON FUNCTION public.resolve_standard_provider_handle(uuid,uuid,integer,text)
          FROM satco_runtime;
      END IF;
    END $$;
    DROP FUNCTION public.resolve_standard_provider_handle(uuid,uuid,integer,text);
    """)
