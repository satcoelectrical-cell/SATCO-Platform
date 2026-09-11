from app.api.v1.routers.cross_discipline_intelligence import router
from app.schemas.cross_discipline_intelligence import (
    AssessmentCreate, DispositionAppend, EligibilityQuery, ReassessmentCreate,
    SupersessionCreate, VerificationQuery, XDIModel,
)


EXPECTED_OPERATIONS = {
    "list_cross_discipline_definitions",
    "get_cross_discipline_runtime_readiness",
    "evaluate_cross_discipline_eligibility",
    "create_cross_discipline_assessment",
    "get_cross_discipline_assessment",
    "list_cross_discipline_assessments",
    "list_cross_discipline_findings",
    "get_cross_discipline_finding",
    "append_finding_disposition",
    "list_finding_dispositions",
    "get_assessment_lineage",
    "verify_historical_assessment",
    "create_cross_discipline_reassessment",
    "supersede_cross_discipline_assessment",
    "get_finding_dependency_explanation",
    "create_cross_discipline_potential_impact",
    "get_cross_discipline_report_projection",
    "create_cross_discipline_ai_explanation",
    "get_cross_discipline_integrated_path",
}


def test_batch_five_exposes_exact_19_operations():
    operations = {
        route.operation_id for route in router.routes
        if getattr(route, "operation_id", None)
        and "/cross-discipline" in getattr(route, "path", "")
    }
    assert operations == EXPECTED_OPERATIONS
    assert len(operations) == 19


def test_all_transport_models_are_strict_and_frozen():
    for model in (
        AssessmentCreate, DispositionAppend, EligibilityQuery,
        ReassessmentCreate, SupersessionCreate, VerificationQuery,
    ):
        assert model.model_config["extra"] == "forbid"
        assert model.model_config["frozen"] is True
