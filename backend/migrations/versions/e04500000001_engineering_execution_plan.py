"""Engineering Execution Plan, Activities and Milestones.

Revision ID: e04500000001
Revises: e04400000001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e04500000001"
down_revision = "e04400000001"
branch_labels = None
depends_on = None

STANDINGS = "'planned','ready','in_progress','blocked','completed','cancelled'"


def upgrade():
    op.create_table(
        "engineering_execution_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("established_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("established_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_execution_plan_version"),
    )
    op.create_index("ix_execution_plan_scope", "engineering_execution_plans", ["organization_id", "project_id"])
    op.create_table(
        "engineering_execution_plan_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("config_json", postgresql.JSONB(), nullable=False),
        sa.Column("config_digest", sa.String(64), nullable=False),
        sa.Column("rationale", sa.String(2000), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision_number >= 1", name="ck_execution_plan_revision_number"),
        sa.CheckConstraint("length(config_digest)=64", name="ck_execution_plan_revision_digest"),
        sa.CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 2000", name="ck_execution_plan_revision_rationale"),
        sa.UniqueConstraint("plan_id", "revision_number", name="uq_execution_plan_revision_number"),
    )
    op.create_index("ix_execution_plan_revision_order", "engineering_execution_plan_revisions", ["organization_id", "plan_id", "revision_number"])
    op.create_table(
        "engineering_execution_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(2000)),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("engineering_workspaces.id", ondelete="RESTRICT")),
        sa.Column("responsible_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("target_date", sa.Date()),
        sa.Column("completion_basis", sa.String(2000), nullable=False),
        sa.Column("standing", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("blocker_rationale", sa.String(2000)),
        sa.Column("blocked_return_standing", sa.String(32)),
        sa.Column("completion_rationale", sa.String(2000)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_execution_activity_title"),
        sa.CheckConstraint("description IS NULL OR length(btrim(description)) BETWEEN 1 AND 2000", name="ck_execution_activity_description"),
        sa.CheckConstraint("length(btrim(completion_basis)) BETWEEN 1 AND 2000", name="ck_execution_activity_completion_basis"),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 199", name="ck_execution_activity_ordinal"),
        sa.CheckConstraint(f"standing IN ({STANDINGS})", name="ck_execution_activity_standing"),
        sa.CheckConstraint("version >= 1", name="ck_execution_activity_version"),
        sa.CheckConstraint("blocker_rationale IS NULL OR length(btrim(blocker_rationale)) BETWEEN 1 AND 2000", name="ck_execution_activity_blocker"),
        sa.CheckConstraint("completion_rationale IS NULL OR length(btrim(completion_rationale)) BETWEEN 1 AND 2000", name="ck_execution_activity_completion_rationale"),
        sa.CheckConstraint("(standing='blocked') = (blocker_rationale IS NOT NULL)", name="ck_execution_activity_blocker_pair"),
        sa.CheckConstraint("(standing='blocked' AND blocked_return_standing IN ('planned','ready','in_progress')) OR (standing<>'blocked' AND blocked_return_standing IS NULL)", name="ck_execution_activity_blocked_return_pair"),
        sa.CheckConstraint("standing <> 'completed' OR completion_rationale IS NOT NULL", name="ck_execution_activity_completion_pair"),
        sa.UniqueConstraint("plan_id", "ordinal", name="uq_execution_activity_ordinal", deferrable=True, initially="DEFERRED"),
    )
    op.create_index("ix_execution_activity_order", "engineering_execution_activities", ["organization_id", "project_id", "plan_id", "ordinal", "id"])
    op.create_index("uq_execution_activity_title", "engineering_execution_activities", ["plan_id", sa.text("lower(btrim(title))")], unique=True)
    op.create_table(
        "engineering_execution_activity_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("from_standing", sa.String(32)), sa.Column("to_standing", sa.String(32), nullable=False),
        sa.Column("activity_version", sa.Integer(), nullable=False), sa.Column("rationale", sa.String(2000), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"from_standing IS NULL OR from_standing IN ({STANDINGS})", name="ck_execution_activity_history_from"),
        sa.CheckConstraint(f"to_standing IN ({STANDINGS})", name="ck_execution_activity_history_to"),
        sa.CheckConstraint("activity_version >= 1", name="ck_execution_activity_history_version"),
        sa.CheckConstraint("length(btrim(rationale)) BETWEEN 1 AND 2000", name="ck_execution_activity_history_rationale"),
        sa.UniqueConstraint("activity_id", "activity_version", name="uq_execution_activity_history_version"),
    )
    op.create_index("ix_execution_activity_history_order", "engineering_execution_activity_history", ["organization_id", "activity_id", "transitioned_at", "id"])
    op.create_table(
        "engineering_execution_milestones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False), sa.Column("completion_basis", sa.String(2000), nullable=False),
        sa.Column("target_date", sa.Date()), sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(title)) BETWEEN 1 AND 200", name="ck_execution_milestone_title"),
        sa.CheckConstraint("length(btrim(completion_basis)) BETWEEN 1 AND 2000", name="ck_execution_milestone_basis"),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 49", name="ck_execution_milestone_ordinal"),
        sa.UniqueConstraint("plan_id", "ordinal", name="uq_execution_milestone_ordinal", deferrable=True, initially="DEFERRED"),
    )
    op.create_index("ix_execution_milestone_order", "engineering_execution_milestones", ["organization_id", "project_id", "plan_id", "ordinal", "id"])
    op.create_index("uq_execution_milestone_title", "engineering_execution_milestones", ["plan_id", sa.text("lower(btrim(title))")], unique=True)
    op.create_table(
        "engineering_execution_milestone_activities",
        sa.Column("milestone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_milestones.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("ordinal BETWEEN 0 AND 199", name="ck_execution_milestone_activity_ordinal"),
        sa.UniqueConstraint("milestone_id", "ordinal", name="uq_execution_milestone_activity_ordinal"),
    )
    op.create_table(
        "engineering_execution_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("predecessor_activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("dependent_activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engineering_execution_activities.id", ondelete="RESTRICT"), nullable=False),
        sa.CheckConstraint("predecessor_activity_id <> dependent_activity_id", name="ck_execution_dependency_not_self"),
        sa.UniqueConstraint("plan_id", "predecessor_activity_id", "dependent_activity_id", name="uq_execution_dependency_edge"),
    )
    op.create_index("ix_execution_dependency_dependent", "engineering_execution_dependencies", ["organization_id", "plan_id", "dependent_activity_id"])
    op.create_table(
        "engineering_execution_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False), sa.Column("idempotency_key", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False), sa.Column("replay_json", postgresql.JSONB(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(fingerprint)=64", name="ck_execution_idempotency_fingerprint"),
        sa.CheckConstraint("length(replay_json::text)<=1024", name="ck_execution_idempotency_replay_size"),
        sa.CheckConstraint("jsonb_typeof(replay_json)='object' AND replay_json->>'schema'='execution.idempotency.v1' AND replay_json->>'operation'=operation AND jsonb_typeof(replay_json->'result')='object' AND replay_json->'result'->>'outcome'='success' AND NOT (replay_json ?| ARRAY['rationale','description','completion_basis','blocker_rationale']) AND NOT ((replay_json->'result') ?| ARRAY['rationale','description','completion_basis','blocker_rationale'])", name="ck_execution_idempotency_shape"),
        sa.CheckConstraint("operation IN ('establish_plan','create_activity','update_activity','transition_activity','replace_dependencies','create_milestone','update_milestone')", name="ck_execution_idempotency_operation"),
        sa.UniqueConstraint("organization_id", "actor_id", "operation", "idempotency_key", name="uq_execution_idempotency_key"),
    )
    op.execute(f"""
    CREATE FUNCTION satco_execution_plan_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE parent_org uuid; parent_status text;
    BEGIN
      SELECT organization_id,status INTO parent_org,parent_status FROM projects WHERE id=NEW.project_id FOR SHARE;
      IF parent_org IS NULL OR NEW.organization_id IS DISTINCT FROM parent_org THEN RAISE EXCEPTION 'execution plan parent scope mismatch'; END IF;
      IF parent_status IN ('completed','cancelled') THEN RAISE EXCEPTION 'execution plan parent terminal'; END IF;
      IF NOT EXISTS (SELECT 1 FROM project_foundations f WHERE f.project_id=NEW.project_id AND f.organization_id=NEW.organization_id) THEN RAISE EXCEPTION 'execution plan requires foundation'; END IF;
      IF TG_OP='UPDATE' AND (NEW.id IS DISTINCT FROM OLD.id OR NEW.project_id IS DISTINCT FROM OLD.project_id OR NEW.organization_id IS DISTINCT FROM OLD.organization_id OR NEW.established_by_id IS DISTINCT FROM OLD.established_by_id OR NEW.established_at IS DISTINCT FROM OLD.established_at OR NEW.version <> OLD.version + 1) THEN RAISE EXCEPTION 'execution plan identity/version immutable'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_execution_plan_guard BEFORE INSERT OR UPDATE ON engineering_execution_plans FOR EACH ROW EXECUTE FUNCTION satco_execution_plan_guard();

    CREATE FUNCTION satco_execution_child_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE root engineering_execution_plans%ROWTYPE; ws_project integer;
    BEGIN
      SELECT * INTO root FROM engineering_execution_plans WHERE id=NEW.plan_id FOR SHARE;
      IF root.id IS NULL OR NEW.organization_id IS DISTINCT FROM root.organization_id OR (TG_TABLE_NAME IN ('engineering_execution_activities','engineering_execution_milestones') AND NEW.project_id IS DISTINCT FROM root.project_id) THEN RAISE EXCEPTION 'execution child scope mismatch'; END IF;
      IF TG_TABLE_NAME='engineering_execution_activities' THEN
        IF NEW.workspace_id IS NOT NULL THEN SELECT project_id INTO ws_project FROM engineering_workspaces WHERE id=NEW.workspace_id FOR SHARE; IF ws_project IS DISTINCT FROM root.project_id THEN RAISE EXCEPTION 'execution activity workspace mismatch'; END IF; END IF;
        IF NEW.responsible_user_id IS NOT NULL AND NEW.responsible_user_id IS DISTINCT FROM (SELECT owner_id FROM projects WHERE id=root.project_id) AND NEW.responsible_user_id IS DISTINCT FROM (SELECT primary_assignee_id FROM projects WHERE id=root.project_id) THEN RAISE EXCEPTION 'execution activity responsible user invalid'; END IF;
        IF TG_OP='INSERT' AND (NEW.standing <> 'planned' OR NEW.version <> 1 OR NEW.blocker_rationale IS NOT NULL OR NEW.blocked_return_standing IS NOT NULL OR NEW.completion_rationale IS NOT NULL) THEN RAISE EXCEPTION 'invalid initial execution activity state'; END IF;
        IF TG_OP='UPDATE' THEN
          IF OLD.standing IN ('completed','cancelled') AND (NEW.standing IS DISTINCT FROM OLD.standing OR NEW.title IS DISTINCT FROM OLD.title OR NEW.description IS DISTINCT FROM OLD.description OR NEW.completion_basis IS DISTINCT FROM OLD.completion_basis) THEN RAISE EXCEPTION 'execution activity terminal immutable'; END IF;
          IF NEW.version <> OLD.version + 1 THEN RAISE EXCEPTION 'execution activity update requires version increment'; END IF;
          IF NEW.standing IS DISTINCT FROM OLD.standing THEN
            IF (OLD.standing='planned' AND NEW.standing NOT IN ('ready','blocked','cancelled')) OR (OLD.standing='ready' AND NEW.standing NOT IN ('in_progress','blocked','cancelled')) OR (OLD.standing='in_progress' AND NEW.standing NOT IN ('completed','blocked','cancelled')) OR (OLD.standing='blocked' AND NEW.standing NOT IN (OLD.blocked_return_standing,'cancelled')) THEN RAISE EXCEPTION 'invalid execution activity transition'; END IF;
            IF NEW.standing IN ('ready','in_progress','completed') AND EXISTS (SELECT 1 FROM engineering_execution_dependencies d JOIN engineering_execution_activities prerequisite ON prerequisite.id=d.predecessor_activity_id WHERE d.plan_id=NEW.plan_id AND d.dependent_activity_id=NEW.id AND prerequisite.standing NOT IN ('completed','cancelled')) THEN RAISE EXCEPTION 'execution activity dependency unsatisfied'; END IF;
          END IF;
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_execution_activity_guard BEFORE INSERT OR UPDATE ON engineering_execution_activities FOR EACH ROW EXECUTE FUNCTION satco_execution_child_guard();
    CREATE TRIGGER trg_execution_milestone_guard BEFORE INSERT OR UPDATE ON engineering_execution_milestones FOR EACH ROW EXECUTE FUNCTION satco_execution_child_guard();

    CREATE FUNCTION satco_execution_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE activity engineering_execution_activities%ROWTYPE;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'execution activity history immutable'; END IF;
      SELECT * INTO activity FROM engineering_execution_activities WHERE id=NEW.activity_id FOR SHARE;
      IF activity.id IS NULL OR activity.plan_id IS DISTINCT FROM NEW.plan_id OR activity.organization_id IS DISTINCT FROM NEW.organization_id OR activity.standing IS DISTINCT FROM NEW.to_standing OR activity.version IS DISTINCT FROM NEW.activity_version THEN RAISE EXCEPTION 'execution history root mismatch'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_execution_history_guard BEFORE INSERT OR UPDATE OR DELETE ON engineering_execution_activity_history FOR EACH ROW EXECUTE FUNCTION satco_execution_history_guard();

    CREATE FUNCTION satco_execution_activity_history_presence_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM engineering_execution_activity_history h WHERE h.activity_id=NEW.id AND h.activity_version=NEW.version AND h.plan_id=NEW.plan_id AND h.organization_id=NEW.organization_id) THEN RAISE EXCEPTION 'execution activity version requires history'; END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER trg_execution_activity_history_presence AFTER INSERT OR UPDATE ON engineering_execution_activities DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_execution_activity_history_presence_guard();

    CREATE FUNCTION satco_execution_revision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE root engineering_execution_plans%ROWTYPE;
    BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'execution revision immutable'; END IF;
      SELECT * INTO root FROM engineering_execution_plans WHERE id=NEW.plan_id FOR SHARE;
      IF root.id IS NULL OR root.organization_id IS DISTINCT FROM NEW.organization_id OR root.version IS DISTINCT FROM NEW.revision_number OR jsonb_typeof(NEW.config_json) <> 'object' OR NEW.config_digest !~ '^[0-9a-f]{{64}}$' THEN RAISE EXCEPTION 'execution revision invalid'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_execution_revision_guard BEFORE INSERT OR UPDATE OR DELETE ON engineering_execution_plan_revisions FOR EACH ROW EXECUTE FUNCTION satco_execution_revision_guard();

    CREATE FUNCTION satco_execution_revision_presence_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM engineering_execution_plan_revisions r WHERE r.plan_id=NEW.id AND r.organization_id=NEW.organization_id AND r.revision_number=NEW.version) THEN RAISE EXCEPTION 'execution plan version requires revision'; END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER trg_execution_revision_presence AFTER INSERT OR UPDATE ON engineering_execution_plans DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION satco_execution_revision_presence_guard();

    CREATE FUNCTION satco_execution_link_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE milestone engineering_execution_milestones%ROWTYPE; activity engineering_execution_activities%ROWTYPE;
    BEGIN
      SELECT * INTO milestone FROM engineering_execution_milestones WHERE id=NEW.milestone_id FOR SHARE;
      SELECT * INTO activity FROM engineering_execution_activities WHERE id=NEW.activity_id FOR SHARE;
      IF milestone.id IS NULL OR activity.id IS NULL OR milestone.plan_id IS DISTINCT FROM activity.plan_id OR milestone.organization_id IS DISTINCT FROM NEW.organization_id OR activity.organization_id IS DISTINCT FROM NEW.organization_id THEN RAISE EXCEPTION 'execution milestone link mismatch'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_execution_link_guard BEFORE INSERT OR UPDATE ON engineering_execution_milestone_activities FOR EACH ROW EXECUTE FUNCTION satco_execution_link_guard();

    CREATE FUNCTION satco_execution_dependency_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE predecessor engineering_execution_activities%ROWTYPE; dependent engineering_execution_activities%ROWTYPE;
    BEGIN
      SELECT * INTO predecessor FROM engineering_execution_activities WHERE id=NEW.predecessor_activity_id FOR SHARE;
      SELECT * INTO dependent FROM engineering_execution_activities WHERE id=NEW.dependent_activity_id FOR SHARE;
      IF predecessor.id IS NULL OR dependent.id IS NULL OR predecessor.plan_id IS DISTINCT FROM NEW.plan_id OR dependent.plan_id IS DISTINCT FROM NEW.plan_id OR predecessor.organization_id IS DISTINCT FROM NEW.organization_id OR dependent.organization_id IS DISTINCT FROM NEW.organization_id THEN RAISE EXCEPTION 'execution dependency scope mismatch'; END IF;
      IF EXISTS (WITH RECURSIVE reachable(id) AS (SELECT d.dependent_activity_id FROM engineering_execution_dependencies d WHERE d.plan_id=NEW.plan_id AND d.predecessor_activity_id=NEW.dependent_activity_id UNION SELECT d.dependent_activity_id FROM engineering_execution_dependencies d JOIN reachable r ON d.predecessor_activity_id=r.id WHERE d.plan_id=NEW.plan_id) SELECT 1 FROM reachable WHERE id=NEW.predecessor_activity_id) THEN RAISE EXCEPTION 'execution dependency cycle'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_execution_dependency_guard BEFORE INSERT OR UPDATE ON engineering_execution_dependencies FOR EACH ROW EXECUTE FUNCTION satco_execution_dependency_guard();

    ALTER TABLE engineering_execution_plans OWNER TO satco; ALTER TABLE engineering_execution_plan_revisions OWNER TO satco; ALTER TABLE engineering_execution_activities OWNER TO satco; ALTER TABLE engineering_execution_activity_history OWNER TO satco; ALTER TABLE engineering_execution_milestones OWNER TO satco; ALTER TABLE engineering_execution_milestone_activities OWNER TO satco; ALTER TABLE engineering_execution_dependencies OWNER TO satco; ALTER TABLE engineering_execution_idempotency OWNER TO satco;
    ALTER FUNCTION satco_execution_plan_guard() OWNER TO satco; ALTER FUNCTION satco_execution_child_guard() OWNER TO satco; ALTER FUNCTION satco_execution_history_guard() OWNER TO satco; ALTER FUNCTION satco_execution_activity_history_presence_guard() OWNER TO satco; ALTER FUNCTION satco_execution_revision_guard() OWNER TO satco; ALTER FUNCTION satco_execution_revision_presence_guard() OWNER TO satco; ALTER FUNCTION satco_execution_link_guard() OWNER TO satco; ALTER FUNCTION satco_execution_dependency_guard() OWNER TO satco;
    REVOKE ALL ON FUNCTION satco_execution_plan_guard(),satco_execution_child_guard(),satco_execution_history_guard(),satco_execution_activity_history_presence_guard(),satco_execution_revision_guard(),satco_execution_revision_presence_guard(),satco_execution_link_guard(),satco_execution_dependency_guard() FROM PUBLIC,satco_runtime;
    GRANT SELECT,INSERT,UPDATE ON engineering_execution_plans,engineering_execution_activities,engineering_execution_milestones TO satco_runtime;
    GRANT SELECT,INSERT,DELETE ON engineering_execution_milestone_activities,engineering_execution_dependencies TO satco_runtime;
    GRANT SELECT,INSERT ON engineering_execution_plan_revisions,engineering_execution_activity_history,engineering_execution_idempotency TO satco_runtime;
    """)


def downgrade():
    for trigger, table in (
        ("trg_execution_dependency_guard", "engineering_execution_dependencies"), ("trg_execution_link_guard", "engineering_execution_milestone_activities"),
        ("trg_execution_revision_guard", "engineering_execution_plan_revisions"), ("trg_execution_history_guard", "engineering_execution_activity_history"),
        ("trg_execution_activity_history_presence", "engineering_execution_activities"), ("trg_execution_revision_presence", "engineering_execution_plans"),
        ("trg_execution_milestone_guard", "engineering_execution_milestones"), ("trg_execution_activity_guard", "engineering_execution_activities"),
        ("trg_execution_plan_guard", "engineering_execution_plans"),
    ): op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON {table}")
    for function in ("satco_execution_dependency_guard", "satco_execution_link_guard", "satco_execution_revision_presence_guard", "satco_execution_revision_guard", "satco_execution_activity_history_presence_guard", "satco_execution_history_guard", "satco_execution_child_guard", "satco_execution_plan_guard"):
        op.execute(f"DROP FUNCTION IF EXISTS {function}()")
    op.drop_index("ix_execution_dependency_dependent", table_name="engineering_execution_dependencies"); op.drop_table("engineering_execution_dependencies")
    op.drop_table("engineering_execution_milestone_activities")
    op.drop_index("uq_execution_milestone_title", table_name="engineering_execution_milestones"); op.drop_index("ix_execution_milestone_order", table_name="engineering_execution_milestones"); op.drop_table("engineering_execution_milestones")
    op.drop_index("ix_execution_activity_history_order", table_name="engineering_execution_activity_history"); op.drop_table("engineering_execution_activity_history")
    op.drop_index("uq_execution_activity_title", table_name="engineering_execution_activities"); op.drop_index("ix_execution_activity_order", table_name="engineering_execution_activities"); op.drop_table("engineering_execution_activities")
    op.drop_table("engineering_execution_idempotency")
    op.drop_index("ix_execution_plan_revision_order", table_name="engineering_execution_plan_revisions"); op.drop_table("engineering_execution_plan_revisions")
    op.drop_index("ix_execution_plan_scope", table_name="engineering_execution_plans"); op.drop_table("engineering_execution_plans")
