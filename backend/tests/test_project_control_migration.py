from alembic.config import Config
from alembic.script import ScriptDirectory
from conftest import TEST_DATABASE_REVISION
def test_project_control_migration_has_exact_parent_and_sole_head():
    script=ScriptDirectory.from_config(Config("alembic.ini")); head=script.get_revision("e04700000001")
    assert script.get_current_head()==TEST_DATABASE_REVISION and head.down_revision=="e04600000001"
