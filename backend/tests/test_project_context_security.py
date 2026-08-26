from app.schemas.project_context import ProjectContextActor,ProjectContextRequest,ProjectContextScope,ProjectContextProtectedNotFound
from app.services.project_context_service import ProjectContextService
class O:
 def __getattr__(self,n): return lambda **k: None
class U: id=2
def test_actor_mismatch_is_payload_free():
 r=ProjectContextService(O()).assemble_project_context(actor=ProjectContextActor(actor_id=1,organization_id="00000000-0000-0000-0000-000000000001"),request=ProjectContextRequest(scope=ProjectContextScope(project_id=1)),current_user=U())
 assert isinstance(r,ProjectContextProtectedNotFound)
