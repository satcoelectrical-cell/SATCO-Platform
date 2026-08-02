from app.api.v1.routers.evidence import router
def test_only_approved_evidence_routes_exist():
    paths={r.path for r in router.routes if "evidence" in getattr(r,"path","")}
    assert paths=={"/evidence","/evidence/{evidence_id}","/projects/{project_id}/evidence","/evidence/{evidence_id}/lifecycle-transitions"}
