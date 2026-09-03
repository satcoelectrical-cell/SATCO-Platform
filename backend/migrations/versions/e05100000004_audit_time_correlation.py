"""PATCH-051 truthful Audit time/correlation corrective migration.

Revision ID: e05100000004
Revises: e05100000003
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e05100000004"
down_revision = "e05100000003"
branch_labels = None
depends_on = None


_AUDIT_TABLE = "package_configuration_audit_events"


def upgrade() -> None:
    # Existing rows cannot truthfully acquire an event time.  Nullable columns
    # preserve that uncertainty; the insert guard below makes it impossible for
    # a post-cutover row to create a new unknown-time/correlation population.
    op.add_column(_AUDIT_TABLE, sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(_AUDIT_TABLE, sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True))

    bind = op.get_bind()
    bind.execute(sa.text("LOCK TABLE package_configuration_audit_events IN ACCESS EXCLUSIVE MODE"))
    bind.execute(sa.text("ALTER TABLE package_configuration_audit_events DISABLE TRIGGER trg_dp_audit_immutable"))
    try:
        # Only canonical UUID text already stored in minimized durable metadata
        # is copied.  Anything absent/malformed remains explicitly unknown.
        bind.execute(sa.text("""
UPDATE package_configuration_audit_events
SET correlation_id = CASE
    WHEN jsonb_typeof(metadata_json->'correlation_id') = 'string'
     AND metadata_json->>'correlation_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    THEN (metadata_json->>'correlation_id')::uuid
    ELSE NULL
END
"""))
    finally:
        bind.execute(sa.text("ALTER TABLE package_configuration_audit_events ENABLE TRIGGER trg_dp_audit_immutable"))

    op.drop_index("ix_dp_audit_organization", table_name=_AUDIT_TABLE)
    op.execute("""
CREATE INDEX ix_dp_audit_organization_occurred_event
ON package_configuration_audit_events
(organization_id, occurred_at DESC, event_id DESC)
""")
    op.execute("""
CREATE INDEX ix_dp_audit_organization_project_occurred_event
ON package_configuration_audit_events
(organization_id, project_id, occurred_at DESC, event_id DESC)
""")
    op.execute("""
CREATE FUNCTION satco_dp_audit_current_insert_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.occurred_at IS NULL OR NEW.correlation_id IS NULL THEN
    RAISE EXCEPTION 'PATCH-051 current Audit requires occurred_at and correlation_id';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_dp_audit_current_insert_guard
BEFORE INSERT ON package_configuration_audit_events
FOR EACH ROW EXECUTE FUNCTION satco_dp_audit_current_insert_guard();
REVOKE EXECUTE ON FUNCTION satco_dp_audit_current_insert_guard()
FROM PUBLIC, satco_runtime, satco_registry_installer;
""")


def downgrade() -> None:
    bind = op.get_bind()
    # Historical metadata remains intact, but a current authoritative timestamp
    # cannot be discarded.  Recovery after new use is therefore forward-only.
    if bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM package_configuration_audit_events WHERE occurred_at IS NOT NULL)"
    )).scalar_one():
        raise RuntimeError("PATCH-051 M4 downgrade is forbidden after current Audit use; recover forward")
    op.execute("DROP FUNCTION IF EXISTS satco_dp_audit_current_insert_guard() CASCADE")
    op.drop_index("ix_dp_audit_organization_project_occurred_event", table_name=_AUDIT_TABLE)
    op.drop_index("ix_dp_audit_organization_occurred_event", table_name=_AUDIT_TABLE)
    op.create_index("ix_dp_audit_organization", _AUDIT_TABLE, ["organization_id"])
    op.drop_column(_AUDIT_TABLE, "correlation_id")
    op.drop_column(_AUDIT_TABLE, "occurred_at")
