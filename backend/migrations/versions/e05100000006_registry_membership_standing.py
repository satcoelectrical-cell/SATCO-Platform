"""PATCH-051 Registry-membership standing ownership correction.

Revision ID: e05100000006
Revises: e05100000005
"""

import sqlalchemy as sa
from alembic import op


revision = "e05100000006"
down_revision = "e05100000005"
branch_labels = None
depends_on = None


_DESCRIPTOR_TABLE = "discipline_package_descriptors"
_MEMBERSHIP_TABLE = "discipline_package_registry_memberships"
_MEMBERSHIP_INDEX = "ix_dp_membership_release_standing"
_PROVENANCE_TABLES = (
    "discipline_package_registry_releases",
    "discipline_package_descriptors",
    "discipline_package_registry_memberships",
    "discipline_package_compatibility_profiles",
    "discipline_package_registry_profile_memberships",
    "discipline_package_compatibility_members",
    "organization_package_configuration_heads",
    "organization_package_selections",
    "project_package_configuration_revisions",
    "project_package_configuration_selections",
    "project_package_configuration_heads",
    "package_configuration_audit_events",
)


def _assert_empty_unreferenced_state() -> None:
    """Refuse any legacy state whose immutable provenance would need rewrite."""

    connection = op.get_bind()
    for table_name in _PROVENANCE_TABLES:
        has_rows = connection.execute(
            sa.text(f'SELECT EXISTS (SELECT 1 FROM "{table_name}" LIMIT 1)')
        ).scalar_one()
        if has_rows:
            raise RuntimeError(
                "PATCH-051 M6 requires an empty, unreferenced Registry state"
            )
    # M3's Workspace binding can retain an exact package reference without a
    # new Registry table row.  It is Registry provenance too: do not permit a
    # legacy bound Workspace to cross this descriptor-identity correction.
    workspace_references = connection.execute(sa.text("""
SELECT EXISTS (
  SELECT 1
  FROM engineering_workspaces
  WHERE bound_package_key IS NOT NULL
     OR bound_project_configuration_revision IS NOT NULL
)
""")).scalar_one()
    if workspace_references:
        raise RuntimeError(
            "PATCH-051 M6 requires an empty, unreferenced Registry state"
        )


def _assert_membership_standing_contract() -> None:
    connection = op.get_bind()
    column_valid = connection.execute(sa.text("""
SELECT EXISTS (
  SELECT 1
  FROM information_schema.columns
  WHERE table_schema = current_schema()
    AND table_name = 'discipline_package_registry_memberships'
    AND column_name = 'standing'
    AND is_nullable = 'NO'
    AND data_type = 'character varying'
)
""")).scalar_one()
    constraint_definition = connection.execute(sa.text("""
SELECT pg_get_constraintdef(constraint_row.oid)
FROM pg_constraint AS constraint_row
JOIN pg_class AS table_row ON table_row.oid = constraint_row.conrelid
JOIN pg_namespace AS namespace_row ON namespace_row.oid = table_row.relnamespace
WHERE namespace_row.nspname = current_schema()
  AND table_row.relname = 'discipline_package_registry_memberships'
  AND constraint_row.conname = 'ck_dp_membership_standing'
  AND constraint_row.contype = 'c'
""")).scalar_one_or_none()
    immutable_trigger_valid = connection.execute(sa.text("""
SELECT EXISTS (
  SELECT 1
  FROM pg_trigger AS trigger_row
  JOIN pg_class AS table_row ON table_row.oid = trigger_row.tgrelid
  JOIN pg_namespace AS namespace_row ON namespace_row.oid = table_row.relnamespace
  JOIN pg_proc AS function_row ON function_row.oid = trigger_row.tgfoid
  WHERE namespace_row.nspname = current_schema()
    AND table_row.relname = 'discipline_package_registry_memberships'
    AND trigger_row.tgname = 'trg_dp_memberships_immutable'
    AND NOT trigger_row.tgisinternal
    AND trigger_row.tgenabled IN ('O', 'A')
    AND function_row.proname = 'satco_dp_immutable'
)
""")).scalar_one()
    if (
        not column_valid
        or constraint_definition is None
        or "executable_supported" not in constraint_definition
        or "historical_read_only" not in constraint_definition
        or not immutable_trigger_valid
    ):
        raise RuntimeError("PATCH-051 M6 membership standing contract is invalid")


def _assert_descriptor_standing(*, expected: bool) -> None:
    present = op.get_bind().execute(sa.text("""
SELECT EXISTS (
  SELECT 1
  FROM information_schema.columns
  WHERE table_schema = current_schema()
    AND table_name = 'discipline_package_descriptors'
    AND column_name = 'standing'
)
""")).scalar_one()
    if present is not expected:
        raise RuntimeError("PATCH-051 M6 descriptor standing state is invalid")


def upgrade() -> None:
    _assert_empty_unreferenced_state()
    _assert_membership_standing_contract()
    _assert_descriptor_standing(expected=True)
    op.create_index(
        _MEMBERSHIP_INDEX,
        _MEMBERSHIP_TABLE,
        ["registry_digest", "standing", "package_key", "package_version"],
    )
    op.drop_column(_DESCRIPTOR_TABLE, "standing")


def downgrade() -> None:
    _assert_empty_unreferenced_state()
    _assert_membership_standing_contract()
    _assert_descriptor_standing(expected=False)
    op.drop_index(_MEMBERSHIP_INDEX, table_name=_MEMBERSHIP_TABLE)
    op.add_column(
        _DESCRIPTOR_TABLE,
        sa.Column("standing", sa.String(length=40), nullable=False),
    )
