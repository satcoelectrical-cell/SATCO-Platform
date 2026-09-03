"""PATCH-051 Audit physical NULLS LAST index correction.

Revision ID: e05100000005
Revises: e05100000004
"""

from alembic import op


revision = "e05100000005"
down_revision = "e05100000004"
branch_labels = None
depends_on = None


_AUDIT_TABLE = "package_configuration_audit_events"


def upgrade() -> None:
    # M4's source used PostgreSQL's descending default (NULLS FIRST).  Replace
    # only the two physical access paths so fresh and already-divergent M4
    # states converge on the accepted NULLS LAST contract.
    op.drop_index("ix_dp_audit_organization_project_occurred_event", table_name=_AUDIT_TABLE)
    op.drop_index("ix_dp_audit_organization_occurred_event", table_name=_AUDIT_TABLE)
    op.execute("""
CREATE INDEX ix_dp_audit_organization_occurred_event
ON package_configuration_audit_events
(organization_id, occurred_at DESC NULLS LAST, event_id DESC)
""")
    op.execute("""
CREATE INDEX ix_dp_audit_organization_project_occurred_event
ON package_configuration_audit_events
(organization_id, project_id, occurred_at DESC NULLS LAST, event_id DESC)
""")


def downgrade() -> None:
    # Restore the exact historical M4 source definition.  This migration only
    # changes physical indexes; it never changes Audit rows or M4 enforcement.
    op.drop_index("ix_dp_audit_organization_project_occurred_event", table_name=_AUDIT_TABLE)
    op.drop_index("ix_dp_audit_organization_occurred_event", table_name=_AUDIT_TABLE)
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
