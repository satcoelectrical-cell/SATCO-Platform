import hashlib
import re

from app.services.project_completeness_service import (
    CATALOG_ID,
    CATALOG_RULES_V1,
    CATALOG_VERSION,
    MAX_EKG_CALLS,
    catalog_canonical_json,
    catalog_descriptor,
    catalog_digest,
)


def test_exact_catalog_identity_order_versions_and_digest_are_stable():
    assert CATALOG_ID == "project_completeness.v1"
    assert CATALOG_VERSION == 1
    assert len(CATALOG_RULES_V1) == 14
    assert tuple(rule.ordinal for rule in CATALOG_RULES_V1) == tuple(range(1, 15))
    ids = tuple(rule.rule_id for rule in CATALOG_RULES_V1)
    assert ids == tuple(sorted(ids))
    assert len(set(ids)) == 14
    assert all(rule.rule_version == 1 and rule.graph_requirement is None for rule in CATALOG_RULES_V1)
    assert catalog_canonical_json() == catalog_canonical_json()
    assert catalog_digest() == hashlib.sha256(catalog_canonical_json()).hexdigest()
    assert catalog_descriptor().catalog_digest == catalog_digest()


def test_every_rule_has_closed_metadata_and_fixed_templates():
    for rule in CATALOG_RULES_V1:
        assert rule.required_sections
        assert rule.applicability.code
        assert rule.predicate.code
        assert rule.question_template == rule.question_template
        assert rule.checklist_template == rule.checklist_template
    assert MAX_EKG_CALLS == 0


def test_catalog_text_has_no_ai_score_or_solution_recommendation_language():
    text = " ".join(
        " ".join((rule.title, rule.description, rule.question_template, rule.checklist_template)).lower()
        for rule in CATALOG_RULES_V1
    )
    for forbidden in (r"recommend", r"material", r"vendor", r"\bbom\b", r"optimiz", r"score", r"percentage", r"\bmodel\b", r"\bai\b"):
        assert re.search(forbidden, text) is None
